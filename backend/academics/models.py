"""
Academic models for PolyVeda.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Department(models.Model):
    """
    Academic departments.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    hod = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_hod',
        limit_choices_to={'role': User.Role.HOD}
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    """
    Academic courses.
    """
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    credits = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    description = models.TextField(blank=True)
    syllabus = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['semester', 'code']
        unique_together = ['code', 'semester']
    
    def __str__(self):
        return f"{self.code} - {self.title}"


class Section(models.Model):
    """
    Student sections within departments.
    """
    name = models.CharField(max_length=10)  # e.g., 'A', 'B', 'C'
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sections')
    semester = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    academic_year = models.CharField(max_length=9)  # e.g., '2023-2024'
    capacity = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sections'
        verbose_name = _('section')
        verbose_name_plural = _('sections')
        unique_together = ['name', 'department', 'semester', 'academic_year']
        ordering = ['department', 'semester', 'name']
    
    def __str__(self):
        return f"{self.department.code} - {self.semester}{self.name} ({self.academic_year})"


class Enrollment(models.Model):
    """
    Student course enrollments.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.CharField(max_length=9)
    semester = models.PositiveIntegerField()
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    grade = models.CharField(max_length=2, blank=True)  # A+, A, B+, B, etc.
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    
    class Meta:
        db_table = 'enrollments'
        verbose_name = _('enrollment')
        verbose_name_plural = _('enrollments')
        unique_together = ['student', 'course', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['course', 'section']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code}"


class Timetable(models.Model):
    """
    Class timetables.
    """
    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', _('Monday')
        TUESDAY = 'tuesday', _('Tuesday')
        WEDNESDAY = 'wednesday', _('Wednesday')
        THURSDAY = 'thursday', _('Thursday')
        FRIDAY = 'friday', _('Friday')
        SATURDAY = 'saturday', _('Saturday')
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetables')
    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_timetables',
        limit_choices_to={'role': User.Role.FACULTY}
    )
    day = models.CharField(max_length=10, choices=DayOfWeek.choices)
    period = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    room = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetables'
        verbose_name = _('timetable')
        verbose_name_plural = _('timetables')
        unique_together = ['section', 'day', 'period', 'academic_year']
        ordering = ['day', 'period']
        indexes = [
            models.Index(fields=['section', 'academic_year']),
            models.Index(fields=['faculty', 'academic_year']),
        ]
    
    def __str__(self):
        return f"{self.section} - {self.course.code} - {self.day} P{self.period}"


class Attendance(models.Model):
    """
    Student attendance records.
    """
    class Status(models.TextChoices):
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        LATE = 'late', _('Late')
        LEAVE = 'leave', _('Leave')
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    period = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABSENT)
    marked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_marked',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendances'
        verbose_name = _('attendance')
        verbose_name_plural = _('attendances')
        unique_together = ['enrollment', 'date', 'period']
        indexes = [
            models.Index(fields=['enrollment', 'date']),
            models.Index(fields=['marked_by', 'date']),
        ]
        ordering = ['-date', 'period']
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.date} P{self.period}"


class Assessment(models.Model):
    """
    Academic assessments (assignments, tests, etc.).
    """
    class Type(models.TextChoices):
        ASSIGNMENT = 'assignment', _('Assignment')
        INTERNAL_TEST = 'internal_test', _('Internal Test')
        LAB_TEST = 'lab_test', _('Lab Test')
        PROJECT = 'project', _('Project')
        QUIZ = 'quiz', _('Quiz')
        PRESENTATION = 'presentation', _('Presentation')
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=Type.choices)
    description = models.TextField(blank=True)
    max_marks = models.PositiveIntegerField()
    weightage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assessments',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments'
        verbose_name = _('assessment')
        verbose_name_plural = _('assessments')
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['course', 'type']),
            models.Index(fields=['created_by', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Submission(models.Model):
    """
    Student submissions for assessments.
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
        limit_choices_to={'role__in': [User.Role.FACULTY, User.Role.HOD]}
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'submissions'
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')
        unique_together = ['assessment', 'student']
        indexes = [
            models.Index(fields=['assessment', 'submitted_at']),
            models.Index(fields=['student', 'submitted_at']),
        ]
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.title}"
    
    def save(self, *args, **kwargs):
        # Check if submission is late
        if self.submitted_at and self.assessment.due_date:
            self.is_late = self.submitted_at > self.assessment.due_date
        super().save(*args, **kwargs)


class Result(models.Model):
    """
    Final results for students.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='results',
        limit_choices_to={'role': User.Role.STUDENT}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    academic_year = models.CharField(max_length=9)
    semester = models.PositiveIntegerField()
    internal_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    external_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    grade = models.CharField(max_length=2, blank=True)
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'results'
        verbose_name = _('result')
        verbose_name_plural = _('results')
        unique_together = ['student', 'course', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['course', 'academic_year']),
            models.Index(fields=['is_published']),
        ]
        ordering = ['-academic_year', 'semester']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code} ({self.academic_year})"