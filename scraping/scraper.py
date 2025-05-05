import requests
from bs4 import BeautifulSoup

def search_mercadolibre(search_param, page=1):
    url = 'https://listado.mercadolibre.com.co/'
    # Ensure page calculation is correct for MercadoLibre's _Desde_ parameter
    # Page 1: _Desde_1 ( (1-1)*48 + 1 )
    # Page 2: _Desde_49 ( (2-1)*48 + 1 )
    # Page 3: _Desde_97 ( (3-1)*48 + 1 )
    offset = (page - 1) * 48 + 1
    search_query = f'{url}{search_param}_Desde_{offset}_NoIndex_True'

    headers = {
        # Using a more generic user agent is sometimes better
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"Requesting URL: {search_query}") # Added for debugging
    try:
        response = requests.get(search_query, headers=headers, timeout=10) # Added timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('li', class_='ui-search-layout__item')
        print(f"Found {len(items)} items on page {page} for '{search_param}'") # Added for debugging

        if not items:
             # Handle cases where no items are found, even with a 200 status
             # This could happen if the page exists but has no results matching the selector
             print(f"No items found matching the selector on page {page} for '{search_param}'.")
             return []

        results = []
        for item in items:
            # Use .get_text(strip=True) for cleaner text extraction
            # Add error handling for missing elements using try-except or conditional checks
            title_tag = item.find('h2', class_='ui-search-item__title')
            title = title_tag.get_text(strip=True) if title_tag else 'No title'

            price_tag = item.find('span', class_='andes-money-amount__fraction')
            price_cents_tag = item.find('span', class_='andes-money-amount__cents')
            price = f"{price_tag.get_text(strip=True)}{'.' + price_cents_tag.get_text(strip=True) if price_cents_tag else ''}" if price_tag else 'No price'

            # Seller info might be nested differently, adjust selector if needed
            seller_tag = item.find('p', class_='ui-search-official-store-label') or item.find('span', class_='ui-search-item__vendor-text') # Example alternative selector
            seller = seller_tag.get_text(strip=True) if seller_tag else 'No seller info'

            # Reviews might be complex, this selector might need refinement based on actual HTML structure
            reviews_tag = item.find('span', class_='ui-search-reviews__rating-number')
            reviews_count_tag = item.find('span', class_='ui-search-reviews__amount')
            reviews = f"{reviews_tag.get_text(strip=True)} ({reviews_count_tag.get_text(strip=True)})" if reviews_tag and reviews_count_tag else 'No reviews'


            image_tag = item.find('img', class_='ui-search-result-image__element') # Adjusted selector potentially
            # Use 'data-src' if 'src' is for a placeholder
            image_url = image_tag['data-src'] if image_tag and 'data-src' in image_tag.attrs else (image_tag['src'] if image_tag and 'src' in image_tag.attrs else 'No image')

            results.append({
                'title': title,
                'price': price,
                'seller': seller,
                'reviews': reviews, # This might need more sophisticated parsing
                'image_url': image_url
            })
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error during request for page {page} of '{search_param}': {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while parsing page {page} of '{search_param}': {e}")
        # Consider logging the specific item causing the error if possible
        return [] # Or handle partially scraped data if appropriate

# Example usage remains for direct script execution
if __name__ == "__main__":
    search_term = 'taladro'
    page_num = 1 # Changed variable name for clarity
    scraped_results = search_mercadolibre(search_term, page_num)
    if scraped_results:
        print(f"
--- Results for '{search_term}', Page {page_num} ---")
        for i, result in enumerate(scraped_results, 1):
            print(f"{i}. Title: {result['title']}")
            print(f"   Price: {result['price']}")
            print(f"   Seller: {result['seller']}")
            print(f"   Reviews: {result['reviews']}")
            print(f"   Image URL: {result['image_url']}
")
    else:
        print(f"No results found or error occurred for '{search_term}', page {page_num}.")