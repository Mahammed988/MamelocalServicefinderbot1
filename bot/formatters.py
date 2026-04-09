"""Format business cards — accepts both ORM objects and plain dicts."""
from config import CATEGORY_EMOJIS
from services.location import format_distance
from services.i18n import t


def _get(biz, key, default=None):
    if isinstance(biz, dict):
        return biz.get(key, default)
    return getattr(biz, key, default)


def format_business_summary(biz, index: int, distance: float = None, lang: str = "en") -> str:
    """Short card shown in search results — name, category, status, distance only.
    Phone/location hidden until customer pays or uses free quota."""
    category = _get(biz, "category", "")
    emoji = CATEGORY_EMOJIS.get(category, "🏪")
    featured = "⭐ " if _get(biz, "is_featured") else ""
    status = t("open", lang) if _get(biz, "is_open") else t("closed", lang)
    dist_str = f"  {format_distance(distance)}" if distance is not None else ""
    area = _get(biz, "area_name")
    area_str = f"\n📌 {area}" if area else ""

    return (
        f"{index}. {featured}{emoji} *{_get(biz, 'name', '')}*\n"
        f"🏷️ {category.replace('_', ' ').title()} | {status}{dist_str}"
        f"{area_str}"
    )


def format_business_card(biz, distance: float = None, lang: str = "en") -> str:
    """Full card — used in featured listing and after access is granted."""
    category = _get(biz, "category", "")
    emoji = CATEGORY_EMOJIS.get(category, "🏪")
    featured = "⭐ *Featured*\n" if _get(biz, "is_featured") else ""
    status = t("open", lang) if _get(biz, "is_open") else t("closed", lang)
    dist_str = f"\n{format_distance(distance)}" if distance is not None else ""
    area = _get(biz, "area_name")
    phone = _get(biz, "phone")
    desc = _get(biz, "description")
    lat = _get(biz, "latitude")
    lon = _get(biz, "longitude")

    area_str = f"\n📌 {area}" if area else ""
    phone_str = f"\n📞 {phone}" if phone else ""
    desc_str = f"\n_{desc}_" if desc else ""
    map_str = (
        f"\n🗺️ [View on Map](https://www.google.com/maps?q={lat},{lon})"
        if lat and lon else ""
    )

    return (
        f"{featured}"
        f"{emoji} *{_get(biz, 'name', '')}*\n"
        f"🏷️ {category.replace('_', ' ').title()} | {status}"
        f"{area_str}"
        f"{phone_str}"
        f"{dist_str}"
        f"{desc_str}"
        f"{map_str}"
    )


def format_business_detail(biz, avg_rating: float, review_count: int,
                            distance: float = None, lang: str = "en") -> str:
    rating_str = (
        f"\n⭐ {avg_rating}/5 ({review_count} review{'s' if review_count != 1 else ''})"
        if review_count else "\n⭐ No reviews yet"
    )
    return format_business_card(biz, distance, lang) + rating_str
