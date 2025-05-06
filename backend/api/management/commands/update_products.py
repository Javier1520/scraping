import sys
import os
from pathlib import Path
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from api.models import SearchQuery, Product

# --- Add scraping directory to sys.path (same as in views.py) ---
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent # api/management/commands -> backend
SCRAPING_DIR = BACKEND_DIR.parent / 'scraping'

if str(SCRAPING_DIR) not in sys.path:
    sys.path.insert(0, str(SCRAPING_DIR))

try:
    from scraper import search_mercadolibre
except ImportError as e:
    print(f"Error importing scraper: {e}")
    def search_mercadolibre(search_param, page=1):
        print("Scraper function not available.")
        return []
# --- End Path Setup ---


class Command(BaseCommand):
    help = 'Periodically updates product data for existing search terms by re-scraping.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting product update process...'))

        search_queries = SearchQuery.objects.all()
        if not search_queries.exists():
            self.stdout.write('No search terms found in the database to update.')
            return

        for query in search_queries:
            self.stdout.write(f"Processing search term: '{query.search_term}' (up to page {query.max_page_scraped})")
            if query.max_page_scraped == 0:
                self.stdout.write(f"Skipping '{query.search_term}' as max_page_scraped is 0.")
                continue

            successful_pages = 0
            total_products_added = 0
            # We re-scrape all pages known for this query
            pages_to_update = range(1, query.max_page_scraped + 1)

            # Option 1: Delete old products before adding new ones (clean refresh)
            # Product.objects.filter(search_query=query, page__in=pages_to_update).delete()
            # self.stdout.write(f"Deleted existing products for pages {pages_to_update.start}-{pages_to_update.stop - 1}")

            # Option 2: Use ignore_conflicts (adds new, leaves existing duplicates)
            # Current implementation uses this approach via bulk_create below.

            with transaction.atomic():
                for page_num in pages_to_update:
                    self.stdout.write(f"  Scraping page {page_num}...")
                    try:
                        # Add a small delay to avoid overwhelming the target site
                        time.sleep(1) # Adjust delay as needed

                        scraped_data = search_mercadolibre(query.search_term, page_num)
                        if not scraped_data:
                            self.stdout.write(f"  No data returned for page {page_num}. Might indicate end of results or issue.")
                            # Optionally break if no data found on a page < max_page_scraped
                            # break
                            continue # Continue to next page

                        products_to_create = []
                        for item in scraped_data:
                            products_to_create.append(
                                Product(
                                    search_query=query,
                                    page=page_num,
                                    title=item.get('title', 'N/A'),
                                    price=item.get('price', 'N/A'),
                                    seller=item.get('seller'),
                                    reviews=item.get('reviews'),
                                    image_url=item.get('image_url')
                                )
                            )

                        if products_to_create:
                            # If using Option 1 (delete first), remove ignore_conflicts=True
                            added_count = len(Product.objects.bulk_create(products_to_create, ignore_conflicts=True))
                            total_products_added += added_count # Note: bulk_create might not return accurate count with ignore_conflicts
                            self.stdout.write(f"  Stored/updated products from page {page_num}. Approx count: {len(products_to_create)}")
                            successful_pages += 1
                        else:
                            self.stdout.write(f"  Scraper returned empty list for page {page_num}.")

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"  Error scraping/saving page {page_num} for '{query.search_term}': {e}"))
                        # Decide whether to continue to the next page or stop for this query
                        # continue
                        break # Stop updating this query on error

                # Update the timestamp regardless of whether all pages succeeded,
                # as an update attempt was made.
                query.last_updated = timezone.now()
                query.save()
                self.stdout.write(f"Finished processing '{query.search_term}'. Successfully processed {successful_pages}/{len(pages_to_update)} pages.")

        self.stdout.write(self.style.SUCCESS('Product update process finished.'))