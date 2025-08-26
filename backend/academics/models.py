"""
Advanced Academic models for PolyVeda with enterprise features.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import uuid
from accounts.models import User, Institution


class AcademicYear(models.Model):
    """
    Academic year management with advanced features.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=50)  # e.g., "2023-2024"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    # Academic calendar
    semesters = JSONField(default=list)  # List of semester periods
    holidays = JSONField(default=list)   # List of holiday dates
    exam_schedules = JSONField(default=dict)
    
    # Configuration
    attendance_threshold = models.DecimalField(
        max_digits=5, decimal_places=2, default=75.00,
        help_text=_('Minimum attendance percentage required')
    )
    grading_system = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage'),
            ('letter_grade', 'Letter Grade'),
            ('gpa', 'GPA'),
            ('custom', 'Custom'),
        ],
        default='percentage'
    )
    grade_scale = JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_years'
        unique_together = ['institution', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.institution.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one current academic year per institution
        if self.is_current:
            AcademicYear.objects.filter(
                institution=self.institution,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Department(models.Model):
    """
    Advanced department model with comprehensive features.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    
    # Department head
    hod = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_hod',
        limit_choices_to={'role': User.Role.HOD}
    )
    
    # Academic information
    established_year = models.PositiveIntegerField(null=True, blank=True)
    accreditation = JSONField(default=dict)
    facilities = JSONField(default=list)
    
    # Contact information
    office_location = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Configuration
    max_students_per_section = models.PositiveIntegerField(default=60)
    max_faculty = models.PositiveIntegerField(default=20)
    department_rules = JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        unique_together = ['institution', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.institution.name} - {self.name} ({self.code})"
    
    @property
    def total_students(self):
        return self.sections.aggregate(
            total=models.Count('enrollments__student', distinct=True)
        )['total'] or 0
    
    @property
    def total_faculty(self):
        return self.faculty.count()


class Course(models.Model):
    """
    Advanced course model with comprehensive curriculum management.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    
    # Basic information
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    short_title = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    # Academic details
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    credits = models.DecimalField(
        max_digits=3, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    hours_per_week = models.PositiveIntegerField(default=3)
    
    # Curriculum
    syllabus = models.TextField(blank=True)
    learning_objectives = ArrayField(models.TextField(), blank=True, default=list)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Assessment structure
    assessment_pattern = JSONField(default=dict)
    grading_criteria = JSONField(default=dict)
    passing_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=40.00
    )
    
    # Course type
    course_type = models.CharField(
        max_length=20,
        choices=[
            ('theory', 'Theory'),
            ('practical', 'Practical'),
            ('lab', 'Laboratory'),
            ('project', 'Project'),
            ('seminar', 'Seminar'),
            ('workshop', 'Workshop'),
            ('internship', 'Internship'),
        ],
        default='theory'
    )
    
    # Advanced features
    is_elective = models.BooleanField(default=False)
    max_students = models.PositiveIntegerField(null=True, blank=True)
    min_students = models.PositiveIntegerField(default=5)
    
    # Resources
    textbooks = JSONField(default=list)
    reference_materials = JSONField(default=list)
    online_resources = JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = ['institution', 'code', 'semester']
        ordering = ['semester', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def total_enrollments(self):
        return self.enrollments.count()
    
    @property
    def average_attendance(self):
        from django.db.models import Avg
        return self.enrollments.aggregate(
            avg_attendance=Avg('attendances__status')
        )['avg_attendance'] or 0


class Section(models.Model):
    """
    Advanced section model with intelligent student management.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='sections')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sections')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='sections')
    
    # Basic information
    name = models.CharField(max_length=10)  # e.g., 'A', 'B', 'C'
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    # Capacity and enrollment
    capacity = models.PositiveIntegerField(default=60)
    current_enrollment = models.PositiveIntegerField(default=0)
    
    # Section advisor
    advisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advised_sections',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    
    # Configuration
    section_rules = JSONField(default=dict)
    special_instructions = models.TextField(blank=True)
    
    # Performance tracking
    average_attendance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    average_performance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sections'
        unique_together = ['institution', 'department', 'academic_year', 'name', 'semester']
        ordering = ['department', 'semester', 'name']
    
    def __str__(self):
        return f"{self.department.code} - {self.semester}{self.name} ({self.academic_year.name})"
    
    @property
    def enrollment_percentage(self):
        if self.capacity > 0:
            return (self.current_enrollment / self.capacity) * 100
        return 0
    
    def update_performance_metrics(self):
        """Update section performance metrics."""
        from django.db.models import Avg
        
        # Update average attendance
        avg_attendance = self.enrollments.aggregate(
            avg=Avg('attendances__status')
        )['avg'] or 0
        self.average_attendance = avg_attendance
        
        # Update average performance
        avg_performance = self.enrollments.aggregate(
            avg=Avg('results__total_marks')
        )['avg'] or 0
        self.average_performance = avg_performance
        
        self.save(update_fields=['average_attendance', 'average_performance'])


class Enrollment(models.Model):
    """
    Advanced enrollment model with comprehensive tracking.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment details
    enrollment_date = models.DateField(auto_now_add=True)
    enrollment_type = models.CharField(
        max_length=20,
        choices=[
            ('regular', 'Regular'),
            ('lateral', 'Lateral Entry'),
            ('transfer', 'Transfer'),
            ('repeater', 'Repeater'),
        ],
        default='regular'
    )
    
    # Academic status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('dropped', 'Dropped'),
            ('suspended', 'Suspended'),
            ('failed', 'Failed'),
        ],
        default='active'
    )
    
    # Performance tracking
    attendance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    current_grade = models.CharField(max_length=2, blank=True)
    grade_points = models.DecimalField(
        max_digits=3, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    
    # Advanced features
    is_audit = models.BooleanField(default=False)
    special_considerations = JSONField(default=dict)
    academic_warnings = ArrayField(models.TextField(), blank=True, default=list)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['course', 'section']),
            models.Index(fields=['status', 'academic_year']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code}"
    
    def update_attendance_percentage(self):
        """Update attendance percentage."""
        total_sessions = self.attendances.count()
        if total_sessions > 0:
            present_sessions = self.attendances.filter(status='present').count()
            self.attendance_percentage = (present_sessions / total_sessions) * 100
            self.save(update_fields=['attendance_percentage'])
    
    @property
    def is_at_risk(self):
        """Check if student is at academic risk."""
        return (
            self.attendance_percentage < 75 or
            len(self.academic_warnings) > 2 or
            self.status == 'suspended'
        )


class Timetable(models.Model):
    """
    Advanced timetable model with intelligent scheduling.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='timetables')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetables')
    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_timetables',
        limit_choices_to={'role': User.Role.FACULTY}
    )
    
    # Schedule details
    day = models.CharField(
        max_length=10,
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
        ]
    )
    period = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Location
    room = models.CharField(max_length=20)
    building = models.CharField(max_length=50, blank=True)
    room_capacity = models.PositiveIntegerField(null=True, blank=True)
    
    # Advanced features
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    meeting_platform = models.CharField(max_length=50, blank=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=True)
    recurrence_pattern = JSONField(default=dict)
    exceptions = JSONField(default=list)  # Dates when class is cancelled/rescheduled
    
    # Status
    is_active = models.BooleanField(default=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetables'
        unique_together = ['section', 'day', 'period', 'academic_year']
        ordering = ['day', 'period']
        indexes = [
            models.Index(fields=['section', 'academic_year']),
            models.Index(fields=['faculty', 'academic_year']),
            models.Index(fields=['room', 'day']),
        ]
    
    def __str__(self):
        return f"{self.section} - {self.course.code} - {self.day} P{self.period}"
    
    @property
    def duration_minutes(self):
        """Calculate class duration in minutes."""
        start = self.start_time
        end = self.end_time
        return (end.hour - start.hour) * 60 + (end.minute - start.minute)
    
    def check_conflicts(self):
        """Check for scheduling conflicts."""
        conflicts = []
        
        # Check faculty conflicts
        faculty_conflicts = Timetable.objects.filter(
            faculty=self.faculty,
            day=self.day,
            period=self.period,
            academic_year=self.academic_year
        ).exclude(pk=self.pk)
        
        if faculty_conflicts.exists():
            conflicts.append('Faculty has another class at this time')
        
        # Check room conflicts
        room_conflicts = Timetable.objects.filter(
            room=self.room,
            day=self.day,
            period=self.period,
            academic_year=self.academic_year
        ).exclude(pk=self.pk)
        
        if room_conflicts.exists():
            conflicts.append('Room is occupied at this time')
        
        return conflicts


class Attendance(models.Model):
    """
    Advanced attendance model with AI-powered analytics.
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    period = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    
    # Attendance status
    status = models.CharField(
        max_length=10,
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('leave', 'Leave'),
            ('half_day', 'Half Day'),
            ('excused', 'Excused'),
        ],
        default='absent'
    )
    
    # Advanced tracking
    marked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_marked',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_method = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('qr_code', 'QR Code'),
            ('biometric', 'Biometric'),
            ('gps', 'GPS'),
            ('facial_recognition', 'Facial Recognition'),
        ],
        default='manual'
    )
    
    # Location tracking
    location = JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_verified'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    confidence_score = models.DecimalField(
        max_digits=3, decimal_places=2,
        null=True, blank=True,
        help_text=_('AI confidence score for automated marking')
    )
    anomaly_detected = models.BooleanField(default=False)
    anomaly_reason = models.TextField(blank=True)
    
    # Additional information
    remarks = models.TextField(blank=True)
    supporting_documents = JSONField(default=list)
    
    class Meta:
        db_table = 'attendances'
        unique_together = ['enrollment', 'date', 'period']
        indexes = [
            models.Index(fields=['enrollment', 'date']),
            models.Index(fields=['marked_by', 'date']),
            models.Index(fields=['status', 'date']),
        ]
        ordering = ['-date', 'period']
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.date} P{self.period}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update enrollment attendance percentage
            self.enrollment.update_attendance_percentage()
            
            # Update section metrics
            self.enrollment.section.update_performance_metrics()
    
    @property
    def is_suspicious(self):
        """Check if attendance marking is suspicious."""
        return (
            self.anomaly_detected or
            (self.confidence_score and self.confidence_score < 0.7) or
            self.marked_method == 'manual' and self.location
        )


