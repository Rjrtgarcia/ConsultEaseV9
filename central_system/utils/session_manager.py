"""
Session management utilities for ConsultEase system.
Provides secure session handling with timeout, lockout, and security features.
"""

import time
import secrets
import hashlib
import logging
import hmac
import base64
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Secure session manager with timeout, lockout, and security features.
    """

    def __init__(self, timeout_minutes: int = 30, lockout_threshold: int = 5, lockout_duration: int = 900):
        """
        Initialize the session manager.

        Args:
            timeout_minutes: Session timeout in minutes
            lockout_threshold: Number of failed attempts before lockout
            lockout_duration: Lockout duration in seconds
        """
        self.timeout_seconds = timeout_minutes * 60
        self.lockout_threshold = lockout_threshold
        self.lockout_duration = lockout_duration

        # Session storage
        self.sessions: Dict[str, dict] = {}

        # Failed login attempts tracking
        self.failed_attempts: Dict[str, dict] = {}

        # Security settings
        self.secure_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        }

        logger.info(f"Session manager initialized with {timeout_minutes}min timeout, {lockout_threshold} attempt threshold")

    def create_session(self, user_id: str, user_type: str = 'student', additional_data: dict = None) -> str:
        """
        Create a new secure session.

        Args:
            user_id: User identifier
            user_type: Type of user (student, admin)
            additional_data: Additional session data

        Returns:
            str: Session ID
        """
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(32)

        # Create session data
        session_data = {
            'user_id': user_id,
            'user_type': user_type,
            'created': time.time(),
            'last_activity': time.time(),
            'ip_address': None,  # To be set by web interface
            'user_agent': None,  # To be set by web interface
            'csrf_token': secrets.token_urlsafe(32)
        }

        if additional_data:
            session_data.update(additional_data)

        self.sessions[session_id] = session_data

        logger.info(f"Created session for {user_type} {user_id}: {session_id[:8]}...")
        return session_id

    def validate_session(self, session_id: str, update_activity: bool = True) -> Tuple[bool, Optional[dict]]:
        """
        Validate a session and optionally update last activity.

        Args:
            session_id: Session ID to validate
            update_activity: Whether to update last activity timestamp

        Returns:
            Tuple of (is_valid, session_data)
        """
        if not session_id or session_id not in self.sessions:
            return False, None

        session = self.sessions[session_id]
        current_time = time.time()

        # Check if session has expired
        if current_time - session['last_activity'] > self.timeout_seconds:
            logger.info(f"Session expired: {session_id[:8]}...")
            self.invalidate_session(session_id)
            return False, None

        # Update last activity if requested
        if update_activity:
            session['last_activity'] = current_time

        return True, session

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.

        Args:
            session_id: Session ID to invalidate

        Returns:
            bool: True if session was found and invalidated
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            logger.info(f"Invalidated session for {session.get('user_type', 'unknown')} {session.get('user_id', 'unknown')}")
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            int: Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.timeout_seconds:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.invalidate_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    def record_failed_attempt(self, identifier: str, ip_address: str = None) -> bool:
        """
        Record a failed login attempt.

        Args:
            identifier: User identifier (username, email, etc.)
            ip_address: IP address of the attempt

        Returns:
            bool: True if user is now locked out
        """
        current_time = time.time()

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
                'locked_until': None,
                'ip_addresses': set()
            }

        attempt_data = self.failed_attempts[identifier]

        # Check if user is currently locked out
        if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
            return True

        # Reset count if lockout period has passed
        if attempt_data['locked_until'] and current_time >= attempt_data['locked_until']:
            attempt_data['count'] = 0
            attempt_data['locked_until'] = None

        # Record the attempt
        attempt_data['count'] += 1
        attempt_data['last_attempt'] = current_time
        if ip_address:
            attempt_data['ip_addresses'].add(ip_address)

        # Check if lockout threshold is reached
        if attempt_data['count'] >= self.lockout_threshold:
            attempt_data['locked_until'] = current_time + self.lockout_duration
            logger.warning(f"User {identifier} locked out after {attempt_data['count']} failed attempts")
            return True

        logger.warning(f"Failed login attempt for {identifier} ({attempt_data['count']}/{self.lockout_threshold})")
        return False

    def is_locked_out(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """
        Check if a user is locked out.

        Args:
            identifier: User identifier

        Returns:
            Tuple of (is_locked_out, time_remaining_seconds)
        """
        if identifier not in self.failed_attempts:
            return False, None

        attempt_data = self.failed_attempts[identifier]
        current_time = time.time()

        if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
            time_remaining = attempt_data['locked_until'] - current_time
            return True, time_remaining

        return False, None

    def clear_failed_attempts(self, identifier: str) -> bool:
        """
        Clear failed attempts for a user (called on successful login).

        Args:
            identifier: User identifier

        Returns:
            bool: True if attempts were cleared
        """
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
            logger.info(f"Cleared failed attempts for {identifier}")
            return True
        return False

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information without updating activity.

        Args:
            session_id: Session ID

        Returns:
            dict: Session information or None
        """
        is_valid, session_data = self.validate_session(session_id, update_activity=False)
        return session_data if is_valid else None

    def get_security_headers(self) -> dict:
        """
        Get security headers to be added to HTTP responses.

        Returns:
            dict: Security headers
        """
        return self.secure_headers.copy()

    def get_active_sessions_count(self) -> int:
        """
        Get the number of active sessions.

        Returns:
            int: Number of active sessions
        """
        # Clean up expired sessions first
        self.cleanup_expired_sessions()
        return len(self.sessions)

    def get_session_stats(self) -> dict:
        """
        Get session statistics.

        Returns:
            dict: Session statistics
        """
        self.cleanup_expired_sessions()

        stats = {
            'active_sessions': len(self.sessions),
            'failed_attempts_tracked': len(self.failed_attempts),
            'locked_out_users': 0,
            'session_timeout_minutes': self.timeout_seconds // 60,
            'lockout_threshold': self.lockout_threshold,
            'lockout_duration_minutes': self.lockout_duration // 60
        }

        # Count locked out users
        current_time = time.time()
        for attempt_data in self.failed_attempts.values():
            if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
                stats['locked_out_users'] += 1

        return stats

    def validate_csrf_token(self, session_id: str, provided_token: str) -> bool:
        """
        Validate CSRF token for a session.

        Args:
            session_id: Session ID
            provided_token: CSRF token provided by client

        Returns:
            bool: True if token is valid
        """
        is_valid, session_data = self.validate_session(session_id, update_activity=False)
        if not is_valid or not session_data:
            return False

        stored_token = session_data.get('csrf_token')
        if not stored_token or not provided_token:
            return False

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(stored_token, provided_token)

    def regenerate_csrf_token(self, session_id: str) -> Optional[str]:
        """
        Regenerate CSRF token for a session.

        Args:
            session_id: Session ID

        Returns:
            str: New CSRF token or None if session invalid
        """
        is_valid, session_data = self.validate_session(session_id, update_activity=False)
        if not is_valid or not session_data:
            return None

        new_token = secrets.token_urlsafe(32)
        self.sessions[session_id]['csrf_token'] = new_token
        logger.debug(f"Regenerated CSRF token for session {session_id[:8]}...")
        return new_token

    def update_session_security_info(self, session_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """
        Update session security information.

        Args:
            session_id: Session ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            bool: True if updated successfully
        """
        is_valid, session_data = self.validate_session(session_id, update_activity=False)
        if not is_valid or not session_data:
            return False

        if ip_address:
            # Check for session hijacking (IP address change)
            stored_ip = session_data.get('ip_address')
            if stored_ip and stored_ip != ip_address:
                logger.warning(f"IP address change detected for session {session_id[:8]}... ({stored_ip} -> {ip_address})")
                # For now, just log it. In production, you might want to invalidate the session

            self.sessions[session_id]['ip_address'] = ip_address

        if user_agent:
            # Check for session hijacking (user agent change)
            stored_ua = session_data.get('user_agent')
            if stored_ua and stored_ua != user_agent:
                logger.warning(f"User agent change detected for session {session_id[:8]}...")

            self.sessions[session_id]['user_agent'] = user_agent

        return True

    def create_secure_session_token(self, session_id: str) -> str:
        """
        Create a secure session token with integrity protection.

        Args:
            session_id: Session ID

        Returns:
            str: Secure session token
        """
        # Create a signature for the session ID
        secret_key = secrets.token_bytes(32)  # In production, use a persistent secret
        signature = hmac.new(secret_key, session_id.encode(), hashlib.sha256).hexdigest()

        # Combine session ID and signature
        token_data = f"{session_id}:{signature}"
        return base64.urlsafe_b64encode(token_data.encode()).decode()

    def verify_secure_session_token(self, token: str) -> Optional[str]:
        """
        Verify a secure session token and extract session ID.

        Args:
            token: Secure session token

        Returns:
            str: Session ID if valid, None otherwise
        """
        try:
            # Decode the token
            token_data = base64.urlsafe_b64decode(token.encode()).decode()
            session_id, signature = token_data.split(':', 1)

            # Verify the signature
            secret_key = secrets.token_bytes(32)  # In production, use the same persistent secret
            expected_signature = hmac.new(secret_key, session_id.encode(), hashlib.sha256).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                return session_id
            else:
                logger.warning("Invalid session token signature")
                return None

        except Exception as e:
            logger.warning(f"Error verifying session token: {e}")
            return None

    def invalidate_all_user_sessions(self, user_id: str, user_type: str = None) -> int:
        """
        Invalidate all sessions for a specific user.

        Args:
            user_id: User ID
            user_type: Optional user type filter

        Returns:
            int: Number of sessions invalidated
        """
        sessions_to_remove = []

        for session_id, session_data in self.sessions.items():
            if session_data.get('user_id') == user_id:
                if user_type is None or session_data.get('user_type') == user_type:
                    sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            self.invalidate_session(session_id)

        if sessions_to_remove:
            logger.info(f"Invalidated {len(sessions_to_remove)} sessions for user {user_id}")

        return len(sessions_to_remove)

    def get_enhanced_security_headers(self, include_csp: bool = True) -> dict:
        """
        Get enhanced security headers including CSP.

        Args:
            include_csp: Whether to include Content Security Policy

        Returns:
            dict: Enhanced security headers
        """
        headers = self.secure_headers.copy()

        if include_csp:
            # Content Security Policy for additional protection
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            headers['Content-Security-Policy'] = csp_policy

        # Additional security headers
        headers.update({
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Cache-Control': 'no-store, no-cache, must-revalidate, private'
        })

        return headers


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.

    Returns:
        SessionManager: Global session manager
    """
    global _session_manager
    if _session_manager is None:
        # Load configuration from config
        from ..config import get_config
        config = get_config()

        security_config = config.get('security', {})
        timeout_minutes = security_config.get('session_timeout', 1800) // 60  # Convert seconds to minutes
        lockout_threshold = security_config.get('password_lockout_threshold', 5)
        lockout_duration = security_config.get('password_lockout_duration', 900)

        _session_manager = SessionManager(
            timeout_minutes=timeout_minutes,
            lockout_threshold=lockout_threshold,
            lockout_duration=lockout_duration
        )

    return _session_manager
