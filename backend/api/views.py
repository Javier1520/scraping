from django.shortcuts import render
import sys
import os
import csv
import io
from pathlib import Path
import time

from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import SearchQuery, Product
# from .serializers import ProductSerializer # Not strictly needed for CSV export

# --- Dynamically add scraping directory to sys.path ---
# Calculate the path to the directory containing the scraping script
# Assumes backend/ and scraping/ are siblings in the project root
BACKEND_DIR = Path(__file__).resolve().parent.parent
SCRAPING_DIR = BACKEND_DIR.parent / 'scraping'

if str(SCRAPING_DIR) not in sys.path:
    sys.path.insert(0, str(SCRAPING_DIR))

try:
    from scraper import search_mercadolibre
except ImportError as e:
    # Handle case where scraper.py might be missing or has issues
    print(f"Error importing scraper: {e}")
    # Define a dummy function or raise a more specific error if crucial
    def search_mercadolibre(search_param, page=1):
        print("Scraper function not available.")
        return []

# --- API View ---

class ProductDataView(APIView):
    """
    API endpoint to retrieve product data for a search term.

    Requires 'search_term' and 'pages_required' query parameters.
    If data is not available or insufficient in the DB, it triggers
    the scraping process, stores the results, and then returns
    the data as a CSV file.
    """

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search_term')
        pages_required_str = request.query_params.get('pages_required')

        if not search_term:
            return Response({"error": "'search_term' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not pages_required_str:
            return Response({"error": "'pages_required' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pages_required = int(pages_required_str)
            if pages_required <= 0:
                raise ValueError("Pages required must be positive.")
        except ValueError:
            return Response({"error": "'pages_required' must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Data Fetching/Scraping Logic ---
        try:
            search_query, created = SearchQuery.objects.get_or_create(
                search_term=search_term.lower() # Store search terms consistently
            )

            pages_to_scrape = []
            if search_query.max_page_scraped < pages_required:
                pages_to_scrape = range(search_query.max_page_scraped + 1, pages_required + 1)

            if pages_to_scrape:
                print(f"Scraping required for '{search_term}' pages {pages_to_scrape.start} to {pages_to_scrape.stop - 1}")
                max_page_successfully_scraped = search_query.max_page_scraped

                with transaction.atomic(): # Ensure DB operations are atomic per request
                    for page_num in pages_to_scrape:
                        print(f"Scraping page {page_num} for '{search_term}'...")
                        try:
                            # Add a small delay between requests
                            time.sleep(1)
                            scraped_data = search_mercadolibre(search_term, page_num)

                            # --- Debug Print ---
                            print(f"Scraper returned for page {page_num}: {type(scraped_data)}, Length: {len(scraped_data) if isinstance(scraped_data, list) else 'N/A'}")
                            if isinstance(scraped_data, list) and len(scraped_data) > 0:
                                print(f"First item sample: {scraped_data[0]}")
                            # --- End Debug Print ---

                            if not scraped_data:
                                print(f"No data returned from scraper for page {page_num}. Stopping scrape for this request.")
                                # Don't update max_page_scraped beyond the last successful page
                                break # Stop trying to scrape further pages for this request

                            products_to_create = []
                            for item in scraped_data:
                                # Basic validation/cleaning could happen here if needed
                                products_to_create.append(
                                    Product(
                                        search_query=search_query,
                                        page=page_num,
                                        title=item.get('title', 'N/A'),
                                        price=item.get('price', 'N/A'),
                                        seller=item.get('seller'),
                                        reviews=item.get('reviews'),
                                        image_url=item.get('image_url')
                                    )
                                )

                            if products_to_create:
                                # Use bulk_create for efficiency
                                # ignore_conflicts=True handles the unique_together constraint gracefully
                                # if an identical product is scraped again (e.g., during updates)
                                Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
                                print(f"Stored {len(products_to_create)} products from page {page_num}.")
                                max_page_successfully_scraped = page_num # Update highest successful page
                            else:
                                # If scraper returns empty list but no error, still treat as end of results
                                print(f"Scraper returned empty list for page {page_num}. Assuming no more results.")
                                break

                        except Exception as e:
                            # Catch exceptions during scraping/saving for a specific page
                            print(f"Error scraping or saving page {page_num} for '{search_term}': {e}")
                            # Decide if you want to stop entirely or just skip this page
                            # For now, we stop scraping further for this request on error
                            break

                    # Update SearchQuery only after attempting all required pages
                    if max_page_successfully_scraped > search_query.max_page_scraped:
                        search_query.max_page_scraped = max_page_successfully_scraped
                        # Update last_updated timestamp implicitly via auto_now=True
                        # or explicitly: search_query.last_updated = timezone.now()
                        search_query.save()
                        print(f"Updated max_page_scraped for '{search_term}' to {max_page_successfully_scraped}")

            # --- Retrieve Data for CSV ---
            # Fetch products up to the number of pages required OR the max successfully scraped
            final_max_page = min(pages_required, search_query.max_page_scraped)
            products = Product.objects.filter(
                search_query=search_query,
                page__lte=final_max_page
            ).order_by('page', 'id') # Order consistently for CSV

            if not products.exists():
                 return Response({"message": f"No products found for '{search_term}' up to page {final_max_page} after attempting scrape."}, status=status.HTTP_404_NOT_FOUND)


            # --- Generate CSV Response ---
            output = io.StringIO()
            writer = csv.writer(output)

            # Define header row
            header = ['page', 'title', 'price', 'seller', 'reviews', 'image_url']
            writer.writerow(header)

            # Write data rows
            for product in products.values_list('page', 'title', 'price', 'seller', 'reviews', 'image_url'):
                 writer.writerow(product)

            output.seek(0)
            response = HttpResponse(output, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="products_{search_term}_pages_1_to_{final_max_page}.csv"'
            return response

        except Exception as e:
            # Catch any unexpected errors during the process
            print(f"Unexpected error in ProductDataView: {e}") # Log this properly
            return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
