from .faculty import Faculty
from .student import Student
from .consultation import Consultation, ConsultationStatus
from .admin import Admin
from .base import Base, init_db, get_db

__all__ = [
    'Faculty',
    'Student',
    'Consultation',
    'ConsultationStatus',
    'Admin',
    'Base',
    'init_db',
    'get_db'
] 