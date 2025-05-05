from django.db import models

# Create your models here.

class SearchQuery(models.Model):
    search_term = models.CharField(max_length=255, unique=True, db_index=True)
    max_page_scraped = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.search_term} (up to page {self.max_page_scraped})'

class Product(models.Model):
    search_query = models.ForeignKey(SearchQuery, related_name='products', on_delete=models.CASCADE)
    page = models.PositiveIntegerField()
    title = models.CharField(max_length=500) # Increased length for potentially long titles
    price = models.CharField(max_length=100) # Store price as char for flexibility with formatting (e.g., '$1.234.56')
    seller = models.CharField(max_length=255, blank=True, null=True)
    reviews = models.CharField(max_length=255, blank=True, null=True) # Store reviews summary as text
    image_url = models.URLField(max_length=2048, blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True) # Timestamp of when this record was created

    class Meta:
        # Prevent duplicate entries for the same product on the same page of the same search
        # Using image_url might be more reliable if titles can change slightly or are identical
        # Using title as part of the constraint for now
        unique_together = ('search_query', 'page', 'title', 'image_url')
        ordering = ['scraped_at'] # Default ordering

    def __str__(self):
        return f'{self.title} (Page {self.page} for \'{self.search_query.search_term}\')'
