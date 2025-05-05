from rest_framework import serializers
from .models import Product, SearchQuery

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # Exclude fields managed internally or less relevant for direct API output
        exclude = ('search_query', 'scraped_at')

class SearchQuerySerializer(serializers.ModelSerializer):
    # Optionally nest products if needed, but for the CSV export, we might handle it differently.
    # products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = SearchQuery
        fields = ('id', 'search_term', 'max_page_scraped', 'last_updated')