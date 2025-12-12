from django.urls import path
from .views import OperationalListView, OperationalCreateView

urlpatterns = [
    path('list/', OperationalListView.as_view(), name='operational_list'),
    path('add/', OperationalCreateView.as_view(), name='operational_add'),
]