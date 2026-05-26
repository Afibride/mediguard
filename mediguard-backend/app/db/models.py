from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_pw = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    notify_emails = Column(Boolean, default=True, nullable=False, server_default="true")
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("PredictionLog", back_populates="user")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    # 6-digit OTP code — alternative to clicking the reset link
    otp_code = Column(String(6), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    featured = Column(Boolean, default=False)
    severity = Column(String, default="Medium")
    symptoms = Column(JSON, nullable=False)
    description = Column(Text, nullable=False)
    causes = Column(Text, default="")
    treatment = Column(Text, default="")
    prevention = Column(JSON, default=list)
    sections = Column(JSON, default=dict)
    symptom_descriptions = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symptoms = Column(JSON, nullable=False)
    predictions = Column(JSON, nullable=False)
    top_disease = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    region = Column(String, default="Bamenda")
    age_group = Column(String, nullable=True, index=True)  # e.g. "0-10", "11-20", …, "60+"

    user = relationship("User", back_populates="predictions")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, default="MediGuard AI Chat")
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    follow_up_questions = Column(JSON, default=list)
    mode = Column(String, nullable=True)
    pregnancy_context = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)


class ChatFeedback(Base):
    """Per-message rating on an AI chat response.

    Stores the user query, a preview of the AI response, and whether the user
    found it helpful. Extracted keywords are used for pattern analysis to
    identify knowledge gaps and improve the system prompt adaptively.
    """
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)   # client-side chat session id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    response_preview = Column(Text, nullable=True)           # first ~300 chars of AI reply
    rating = Column(Boolean, nullable=False)                 # True = helpful, False = not helpful
    query_keywords = Column(JSON, default=list)              # extracted from query, client-side
    mode = Column(String, nullable=True)                     # "symptom_check", "general", etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PredictionFeedback(Base):
    """User-submitted feedback on a prediction result.

    Stores whether the top prediction was confirmed correct after a clinical
    visit, enabling accuracy tracking and future model improvement.
    """
    __tablename__ = "prediction_feedback"

    id = Column(Integer, primary_key=True, index=True)
    prediction_log_id = Column(Integer, ForeignKey("prediction_logs.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    top_predicted = Column(String, nullable=False)
    was_helpful = Column(Boolean, nullable=False)
    confirmed_disease = Column(String, nullable=True)   # what the doctor actually said
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class NewsletterSubscriber(Base):
    """Guest (non-registered) user who opted-in to monthly health digests and
    outbreak alerts. Registered users use the ``User.notify_emails`` flag instead.
    """
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, default="Friend", nullable=False)
    # Random token used in the one-click unsubscribe link
    unsubscribe_token = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
