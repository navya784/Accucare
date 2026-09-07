from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.database import Base


class DoctorAccount(Base):
    """A doctor's login account. Phase 4 adds password hashing and JWT
    issuance on top of this table."""
    __tablename__ = "doctor_accounts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="doctor")
    chat_messages = relationship("ChatHistory", back_populates="doctor")


class Patient(Base):
    """A patient record. Kept intentionally simple for now - just enough
    to link a Report to a named patient, matching what your report
    generator already collects (name, age, gender)."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="patient")


class Report(Base):
    """One generated clinical report - what generate_patient_report()
    currently only writes to a throwaway .txt file. Persisting these is
    the core of Phase 3."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_accounts.id"), nullable=True)

    current_symptoms = Column(Text, nullable=True)
    vitals_json = Column(Text, nullable=True)  # stored as JSON text - simplest correct option for SQLite
    medical_history = Column(Text, nullable=True)
    lab_results = Column(Text, nullable=True)
    imaging_findings = Column(Text, nullable=True)
    doctor_notes = Column(Text, nullable=True)

    report_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="reports")
    doctor = relationship("DoctorAccount", back_populates="reports")


class ChatHistory(Base):
    """One message in the doctor chatbot (Phase 2's /clinical/chat).
    Each question+answer pair is stored as two rows (role='user' /
    role='assistant') so a full conversation can be reconstructed."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_accounts.id"), nullable=True)
    session_id = Column(String, index=True, nullable=True)  # groups messages into one conversation

    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)  # only populated on assistant messages
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("DoctorAccount", back_populates="chat_messages")


class Document(Base):
    """Tracks each guideline PDF that's been ingested into ChromaDB -
    needed for Phase 6's admin panel (upload/delete guideline docs,
    rebuild embeddings), but the table itself belongs here in Phase 3."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, unique=True)
    source_folder = Column(String, nullable=True)  # e.g. "nice" or "who"
    chunk_count = Column(Integer, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)