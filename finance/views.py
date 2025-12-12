from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import Invoice

# Fungsi Helper PDF (Copy paste yg tadi biar masing-masing apps mandiri)
def render_pdf_view(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response

class InvoicePDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Ambil invoice berdasarkan ID Distribution (karena OneToOne)
        # Atau bisa juga berdasarkan PK Invoice-nya sendiri.
        # Di sini kita pakai PK Invoice agar aman.
        invoice = get_object_or_404(Invoice, distribution__id=pk) 
        
        context = {
            'inv': invoice,
            'company_name': 'CV SEMBADA TANI',
            'company_address': 'Jalan Raya Pupuk No. 1, Semarang',
        }
        return render_pdf_view('finance/pdf_invoice.html', context)