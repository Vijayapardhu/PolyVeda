"""
User models for PolyVeda.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for PolyVeda.
    """
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        FACULTY = 'faculty', _('Faculty')
        HOD = 'hod', _('Head of Department')
        ADMIN = 'admin', _('Administrator')
        MANAGEMENT = 'management', _('Management')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending Approval')

    # Override username field to use email
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Role and status
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('User role in the system')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Account status')
    )
    
    # Additional fields
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Contact phone number')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_expires = models.DateTimeField(null=True, blank=True)
    
    # Password reset
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    
    # Device management
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_user_agent = models.TextField(blank=True)
    
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
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name
    
    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == self.Role.STUDENT
    
    @property
    def is_faculty(self):
        """Check if user is faculty."""
        return self.role == self.Role.FACULTY
    
    @property
    def is_hod(self):
        """Check if user is HOD."""
        return self.role == self.Role.HOD
    
    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.role == self.Role.ADMIN
    
    @property
    def is_management(self):
        """Check if user is management."""
        return self.role == self.Role.MANAGEMENT
    
    @property
    def is_active_user(self):
        """Check if user account is active."""
        return self.status == self.Status.ACTIVE


class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
        ],
        blank=True
    )
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True
    )
    
    # Academic Information (for students)
    roll_number = models.CharField(max_length=20, blank=True, unique=True)
    branch = models.CharField(max_length=50, blank=True)
    semester = models.PositiveIntegerField(null=True, blank=True)
    year_of_admission = models.PositiveIntegerField(null=True, blank=True)
    section = models.CharField(max_length=10, blank=True)
    
    # Faculty Information
    employee_id = models.CharField(max_length=20, blank=True, unique=True)
    department = models.CharField(max_length=50, blank=True)
    designation = models.CharField(max_length=50, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    
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
    
    # Special Categories
    special_category = models.CharField(
        max_length=50,
        choices=[
            ('general', _('General')),
            ('obc', _('OBC')),
            ('sc', _('SC')),
            ('st', _('ST')),
            ('ews', _('EWS')),
            ('pwd', _('Person with Disability')),
        ],
        default='general'
    )
    ncc_cadet = models.BooleanField(default=False)
    ncc_rank = models.CharField(max_length=20, blank=True)
    
    # Profile Picture
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text=_('Profile picture (max 2MB)')
    )
    
    # Documents
    id_proof = models.FileField(
        upload_to='documents/id_proofs/',
        null=True,
        blank=True,
        help_text=_('Government ID proof')
    )
    address_proof = models.FileField(
        upload_to='documents/address_proofs/',
        null=True,
        blank=True,
        help_text=_('Address proof document')
    )
    
    # Timestamps
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


class UserSession(models.Model):
    """
    Track user sessions for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} at {self.created_at}"


class AuditLog(models.Model):
    """
    Audit trail for user actions.
    """
    class Action(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
        help_text=_('User who performed the action')
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    entity = models.CharField(max_length=50, help_text=_('Model/entity being acted upon'))
    entity_id = models.CharField(max_length=50, help_text=_('ID of the entity'))
    details = models.JSONField(default=dict, help_text=_('Additional details about the action'))
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['entity', 'entity_id']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.actor} {self.action} {self.entity}:{self.entity_id} at {self.timestamp}"