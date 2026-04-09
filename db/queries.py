from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
from typing import Optional, List
from .models import User, Business, Subscription, Review, SearchLog, PaymentRequest, CustomerViewAccess
from services.location import haversine_distance


# ── Users ──────────────────────────────────────────────────────────────────

def get_or_create_user(db: Session, telegram_id: int, name: str, username: str = None) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, name=name, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_user(db: Session, telegram_id: int) -> Optional[User]:
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()


def set_user_language(db: Session, telegram_id: int, language: str):
    user = get_user(db, telegram_id)
    if user:
        user.language = language
        db.commit()


# ── Businesses ─────────────────────────────────────────────────────────────

def create_business(db: Session, **kwargs) -> Business:
    biz = Business(**kwargs)
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


def get_business(db: Session, business_id: int) -> Optional[Business]:
    return db.query(Business).filter(Business.id == business_id).first()


def get_businesses_by_owner(db: Session, owner_telegram_id: int) -> List[Business]:
    return db.query(Business).filter(Business.owner_telegram_id == owner_telegram_id).all()


def get_pending_businesses(db: Session) -> List[Business]:
    return db.query(Business).filter(Business.is_approved == False).all()


def update_business(db: Session, business_id: int, **kwargs) -> Optional[Business]:
    biz = get_business(db, business_id)
    if biz:
        for key, value in kwargs.items():
            setattr(biz, key, value)
        db.commit()
        db.refresh(biz)
    return biz


def delete_business(db: Session, business_id: int) -> bool:
    biz = get_business(db, business_id)
    if biz:
        db.delete(biz)
        db.commit()
        return True
    return False


def search_businesses(
    db: Session,
    category: str = None,
    keyword: str = None,
    lat: float = None,
    lon: float = None,
    area: str = None,
    limit: int = 20,
) -> List[dict]:
    """Search businesses and return sorted results with distance."""
    query = db.query(Business).filter(Business.is_approved == True)

    if category:
        query = query.filter(Business.category == category)

    if keyword:
        query = query.filter(
            or_(
                Business.name.ilike(f"%{keyword}%"),
                Business.description.ilike(f"%{keyword}%"),
                Business.area_name.ilike(f"%{keyword}%"),
            )
        )

    if area and not lat:
        query = query.filter(Business.area_name.ilike(f"%{area}%"))

    businesses = query.all()

    results = []
    for biz in businesses:
        distance = None
        if lat and lon and biz.latitude and biz.longitude:
            distance = haversine_distance(lat, lon, biz.latitude, biz.longitude)

        biz.search_count += 1

        # Snapshot all fields into a plain dict so session can safely close
        results.append({
            "business": {
                "id": biz.id,
                "name": biz.name,
                "category": biz.category,
                "latitude": biz.latitude,
                "longitude": biz.longitude,
                "area_name": biz.area_name,
                "phone": biz.phone,
                "telegram_username": biz.telegram_username,
                "whatsapp": biz.whatsapp,
                "description": biz.description,
                "is_featured": biz.is_featured,
                "is_open": biz.is_open,
            },
            "distance": distance,
        })

    db.commit()

    results.sort(
        key=lambda x: (
            not x["business"]["is_featured"],
            x["distance"] if x["distance"] is not None else float("inf"),
        )
    )

    return results[:limit]


def get_all_businesses(db: Session) -> List[Business]:
    return db.query(Business).filter(Business.is_approved == True).all()


# ── Reviews ────────────────────────────────────────────────────────────────

def add_review(db: Session, business_id: int, user_id: int, rating: int, comment: str = None) -> Review:
    # One review per user per business
    existing = db.query(Review).filter(
        Review.business_id == business_id,
        Review.user_id == user_id
    ).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
        db.commit()
        return existing

    review = Review(business_id=business_id, user_id=user_id, rating=rating, comment=comment)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_business_rating(db: Session, business_id: int) -> tuple:
    """Returns (avg_rating, count)."""
    result = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(Review.business_id == business_id).first()
    avg = round(result[0], 1) if result[0] else 0
    return avg, result[1]


# ── Subscriptions ──────────────────────────────────────────────────────────

def set_subscription(db: Session, business_id: int, expiry_date: datetime) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    if sub:
        sub.is_active = True
        sub.expiry_date = expiry_date
    else:
        sub = Subscription(business_id=business_id, is_active=True, expiry_date=expiry_date)
        db.add(sub)
    db.commit()
    return sub