class Assessment(models.Model):
    """
    Advanced assessment model with comprehensive evaluation features.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='assessments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    
    # Assessment type
    type = models.CharField(
        max_length=20,
        choices=[
            ('assignment', 'Assignment'),
            ('internal_test', 'Internal Test'),
            ('lab_test', 'Lab Test'),
            ('project', 'Project'),
            ('quiz', 'Quiz'),
            ('presentation', 'Presentation'),
            ('viva', 'Viva'),
            ('practical', 'Practical'),
            ('mid_semester', 'Mid Semester'),
            ('end_semester', 'End Semester'),
            ('continuous_evaluation', 'Continuous Evaluation'),
        ]
    )
    
    # Assessment structure
    max_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    weightage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Timing
    due_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    late_submission_penalty = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    
    # Advanced features
    is_group_assessment = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1)
    plagiarism_check_enabled = models.BooleanField(default=True)
    plagiarism_threshold = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00
    )
    
    # Rubric
    rubric = JSONField(default=dict)
    evaluation_criteria = ArrayField(models.TextField(), blank=True, default=list)
    
    # Resources
    attachments = JSONField(default=list)
    sample_solutions = JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_assessments',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assessments',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['course', 'type']),
            models.Index(fields=['created_by', 'due_date']),
            models.Index(fields=['is_published', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def submission_count(self):
        return self.submissions.count()
    
    @property
    def average_score(self):
        from django.db.models import Avg
        return self.submissions.aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    def publish(self, published_by):
        """Publish the assessment."""
        self.is_published = True
        self.published_at = timezone.now()
        self.published_by = published_by
        self.save(update_fields=['is_published', 'published_at', 'published_by'])


class Submission(models.Model):
    """
    Advanced submission model with comprehensive evaluation features.
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    
    # Submission details
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission_method = models.CharField(
        max_length=20,
        choices=[
            ('file_upload', 'File Upload'),
            ('text_entry', 'Text Entry'),
            ('url', 'URL'),
            ('offline', 'Offline'),
        ],
        default='file_upload'
    )
    
    # Files and content
    files = JSONField(default=list)
    text_content = models.TextField(blank=True)
    submission_url = models.URLField(blank=True)
    
    # Evaluation
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    grade = models.CharField(max_length=2, blank=True)
    
    # Feedback
    feedback = models.TextField(blank=True)
    rubric_scores = JSONField(default=dict)
    comments = JSONField(default=list)
    
    # Grading
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    grading_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Advanced features
    is_late = models.BooleanField(default=False)
    late_penalty_applied = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    
    # Plagiarism detection
    plagiarism_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    plagiarism_report = JSONField(default=dict)
    is_plagiarized = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
            ('graded', 'Graded'),
            ('returned', 'Returned'),
            ('resubmitted', 'Resubmitted'),
        ],
        default='submitted'
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'submissions'
        unique_together = ['assessment', 'student']
        indexes = [
            models.Index(fields=['assessment', 'submitted_at']),
            models.Index(fields=['student', 'submitted_at']),
            models.Index(fields=['status', 'submitted_at']),
        ]
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.title}"
    
    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.submitted_at and self.assessment.due_date:
            self.is_late = self.submitted_at > self.assessment.due_date
        
        # Calculate percentage if score is provided
        if self.score and self.assessment.max_marks:
            self.percentage = (self.score / self.assessment.max_marks) * 100
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        return timezone.now() > self.assessment.due_date
    
    def apply_late_penalty(self):
        """Apply late submission penalty."""
        if self.is_late and self.assessment.late_submission_penalty > 0:
            penalty_amount = (self.score * self.assessment.late_submission_penalty) / 100
            self.score -= penalty_amount
            self.late_penalty_applied = penalty_amount
            self.save(update_fields=['score', 'late_penalty_applied'])


