from django.urls import path
from .views import (
    PenebusanCreateView, SalesOrderListView, 
    PenyaluranCreateView, DistributionListView, SuratJalanPDFView
)

urlpatterns = [
    #-- Penebusan (Sales Order) URLs ---
    path('penebusan/list/', SalesOrderListView.as_view(), name='so_list'),
    path('penebusan/add/', PenebusanCreateView.as_view(), name='penebusan_add'),
    
    #-- Penyaluran (Distribusi) URLs ---
    path('penyaluran/list/', DistributionListView.as_view(), name='dist_list'),
    path('penyaluran/add/', PenyaluranCreateView.as_view(), name='penyaluran_add'),
    path('penyaluran/print-sj/<int:pk>/', SuratJalanPDFView.as_view(), name='print_sj'),
]