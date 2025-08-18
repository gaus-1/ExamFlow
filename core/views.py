from django.shortcuts import render
from .utils import generate_qr_code
from .models import Subject, Task

def home(request):
    qr_code = generate_qr_code("https://t.me/ExamFlowBot")
    subjects = Subject.objects.all()[:6]
    total_subjects = Subject.objects.count()
    total_tasks = Task.objects.count()
    context = {
        'qr_code': qr_code,
        'subjects': subjects,
        'total_subjects': total_subjects,
        'total_tasks': total_tasks,
    }
    return render(request, 'home.html', context)