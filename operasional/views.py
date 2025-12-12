from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import OperationalCost
from .forms import OperationalForm

# --- 1. LIST BIAYA OPERASIONAL ---
class OperationalListView(LoginRequiredMixin, ListView):
    model = OperationalCost
    template_name = 'operational/cost_list.html'
    context_object_name = 'expenses'
    ordering = ['-created_at']

# --- 2. INPUT BIAYA BARU ---
class OperationalCreateView(LoginRequiredMixin, CreateView):
    model = OperationalCost
    form_class = OperationalForm
    template_name = 'operational/cost_form.html'
    success_url = reverse_lazy('operational_list')

    def form_valid(self, form):
        # Otomatis catat siapa yang input
        form.instance.created_by = self.request.user
        messages.success(self.request, "Pengajuan biaya berhasil disimpan! Menunggu ACC Owner.")
        return super().form_valid(form)