from django.urls import path
from .views import InvoicePDFView, InvoiceListView, PaymentCreateView

urlpatterns = [
    # PDF
    path('invoice/print/<int:pk>/', InvoicePDFView.as_view(), name='print_invoice'),
    
    # Monitoring & Transaksi
    path('invoice/list/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/pay/<int:pk>/', PaymentCreateView.as_view(), name='payment_add'),
]