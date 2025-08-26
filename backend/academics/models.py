"""
Academic models for PolyVeda with SQLite compatibility.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid


class AcademicYear(models.Model):
    """
    Academic year management for institutions.
    """
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    semesters = models.TextField(default='[]')  # JSON array stored as text for SQLite
    holidays = models.TextField(default='[]')  # JSON array stored as text for SQLite
    exam_schedules = models.TextField(default='[]')  # JSON array stored as text for SQLite
    attendance_threshold = models.PositiveIntegerField(default=75)
    grading_system = models.CharField(max_length=20, default='percentage')
    grade_scale = models.TextField(default='{}')  # JSON stored as text for SQLite
    
    class Meta:
        db_table = 'academic_years'
        unique_together = [['institution', 'name']]
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date__lt=models.F('end_date')),
                name='valid_academic_year_dates'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.institution.name}"
    
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
    Academic departments within institutions.
    """
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    accreditation = models.TextField(default='{}')  # JSON stored as text for SQLite
    facilities = models.TextField(default='[]')  # JSON array stored as text for SQLite
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    office_location = models.CharField(max_length=200, blank=True)
    max_students_per_section = models.PositiveIntegerField(default=60)
    max_faculty = models.PositiveIntegerField(default=20)
    department_rules = models.TextField(default='{}')  # JSON stored as text for SQLite
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        unique_together = [['institution', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.institution.name}"
    
    @property
    def total_students(self):
        return self.courses.aggregate(
            total=models.Count('enrollments__student', distinct=True)
        )['total'] or 0
    
    @property
    def total_faculty(self):
        return self.courses.aggregate(
            total=models.Count('faculty', distinct=True)
        )['total'] or 0


class Course(models.Model):
    """
    Academic courses offered by departments.
    """
    class CourseType(models.TextChoices):
        THEORY = 'theory', _('Theory')
        PRACTICAL = 'practical', _('Practical')
        LABORATORY = 'laboratory', _('Laboratory')
        PROJECT = 'project', _('Project')
        SEMINAR = 'seminar', _('Seminar')
        WORKSHOP = 'workshop', _('Workshop')
    
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='courses')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    short_title = models.CharField(max_length=50, blank=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    credits = models.PositiveIntegerField()
    hours_per_week = models.PositiveIntegerField(default=3)
    learning_objectives = models.TextField(default='[]')  # JSON array stored as text for SQLite
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    assessment_pattern = models.TextField(default='{}')  # JSON stored as text for SQLite
    grading_criteria = models.TextField(default='{}')  # JSON stored as text for SQLite
    passing_marks = models.PositiveIntegerField(default=40)
    course_type = models.CharField(max_length=20, choices=CourseType.choices, default=CourseType.THEORY)
    is_elective = models.BooleanField(default=False)
    max_students = models.PositiveIntegerField(default=60)
    min_students = models.PositiveIntegerField(default=5)
    textbooks = models.TextField(default='[]')  # JSON array stored as text for SQLite
    reference_materials = models.TextField(default='[]')  # JSON array stored as text for SQLite
    online_resources = models.TextField(default='[]')  # JSON array stored as text for SQLite
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = [['institution', 'code']]
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def total_enrollments(self):
        return self.enrollments.count()
    
    @property
    def average_attendance(self):
        from .models import Attendance
        attendances = Attendance.objects.filter(
            enrollment__course=self
        ).aggregate(
            avg=models.Avg('status')
        )
        return attendances['avg'] or 0


class Section(models.Model):
    """
    Course sections for specific academic years.
    """
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='sections')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()
    current_enrollment = models.PositiveIntegerField(default=0)
    advisor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='advised_sections')
    section_rules = models.TextField(default='{}')  # JSON stored as text for SQLite
    special_instructions = models.TextField(blank=True)
    average_attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_performance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sections'
        unique_together = [['course', 'academic_year', 'name']]
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.academic_year.name})"
    
    @property
    def enrollment_percentage(self):
        if self.capacity > 0:
            return (self.current_enrollment / self.capacity) * 100
        return 0
    
    def update_performance_metrics(self):
        """Update average attendance and performance metrics."""
        from .models import Attendance, Result
        
        # Calculate average attendance
        attendance_avg = Attendance.objects.filter(
            enrollment__section=self
        ).aggregate(
            avg=models.Avg('status')
        )['avg'] or 0
        
        # Calculate average performance
        performance_avg = Result.objects.filter(
            enrollment__section=self
        ).aggregate(
            avg=models.Avg('percentage')
        )['avg'] or 0
        
        self.average_attendance = attendance_avg
        self.average_performance = performance_avg
        self.save(update_fields=['average_attendance', 'average_performance'])


