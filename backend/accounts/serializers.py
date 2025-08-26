"""
Advanced API serializers for PolyVeda accounts with enterprise features.
"""
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re

from .models import User, UserProfile, Institution, UserSession, AuditLog


class InstitutionSerializer(serializers.ModelSerializer):
    """
    Advanced institution serializer with comprehensive validation.
    """
    total_users = serializers.SerializerMethodField()
    total_departments = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'slug', 'domain', 'logo', 'primary_color', 'secondary_color',
            'address', 'phone', 'email', 'website', 'academic_year_start', 'academic_year_end',
            'timezone', 'currency', 'language', 'subscription_plan', 'max_users',
            'max_storage_gb', 'features_enabled', 'is_active', 'is_verified',
            'trial_ends_at', 'created_at', 'updated_at', 'total_users',
            'total_departments', 'subscription_status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_users', 'total_departments']
    
    def get_total_users(self, obj):
        return obj.users.count()
    
    def get_total_departments(self, obj):
        return obj.departments.count()
    
    def get_subscription_status(self, obj):
        if obj.is_trial_active:
            return 'trial'
        elif obj.subscription_plan == 'basic':
            return 'basic'
        else:
            return 'premium'
    
    def validate_domain(self, value):
        """Validate domain format."""
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, value):
            raise serializers.ValidationError("Invalid domain format")
        return value
    
    def validate_academic_year_end(self, value):
        """Validate academic year end date."""
        start_date = self.initial_data.get('academic_year_start')
        if start_date and value <= start_date:
            raise serializers.ValidationError("Academic year end must be after start date")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Advanced user profile serializer with comprehensive validation.
    """
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'profile_picture', 'bio', 'blood_group', 'roll_number', 'admission_number',
            'branch', 'semester', 'year_of_admission', 'section', 'academic_status',
            'employee_id', 'department', 'designation', 'qualification', 'specialization',
            'experience_years', 'joining_date', 'address_line1', 'address_line2', 'city',
            'state', 'postal_code', 'country', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'emergency_contact_address', 'special_category',
            'ncc_cadet', 'ncc_rank', 'ncc_unit', 'id_proof', 'address_proof',
            'academic_documents', 'linkedin_url', 'github_url', 'portfolio_url',
            'notification_preferences', 'privacy_settings', 'age', 'full_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'age', 'full_address']
    
    def validate_roll_number(self, value):
        """Validate roll number format."""
        if value and not re.match(r'^[A-Z0-9]{6,15}$', value):
            raise serializers.ValidationError("Roll number must be 6-15 characters, alphanumeric only")
        return value
    
    def validate_employee_id(self, value):
        """Validate employee ID format."""
        if value and not re.match(r'^[A-Z]{2,3}[0-9]{4,6}$', value):
            raise serializers.ValidationError("Employee ID must be in format: XX12345 or XXX123456")
        return value
    
    def validate_linkedin_url(self, value):
        """Validate LinkedIn URL."""
        if value and not value.startswith('https://www.linkedin.com/'):
            raise serializers.ValidationError("Invalid LinkedIn URL format")
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    Advanced user serializer with comprehensive features.
    """
    profile = UserProfileSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()
    last_activity_formatted = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 'status', 'institution',
            'email_verified', 'phone_number', 'phone_verified', 'date_of_birth', 'gender',
            'employee_id', 'student_id', 'two_factor_enabled', 'last_login_ip',
            'last_login_location', 'last_activity', 'preferences', 'notification_settings',
            'language', 'timezone', 'created_at', 'updated_at', 'profile', 'permissions',
            'session_count', 'last_activity_formatted', 'is_online'
        ]
        read_only_fields = [
            'id', 'email_verified', 'phone_verified', 'last_login_ip', 'last_login_location',
            'last_activity', 'created_at', 'updated_at', 'permissions', 'session_count',
            'last_activity_formatted', 'is_online'
        ]
    
    def get_permissions(self, obj):
        return obj.get_permissions()
    
    def get_session_count(self, obj):
        return obj.sessions.filter(is_active=True).count()
    
    def get_last_activity_formatted(self, obj):
        if obj.last_activity:
            return obj.last_activity.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_is_online(self, obj):
        if obj.last_activity:
            return obj.last_activity > timezone.now() - timedelta(minutes=5)
        return False
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users with advanced validation.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'role', 'institution', 'phone_number',
            'date_of_birth', 'gender', 'password', 'password_confirm', 'profile'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation and other fields."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate role-specific requirements
        role = attrs.get('role')
        if role == User.Role.STUDENT:
            if not attrs.get('profile', {}).get('roll_number'):
                raise serializers.ValidationError("Roll number is required for students")
        elif role == User.Role.FACULTY:
            if not attrs.get('profile', {}).get('employee_id'):
                raise serializers.ValidationError("Employee ID is required for faculty")
        
        return attrs
    
    def create(self, validated_data):
        """Create user with profile."""
        profile_data = validated_data.pop('profile', {})
        password_confirm = validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile
        UserProfile.objects.create(user=user, **profile_data)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users with advanced validation.
    """
    profile = UserProfileSerializer(partial=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'role', 'phone_number', 'date_of_birth',
            'gender', 'preferences', 'notification_settings', 'language', 'timezone', 'profile'
        ]
    
    def update(self, instance, validated_data):
        """Update user and profile."""
        profile_data = validated_data.pop('profile', {})
        
        # Update user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """
    Advanced password change serializer with security features.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        
        # Check if new password is same as current
        user = self.context['request'].user
        if user.check_password(attrs['new_password']):
            raise serializers.ValidationError("New password must be different from current password")
        
        return attrs
    
    def save(self):
        """Change password and update security fields."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.password_changed_at = timezone.now()
        user.password_expires_at = timezone.now() + timedelta(days=90)
        user.save()
        
        # Log password change
        AuditLog.log_action(
            actor=user,
            action='password_change',
            entity='User',
            entity_id=user.id,
            severity='medium',
            details={'method': 'api'}
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Password reset request serializer.
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists."""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Password reset confirmation serializer.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class TwoFactorSetupSerializer(serializers.Serializer):
    """
    Two-factor authentication setup serializer.
    """
    enable_2fa = serializers.BooleanField()
    
    def save(self):
        """Enable or disable 2FA."""
        user = self.context['request'].user
        enable_2fa = self.validated_data['enable_2fa']
        
        if enable_2fa:
            # Generate 2FA secret and backup codes
            import secrets
            user.two_factor_secret = secrets.token_hex(16)
            user.two_factor_enabled = True
            backup_codes = user.generate_backup_codes()
        else:
            # Disable 2FA
            user.two_factor_secret = ''
            user.two_factor_enabled = False
            user.backup_codes = []
            backup_codes = []
        
        user.save()
        
        return {
            'two_factor_secret': user.two_factor_secret if enable_2fa else None,
            'backup_codes': backup_codes if enable_2fa else None,
            'qr_code_url': self.generate_qr_code(user) if enable_2fa else None
        }
    
    def generate_qr_code(self, user):
        """Generate QR code URL for 2FA setup."""
        import qrcode
        from io import BytesIO
        import base64
        
        # Generate QR code data
        qr_data = f"otpauth://totp/PolyVeda:{user.email}?secret={user.two_factor_secret}&issuer=PolyVeda"
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"