def is_subscription_active(db: Session, business_id: int) -> bool:
    sub = db.query(Subscription).filter(
        Subscription.business_id == business_id,
        Subscription.is_active == True,
        Subscription.expiry_date > datetime.utcnow()
    ).first()
    return sub is not None


# ── Payment Requests ───────────────────────────────────────────────────────

def create_payment_request(db: Session, telegram_id: int, payment_type: str,
                            reference_id: int, amount: int,
                            screenshot_file_id: str = None) -> PaymentRequest:
    pr = PaymentRequest(
        telegram_id=telegram_id,
        payment_type=payment_type,
        reference_id=reference_id,
        amount=amount,
        screenshot_file_id=screenshot_file_id,
        status="pending",
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def get_payment_request(db: Session, pr_id: int) -> Optional[PaymentRequest]:
    return db.query(PaymentRequest).filter(PaymentRequest.id == pr_id).first()


def get_pending_payments(db: Session) -> List[PaymentRequest]:
    return db.query(PaymentRequest).filter(PaymentRequest.status == "pending").all()


def approve_payment(db: Session, pr_id: int) -> Optional[PaymentRequest]:
    pr = get_payment_request(db, pr_id)
    if pr:
        pr.status = "approved"
        db.commit()
        db.refresh(pr)
    return pr


def reject_payment(db: Session, pr_id: int) -> Optional[PaymentRequest]:
    pr = get_payment_request(db, pr_id)
    if pr:
        pr.status = "rejected"
        db.commit()
        db.refresh(pr)
    return pr


def has_pending_payment(db: Session, telegram_id: int,
                         payment_type: str, reference_id: int) -> bool:
    return db.query(PaymentRequest).filter(
        PaymentRequest.telegram_id == telegram_id,
        PaymentRequest.payment_type == payment_type,
        PaymentRequest.reference_id == reference_id,
        PaymentRequest.status == "pending",
    ).first() is not None


# ── Owner listing quota ────────────────────────────────────────────────────

def owner_approved_listing_count(db: Session, owner_telegram_id: int) -> int:
    """Count how many approved listings this owner already has."""
    return db.query(Business).filter(
        Business.owner_telegram_id == owner_telegram_id,
        Business.is_approved == True,
    ).count()


def owner_total_listing_count(db: Session, owner_telegram_id: int) -> int:
    """Count all listings (approved + pending) for this owner."""
    return db.query(Business).filter(
        Business.owner_telegram_id == owner_telegram_id,
    ).count()


# ── Customer view access ───────────────────────────────────────────────────

def get_free_views_used(db: Session, telegram_id: int) -> int:
    """Count how many paid/free detail views this customer has used."""
    return db.query(CustomerViewAccess).filter(
        CustomerViewAccess.telegram_id == telegram_id
    ).count()


def has_view_access(db: Session, telegram_id: int, business_id: int) -> bool:
    return db.query(CustomerViewAccess).filter(
        CustomerViewAccess.telegram_id == telegram_id,
        CustomerViewAccess.business_id == business_id,
    ).first() is not None


def grant_view_access(db: Session, telegram_id: int, business_id: int) -> CustomerViewAccess:
    if not has_view_access(db, telegram_id, business_id):
        access = CustomerViewAccess(telegram_id=telegram_id, business_id=business_id)
        db.add(access)
        db.commit()
        db.refresh(access)
        return access


# ── Analytics ──────────────────────────────────────────────────────────────
def log_search(db: Session, user_telegram_id: int, query: str = None,
               category: str = None, area: str = None, results_count: int = 0):
    log = SearchLog(
        user_telegram_id=user_telegram_id,
        query=query,
        category=category,
        area=area,
        results_count=results_count,
    )
    db.add(log)
    db.commit()


def get_analytics(db: Session) -> dict:
    total_searches = db.query(func.count(SearchLog.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_businesses = db.query(func.count(Business.id)).filter(Business.is_approved == True).scalar()

    top_businesses = (
        db.query(Business)
        .filter(Business.is_approved == True)
        .order_by(Business.search_count.desc())
        .limit(5)
        .all()
    )

    return {
        "total_searches": total_searches,
        "total_users": total_users,
        "total_businesses": total_businesses,
        "top_businesses": top_businesses,
    }
