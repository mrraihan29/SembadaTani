from django.shortcuts import render
from django.utils import timezone

def dashboard_view(request):
    context = {
        'today': timezone.now(),
    }
    return render(request, 'dashboard.html', context)