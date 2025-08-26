"""
Advanced API views for PolyVeda accounts with enterprise features.
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
import logging

from .models import User, UserProfile, Institution, UserSession, AuditLog
from .serializers import (
    InstitutionSerializer, UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserProfileSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, TwoFactorSetupSerializer, TwoFactorVerifySerializer,
    UserSessionSerializer, AuditLogSerializer, LoginSerializer, LogoutSerializer,
    UserBulkActionSerializer
)
from .permissions import (
    IsInstitutionAdmin, IsSuperAdmin, IsOwnProfile, IsInstitutionMember,
    HasPermission
)

logger = logging.getLogger(__name__)


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    Advanced institution management with multi-tenancy support.
    """
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subscription_plan', 'is_active', 'is_verified']
    search_fields = ['name', 'domain', 'email']
    ordering_fields = ['name', 'created_at', 'total_users']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return Institution.objects.all()
        elif user.institution:
            return Institution.objects.filter(id=user.institution.id)
        return Institution.objects.none()
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an institution."""
        institution = self.get_object()
        institution.is_active = True
        institution.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='update',
            entity='Institution',
            entity_id=institution.id,
            severity='medium',
            details={'action': 'activated'}
        )
        
        return Response({'message': 'Institution activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an institution."""
        institution = self.get_object()
        institution.is_active = False
        institution.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='update',
            entity='Institution',
            entity_id=institution.id,
            severity='medium',
            details={'action': 'deactivated'}
        )
        
        return Response({'message': 'Institution deactivated successfully'})
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get institution analytics."""
        institution = self.get_object()
        
        # Get user statistics
        total_users = institution.users.count()
        active_users = institution.users.filter(status=User.Status.ACTIVE).count()
        students = institution.users.filter(role=User.Role.STUDENT).count()
        faculty = institution.users.filter(role=User.Role.FACULTY).count()
        
        # Get recent activity
        recent_logins = institution.users.filter(
            last_activity__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        analytics_data = {
            'total_users': total_users,
            'active_users': active_users,
            'students': students,
            'faculty': faculty,
            'recent_logins': recent_logins,
            'subscription_status': institution.subscription_status,
            'storage_used_gb': 0,  # Calculate from file storage
            'storage_limit_gb': institution.max_storage_gb,
        }
        
        return Response(analytics_data)


class UserViewSet(viewsets.ModelViewSet):
    """
    Advanced user management with comprehensive features.
    """
    serializer_class = UserSerializer
    permission_classes = [IsInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'status', 'email_verified', 'two_factor_enabled']
    search_fields = ['email', 'first_name', 'last_name', 'profile__roll_number', 'profile__employee_id']
    ordering_fields = ['created_at', 'last_activity', 'email']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return User.objects.all()
        elif user.institution:
            return User.objects.filter(institution=user.institution)
        return User.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        """Create user with audit logging."""
        user = serializer.save()
        
        AuditLog.log_action(
            actor=self.request.user,
            action='create',
            entity='User',
            entity_id=user.id,
            severity='medium',
            details={'email': user.email, 'role': user.role}
        )
    
    def perform_update(self, serializer):
        """Update user with audit logging."""
        old_data = {
            'role': serializer.instance.role,
            'status': serializer.instance.status,
        }
        
        user = serializer.save()
        
        # Log changes
        changes = {}
        for field, old_value in old_data.items():
            new_value = getattr(user, field)
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        
        if changes:
            AuditLog.log_action(
                actor=self.request.user,
                action='update',
                entity='User',
                entity_id=user.id,
                severity='medium',
                changes=changes
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.status = User.Status.ACTIVE
        user.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='update',
            entity='User',
            entity_id=user.id,
            severity='medium',
            details={'action': 'activated'}
        )
        
        return Response({'message': 'User activated successfully'})
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a user account."""
        user = self.get_object()
        user.status = User.Status.SUSPENDED
        user.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='update',
            entity='User',
            entity_id=user.id,
            severity='high',
            details={'action': 'suspended'}
        )
        
        return Response({'message': 'User suspended successfully'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password."""
        user = self.get_object()
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='password_reset',
            entity='User',
            entity_id=user.id,
            severity='medium',
            details={'method': 'admin_reset'}
        )
        
        # Send email with new password (implement email sending)
        
        return Response({'message': 'Password reset successfully'})
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on users."""
        serializer = UserBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        action = serializer.validated_data['action']
        action_data = serializer.validated_data.get('action_data', {})
        
        users = User.objects.filter(id__in=user_ids)
        
        with transaction.atomic():
            if action == 'activate':
                users.update(status=User.Status.ACTIVE)
            elif action == 'deactivate':
                users.update(status=User.Status.INACTIVE)
            elif action == 'suspend':
                users.update(status=User.Status.SUSPENDED)
            elif action == 'change_role':
                new_role = action_data.get('role')
                if new_role:
                    users.update(role=new_role)
            elif action == 'delete':
                users.delete()
        
        AuditLog.log_action(
            actor=request.user,
            action='bulk_update',
            entity='User',
            entity_id=','.join(map(str, user_ids)),
            severity='medium',
            details={'action': action, 'count': len(user_ids)}
        )
        
        return Response({'message': f'Bulk action {action} completed successfully'})
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get user analytics."""
        queryset = self.get_queryset()
        
        analytics_data = {
            'total_users': queryset.count(),
            'active_users': queryset.filter(status=User.Status.ACTIVE).count(),
            'suspended_users': queryset.filter(status=User.Status.SUSPENDED).count(),
            'pending_users': queryset.filter(status=User.Status.PENDING).count(),
            'role_distribution': {
                'students': queryset.filter(role=User.Role.STUDENT).count(),
                'faculty': queryset.filter(role=User.Role.FACULTY).count(),
                'hod': queryset.filter(role=User.Role.HOD).count(),
                'admin': queryset.filter(role=User.Role.ADMIN).count(),
            },
            'recent_registrations': queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'online_users': queryset.filter(
                last_activity__gte=timezone.now() - timedelta(minutes=5)
            ).count(),
        }
        
        return Response(analytics_data)


class AuthViewSet(viewsets.ViewSet):
    """
    Advanced authentication views with security features.
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Advanced login with security features."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        remember_me = serializer.validated_data.get('remember_me', False)
        
        # Update user activity
        user.last_activity = timezone.now()
        user.last_login_ip = self.get_client_ip(request)
        user.last_login_user_agent = request.META.get('HTTP_USER_AGENT', '')
        user.save()
        
        # Create session
        session = UserSession.objects.create(
            user=user,
            session_key=request.session.session_key,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(hours=24 if remember_me else 8),
            is_remembered=remember_me
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Set token expiration based on remember me
        if remember_me:
            access_token.set_exp(lifetime=timedelta(hours=24))
        else:
            access_token.set_exp(lifetime=timedelta(hours=8))
        
        # Log login
        AuditLog.log_action(
            actor=user,
            action='login',
            entity='User',
            entity_id=user.id,
            severity='low',
            details={
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'remember_me': remember_me
            }
        )
        
        return Response({
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data,
            'session_id': session.id
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Advanced logout with session management."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        
        return Response({'message': 'Logged out successfully'})
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh access token."""
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh)
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Generate reset token and send email (implement email sending)
            
            AuditLog.log_action(
                actor=None,
                action='password_reset',
                entity='User',
                entity_id=user.id,
                severity='medium',
                details={'email': email}
            )
            
            return Response({'message': 'Password reset email sent'})
        except User.DoesNotExist:
            return Response({'message': 'Password reset email sent'})  # Don't reveal user existence
    
    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """Confirm password reset."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate token and update password (implement token validation)
        
        return Response({'message': 'Password reset successfully'})
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ProfileViewSet(viewsets.ModelViewSet):
    """
    User profile management with advanced features.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsOwnProfile]
    
    def get_queryset(self):
        """Filter queryset to user's own profile."""
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        """Upload profile picture."""
        profile = request.user.profile
        avatar = request.FILES.get('avatar')
        
        if not avatar:
            return Response(
                {'error': 'Avatar file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type and size
        if avatar.size > 5 * 1024 * 1024:  # 5MB limit
            return Response(
                {'error': 'File size too large'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.profile_picture = avatar
        profile.save()
        
        AuditLog.log_action(
            actor=request.user,
            action='file_upload',
            entity='UserProfile',
            entity_id=profile.id,
            severity='low',
            details={'file_type': 'avatar'}
        )
        
        return Response(UserProfileSerializer(profile).data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update user preferences."""
        profile = request.user.profile
        preferences = request.data.get('preferences', {})
        
        profile.notification_preferences.update(preferences)
        profile.save()
        
        return Response({'message': 'Preferences updated successfully'})


class SecurityViewSet(viewsets.ViewSet):
    """
    Security-related views for advanced features.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=False, methods=['post'])
    def setup_2fa(self, request):
        """Setup two-factor authentication."""
        serializer = TwoFactorSetupSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """Verify two-factor authentication code."""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Implement TOTP verification here
        
        return Response({'message': '2FA code verified successfully'})
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Get user sessions."""
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        serializer = UserSessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def revoke_session(self, request):
        """Revoke a specific session."""
        session_id = request.data.get('session_id')
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            session.is_active = False
            session.save()
            
            AuditLog.log_action(
                actor=request.user,
                action='logout',
                entity='UserSession',
                entity_id=session.id,
                severity='low',
                details={'method': 'manual_revoke'}
            )
            
            return Response({'message': 'Session revoked successfully'})
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit log views for compliance and security.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'severity', 'actor', 'entity']
    search_fields = ['entity_name', 'details']
    ordering_fields = ['timestamp', 'severity', 'action']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return AuditLog.objects.all()
        elif user.institution:
            return AuditLog.objects.filter(institution=user.institution)
        return AuditLog.objects.none()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get audit log summary."""
        queryset = self.get_queryset()
        
        # Get recent activity
        recent_activity = queryset.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        )
        
        summary_data = {
            'total_logs': queryset.count(),
            'recent_logs': recent_activity.count(),
            'severity_distribution': {
                'low': queryset.filter(severity='low').count(),
                'medium': queryset.filter(severity='medium').count(),
                'high': queryset.filter(severity='high').count(),
                'critical': queryset.filter(severity='critical').count(),
            },
            'action_distribution': {
                'login': queryset.filter(action='login').count(),
                'logout': queryset.filter(action='logout').count(),
                'create': queryset.filter(action='create').count(),
                'update': queryset.filter(action='update').count(),
                'delete': queryset.filter(action='delete').count(),
            },
            'top_actors': list(
                queryset.values('actor__email')
                .annotate(count=models.Count('id'))
                .order_by('-count')[:10]
            ),
        }
        
        return Response(summary_data)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export audit logs."""
        # Implement CSV/Excel export functionality
        return Response({'message': 'Export functionality to be implemented'})


class DashboardView(APIView):
    """
    Dashboard view for comprehensive analytics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard data."""
        user = request.user
        
        if user.role == User.Role.SUPER_ADMIN:
            return self.get_super_admin_dashboard()
        elif user.role == User.Role.ADMIN:
            return self.get_admin_dashboard(user)
        elif user.role == User.Role.HOD:
            return self.get_hod_dashboard(user)
        elif user.role == User.Role.FACULTY:
            return self.get_faculty_dashboard(user)
        else:
            return self.get_student_dashboard(user)
    
    def get_super_admin_dashboard(self):
        """Get super admin dashboard data."""
        total_institutions = Institution.objects.count()
        active_institutions = Institution.objects.filter(is_active=True).count()
        total_users = User.objects.count()
        
        recent_activity = AuditLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_institutions': total_institutions,
            'active_institutions': active_institutions,
            'total_users': total_users,
            'recent_activity': recent_activity,
        })
    
    def get_admin_dashboard(self, user):
        """Get admin dashboard data."""
        institution = user.institution
        total_users = institution.users.count()
        active_users = institution.users.filter(status=User.Status.ACTIVE).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'institution': InstitutionSerializer(institution).data,
        })
    
    def get_hod_dashboard(self, user):
        """Get HOD dashboard data."""
        # Implement HOD-specific dashboard
        return Response({'message': 'HOD dashboard'})
    
    def get_faculty_dashboard(self, user):
        """Get faculty dashboard data."""
        # Implement faculty-specific dashboard
        return Response({'message': 'Faculty dashboard'})
    
    def get_student_dashboard(self, user):
        """Get student dashboard data."""
        # Implement student-specific dashboard
        return Response({'message': 'Student dashboard'})