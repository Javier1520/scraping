# Django Project

This is a Django project that requires Python 3.10 and Pipenv for dependency management.

## Prerequisites

- Python 3.10 installed
- [Pipenv](https://pipenv.pypa.io/en/latest/) installed

To install Pipenv:

```bash
pip install pipenv
```

## Setup Instructions

1. **Enter the Pipenv shell:**

   ```bash
   pipenv shell
   ```

2. **Install dependencies (run this inside the folder containing the `Pipfile`):**

   ```bash
   pipenv install
   ```

3. **Set the Python interpreter in your code editor (e.g., press `F1` in VS Code and search for "Python: Select Interpreter"). Choose the one from Pipenv.**

4. **Create a `.env` file in the root directory with the following content:**

   > You can delete the PostgreSQL-related variables if you're using SQLite (which is the default).

   ```env
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost

   # PostgreSQL Database Configuration
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

5. **Run the Django project:**

   ```bash
   python manage.py runserver
   ```

## Notes

* If PostgreSQL variables are not provided, the project will default to using SQLite.

```

```


![architecture](https://github.com/user-attachments/assets/b81de59b-545c-449f-ba34-61f522bc30e9)
