"""
Custom views for PolyVeda project.
"""
from django.shortcuts import render
from django.http import JsonResponse


def handler404(request, exception):
    """Custom 404 error handler."""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Not Found',
            'message': 'The requested resource was not found.',
            'status_code': 404
        }, status=404)
    
    return render(request, '404.html', status=404)


def handler500(request):
    """Custom 500 error handler."""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred.',
            'status_code': 500
        }, status=500)
    
    return render(request, '500.html', status=500)