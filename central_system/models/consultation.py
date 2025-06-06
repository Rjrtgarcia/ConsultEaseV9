from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class ConsultationStatus(enum.Enum):
    """
    Consultation status enum.
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    BUSY = "busy"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Consultation(Base):
    """
    Consultation model.
    Represents a consultation request between a student and faculty.
    """
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    request_message = Column(String, nullable=False)
    course_code = Column(String, nullable=True)
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.PENDING)
    requested_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime, nullable=True)
    busy_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", backref="consultations")
    faculty = relationship("Faculty", backref="consultations")

    def __repr__(self):
        return f"<Consultation {self.id}>"
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        """
        return {
            "id": self.id,
            "student_id": self.student_id,
            "faculty_id": self.faculty_id,
            "request_message": self.request_message,
            "course_code": self.course_code,
            "status": self.status.value,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "busy_at": self.busy_at.isoformat() if self.busy_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        } 