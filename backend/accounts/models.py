"""
Enterprise-Grade User models for PolyVeda with SQLite compatibility.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib
import secrets
import jwt
from django.conf import settings


class BlockchainCredential(models.Model):
    """
    Blockchain-based credential verification system.
    """
    credential_hash = models.CharField(max_length=64, unique=True)
    blockchain_tx_id = models.CharField(max_length=255, blank=True)
    credential_type = models.CharField(
        max_length=50,
        choices=[
            ('degree', 'Degree Certificate'),
            ('transcript', 'Academic Transcript'),
            ('achievement', 'Achievement Badge'),
            ('certification', 'Professional Certification'),
            ('microcredential', 'Micro-Credential'),
        ]
    )
    metadata = models.TextField(default='{}')  # JSON stored as text for SQLite
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blockchain_credentials'
        indexes = [
            models.Index(fields=['credential_hash']),
            models.Index(fields=['credential_type']),
            models.Index(fields=['is_verified']),
        ]


class AIInsight(models.Model):
    """
    AI-powered insights and predictions.
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ('attendance_prediction', 'Attendance Prediction'),
            ('performance_forecast', 'Performance Forecast'),
            ('risk_assessment', 'Risk Assessment'),
            ('recommendation', 'Recommendation'),
            ('anomaly_detection', 'Anomaly Detection'),
        ]
    )
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)
    prediction_data = models.TextField(default='{}')  # JSON stored as text for SQLite
    model_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_insights'
        indexes = [
            models.Index(fields=['user', 'insight_type']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['created_at']),
        ]


class ComplianceAudit(models.Model):
    """
    Comprehensive compliance and regulatory audit tracking.
    """
    class ComplianceType(models.TextChoices):
        GDPR = 'gdpr', _('GDPR Compliance')
        FERPA = 'ferpa', _('FERPA Compliance')
        SOC2 = 'soc2', _('SOC 2 Compliance')
        ISO27001 = 'iso27001', _('ISO 27001 Compliance')
        HIPAA = 'hipaa', _('HIPAA Compliance')
        PCI_DSS = 'pci_dss', _('PCI DSS Compliance')
        CCPA = 'ccpa', _('CCPA Compliance')
    
    compliance_type = models.CharField(max_length=20, choices=ComplianceType.choices)
    audit_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('remediated', 'Remediated'),
        ],
        default='pending'
    )
    findings = models.TextField(default='{}')  # JSON stored as text for SQLite
    remediation_plan = models.TextField(default='{}')  # JSON stored as text for SQLite
    auditor = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='conducted_audits')
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE, related_name='compliance_audits')
    
    class Meta:
        db_table = 'compliance_audits'
        indexes = [
            models.Index(fields=['compliance_type', 'status']),
            models.Index(fields=['audit_date']),
            models.Index(fields=['institution', 'compliance_type']),
        ]


