"""
Audit logging system for ConsultEase.
Tracks security-relevant events and user actions.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Create separate base for audit logs to avoid circular imports
AuditBase = declarative_base()


class AuditLog(AuditBase):
    """Audit log model for tracking system events."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=True, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(String, nullable=True)  # 'success', 'failure', 'warning'
    timestamp = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username or 'system'} at {self.timestamp}>"

    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource': self.resource,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AuditLogger:
    """Centralized audit logging system."""
    
    def __init__(self):
        self.session = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize audit database connection."""
        try:
            # Use the same database as the main application
            from ..models.base import engine
            
            # Create audit tables if they don't exist
            AuditBase.metadata.create_all(bind=engine)
            
            # Create session factory
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            logger.info("Audit logging system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logging: {e}")
            self.session = None
    
    def log_event(self, action: str, user_id: Optional[int] = None, username: Optional[str] = None,
                  resource: Optional[str] = None, details: Optional[str] = None,
                  ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                  success: str = 'success'):
        """
        Log an audit event.
        
        Args:
            action: Action performed (e.g., 'login', 'logout', 'password_change')
            user_id: User ID if applicable
            username: Username if applicable
            resource: Resource accessed (e.g., 'admin_dashboard', 'faculty_data')
            details: Additional details about the event
            ip_address: IP address of the user
            user_agent: User agent string
            success: Event outcome ('success', 'failure', 'warning')
        """
        if not self.session:
            logger.warning("Audit logging not available - session not initialized")
            return
        
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource=resource,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                timestamp=datetime.now()
            )
            
            self.session.add(audit_entry)
            self.session.commit()
            
            # Also log to standard logger for immediate visibility
            log_level = logging.INFO if success == 'success' else logging.WARNING
            logger.log(log_level, f"AUDIT: {action} by {username or 'system'} - {success}")
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            if self.session:
                self.session.rollback()
    
    def log_authentication(self, username: str, success: bool, ip_address: Optional[str] = None,
                          details: Optional[str] = None):
        """Log authentication attempt."""
        self.log_event(
            action='authentication',
            username=username,
            resource='login',
            details=details,
            ip_address=ip_address,
            success='success' if success else 'failure'
        )
    
    def log_password_change(self, user_id: int, username: str, forced: bool = False,
                           ip_address: Optional[str] = None):
        """Log password change event."""
        details = "Forced password change" if forced else "User-initiated password change"
        self.log_event(
            action='password_change',
            user_id=user_id,
            username=username,
            resource='user_account',
            details=details,
            ip_address=ip_address,
            success='success'
        )
    
    def log_admin_action(self, admin_id: int, admin_username: str, action: str,
                        target_resource: str, details: Optional[str] = None,
                        ip_address: Optional[str] = None):
        """Log administrative action."""
        self.log_event(
            action=f'admin_{action}',
            user_id=admin_id,
            username=admin_username,
            resource=target_resource,
            details=details,
            ip_address=ip_address,
            success='success'
        )
    
    def log_consultation_request(self, student_id: int, faculty_id: int,
                                details: Optional[str] = None):
        """Log consultation request."""
        self.log_event(
            action='consultation_request',
            user_id=student_id,
            resource=f'faculty_{faculty_id}',
            details=details,
            success='success'
        )
    
    def log_system_event(self, event: str, details: Optional[str] = None,
                        success: str = 'success'):
        """Log system-level event."""
        self.log_event(
            action=f'system_{event}',
            username='system',
            details=details,
            success=success
        )
    
    def log_security_event(self, event: str, username: Optional[str] = None,
                          ip_address: Optional[str] = None, details: Optional[str] = None):
        """Log security-related event."""
        self.log_event(
            action=f'security_{event}',
            username=username,
            resource='security',
            details=details,
            ip_address=ip_address,
            success='warning'
        )
    
    def get_recent_logs(self, limit: int = 100, action_filter: Optional[str] = None,
                       username_filter: Optional[str] = None) -> list:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of logs to return
            action_filter: Filter by action type
            username_filter: Filter by username
            
        Returns:
            List of audit log dictionaries
        """
        if not self.session:
            return []
        
        try:
            query = self.session.query(AuditLog)
            
            if action_filter:
                query = query.filter(AuditLog.action.like(f'%{action_filter}%'))
            
            if username_filter:
                query = query.filter(AuditLog.username == username_filter)
            
            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """
        Clean up old audit logs.
        
        Args:
            days_to_keep: Number of days of logs to retain
        """
        if not self.session:
            return
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = self.session.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            self.session.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audit log entries")
                self.log_system_event('audit_cleanup', f'Deleted {deleted_count} entries older than {days_to_keep} days')
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            if self.session:
                self.session.rollback()
    
    def close(self):
        """Close audit logger session."""
        if self.session:
            self.session.close()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit_event(action: str, **kwargs):
    """Convenience function to log audit events."""
    audit_logger = get_audit_logger()
    audit_logger.log_event(action, **kwargs)


def log_authentication(username: str, success: bool, **kwargs):
    """Convenience function to log authentication events."""
    audit_logger = get_audit_logger()
    audit_logger.log_authentication(username, success, **kwargs)


def log_security_event(event: str, **kwargs):
    """Convenience function to log security events."""
    audit_logger = get_audit_logger()
    audit_logger.log_security_event(event, **kwargs)
