"""
Serializers for academics app.
"""
from rest_framework import serializers
from .models import (
    AcademicYear, Department, Course, Section, Enrollment,
    Timetable, Attendance, Assessment, Submission, Result
)
from accounts.serializers import UserSerializer, InstitutionSerializer


class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for AcademicYear model."""
    institution = InstitutionSerializer(read_only=True)
    
    class Meta:
        model = AcademicYear
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    institution = InstitutionSerializer(read_only=True)
    total_students = serializers.ReadOnlyField()
    total_faculty = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    institution = InstitutionSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    total_enrollments = serializers.ReadOnlyField()
    average_attendance = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model."""
    institution = InstitutionSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    advisor = UserSerializer(read_only=True)
    enrollment_percentage = serializers.ReadOnlyField()
    average_attendance = serializers.ReadOnlyField()
    average_performance = serializers.ReadOnlyField()
    
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model."""
    student = UserSerializer(read_only=True)
    section = SectionSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    attendance_percentage = serializers.ReadOnlyField()
    is_at_risk = serializers.ReadOnlyField()
    
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TimetableSerializer(serializers.ModelSerializer):
    """Serializer for Timetable model."""
    institution = InstitutionSerializer(read_only=True)
    section = SectionSerializer(read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = Timetable
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""
    enrollment = EnrollmentSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    is_suspicious = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment model."""
    institution = InstitutionSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    published_by = UserSerializer(read_only=True)
    submission_count = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SubmissionSerializer(serializers.ModelSerializer):
    """Serializer for Submission model."""
    student = UserSerializer(read_only=True)
    assessment = AssessmentSerializer(read_only=True)
    graded_by = UserSerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ResultSerializer(serializers.ModelSerializer):
    """Serializer for Result model."""
    institution = InstitutionSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    is_pass = serializers.ReadOnlyField()
    cgpa_equivalent = serializers.ReadOnlyField()
    
    class Meta:
        model = Result
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']