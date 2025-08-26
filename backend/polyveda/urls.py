"""
URL configuration for PolyVeda project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views import health_check, system_status, api_status, MetricsView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check endpoints for Render
    path('health/', health_check, name='health_check'),
    path('status/', system_status, name='system_status'),
    path('api-status/', api_status, name='api_status'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    
    # API endpoints
    path('api/', include('accounts.urls')),
    path('api/', include('academics.urls')),
    path('api/', include('resources.urls')),
    path('api/', include('announcements.urls')),
    path('api/', include('forms.urls')),
    path('api/', include('support.urls')),
    path('api/', include('analytics.urls')),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Frontend routes (for SPA)
    path('', include('frontend.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'