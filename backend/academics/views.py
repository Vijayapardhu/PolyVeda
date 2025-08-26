"""
API views for academics app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    AcademicYear, Department, Course, Section, Enrollment,
    Timetable, Attendance, Assessment, Submission, Result
)
from .serializers import (
    AcademicYearSerializer, DepartmentSerializer, CourseSerializer,
    SectionSerializer, EnrollmentSerializer, TimetableSerializer,
    AttendanceSerializer, AssessmentSerializer, SubmissionSerializer,
    ResultSerializer
)
from accounts.permissions import IsInstitutionMember, IsFacultyOrHigher


class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AcademicYear model.
    """
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'is_current']
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'name']
    ordering = ['-start_date']

    def get_queryset(self):
        return AcademicYear.objects.filter(institution=self.request.user.institution)

    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this academic year as current."""
        academic_year = self.get_object()
        AcademicYear.objects.filter(
            institution=academic_year.institution
        ).update(is_current=False)
        academic_year.is_current = True
        academic_year.save()
        return Response({'status': 'Academic year set as current'})


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department model.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'established_year']
    ordering = ['name']

    def get_queryset(self):
        return Department.objects.filter(institution=self.request.user.institution)

    @action(detail=True)
    def statistics(self, request, pk=None):
        """Get department statistics."""
        department = self.get_object()
        stats = {
            'total_students': department.total_students,
            'total_faculty': department.total_faculty,
            'total_courses': department.courses.count(),
            'total_sections': department.courses.aggregate(
                total=Count('sections')
            )['total'] or 0,
        }
        return Response(stats)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course model.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'department', 'course_type', 'is_elective', 'is_archived']
    search_fields = ['title', 'code', 'description']
    ordering_fields = ['title', 'code', 'credits']
    ordering = ['code']

    def get_queryset(self):
        return Course.objects.filter(institution=self.request.user.institution)

    @action(detail=True)
    def statistics(self, request, pk=None):
        """Get course statistics."""
        course = self.get_object()
        stats = {
            'total_enrollments': course.total_enrollments,
            'average_attendance': course.average_attendance,
            'total_sections': course.sections.count(),
            'total_assessments': course.assessments.count(),
        }
        return Response(stats)


class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Section model.
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'course', 'academic_year', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'capacity', 'current_enrollment']
    ordering = ['course__code', 'name']

    def get_queryset(self):
        return Section.objects.filter(institution=self.request.user.institution)

    @action(detail=True)
    def statistics(self, request, pk=None):
        """Get section statistics."""
        section = self.get_object()
        stats = {
            'enrollment_percentage': section.enrollment_percentage,
            'average_attendance': section.average_attendance,
            'average_performance': section.average_performance,
            'total_students': section.enrollments.count(),
        }
        return Response(stats)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment model.
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['section', 'academic_year', 'enrollment_type', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'student__email']
    ordering_fields = ['enrollment_date', 'attendance_percentage']
    ordering = ['-enrollment_date']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['student']:
            return Enrollment.objects.filter(student=user)
        return Enrollment.objects.filter(section__institution=user.institution)

    @action(detail=True, methods=['post'])
    def update_attendance(self, request, pk=None):
        """Update attendance percentage for enrollment."""
        enrollment = self.get_object()
        enrollment.update_attendance_percentage()
        return Response({'status': 'Attendance updated'})


class TimetableViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Timetable model.
    """
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'section', 'day_of_week', 'is_online']
    ordering_fields = ['day_of_week', 'start_time']
    ordering = ['day_of_week', 'start_time']

    def get_queryset(self):
        return Timetable.objects.filter(institution=self.request.user.institution)

    @action(detail=True)
    def conflicts(self, request, pk=None):
        """Check for timetable conflicts."""
        timetable = self.get_object()
        has_conflicts = timetable.check_conflicts()
        return Response({'has_conflicts': has_conflicts})


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance model.
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['enrollment', 'status', 'marked_method', 'is_verified']
    ordering_fields = ['date', 'marked_at']
    ordering = ['-date']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['student']:
            return Attendance.objects.filter(enrollment__student=user)
        return Attendance.objects.filter(enrollment__section__institution=user.institution)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify attendance record."""
        attendance = self.get_object()
        attendance.is_verified = True
        attendance.verified_by = request.user
        attendance.verified_at = timezone.now()
        attendance.save()
        return Response({'status': 'Attendance verified'})


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Assessment model.
    """
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsFacultyOrHigher]
    filterset_fields = ['institution', 'course', 'assessment_type', 'is_published']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'total_marks']
    ordering = ['-due_date']

    def get_queryset(self):
        return Assessment.objects.filter(institution=self.request.user.institution)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish assessment."""
        assessment = self.get_object()
        assessment.publish(request.user)
        return Response({'status': 'Assessment published'})

    @action(detail=True)
    def statistics(self, request, pk=None):
        """Get assessment statistics."""
        assessment = self.get_object()
        stats = {
            'submission_count': assessment.submission_count,
            'average_score': assessment.average_score,
            'is_overdue': assessment.is_overdue,
        }
        return Response(stats)


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Submission model.
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['assessment', 'student', 'status', 'submission_method']
    ordering_fields = ['submitted_at', 'marks_obtained']
    ordering = ['-submitted_at']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['student']:
            return Submission.objects.filter(student=user)
        return Submission.objects.filter(assessment__institution=user.institution)

    @action(detail=True, methods=['post'])
    def apply_late_penalty(self, request, pk=None):
        """Apply late submission penalty."""
        submission = self.get_object()
        submission.apply_late_penalty()
        return Response({'status': 'Late penalty applied'})


class ResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Result model.
    """
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]
    filterset_fields = ['institution', 'student', 'course', 'academic_year', 'status']
    ordering_fields = ['percentage', 'marks_obtained']
    ordering = ['-academic_year', 'course__code']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['student']:
            return Result.objects.filter(student=user)
        return Result.objects.filter(institution=user.institution)

    @action(detail=True)
    def cgpa_equivalent(self, request, pk=None):
        """Get CGPA equivalent for result."""
        result = self.get_object()
        cgpa = result.cgpa_equivalent
        return Response({'cgpa_equivalent': cgpa})


