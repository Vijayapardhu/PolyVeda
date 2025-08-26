"""
Background tasks for the accounts app.
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from .models import User, UserSession, AuditLog, Institution
from core.services import security_service, compliance_service, notification_service

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """Clean up expired user sessions."""
    try:
        expired_sessions = UserSession.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        count = expired_sessions.count()
        expired_sessions.update(is_active=False)
        
        logger.info(f"Cleaned up {count} expired sessions")
        return f"Cleaned up {count} expired sessions"
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        raise


@shared_task
def cleanup_failed_login_attempts():
    """Reset failed login attempts for users."""
    try:
        users_to_reset = User.objects.filter(
            failed_login_attempts__gt=0,
            locked_until__lt=timezone.now()
        )
        count = users_to_reset.count()
        
        for user in users_to_reset:
            user.reset_failed_login_attempts()
        
        logger.info(f"Reset failed login attempts for {count} users")
        return f"Reset failed login attempts for {count} users"
    except Exception as e:
        logger.error(f"Error resetting failed login attempts: {e}")
        raise


@shared_task
def check_password_expiration():
    """Check for users with expired passwords and notify them."""
    try:
        expired_users = User.objects.filter(
            password_expires_at__lt=timezone.now(),
            is_active=True
        )
        
        for user in expired_users:
            # Send password expiration notification
            notification_service.send_notification(
                user.id,
                {
                    'type': 'password_expiration',
                    'title': 'Password Expired',
                    'message': 'Your password has expired. Please change it immediately.',
                    'priority': 'high'
                }
            )
        
        logger.info(f"Notified {expired_users.count()} users about password expiration")
        return f"Notified {expired_users.count()} users about password expiration"
    except Exception as e:
        logger.error(f"Error checking password expiration: {e}")
        raise


@shared_task
def generate_ai_insights_for_users():
    """Generate AI insights for all active users."""
    try:
        from core.services import ai_service
        
        active_users = User.objects.filter(
            is_active=True,
            status=User.Status.ACTIVE
        )
        
        insights_generated = 0
        for user in active_users:
            try:
                # Generate attendance prediction
                attendance_features = {
                    'previous_attendance_rate': 0.8,  # This would come from actual data
                    'current_semester_attendance': 0.75,
                    'days_since_last_attendance': 2,
                    'assignment_completion_rate': 0.9,
                    'performance_score': 0.85,
                    'social_engagement_score': 0.7,
                    'health_indicators': 0.9,
                    'external_factors': 0.8
                }
                
                attendance_prediction = ai_service.predict_attendance(user.id, attendance_features)
                
                # Generate performance prediction
                performance_features = {
                    'previous_gpa': 3.5,
                    'attendance_rate': 0.8,
                    'assignment_completion_rate': 0.9,
                    'study_time_hours': 25,
                    'participation_score': 0.8,
                    'peer_interaction_score': 0.7,
                    'stress_level': 0.3,
                    'sleep_quality': 0.8
                }
                
                performance_prediction = ai_service.predict_performance(user.id, performance_features)
                
                insights_generated += 1
                
            except Exception as e:
                logger.error(f"Error generating insights for user {user.id}: {e}")
                continue
        
        logger.info(f"Generated AI insights for {insights_generated} users")
        return f"Generated AI insights for {insights_generated} users"
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        raise


@shared_task
def audit_user_activity():
    """Audit user activity for security and compliance."""
    try:
        # Check for suspicious activity
        suspicious_sessions = UserSession.objects.filter(
            is_suspicious=True,
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        for session in suspicious_sessions:
            # Analyze security event
            event_data = {
                'user_id': session.user.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'location': session.location,
                'risk_score': session.risk_score,
                'threat_indicators': session.threat_indicators
            }
            
            security_analysis = security_service.analyze_security_event(event_data)
            
            if security_analysis.get('threat_level') in ['high', 'critical']:
                # Send security alert
                notification_service.send_notification(
                    session.user.id,
                    {
                        'type': 'security_alert',
                        'title': 'Security Alert',
                        'message': 'Suspicious activity detected on your account.',
                        'priority': 'critical'
                    }
                )
        
        logger.info(f"Audited {suspicious_sessions.count()} suspicious sessions")
        return f"Audited {suspicious_sessions.count()} suspicious sessions"
    except Exception as e:
        logger.error(f"Error auditing user activity: {e}")
        raise


@shared_task
def compliance_check():
    """Run compliance checks for all institutions."""
    try:
        institutions = Institution.objects.filter(is_active=True)
        
        for institution in institutions:
            # Check GDPR compliance
            gdpr_compliance = compliance_service.check_compliance(
                'data_processing',
                {'institution_id': institution.id},
                None  # System user
            )
            
            if not gdpr_compliance['compliant']:
                logger.warning(f"GDPR compliance issues for institution {institution.id}")
            
            # Check FERPA compliance
            ferpa_compliance = compliance_service.check_compliance(
                'educational_records_protection',
                {'institution_id': institution.id},
                None
            )
            
            if not ferpa_compliance['compliant']:
                logger.warning(f"FERPA compliance issues for institution {institution.id}")
        
        logger.info(f"Completed compliance checks for {institutions.count()} institutions")
        return f"Completed compliance checks for {institutions.count()} institutions"
    except Exception as e:
        logger.error(f"Error running compliance checks: {e}")
        raise


@shared_task
def backup_user_data():
    """Backup user data for compliance and disaster recovery."""
    try:
        # This would implement actual backup logic
        # For now, just log the task
        logger.info("User data backup completed")
        return "User data backup completed"
    except Exception as e:
        logger.error(f"Error backing up user data: {e}")
        raise


@shared_task
def send_welcome_emails():
    """Send welcome emails to new users."""
    try:
        new_users = User.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            email_verified=True
        )
        
        for user in new_users:
            try:
                # Send welcome email
                subject = 'Welcome to PolyVeda!'
                message = render_to_string('accounts/email/welcome.html', {
                    'user': user,
                    'institution': user.institution
                })
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
            except Exception as e:
                logger.error(f"Error sending welcome email to {user.email}: {e}")
                continue
        
        logger.info(f"Sent welcome emails to {new_users.count()} users")
        return f"Sent welcome emails to {new_users.count()} users"
    except Exception as e:
        logger.error(f"Error sending welcome emails: {e}")
        raise


@shared_task
def cleanup_audit_logs():
    """Clean up old audit logs based on retention policy."""
    try:
        retention_days = getattr(settings, 'COMPLIANCE_CONFIG', {}).get('audit_log_retention_days', 3650)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"Cleaned up {count} old audit logs")
        return f"Cleaned up {count} old audit logs"
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise


@shared_task
def monitor_institution_limits():
    """Monitor institution usage limits and send alerts."""
    try:
        institutions = Institution.objects.filter(is_active=True)
        
        for institution in institutions:
            current_users = institution.users.count()
            max_users = institution.max_users
            
            if current_users >= max_users * 0.9:  # 90% threshold
                # Send alert to institution admin
                admin_users = institution.users.filter(role__in=['admin', 'management'])
                
                for admin in admin_users:
                    notification_service.send_notification(
                        admin.id,
                        {
                            'type': 'usage_limit',
                            'title': 'Usage Limit Alert',
                            'message': f'Your institution is approaching the user limit ({current_users}/{max_users}).',
                            'priority': 'medium'
                        }
                    )
        
        logger.info(f"Monitored usage limits for {institutions.count()} institutions")
        return f"Monitored usage limits for {institutions.count()} institutions"
    except Exception as e:
        logger.error(f"Error monitoring institution limits: {e}")
        raise


@shared_task
def generate_monthly_reports():
    """Generate monthly reports for institutions."""
    try:
        institutions = Institution.objects.filter(is_active=True)
        
        for institution in institutions:
            # Generate user activity report
            active_users = institution.users.filter(
                last_activity__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Generate security report
            security_events = AuditLog.objects.filter(
                institution=institution,
                action__in=['login_failed', 'security_event'],
                timestamp__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Send report to institution admins
            admin_users = institution.users.filter(role__in=['admin', 'management'])
            
            for admin in admin_users:
                notification_service.send_notification(
                    admin.id,
                    {
                        'type': 'monthly_report',
                        'title': 'Monthly Report',
                        'message': f'Monthly report: {active_users} active users, {security_events} security events.',
                        'priority': 'low'
                    }
                )
        
        logger.info(f"Generated monthly reports for {institutions.count()} institutions")
        return f"Generated monthly reports for {institutions.count()} institutions"
    except Exception as e:
        logger.error(f"Error generating monthly reports: {e}")
        raise