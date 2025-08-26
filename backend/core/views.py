"""
Core views for PolyVeda including health checks and system status.
"""
import os
import platform
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for Render deployment.
    """
    try:
        # Check database connection
        db_status = "healthy"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            logger.error(f"Database health check failed: {e}")

        # Check cache connection
        cache_status = "healthy"
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") != "ok":
                cache_status = "unhealthy"
        except Exception as e:
            cache_status = f"unhealthy: {str(e)}"
            logger.error(f"Cache health check failed: {e}")

        # Overall health status
        overall_status = "healthy"
        if any(status != "healthy" for status in [db_status, cache_status]):
            overall_status = "unhealthy"

        response_data = {
            "status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "environment": getattr(settings, 'ENVIRONMENT', 'production'),
            "services": {
                "database": db_status,
                "cache": cache_status,
            },
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "django_version": "4.2.7",
            }
        }

        status_code = 200 if overall_status == "healthy" else 503
        return JsonResponse(response_data, status=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def system_status(request):
    """
    Detailed system status endpoint for monitoring.
    """
    try:
        # Django settings
        django_settings = {
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "database_engine": settings.DATABASES['default']['ENGINE'],
            "cache_backend": settings.CACHES['default']['BACKEND'],
            "static_root": str(settings.STATIC_ROOT),
            "media_root": str(settings.MEDIA_ROOT),
        }

        # Application status
        app_status = {
            "production": getattr(settings, 'PRODUCTION', False),
            "enable_analytics": getattr(settings, 'ENABLE_ANALYTICS', False),
            "enable_monitoring": getattr(settings, 'ENABLE_MONITORING', False),
            "enable_backup": getattr(settings, 'ENABLE_BACKUP', False),
        }

        response_data = {
            "status": "operational",
            "timestamp": timezone.now().isoformat(),
            "django": django_settings,
            "application": app_status,
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MetricsView(View):
    """
    Metrics endpoint for monitoring and analytics.
    """
    
    def get(self, request):
        """Get system metrics."""
        try:
            # Basic metrics
            metrics = {
                "timestamp": timezone.now().isoformat(),
            }

            # Database metrics
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables")
                    table_count = cursor.fetchone()[0]
                    
                    metrics["database"] = {
                        "table_count": table_count,
                    }
            except Exception as e:
                metrics["database"] = {"error": str(e)}

            return JsonResponse(metrics)

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return JsonResponse({
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_status(request):
    """
    API status endpoint for checking API health.
    """
    try:
        # Check if key services are available
        services_status = {
            "database": "operational",
            "cache": "operational",
        }

        # Test database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            services_status["database"] = "degraded"

        # Test cache
        try:
            cache.set("api_test", "ok", 10)
            if cache.get("api_test") != "ok":
                services_status["cache"] = "degraded"
        except Exception:
            services_status["cache"] = "degraded"

        # Overall API status
        overall_status = "operational"
        if any(status == "degraded" for status in services_status.values()):
            overall_status = "degraded"

        response_data = {
            "status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "services": services_status,
            "endpoints": {
                "health": "/health/",
                "status": "/status/",
                "metrics": "/metrics/",
                "api_docs": "/api/schema/",
            }
        }

        status_code = 200 if overall_status == "operational" else 503
        return JsonResponse(response_data, status=status_code)

    except Exception as e:
        logger.error(f"API status check failed: {e}")
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=500)


def custom_404(request, exception):
    """Custom 404 error handler."""
    return JsonResponse({
        "error": "Page not found",
        "status_code": 404,
        "message": "The requested resource was not found on this server."
    }, status=404)


def custom_500(request):
    """Custom 500 error handler."""
    return JsonResponse({
        "error": "Internal server error",
        "status_code": 500,
        "message": "An internal server error occurred. Please try again later."
    }, status=500)