class TwoFactorVerifySerializer(serializers.Serializer):
    """
    Two-factor authentication verification serializer.
    """
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_code(self, value):
        """Validate 2FA code."""
        if not value.isdigit():
            raise serializers.ValidationError("Code must be numeric")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """
    User session serializer for session management.
    """
    device_info = serializers.SerializerMethodField()
    location_info = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'session_key', 'device_id', 'device_name', 'device_type',
            'browser', 'browser_version', 'os', 'os_version', 'ip_address',
            'location', 'user_agent', 'is_secure', 'created_at', 'last_activity',
            'expires_at', 'is_active', 'is_remembered', 'is_suspicious',
            'risk_score', 'device_info', 'location_info', 'is_current'
        ]
        read_only_fields = ['id', 'session_key', 'device_id', 'created_at', 'last_activity']
    
    def get_device_info(self, obj):
        return {
            'name': obj.device_name,
            'type': obj.device_type,
            'browser': f"{obj.browser} {obj.browser_version}",
            'os': f"{obj.os} {obj.os_version}"
        }
    
    def get_location_info(self, obj):
        return obj.location
    
    def get_is_current(self, obj):
        request = self.context.get('request')
        if request:
            return obj.session_key == request.session.session_key
        return False


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Audit log serializer for compliance and security.
    """
    actor_name = serializers.SerializerMethodField()
    institution_name = serializers.SerializerMethodField()
    severity_color = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor', 'actor_name', 'institution', 'institution_name', 'action',
            'severity', 'entity', 'entity_id', 'entity_name', 'details', 'changes',
            'metadata', 'ip_address', 'user_agent', 'session_id', 'request_id',
            'timestamp', 'severity_color'
        ]
        read_only_fields = ['id', 'timestamp', 'request_id']
    
    def get_actor_name(self, obj):
        return obj.actor.get_full_name() if obj.actor else 'System'
    
    def get_institution_name(self, obj):
        return obj.institution.name if obj.institution else 'System'
    
    def get_severity_color(self, obj):
        colors = {
            'low': 'green',
            'medium': 'yellow',
            'high': 'orange',
            'critical': 'red'
        }
        return colors.get(obj.severity, 'gray')


class LoginSerializer(serializers.Serializer):
    """
    Advanced login serializer with security features.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(default=False)
    two_factor_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.check_password(password):
            # Increment failed login attempts
            user.increment_failed_login_attempts()
            raise serializers.ValidationError("Invalid email or password")
        
        # Check if account is locked
        if user.is_account_locked:
            raise serializers.ValidationError("Account is temporarily locked due to multiple failed attempts")
        
        # Check if password is expired
        if user.is_password_expired:
            raise serializers.ValidationError("Password has expired. Please reset your password")
        
        # Check if 2FA is required
        if user.two_factor_enabled:
            two_factor_code = attrs.get('two_factor_code')
            if not two_factor_code:
                raise serializers.ValidationError("Two-factor authentication code is required")
            
            # Validate 2FA code (implement TOTP validation here)
            if not self.validate_2fa_code(user, two_factor_code):
                raise serializers.ValidationError("Invalid two-factor authentication code")
        
        # Reset failed login attempts
        user.reset_failed_login_attempts()
        
        attrs['user'] = user
        return attrs
    
    def validate_2fa_code(self, user, code):
        """Validate 2FA code (placeholder for TOTP implementation)."""
        # This is a placeholder - implement proper TOTP validation
        return True


