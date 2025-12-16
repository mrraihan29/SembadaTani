from django.urls import path
from .views import (
    PenebusanCreateView, SalesOrderListView, PenyaluranCreateView, 
    DistributionListView, SuratJalanPDFView, StockCardListView,
    AllocationReportView
)

urlpatterns = [
    #-- Penebusan (Sales Order) URLs ---
    path('penebusan/list/', SalesOrderListView.as_view(), name='so_list'),
    path('penebusan/add/', PenebusanCreateView.as_view(), name='penebusan_add'),
    
    #-- Penyaluran (Distribusi) URLs ---
    path('penyaluran/list/', DistributionListView.as_view(), name='dist_list'),
    path('penyaluran/add/', PenyaluranCreateView.as_view(), name='penyaluran_add'),
    path('penyaluran/print-sj/<int:pk>/', SuratJalanPDFView.as_view(), name='print_sj'),

    #-- Laporan Kartu Stok URLs ---
    path('stock-card/', StockCardListView.as_view(), name='stock_card_list'),
    
    path('allocation-report/', AllocationReportView.as_view(), name='allocation_report'),
]