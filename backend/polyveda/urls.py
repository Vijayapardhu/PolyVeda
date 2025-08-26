"""
URL configuration for PolyVeda project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include([
        # Authentication
        path('auth/', include('accounts.urls')),
        
        # Core modules
        path('academics/', include('academics.urls')),
        path('resources/', include('resources.urls')),
        path('announcements/', include('announcements.urls')),
        path('forms/', include('forms.urls')),
        path('support/', include('support.urls')),
        path('analytics/', include('analytics.urls')),
    ])),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Frontend routes (for SPA or template-based views)
    path('', include('accounts.urls_frontend')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'polyveda.views.handler404'
handler500 = 'polyveda.views.handler500'