class Enrollment(models.Model):
    """
    Student enrollment in course sections.
    """
    class EnrollmentType(models.TextChoices):
        REGULAR = 'regular', _('Regular')
        AUDIT = 'audit', _('Audit')
        DROP_IN = 'drop_in', _('Drop-in')
        TRANSFER = 'transfer', _('Transfer')
    
    class EnrollmentStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        DROPPED = 'dropped', _('Dropped')
        COMPLETED = 'completed', _('Completed')
        SUSPENDED = 'suspended', _('Suspended')
    
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_type = models.CharField(max_length=20, choices=EnrollmentType.choices, default=EnrollmentType.REGULAR)
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    current_grade = models.CharField(max_length=5, blank=True)
    is_audit = models.BooleanField(default=False)
    special_considerations = models.TextField(default='{}')  # JSON stored as text for SQLite
    academic_warnings = models.TextField(default='[]')  # JSON array stored as text for SQLite
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = [['student', 'section']]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.section}"
    
    def update_attendance_percentage(self):
        """Update attendance percentage based on attendance records."""
        from .models import Attendance
        
        total_classes = Attendance.objects.filter(enrollment=self).count()
        if total_classes > 0:
            present_classes = Attendance.objects.filter(
                enrollment=self,
                status__in=['present', 'half_day']
            ).count()
            self.attendance_percentage = (present_classes / total_classes) * 100
            self.save(update_fields=['attendance_percentage'])
    
    @property
    def is_at_risk(self):
        """Check if student is at risk based on attendance."""
        return self.attendance_percentage < 75


