Here's a concise `README.md` explaining the five extracted fields from the `search_mercadolibre` function, including their purpose and fallback values:

````markdown
# MercadoLibre Scraper

This script scrapes product data from [MercadoLibre Colombia](https://listado.mercadolibre.com.co/) based on a search term and page number.

## Extracted Fields

The following five fields are extracted from each product listing:

| Field       | Description                                      | Fallback         |
|-------------|--------------------------------------------------|------------------|
| `title`     | The product title (`a.poly-component__title`)    | `'No title'`     |
| `price`     | The product price (`span.andes-money-amount...`) | `'No price'`     |
| `seller`    | Seller or store name (`span.poly-component__seller`) | `'No seller info'` |
| `reviews`   | Text reviews count or rating (`span.andes-visually-hidden`) | `'No reviews'` |
| `image_url` | URL of the product image (`img.poly-component__picture`) | `'No image'` |

> Note: `image_url` is a direct link to the product image. All fields are scraped using BeautifulSoup and have safe fallback values to avoid `NoneType` errors.

## Example Usage

```python
results = search_mercadolibre("laptop", page=1)
for item in results:
    print(item['title'], item['price'], item['image_url'])
````

The function automatically handles pagination and user-agent headers.
