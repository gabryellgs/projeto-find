from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.api_iot_scan, name='api_iot_scan'),
]