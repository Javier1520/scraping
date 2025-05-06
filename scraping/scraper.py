import requests
from bs4 import BeautifulSoup

def search_mercadolibre(search_param, page=1):
    base_url = 'https://listado.mercadolibre.com.co/'
    offset = (page - 1) * 48 + 1
    search_url = f'{base_url}{search_param}_Desde_{offset}_NoIndex_True'

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        )
    }

    print(f"Requesting URL: {search_url}")
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('li', class_='ui-search-layout__item')
        print(f"Found {len(items)} items on page {page} for '{search_param}'")

        if not items:
            print(f"No items found matching the selector on page {page} for '{search_param}'.")
            return []

        results = []
        for item in items:
            title_tag = item.find('a', class_='poly-component__title')
            price_tag = item.find('span', class_='andes-money-amount andes-money-amount--cents-superscript')
            seller_tag = item.find('span', class_='poly-component__seller')
            reviews_tag = item.find('span', class_='andes-visually-hidden')
            image_tag = item.find('img', class_='poly-component__picture')

            results.append({
                'title': title_tag.get_text(strip=True) if title_tag else 'No title',
                'price': price_tag.get_text(strip=True) if price_tag else 'No price',
                'seller': seller_tag.get_text(strip=True) if seller_tag else 'No seller info',
                'reviews': reviews_tag.get_text(strip=True) if reviews_tag else 'No reviews',
                'image_url': (
                    image_tag.get('src') if image_tag and image_tag.has_attr('src') else 'No image'
                )
            })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error during request for page {page} of '{search_param}': {e}")
        return []
    except Exception as e:
        print(f"Unexpected error while parsing page {page} of '{search_param}': {e}")
        return []
