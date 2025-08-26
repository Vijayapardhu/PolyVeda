"""
URL configuration for academics app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'academic-years', views.AcademicYearViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'sections', views.SectionViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)
router.register(r'timetables', views.TimetableViewSet)
router.register(r'attendances', views.AttendanceViewSet)
router.register(r'assessments', views.AssessmentViewSet)
router.register(r'submissions', views.SubmissionViewSet)
router.register(r'results', views.ResultViewSet)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Custom endpoints
    path('dashboard/', views.AcademicDashboardView.as_view(), name='academic-dashboard'),
    path('reports/', views.AcademicReportsView.as_view(), name='academic-reports'),
    path('analytics/', views.AcademicAnalyticsView.as_view(), name='academic-analytics'),
]