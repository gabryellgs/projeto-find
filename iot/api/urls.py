from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.api_iot_scan, name='api_iot_scan'),
    path('latest-scan/', views.api_iot_latest_scan, name='api_iot_latest_scan'),
]