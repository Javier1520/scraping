from django.urls import path
from .views import ProductDataView

urlpatterns = [
    path('products', ProductDataView.as_view(), name='product-data'),
]