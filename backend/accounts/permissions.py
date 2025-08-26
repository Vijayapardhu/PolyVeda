"""
Advanced permission classes for PolyVeda with enterprise security features.
"""
from rest_framework import permissions
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class IsInstitutionMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the institution.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have access to everything
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user has an institution
        if not request.user.institution:
            return False
        
        # Check if user's institution is active
        if not request.user.institution.is_active:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the object."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have access to everything
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if object belongs to user's institution
        if hasattr(obj, 'institution'):
            return obj.institution == request.user.institution
        
        # Check if object is related to user's institution
        if hasattr(obj, 'user') and hasattr(obj.user, 'institution'):
            return obj.user.institution == request.user.institution
        
        return False


class IsInstitutionAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of their institution.
    """
    
    def has_permission(self, request, view):
        """Check if user has admin permission."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have access to everything
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user is admin or management
        if request.user.role not in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            return False
        
        # Check if user has an institution
        if not request.user.institution:
            return False
        
        # Check if user's institution is active
        if not request.user.institution.is_active:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has admin permission for the object."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have access to everything
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user is admin or management
        if request.user.role not in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            return False
        
        # Check if object belongs to user's institution
        if hasattr(obj, 'institution'):
            return obj.institution == request.user.institution
        
        # Check if object is related to user's institution
        if hasattr(obj, 'user') and hasattr(obj.user, 'institution'):
            return obj.user.institution == request.user.institution
        
        return False


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission to check if user is a super admin.
    """
    
    def has_permission(self, request, view):
        """Check if user is super admin."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.role == request.user.Role.SUPER_ADMIN
    
    def has_object_permission(self, request, view, obj):
        """Check if user is super admin."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.role == request.user.Role.SUPER_ADMIN


class IsOwnProfile(permissions.BasePermission):
    """
    Permission to check if user is accessing their own profile.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is accessing their own profile."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins can access any profile
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Institution admins can access profiles in their institution
        if request.user.role in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            if hasattr(obj, 'user') and hasattr(obj.user, 'institution'):
                return obj.user.institution == request.user.institution
        
        # Users can only access their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class HasPermission(permissions.BasePermission):
    """
    Permission to check if user has specific permission.
    """
    
    def __init__(self, required_permission):
        """Initialize with required permission."""
        self.required_permission = required_permission
    
    def has_permission(self, request, view):
        """Check if user has the required permission."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have all permissions
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user has the required permission
        return request.user.has_permission(self.required_permission)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has the required permission for the object."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have all permissions
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user has the required permission
        if not request.user.has_permission(self.required_permission):
            return False
        
        # Check institution-based access
        if hasattr(obj, 'institution'):
            return obj.institution == request.user.institution
        
        if hasattr(obj, 'user') and hasattr(obj.user, 'institution'):
            return obj.user.institution == request.user.institution
        
        return True


class IsActiveUser(permissions.BasePermission):
    """
    Permission to check if user account is active.
    """
    
    def has_permission(self, request, view):
        """Check if user account is active."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.status == request.user.Status.ACTIVE
    
    def has_object_permission(self, request, view, obj):
        """Check if user account is active."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.status == request.user.Status.ACTIVE


class IsNotLocked(permissions.BasePermission):
    """
    Permission to check if user account is not locked.
    """
    
    def has_permission(self, request, view):
        """Check if user account is not locked."""
        if not request.user.is_authenticated:
            return False
        
        return not request.user.is_account_locked
    
    def has_object_permission(self, request, view, obj):
        """Check if user account is not locked."""
        if not request.user.is_authenticated:
            return False
        
        return not request.user.is_account_locked


class IsNotExpired(permissions.BasePermission):
    """
    Permission to check if user password is not expired.
    """
    
    def has_permission(self, request, view):
        """Check if user password is not expired."""
        if not request.user.is_authenticated:
            return False
        
        return not request.user.is_password_expired
    
    def has_object_permission(self, request, view, obj):
        """Check if user password is not expired."""
        if not request.user.is_authenticated:
            return False
        
        return not request.user.is_password_expired


class RateLimitPermission(permissions.BasePermission):
    """
    Permission to implement rate limiting.
    """
    
    def __init__(self, rate_limit_key, max_requests, window_seconds):
        """Initialize rate limiting parameters."""
        self.rate_limit_key = rate_limit_key
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def has_permission(self, request, view):
        """Check rate limiting."""
        if not request.user.is_authenticated:
            return True  # Allow unauthenticated requests
        
        # Generate cache key
        cache_key = f"rate_limit:{self.rate_limit_key}:{request.user.id}"
        
        # Get current request count
        current_count = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if current_count >= self.max_requests:
            return False
        
        # Increment count
        cache.set(cache_key, current_count + 1, self.window_seconds)
        
        return True


class InstitutionSubscriptionPermission(permissions.BasePermission):
    """
    Permission to check institution subscription limits.
    """
    
    def has_permission(self, request, view):
        """Check institution subscription limits."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins bypass subscription checks
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user has an institution
        if not request.user.institution:
            return False
        
        institution = request.user.institution
        
        # Check if institution is active
        if not institution.is_active:
            return False
        
        # Check if institution is in trial or has active subscription
        if not (institution.is_trial_active or institution.subscription_plan != 'basic'):
            return False
        
        # Check user limits
        current_users = institution.users.count()
        if current_users >= institution.max_users:
            return False
        
        return True