class Institution(models.Model):
    """
    Enterprise multi-tenant institution model with advanced features.
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
    
    # Enterprise Features
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
            ('premium', 'Premium'),
            ('custom', 'Custom'),
        ],
        default='basic'
    )
    max_users = models.PositiveIntegerField(default=1000)
    max_storage_gb = models.PositiveIntegerField(default=10)
    features_enabled = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    # Advanced Configuration
    ai_features_enabled = models.TextField(default='{}')  # JSON stored as text for SQLite
    blockchain_enabled = models.BooleanField(default=False)
    compliance_frameworks = models.TextField(default='[]')  # JSON array stored as text for SQLite
    custom_integrations = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    # Security & Compliance
    encryption_key = models.BinaryField(null=True, blank=True)
    data_retention_policy = models.TextField(default='{}')  # JSON stored as text for SQLite
    privacy_settings = models.TextField(default='{}')  # JSON stored as text for SQLite
    security_config = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    # Performance & Monitoring
    performance_metrics = models.TextField(default='{}')  # JSON stored as text for SQLite
    sla_config = models.TextField(default='{}')  # JSON stored as text for SQLite
    monitoring_config = models.TextField(default='{}')  # JSON stored as text for SQLite
    
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
    
    def save(self, *args, **kwargs):
        if not self.encryption_key:
            import secrets
            self.encryption_key = secrets.token_bytes(32)
        super().save(*args, **kwargs)
    
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
    Enterprise-grade user model with advanced security and compliance features.
    """
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        FACULTY = 'faculty', _('Faculty')
        HOD = 'hod', _('Head of Department')
        ADMIN = 'admin', _('Administrator')
        MANAGEMENT = 'management', _('Management')
        SUPER_ADMIN = 'super_admin', _('Super Administrator')
        AUDITOR = 'auditor', _('Auditor')
        SUPPORT = 'support', _('Support Staff')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending Approval')
        LOCKED = 'locked', _('Account Locked')
        EXPIRED = 'expired', _('Account Expired')
        UNDER_REVIEW = 'under_review', _('Under Review')
        COMPLIANCE_HOLD = 'compliance_hold', _('Compliance Hold')

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
    permissions = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    # Enterprise Security features
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    backup_codes = models.TextField(default='[]')  # JSON array stored as text for SQLite
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expires_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Advanced Security
    biometric_enabled = models.BooleanField(default=False)
    biometric_data_hash = models.CharField(max_length=64, blank=True)
    hardware_token_enabled = models.BooleanField(default=False)
    hardware_token_id = models.CharField(max_length=100, blank=True)
    
    # Session management
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_location = models.TextField(default='{}')  # JSON stored as text for SQLite
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
    
    # Enterprise Features
    preferences = models.TextField(default='{}')  # JSON stored as text for SQLite
    notification_settings = models.TextField(default='{}')  # JSON stored as text for SQLite
    language = models.CharField(max_length=10, default='en-IN')
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    # Compliance & Privacy
    privacy_consent = models.BooleanField(default=False)
    privacy_consent_date = models.DateTimeField(null=True, blank=True)
    data_processing_consent = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    data_export_requested = models.BooleanField(default=False)
    data_deletion_requested = models.BooleanField(default=False)
    
    # AI & Analytics
    ai_preferences = models.TextField(default='{}')  # JSON stored as text for SQLite
    analytics_consent = models.BooleanField(default=False)
    personalized_recommendations = models.BooleanField(default=True)
    
    # Blockchain & Credentials
    blockchain_wallet_address = models.CharField(max_length=42, blank=True)
    digital_credentials = models.TextField(default='[]')  # JSON array stored as text for SQLite
    
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
            models.Index(fields=['blockchain_wallet_address']),
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
        import json
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = json.dumps(codes)
        self.save(update_fields=['backup_codes'])
        return codes
    
    def verify_backup_code(self, code):
        """Verify a backup code and remove it if valid."""
        import json
        codes = json.loads(self.backup_codes)
        if code in codes:
            codes.remove(code)
            self.backup_codes = json.dumps(codes)
            self.save(update_fields=['backup_codes'])
            return True
        return False
    
    def get_permissions(self):
        """Get user permissions including role-based and custom permissions."""
        import json
        cache_key = f"user_permissions_{self.id}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            # Base role permissions
            role_permissions = self.get_role_permissions()
            # Custom permissions
            custom_permissions = json.loads(self.permissions).get('custom', {})
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
                'access_ai_insights': True,
                'view_digital_credentials': True,
            },
            'faculty': {
                'view_own_profile': True,
                'manage_own_courses': True,
                'take_attendance': True,
                'grade_assignments': True,
                'view_student_profiles': True,
                'create_announcements': True,
                'access_ai_insights': True,
                'generate_reports': True,
            },
            'hod': {
                'view_own_profile': True,
                'manage_department': True,
                'view_department_reports': True,
                'approve_requests': True,
                'manage_faculty': True,
                'access_advanced_analytics': True,
                'manage_compliance': True,
            },
            'admin': {
                'view_own_profile': True,
                'manage_users': True,
                'manage_system': True,
                'view_all_reports': True,
                'manage_institution': True,
                'access_enterprise_features': True,
                'manage_security': True,
            },
            'management': {
                'view_own_profile': True,
                'view_analytics': True,
                'view_financial_reports': True,
                'manage_policies': True,
                'access_executive_dashboard': True,
                'manage_compliance': True,
            },
            'auditor': {
                'view_own_profile': True,
                'conduct_audits': True,
                'view_compliance_reports': True,
                'access_audit_logs': True,
                'generate_compliance_reports': True,
            },
            'support': {
                'view_own_profile': True,
                'manage_support_tickets': True,
                'view_user_profiles': True,
                'access_support_tools': True,
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
    
    def generate_jwt_token(self, expires_in=3600):
        """Generate JWT token for API access."""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'role': self.role,
            'institution_id': self.institution.id if self.institution else None,
            'exp': timezone.now() + timedelta(seconds=expires_in),
            'iat': timezone.now(),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def get_ai_insights(self, insight_type=None):
        """Get AI insights for the user."""
        insights = self.ai_insights.filter(expires_at__gt=timezone.now())
        if insight_type:
            insights = insights.filter(insight_type=insight_type)
        return insights.order_by('-created_at')
    
    def get_digital_credentials(self):
        """Get user's digital credentials."""
        import json
        credential_hashes = json.loads(self.digital_credentials)
        return BlockchainCredential.objects.filter(
            credential_hash__in=credential_hashes
        )
    
    def request_data_export(self):
        """Request data export for GDPR compliance."""
        self.data_export_requested = True
        self.save(update_fields=['data_export_requested'])
        # Trigger data export process
    
    def request_data_deletion(self):
        """Request data deletion for GDPR compliance."""
        self.data_deletion_requested = True
        self.save(update_fields=['data_deletion_requested'])
        # Trigger data deletion process


class UserProfile(models.Model):
    """
    Enterprise-grade user profile with comprehensive information and compliance features.
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
    academic_documents = models.TextField(default='[]')  # JSON array stored as text for SQLite
    
    # Social Media
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Enterprise Features
    preferences = models.TextField(default='{}')  # JSON stored as text for SQLite
    notification_preferences = models.TextField(default='{}')  # JSON stored as text for SQLite
    privacy_settings = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    # Compliance & Verification
    kyc_verified = models.BooleanField(default=False)
    kyc_verification_date = models.DateTimeField(null=True, blank=True)
    kyc_documents = models.TextField(default='[]')  # JSON array stored as text for SQLite
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    
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
    Enterprise-grade session tracking with advanced security features.
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
    location = models.TextField(default='{}')  # JSON stored as text for SQLite
    user_agent = models.TextField()
    is_secure = models.BooleanField(default=False)
    
    # Advanced Security
    device_fingerprint = models.CharField(max_length=64, blank=True)
    risk_score = models.PositiveIntegerField(default=0)
    threat_indicators = models.TextField(default='[]')  # JSON array stored as text for SQLite
    
    # Session management
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_remembered = models.BooleanField(default=False)
    
    # Security flags
    is_suspicious = models.BooleanField(default=False)
    anomaly_detected = models.BooleanField(default=False)
    security_events = models.TextField(default='[]')  # JSON array stored as text for SQLite
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['device_fingerprint']),
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
    
    def add_security_event(self, event_type, details):
        """Add security event to session."""
        import json
        events = json.loads(self.security_events)
        events.append({
            'type': event_type,
            'details': details,
            'timestamp': timezone.now().isoformat()
        })
        self.security_events = json.dumps(events)
        self.save(update_fields=['security_events'])


class AuditLog(models.Model):
    """
    Enterprise-grade audit trail for comprehensive compliance and security.
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
        SECURITY_EVENT = 'security_event', _('Security Event')
        COMPLIANCE_CHECK = 'compliance_check', _('Compliance Check')
        AI_INSIGHT_GENERATED = 'ai_insight_generated', _('AI Insight Generated')
        BLOCKCHAIN_CREDENTIAL = 'blockchain_credential', _('Blockchain Credential')
    
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
    details = models.TextField(default='{}', help_text=_('Additional details about the action'))  # JSON stored as text for SQLite
    changes = models.TextField(default='{}', help_text=_('Field changes for updates'))  # JSON stored as text for SQLite
    metadata = models.TextField(default='{}', help_text=_('Additional metadata'))  # JSON stored as text for SQLite
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    request_id = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # Compliance
    compliance_framework = models.CharField(max_length=20, blank=True)
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal'
    )
    
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
            models.Index(fields=['compliance_framework', 'timestamp']),
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