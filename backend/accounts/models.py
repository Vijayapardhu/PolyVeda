"""
Advanced User models for PolyVeda with enterprise features.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib
import secrets


class Institution(models.Model):
    """
    Multi-tenant institution model for enterprise deployment.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    domain = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='institutions/logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#64748B')
    
    # Contact Information
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Academic Information
    academic_year_start = models.DateField()
    academic_year_end = models.DateField()
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    currency = models.CharField(max_length=3, default='INR')
    language = models.CharField(max_length=10, default='en-IN')
    
    # Subscription & Limits
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
            ('custom', 'Custom'),
        ],
        default='basic'
    )
    max_users = models.PositiveIntegerField(default=1000)
    max_storage_gb = models.PositiveIntegerField(default=10)
    features_enabled = JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institutions'
        verbose_name = _('institution')
        verbose_name_plural = _('institutions')
    
    def __str__(self):
        return self.name
    
    @property
    def is_trial_active(self):
        return self.trial_ends_at and self.trial_ends_at > timezone.now()
    
    @property
    def current_academic_year(self):
        now = timezone.now().date()
        if self.academic_year_start <= now <= self.academic_year_end:
            return f"{self.academic_year_start.year}-{self.academic_year_end.year}"
        return None


class User(AbstractUser):
    """
    Advanced User model with enterprise features.
    """
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        FACULTY = 'faculty', _('Faculty')
        HOD = 'hod', _('Head of Department')
        ADMIN = 'admin', _('Administrator')
        MANAGEMENT = 'management', _('Management')
        SUPER_ADMIN = 'super_admin', _('Super Administrator')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending Approval')
        LOCKED = 'locked', _('Account Locked')
        EXPIRED = 'expired', _('Account Expired')

    # Multi-tenancy
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    
    # Core fields
    username = None
    email = models.EmailField(_('email address'), unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_expires = models.DateTimeField(null=True, blank=True)
    
    # Advanced authentication
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    permissions = JSONField(default=dict)
    
    # Security features
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    backup_codes = ArrayField(models.CharField(max_length=10), blank=True, default=list)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expires_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Session management
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_location = JSONField(default=dict)
    last_login_user_agent = models.TextField(blank=True)
    session_timeout = models.PositiveIntegerField(default=30)  # minutes
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    phone_verified = models.BooleanField(default=False)
    
    # Advanced profile
    employee_id = models.CharField(max_length=20, blank=True, unique=True)
    student_id = models.CharField(max_length=20, blank=True, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', _('Male')), ('female', _('Female')), ('other', _('Other'))],
        blank=True
    )
    
    # Preferences
    preferences = JSONField(default=dict)
    notification_settings = JSONField(default=dict)
    language = models.CharField(max_length=10, default='en-IN')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    modified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_users'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['institution']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Set password expiration
        if not self.password_expires_at and self.password:
            self.password_expires_at = timezone.now() + timedelta(days=90)
        
        # Update modified_by
        if not self.pk:  # New user
            self.created_by = getattr(self, '_current_user', None)
        else:
            self.modified_by = getattr(self, '_current_user', None)
        
        super().save(*args, **kwargs)
    
    @property
    def is_password_expired(self):
        return self.password_expires_at and self.password_expires_at < timezone.now()
    
    @property
    def is_account_locked(self):
        return self.locked_until and self.locked_until > timezone.now()
    
    @property
    def can_login(self):
        return (
            self.is_active and
            self.status == self.Status.ACTIVE and
            not self.is_account_locked and
            not self.is_password_expired
        )
    
    def increment_failed_login_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def reset_failed_login_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def generate_backup_codes(self):
        """Generate new backup codes for 2FA."""
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = codes
        self.save(update_fields=['backup_codes'])
        return codes
    
    def verify_backup_code(self, code):
        """Verify a backup code and remove it if valid."""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save(update_fields=['backup_codes'])
            return True
        return False
    
    def get_permissions(self):
        """Get user permissions including role-based and custom permissions."""
        cache_key = f"user_permissions_{self.id}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            # Base role permissions
            role_permissions = self.get_role_permissions()
            # Custom permissions
            custom_permissions = self.permissions.get('custom', {})
            # Merge permissions
            permissions = {**role_permissions, **custom_permissions}
            cache.set(cache_key, permissions, 300)  # Cache for 5 minutes
        
        return permissions
    
    def get_role_permissions(self):
        """Get permissions based on user role."""
        permissions = {
            'student': {
                'view_own_profile': True,
                'view_own_courses': True,
                'view_own_attendance': True,
                'view_own_results': True,
                'submit_assignments': True,
                'create_support_tickets': True,
            },
            'faculty': {
                'view_own_profile': True,
                'manage_own_courses': True,
                'take_attendance': True,
                'grade_assignments': True,
                'view_student_profiles': True,
                'create_announcements': True,
            },
            'hod': {
                'view_own_profile': True,
                'manage_department': True,
                'view_department_reports': True,
                'approve_requests': True,
                'manage_faculty': True,
            },
            'admin': {
                'view_own_profile': True,
                'manage_users': True,
                'manage_system': True,
                'view_all_reports': True,
                'manage_institution': True,
            },
            'management': {
                'view_own_profile': True,
                'view_analytics': True,
                'view_financial_reports': True,
                'manage_policies': True,
            },
            'super_admin': {
                'all_permissions': True,
            }
        }
        return permissions.get(self.role, {})
    
    def has_permission(self, permission):
        """Check if user has specific permission."""
        user_permissions = self.get_permissions()
        return user_permissions.get('all_permissions', False) or user_permissions.get(permission, False)


class UserProfile(models.Model):
    """
    Advanced user profile with comprehensive information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True
    )
    
    # Academic Information (for students)
    roll_number = models.CharField(max_length=20, blank=True, unique=True)
    admission_number = models.CharField(max_length=20, blank=True, unique=True)
    branch = models.CharField(max_length=50, blank=True)
    semester = models.PositiveIntegerField(null=True, blank=True)
    year_of_admission = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=10, blank=True)
    academic_status = models.CharField(
        max_length=20,
        choices=[
            ('regular', 'Regular'),
            ('backlog', 'Backlog'),
            ('detained', 'Detained'),
            ('completed', 'Completed'),
        ],
        default='regular'
    )
    
    # Faculty Information
    employee_id = models.CharField(max_length=20, blank=True, unique=True)
    department = models.CharField(max_length=50, blank=True)
    designation = models.CharField(max_length=50, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=17, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    emergency_contact_address = models.TextField(blank=True)
    
    # Special Categories
    special_category = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'),
            ('obc', 'OBC'),
            ('sc', 'SC'),
            ('st', 'ST'),
            ('ews', 'EWS'),
            ('pwd', 'Person with Disability'),
        ],
        default='general'
    )
    ncc_cadet = models.BooleanField(default=False)
    ncc_rank = models.CharField(max_length=20, blank=True)
    ncc_unit = models.CharField(max_length=50, blank=True)
    
    # Documents
    id_proof = models.FileField(upload_to='documents/id_proofs/', null=True, blank=True)
    address_proof = models.FileField(upload_to='documents/address_proofs/', null=True, blank=True)
    academic_documents = JSONField(default=list)  # List of document URLs
    
    # Social Media
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Preferences
    notification_preferences = JSONField(default=dict)
    privacy_settings = JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
    
    @property
    def full_address(self):
        """Return the complete address."""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code]
        return ', '.join(filter(None, parts))
    
    @property
    def age(self):
        """Calculate age from date of birth."""
        if self.user.date_of_birth:
            today = timezone.now().date()
            return today.year - self.user.date_of_birth.year - (
                (today.month, today.day) < (self.user.date_of_birth.month, self.user.date_of_birth.day)
            )
        return None


class UserSession(models.Model):
    """
    Advanced session tracking with security features.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_id = models.UUIDField(default=uuid.uuid4, editable=False)
    device_name = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
        ],
        default='desktop'
    )
    browser = models.CharField(max_length=50, blank=True)
    browser_version = models.CharField(max_length=20, blank=True)
    os = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=20, blank=True)
    
    # Location and security
    ip_address = models.GenericIPAddressField()
    location = JSONField(default=dict)
    user_agent = models.TextField()
    is_secure = models.BooleanField(default=False)
    
    # Session management
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_remembered = models.BooleanField(default=False)
    
    # Security flags
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} at {self.created_at}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def extend_session(self, hours=24):
        """Extend session expiration."""
        self.expires_at = timezone.now() + timedelta(hours=hours)
        self.save(update_fields=['expires_at'])


