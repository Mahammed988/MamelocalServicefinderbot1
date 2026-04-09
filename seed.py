"""Seed the database with 20 example businesses."""
from db.models import init_db, SessionLocal
from db.queries import create_business

BUSINESSES = [
    # Mechanics
    {"name": "Al-Amin Auto Repair", "category": "mechanic", "phone": "+1-555-0101",
     "area_name": "Downtown", "latitude": 24.7136, "longitude": 46.6753,
     "description": "Full car service, AC repair, engine diagnostics.", "is_featured": True, "is_approved": True},
    {"name": "Quick Fix Garage", "category": "mechanic", "phone": "+1-555-0102",
     "area_name": "Westside", "latitude": 24.7200, "longitude": 46.6600,
     "description": "Fast oil changes and tire service.", "is_featured": False, "is_approved": True},
    {"name": "City Motors Workshop", "category": "mechanic", "phone": "+1-555-0103",
     "area_name": "Northgate", "latitude": 24.7300, "longitude": 46.6800,
     "description": "Specializing in Japanese and Korean cars.", "is_featured": False, "is_approved": True},
    {"name": "Pro Auto Center", "category": "mechanic", "phone": "+1-555-0104",
     "area_name": "Eastside", "latitude": 24.7050, "longitude": 46.6900,
     "description": "24/7 roadside assistance available.", "is_featured": True, "is_approved": True},

    # Pharmacies
    {"name": "HealthPlus Pharmacy", "category": "pharmacy", "phone": "+1-555-0201",
     "area_name": "Downtown", "latitude": 24.7140, "longitude": 46.6760,
     "description": "Open 24 hours. Prescription & OTC medicines.", "is_featured": True, "is_approved": True},
    {"name": "Green Leaf Pharmacy", "category": "pharmacy", "phone": "+1-555-0202",
     "area_name": "Westside", "latitude": 24.7210, "longitude": 46.6610,
     "description": "Natural supplements and vitamins.", "is_featured": False, "is_approved": True},
    {"name": "MediCare Drugstore", "category": "pharmacy", "phone": "+1-555-0203",
     "area_name": "Southpark", "latitude": 24.7000, "longitude": 46.6700,
     "description": "Affordable generics and home delivery.", "is_featured": False, "is_approved": True},
    {"name": "City Pharmacy", "category": "pharmacy", "phone": "+1-555-0204",
     "area_name": "Northgate", "latitude": 24.7310, "longitude": 46.6810,
     "description": "Friendly staff, quick service.", "is_featured": False, "is_approved": True},

    # Mobile Clinics
    {"name": "MobiHealth Clinic", "category": "mobile_clinic", "phone": "+1-555-0301",
     "area_name": "Downtown", "latitude": 24.7130, "longitude": 46.6740,
     "description": "General checkups, blood tests, vaccinations.", "is_featured": True, "is_approved": True},
    {"name": "CareOnWheels", "category": "mobile_clinic", "phone": "+1-555-0302",
     "area_name": "Eastside", "latitude": 24.7060, "longitude": 46.6910,
     "description": "Pediatric and maternal care.", "is_featured": False, "is_approved": True},
    {"name": "QuickCare Mobile", "category": "mobile_clinic", "phone": "+1-555-0303",
     "area_name": "Westside", "latitude": 24.7220, "longitude": 46.6620,
     "description": "Minor injuries and urgent care.", "is_featured": False, "is_approved": True},

    # Supermarkets
    {"name": "FreshMart Supermarket", "category": "supermarket", "phone": "+1-555-0401",
     "area_name": "Downtown", "latitude": 24.7145, "longitude": 46.6770,
     "description": "Fresh produce, bakery, and deli.", "is_featured": True, "is_approved": True},
    {"name": "ValueShop", "category": "supermarket", "phone": "+1-555-0402",
     "area_name": "Northgate", "latitude": 24.7320, "longitude": 46.6820,
     "description": "Best prices in town, daily deals.", "is_featured": False, "is_approved": True},
    {"name": "Family Grocery", "category": "supermarket", "phone": "+1-555-0403",
     "area_name": "Southpark", "latitude": 24.7010, "longitude": 46.6710,
     "description": "Organic and imported products.", "is_featured": False, "is_approved": True},
    {"name": "QuickStop Mart", "category": "supermarket", "phone": "+1-555-0404",
     "area_name": "Westside", "latitude": 24.7230, "longitude": 46.6630,
     "description": "Convenience store, open till midnight.", "is_featured": False, "is_approved": True},

    # Electronics
    {"name": "TechZone Electronics", "category": "electronics", "phone": "+1-555-0501",
     "area_name": "Downtown", "latitude": 24.7150, "longitude": 46.6780,
     "description": "Phones, laptops, accessories. Repair service.", "is_featured": True, "is_approved": True},
    {"name": "GadgetHub", "category": "electronics", "phone": "+1-555-0502",
     "area_name": "Eastside", "latitude": 24.7070, "longitude": 46.6920,
     "description": "Smart home devices and gaming gear.", "is_featured": False, "is_approved": True},
    {"name": "PowerTech Store", "category": "electronics", "phone": "+1-555-0503",
     "area_name": "Northgate", "latitude": 24.7330, "longitude": 46.6830,
     "description": "Authorized Samsung and Apple reseller.", "is_featured": False, "is_approved": True},
    {"name": "FixIt Electronics", "category": "electronics", "phone": "+1-555-0504",
     "area_name": "Westside", "latitude": 24.7240, "longitude": 46.6640,
     "description": "Screen replacement, battery swap, data recovery.", "is_featured": False, "is_approved": True},
    {"name": "Digital World", "category": "electronics", "phone": "+1-555-0505",
     "area_name": "Southpark", "latitude": 24.7020, "longitude": 46.6720,
     "description": "CCTV, networking, and smart systems.", "is_featured": False, "is_approved": True},
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        from db.models import Business
        existing = db.query(Business).count()
        if existing > 0:
            print(f"Database already has {existing} businesses. Skipping seed.")
            return

        for data in BUSINESSES:
            create_business(db, **data)

        print(f"✅ Seeded {len(BUSINESSES)} businesses.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
