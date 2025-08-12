from django.shortcuts import render
from .utils import generate_qr_code

def home(request):
    qr_code = generate_qr_code("https://t.me/ExamFlowBot")
    return render(request, 'home.html', {'qr_code': qr_code})