class AuditLog(models.Model):
    """
    Comprehensive audit trail for compliance and security.
    """
    class Action(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        LOGIN_FAILED = 'login_failed', _('Login Failed')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
        EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
        PERMISSION_CHANGE = 'permission_change', _('Permission Change')
        ROLE_CHANGE = 'role_change', _('Role Change')
        STATUS_CHANGE = 'status_change', _('Status Change')
        FILE_UPLOAD = 'file_upload', _('File Upload')
        FILE_DOWNLOAD = 'file_download', _('File Download')
        DATA_EXPORT = 'data_export', _('Data Export')
        DATA_IMPORT = 'data_import', _('Data Import')
        SYSTEM_CONFIG = 'system_config', _('System Configuration')
    
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Core fields
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
        help_text=_('User who performed the action')
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    
    # Entity information
    entity = models.CharField(max_length=50, help_text=_('Model/entity being acted upon'))
    entity_id = models.CharField(max_length=50, help_text=_('ID of the entity'))
    entity_name = models.CharField(max_length=200, blank=True)
    
    # Details
    details = JSONField(default=dict, help_text=_('Additional details about the action'))
    changes = JSONField(default=dict, help_text=_('Field changes for updates'))
    metadata = JSONField(default=dict, help_text=_('Additional metadata'))
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    request_id = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['entity', 'entity_id']),
            models.Index(fields=['institution', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.actor} {self.action} {self.entity}:{self.entity_id} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, actor, action, entity, entity_id, **kwargs):
        """Convenience method to log an action."""
        return cls.objects.create(
            actor=actor,
            institution=actor.institution if actor else None,
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            **kwargs
        )