from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    DateTime, ForeignKey, Text, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255))
    username = Column(String(255), nullable=True)
    language = Column(String(10), default="en")
    role = Column(String(20), default="user")  # user / admin / business
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="user")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    telegram_username = Column(String(100), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False)
    is_open = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    owner_telegram_id = Column(Integer, nullable=True)
    search_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="business")
    subscription = relationship("Subscription", back_populates="business", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    is_active = Column(Boolean, default=False)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="subscription")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(Integer, nullable=False)
    query = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True)
    area = Column(String(255), nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaymentRequest(Base):
    """Tracks TeleBirr payment screenshots pending admin approval."""
    __tablename__ = "payment_requests"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)   # who paid
    payment_type = Column(String(20), nullable=False)           # "listing" | "view"
    reference_id = Column(Integer, nullable=True)               # business_id for listing; business_id for view
    amount = Column(Integer, nullable=False)                    # 300 or 3
    screenshot_file_id = Column(String(255), nullable=True)     # Telegram file_id
    status = Column(String(20), default="pending")              # pending | approved | rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class CustomerViewAccess(Base):
    """Tracks which business details a customer has paid to unlock."""
    __tablename__ = "customer_view_access"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)


# DB setup
def _make_engine():
    url = DATABASE_URL
    # Railway PostgreSQL URLs start with postgres:// — SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql://") and "pg8000" not in url:
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)

    kwargs = {}
    if "sqlite" in url:
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(url, **kwargs)

engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