class FeaturePermission(permissions.BasePermission):
    """
    Permission to check if institution has access to specific features.
    """
    
    def __init__(self, required_feature):
        """Initialize with required feature."""
        self.required_feature = required_feature
    
    def has_permission(self, request, view):
        """Check if institution has access to the required feature."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have access to all features
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if user has an institution
        if not request.user.institution:
            return False
        
        institution = request.user.institution
        
        # Check if institution is active
        if not institution.is_active:
            return False
        
        # Check if feature is enabled
        features_enabled = institution.features_enabled or {}
        return features_enabled.get(self.required_feature, False)


class TimeBasedPermission(permissions.BasePermission):
    """
    Permission to check time-based access restrictions.
    """
    
    def __init__(self, start_time=None, end_time=None, days_of_week=None):
        """Initialize time-based restrictions."""
        self.start_time = start_time
        self.end_time = end_time
        self.days_of_week = days_of_week or [0, 1, 2, 3, 4, 5, 6]  # All days
    
    def has_permission(self, request, view):
        """Check time-based access."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins bypass time restrictions
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        now = timezone.now()
        
        # Check day of week
        if now.weekday() not in self.days_of_week:
            return False
        
        # Check time restrictions
        if self.start_time and now.time() < self.start_time:
            return False
        
        if self.end_time and now.time() > self.end_time:
            return False
        
        return True


class IPRestrictionPermission(permissions.BasePermission):
    """
    Permission to check IP-based access restrictions.
    """
    
    def __init__(self, allowed_ips=None, blocked_ips=None):
        """Initialize IP restrictions."""
        self.allowed_ips = allowed_ips or []
        self.blocked_ips = blocked_ips or []
    
    def has_permission(self, request, view):
        """Check IP-based access."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins bypass IP restrictions
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            return False
        
        # Check allowed IPs (if specified)
        if self.allowed_ips and client_ip not in self.allowed_ips:
            return False
        
        return True
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionPermission(permissions.BasePermission):
    """
    Permission to check session-based access.
    """
    
    def has_permission(self, request, view):
        """Check session-based access."""
        if not request.user.is_authenticated:
            return False
        
        # Check if user has active sessions
        active_sessions = request.user.sessions.filter(is_active=True)
        
        # Check session timeout
        for session in active_sessions:
            if session.is_expired:
                session.is_active = False
                session.save()
        
        # Check if user has any active sessions
        if not active_sessions.exists():
            return False
        
        return True


class AuditPermission(permissions.BasePermission):
    """
    Permission to check audit-related access.
    """
    
    def has_permission(self, request, view):
        """Check audit access permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have full audit access
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Institution admins have audit access to their institution
        if request.user.role in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            return True
        
        # HODs have limited audit access
        if request.user.role == request.user.Role.HOD:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check audit object permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have full access
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check if audit log belongs to user's institution
        if hasattr(obj, 'institution'):
            return obj.institution == request.user.institution
        
        return False


class DataExportPermission(permissions.BasePermission):
    """
    Permission to check data export access.
    """
    
    def has_permission(self, request, view):
        """Check data export permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have full export access
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Institution admins have export access
        if request.user.role in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            return True
        
        # HODs have limited export access
        if request.user.role == request.user.Role.HOD:
            return True
        
        return False


class SensitiveDataPermission(permissions.BasePermission):
    """
    Permission to check access to sensitive data.
    """
    
    def has_permission(self, request, view):
        """Check sensitive data access permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have full access
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Institution admins have access
        if request.user.role in [request.user.Role.ADMIN, request.user.Role.MANAGEMENT]:
            return True
        
        # HODs have limited access
        if request.user.role == request.user.Role.HOD:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check sensitive data object permissions."""
        if not request.user.is_authenticated:
            return False
        
        # Super admins have full access
        if request.user.role == request.user.Role.SUPER_ADMIN:
            return True
        
        # Check institution-based access
        if hasattr(obj, 'institution'):
            return obj.institution == request.user.institution
        
        if hasattr(obj, 'user') and hasattr(obj.user, 'institution'):
            return obj.user.institution == request.user.institution
        
        return False


# Permission mixins for common patterns
class InstitutionAdminMixin:
    """Mixin to add institution admin permissions."""
    permission_classes = [IsInstitutionAdmin]


class SuperAdminMixin:
    """Mixin to add super admin permissions."""
    permission_classes = [IsSuperAdmin]


class OwnProfileMixin:
    """Mixin to add own profile permissions."""
    permission_classes = [IsOwnProfile]


class ActiveUserMixin:
    """Mixin to add active user permissions."""
    permission_classes = [IsActiveUser]


class NotLockedMixin:
    """Mixin to add not locked permissions."""
    permission_classes = [IsNotLocked]


class NotExpiredMixin:
    """Mixin to add not expired permissions."""
    permission_classes = [IsNotExpired]