class Result(models.Model):
    """
    Advanced result model with comprehensive grade management.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='results',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='results')
    
    # Marks breakdown
    internal_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    external_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    total_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Grading
    grade = models.CharField(max_length=2, blank=True)
    grade_points = models.DecimalField(
        max_digits=3, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    letter_grade = models.CharField(max_length=3, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('published', 'Published'),
            ('revalued', 'Revalued'),
            ('supplementary', 'Supplementary'),
        ],
        default='pending'
    )
    
    # Advanced features
    is_backlog = models.BooleanField(default=False)
    backlog_count = models.PositiveIntegerField(default=0)
    improvement_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Publication
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_results',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD, User.Role.ADMIN]}
    )
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'results'
        unique_together = ['student', 'course', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['course', 'academic_year']),
            models.Index(fields=['is_published']),
            models.Index(fields=['status', 'academic_year']),
        ]
        ordering = ['-academic_year', 'course']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code} ({self.academic_year.name})"
    
    def save(self, *args, **kwargs):
        # Calculate total marks
        if self.internal_marks is not None and self.external_marks is not None:
            self.total_marks = self.internal_marks + self.external_marks
        
        # Calculate percentage
        if self.total_marks and self.course.max_marks:
            self.percentage = (self.total_marks / self.course.max_marks) * 100
        
        super().save(*args, **kwargs)
    
    @property
    def is_pass(self):
        return self.percentage and self.percentage >= self.course.passing_marks
    
    @property
    def cgpa_equivalent(self):
        """Convert grade points to CGPA equivalent."""
        if self.grade_points:
            return self.grade_points
        return 0