class AcademicDashboardView(viewsets.ViewSet):
    """
    Academic dashboard view.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstitutionMember]

    def list(self, request):
        """Get academic dashboard data."""
        user = request.user
        institution = user.institution
        
        # Get current academic year
        current_year = AcademicYear.objects.filter(
            institution=institution,
            is_current=True
        ).first()
        
        if not current_year:
            return Response({'error': 'No current academic year found'})
        
        # Dashboard statistics
        stats = {
            'total_departments': Department.objects.filter(institution=institution).count(),
            'total_courses': Course.objects.filter(institution=institution).count(),
            'total_sections': Section.objects.filter(
                institution=institution,
                academic_year=current_year
            ).count(),
            'total_students': Enrollment.objects.filter(
                section__institution=institution,
                academic_year=current_year
            ).count(),
            'total_faculty': user.institution.users.filter(role='faculty').count(),
            'average_attendance': Attendance.objects.filter(
                enrollment__section__institution=institution,
                enrollment__academic_year=current_year
            ).aggregate(avg=Avg('status'))['avg'] or 0,
        }
        
        return Response(stats)


class AcademicReportsView(viewsets.ViewSet):
    """
    Academic reports view.
    """
    permission_classes = [permissions.IsAuthenticated, IsFacultyOrHigher]

    def list(self, request):
        """Get available reports."""
        reports = [
            {'id': 'attendance', 'name': 'Attendance Report', 'description': 'Student attendance analysis'},
            {'id': 'performance', 'name': 'Performance Report', 'description': 'Student performance analysis'},
            {'id': 'enrollment', 'name': 'Enrollment Report', 'description': 'Course enrollment statistics'},
            {'id': 'assessment', 'name': 'Assessment Report', 'description': 'Assessment and grading analysis'},
        ]
        return Response(reports)

    @action(detail=True)
    def attendance(self, request, pk=None):
        """Generate attendance report."""
        # Implementation for attendance report
        return Response({'message': 'Attendance report generated'})

    @action(detail=True)
    def performance(self, request, pk=None):
        """Generate performance report."""
        # Implementation for performance report
        return Response({'message': 'Performance report generated'})


class AcademicAnalyticsView(viewsets.ViewSet):
    """
    Academic analytics view.
    """
    permission_classes = [permissions.IsAuthenticated, IsFacultyOrHigher]

    def list(self, request):
        """Get academic analytics data."""
        user = request.user
        institution = user.institution
        
        # Analytics data
        analytics = {
            'attendance_trends': self._get_attendance_trends(institution),
            'performance_metrics': self._get_performance_metrics(institution),
            'enrollment_analysis': self._get_enrollment_analysis(institution),
        }
        
        return Response(analytics)

    def _get_attendance_trends(self, institution):
        """Get attendance trends."""
        # Implementation for attendance trends
        return {'trend': 'increasing', 'percentage': 85}

    def _get_performance_metrics(self, institution):
        """Get performance metrics."""
        # Implementation for performance metrics
        return {'average_score': 75, 'pass_rate': 90}

    def _get_enrollment_analysis(self, institution):
        """Get enrollment analysis."""
        # Implementation for enrollment analysis
        return {'total_enrollments': 1200, 'growth_rate': 5}