class Timetable(models.Model):
    """
    Class timetables for course sections.
    """
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='timetables')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    day_of_week = models.PositiveIntegerField(choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    building = models.CharField(max_length=50, blank=True)
    room_capacity = models.PositiveIntegerField(default=60)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    meeting_platform = models.CharField(max_length=50, blank=True)
    is_recurring = models.BooleanField(default=True)
    recurrence_pattern = models.TextField(default='{}')  # JSON stored as text for SQLite
    exceptions = models.TextField(default='[]')  # JSON array stored as text for SQLite
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetables'
        unique_together = [['section', 'day_of_week', 'start_time']]
    
    def __str__(self):
        return f"{self.section} - {self.get_day_of_week_display()} {self.start_time}"
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes."""
        start = self.start_time
        end = self.end_time
        return (end.hour - start.hour) * 60 + (end.minute - start.minute)
    
    def check_conflicts(self):
        """Check for timetable conflicts."""
        return Timetable.objects.filter(
            section__academic_year=self.section.academic_year,
            day_of_week=self.day_of_week,
            room=self.room,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk).exists()


class Attendance(models.Model):
    """
    Student attendance records.
    """
    class Status(models.TextChoices):
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        LATE = 'late', _('Late')
        HALF_DAY = 'half_day', _('Half Day')
        EXCUSED = 'excused', _('Excused')
    
    class MarkedMethod(models.TextChoices):
        MANUAL = 'manual', _('Manual')
        QR_CODE = 'qr_code', _('QR Code')
        BIOMETRIC = 'biometric', _('Biometric')
        GPS = 'gps', _('GPS')
        FACIAL_RECOGNITION = 'facial_recognition', _('Facial Recognition')
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABSENT)
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_method = models.CharField(max_length=20, choices=MarkedMethod.choices, default=MarkedMethod.MANUAL)
    location = models.TextField(default='{}')  # JSON stored as text for SQLite
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_attendances')
    verified_at = models.DateTimeField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    anomaly_detected = models.BooleanField(default=False)
    anomaly_reason = models.TextField(blank=True)
    supporting_documents = models.TextField(default='[]')  # JSON array stored as text for SQLite
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendances'
        unique_together = [['enrollment', 'date']]
        indexes = [
            models.Index(fields=['enrollment', 'date']),
            models.Index(fields=['status', 'date']),
            models.Index(fields=['marked_method']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.date} - {self.status}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update enrollment attendance percentage
        self.enrollment.update_attendance_percentage()
        # Update section metrics
        self.enrollment.section.update_performance_metrics()
    
    @property
    def is_suspicious(self):
        """Check if attendance record is suspicious."""
        return self.anomaly_detected or (self.confidence_score and self.confidence_score < 0.7)


class Assessment(models.Model):
    """
    Academic assessments and assignments.
    """
    class Type(models.TextChoices):
        QUIZ = 'quiz', _('Quiz')
        ASSIGNMENT = 'assignment', _('Assignment')
        MIDTERM = 'midterm', _('Midterm')
        FINAL = 'final', _('Final')
        PROJECT = 'project', _('Project')
        PRESENTATION = 'presentation', _('Presentation')
        LAB_REPORT = 'lab_report', _('Lab Report')
        RESEARCH_PAPER = 'research_paper', _('Research Paper')
    
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='assessments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assessment_type = models.CharField(max_length=20, choices=Type.choices)
    instructions = models.TextField(blank=True)
    total_marks = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    late_submission_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_group_assessment = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1)
    plagiarism_check_enabled = models.BooleanField(default=False)
    plagiarism_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    rubric = models.TextField(default='{}')  # JSON stored as text for SQLite
    evaluation_criteria = models.TextField(default='[]')  # JSON array stored as text for SQLite
    attachments = models.TextField(default='[]')  # JSON array stored as text for SQLite
    sample_solutions = models.TextField(default='[]')  # JSON array stored as text for SQLite
    due_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='published_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments'
        indexes = [
            models.Index(fields=['course', 'due_date']),
            models.Index(fields=['assessment_type']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.course.code}"
    
    @property
    def submission_count(self):
        return self.submissions.count()
    
    @property
    def average_score(self):
        from .models import Submission
        submissions = Submission.objects.filter(assessment=self, is_graded=True)
        if submissions.exists():
            return submissions.aggregate(avg=models.Avg('percentage'))['avg']
        return 0
    
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
    Student submissions for assessments.
    """
    class SubmissionMethod(models.TextChoices):
        FILE_UPLOAD = 'file_upload', _('File Upload')
        TEXT_ENTRY = 'text_entry', _('Text Entry')
        URL_SUBMISSION = 'url_submission', _('URL Submission')
        HANDWRITTEN = 'handwritten', _('Handwritten')
    
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', _('Submitted')
        LATE = 'late', _('Late')
        GRADED = 'graded', _('Graded')
        RETURNED = 'returned', _('Returned')
        REJECTED = 'rejected', _('Rejected')
    
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='submissions')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    submission_method = models.CharField(max_length=20, choices=SubmissionMethod.choices, default=SubmissionMethod.FILE_UPLOAD)
    files = models.TextField(default='[]')  # JSON array stored as text for SQLite
    text_content = models.TextField(blank=True)
    submission_url = models.URLField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=5, blank=True)
    rubric_scores = models.TextField(default='{}')  # JSON stored as text for SQLite
    comments = models.TextField(default='{}')  # JSON stored as text for SQLite
    grading_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    late_penalty_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    plagiarism_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    plagiarism_report = models.TextField(default='{}')  # JSON stored as text for SQLite
    is_plagiarized = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'submissions'
        unique_together = [['student', 'assessment']]
        indexes = [
            models.Index(fields=['student', 'assessment']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.title}"
    
    def save(self, *args, **kwargs):
        # Calculate percentage if marks are provided
        if self.marks_obtained and self.assessment.total_marks:
            self.percentage = (self.marks_obtained / self.assessment.total_marks) * 100
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        return self.submitted_at > self.assessment.due_date
    
    def apply_late_penalty(self):
        """Apply late submission penalty."""
        if self.is_overdue and self.assessment.late_submission_penalty > 0:
            penalty_amount = (self.assessment.late_submission_penalty / 100) * self.marks_obtained
            self.marks_obtained -= penalty_amount
            self.late_penalty_applied = penalty_amount
            self.save(update_fields=['marks_obtained', 'late_penalty_applied'])


class Result(models.Model):
    """
    Academic results and grades.
    """
    class Status(models.TextChoices):
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        INCOMPLETE = 'incomplete', _('Incomplete')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
    
    institution = models.ForeignKey('accounts.Institution', on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='results')
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    letter_grade = models.CharField(max_length=5, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INCOMPLETE)
    is_backlog = models.BooleanField(default=False)
    backlog_count = models.PositiveIntegerField(default=0)
    improvement_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'results'
        unique_together = [['student', 'course', 'academic_year']]
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['course', 'academic_year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code} - {self.percentage}%"
    
    def save(self, *args, **kwargs):
        # Calculate total marks and percentage
        if self.marks_obtained and self.total_marks:
            self.percentage = (self.marks_obtained / self.total_marks) * 100
        super().save(*args, **kwargs)
    
    @property
    def is_pass(self):
        return self.percentage >= self.course.passing_marks
    
    @property
    def cgpa_equivalent(self):
        """Convert percentage to CGPA equivalent."""
        if self.percentage >= 90:
            return 4.0
        elif self.percentage >= 80:
            return 3.5
        elif self.percentage >= 70:
            return 3.0
        elif self.percentage >= 60:
            return 2.5
        elif self.percentage >= 50:
            return 2.0
        else:
            return 0.0