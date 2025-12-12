from django.urls import path
from .views import InvoicePDFView

urlpatterns = [
    path('invoice/print/<int:pk>/', InvoicePDFView.as_view(), name='print_invoice'),
]