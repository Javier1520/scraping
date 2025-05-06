# AWS EC2 + RDS + Nginx Deployment Steps

This document outlines the general steps to deploy the Django application to an AWS EC2 instance using RDS for the PostgreSQL database and Nginx as a reverse proxy.

## 1. AWS Setup

*   **RDS PostgreSQL Instance:**
    *   Create a PostgreSQL instance on AWS RDS.
    *   Configure security groups to allow connections from your EC2 instance (typically on port 5432).
    *   Note the database endpoint, username, password, and database name.
*   **EC2 Instance:**
    *   Launch an EC2 instance (e.g., Ubuntu).
    *   Configure security groups to allow inbound traffic on ports 80 (HTTP) and 443 (HTTPS, if applicable), and SSH (port 22) from your IP.
    *   Associate an Elastic IP address (optional but recommended).

## 2. Server Setup (EC2 Instance)

*   **Connect via SSH:** Connect to your EC2 instance.
*   **Update System:**
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```
*   **Install Required Packages:**
    ```bash
    sudo apt install -y python3-pip python3-dev python3-venv libpq-dev postgresql postgresql-contrib nginx curl
    ```
*   **Clone Project:** Clone your project repository onto the server.
    ```bash
    git clone <your-repo-url>
    cd <your-project-directory>/backend
    ```
*   **Create Virtual Environment:**
    ```bash
    python3 -m venv ../venv # Create venv outside backend
    source ../venv/bin/activate
    ```
*   **Install Dependencies:**
    ```bash
    pip install pipenv
    pipenv install --system --deploy # Installs dependencies from Pipfile.lock into the system Python within the venv
    # OR, if you prefer not using --system:
    # pipenv install --deploy
    # You might need to adjust Gunicorn/Nginx paths accordingly
    ```

## 3. Application Configuration

*   **Environment Variables:**
    *   Create a `.env` file in the `backend` directory.
    *   Copy the contents from `.env.example`.
    *   Fill in the actual values, **especially:**
        *   `SECRET_KEY` (generate a new strong key: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' `)
        *   `DEBUG=False`
        *   `ALLOWED_HOSTS` (your EC2 instance's public IP and/or domain name, e.g., `ALLOWED_HOSTS=your_domain.com,xx.xx.xx.xx`)
        *   `DATABASE_URL` (using the RDS instance details: `postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/DB_NAME`)
*   **Static Files:**
    ```bash
    # Ensure STATIC_ROOT is set in settings.py if not already
    # STATIC_ROOT = BASE_DIR / 'staticfiles'
    python manage.py collectstatic --noinput
    ```
*   **Database Migrations:**
    ```bash
    python manage.py migrate --noinput
    ```
*   **Create Superuser (Optional):**
    ```bash
    python manage.py createsuperuser
    ```

## 4. Gunicorn Setup (Application Server)

*   **Test Gunicorn:**
    ```bash
    # Make sure you are in the backend directory and venv is active
    # pipenv run gunicorn --bind 0.0.0.0:8000 core.wsgi:application
    # Or if using --system install:
    gunicorn --bind 0.0.0.0:8000 core.wsgi:application
    ```
    Access `http://<your-ec2-ip>:8000` in your browser to test. Stop Gunicorn (Ctrl+C).
*   **Create Gunicorn Socket and Service (Systemd):**
    *   Create `/etc/systemd/system/gunicorn.socket`:
        ```ini
        [Unit]
        Description=gunicorn socket

        [Socket]
        ListenStream=/run/gunicorn.sock # Matches Nginx config

        [Install]
        WantedBy=sockets.target
        ```
    *   Create `/etc/systemd/system/gunicorn.service` (adjust paths and user):
        ```ini
        [Unit]
        Description=gunicorn daemon
        Requires=gunicorn.socket
        After=network.target

        [Service]
        User=ubuntu # Or your deployment user
        Group=www-data # Or your deployment group
        WorkingDirectory=/path/to/your/project/backend
        ExecStart=/path/to/your/venv/bin/gunicorn \
                  --access-logfile - \
                  --workers 3 \
                  --bind unix:/run/gunicorn.sock \
                  core.wsgi:application

        [Install]
        WantedBy=multi-user.target
        ```
    *   Start and enable Gunicorn:
        ```bash
        sudo systemctl start gunicorn.socket
        sudo systemctl enable gunicorn.socket
        sudo systemctl status gunicorn.socket # Check it's active
        # If status looks okay, Gunicorn service will start on first connection
        # Or start it manually to test: sudo systemctl start gunicorn
        sudo systemctl status gunicorn # Check service status
        # Check for errors if needed:
        # sudo journalctl -u gunicorn
        # sudo journalctl -u gunicorn.socket
        ```

## 5. Nginx Setup

*   **Create Nginx Configuration:**
    *   Copy or create your Nginx configuration (like the one in `deploy/nginx.conf`).
    *   Place it in `/etc/nginx/sites-available/your_project`.
    *   **Crucially, update:**
        *   `server_name` to your domain or IP.
        *   The `server unix:...` path in the `upstream` block to match the Gunicorn socket (`/run/gunicorn.sock`).
        *   The `alias /path/to/your/project/staticfiles/` path to your actual static files directory (e.g., `/path/to/your/project/backend/staticfiles/`).
        *   The `alias /path/to/your/project/media/` path if you use media files.
*   **Enable Site:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/your_project /etc/nginx/sites-enabled/
    sudo nginx -t # Test configuration
    ```
*   **Restart Nginx:**
    ```bash
    sudo systemctl restart nginx
    ```
*   **Firewall (if using ufw):**
    ```bash
    sudo ufw allow 'Nginx Full' # Or specific ports if needed
    ```
    **Crontab**
    ```bash
    contrab -e
    ```
    ```#cronjob to log in cron.log
    #* * * * * /home/javier/.local/share/virtualenvs/backend-uLGiGImz/bin/python /home/javier/projects/scraping/backend/manage.py update_products >> /home/javier/projects/scraping/backend/cron.log 2>&1
    ```

## 6. Access Your Site

Navigate to your EC2 instance's public IP address or your domain name in a web browser. You should see your Django application served via Nginx and Gunicorn.

## 7. HTTPS (Recommended)

Use Let's Encrypt with Certbot to easily set up free SSL certificates:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com # Follow prompts
# Test automatic renewal
sudo certbot renew --dry-run
```
Certbot should automatically update your Nginx configuration for HTTPS.