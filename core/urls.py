from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('demo/', views.theme_demo, name='theme_demo'),
]
