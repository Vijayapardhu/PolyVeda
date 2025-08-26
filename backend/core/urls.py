"""
URL configuration for core app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('status/', views.system_status, name='system_status'),
    path('api-status/', views.api_status, name='api_status'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
]