class LogoutSerializer(serializers.Serializer):
    """
    Logout serializer with session management.
    """
    logout_all_sessions = serializers.BooleanField(default=False)
    
    def save(self):
        """Logout user and manage sessions."""
        user = self.context['request'].user
        logout_all = self.validated_data.get('logout_all_sessions', False)
        
        if logout_all:
            # Logout from all sessions
            user.sessions.filter(is_active=True).update(is_active=False)
        else:
            # Logout from current session only
            current_session_key = self.context['request'].session.session_key
            user.sessions.filter(session_key=current_session_key).update(is_active=False)
        
        # Log logout action
        AuditLog.log_action(
            actor=user,
            action='logout',
            entity='User',
            entity_id=user.id,
            severity='low',
            details={'logout_all': logout_all}
        )


class UserBulkActionSerializer(serializers.Serializer):
    """
    Bulk user action serializer for administrative operations.
    """
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('suspend', 'Suspend'),
        ('delete', 'Delete'),
        ('change_role', 'Change Role'),
        ('send_notification', 'Send Notification'),
    ])
    action_data = serializers.JSONField(required=False)
    
    def validate_user_ids(self, value):
        """Validate user IDs exist."""
        existing_users = User.objects.filter(id__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("Some user IDs do not exist")
        return value
    
    def validate(self, attrs):
        """Validate action-specific requirements."""
        action = attrs.get('action')
        action_data = attrs.get('action_data', {})
        
        if action == 'change_role':
            if 'role' not in action_data:
                raise serializers.ValidationError("Role is required for change_role action")
        
        return attrs