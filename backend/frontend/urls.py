"""
Frontend URLs for PolyVeda.
"""
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # Main dashboard
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Login page
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    
    # Other frontend routes
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('courses/', TemplateView.as_view(template_name='courses.html'), name='courses'),
    path('attendance/', TemplateView.as_view(template_name='attendance.html'), name='attendance'),
    path('assignments/', TemplateView.as_view(template_name='assignments.html'), name='assignments'),
    path('results/', TemplateView.as_view(template_name='results.html'), name='results'),
]