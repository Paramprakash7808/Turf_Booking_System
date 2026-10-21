import os
import django
from datetime import time, date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.contrib.auth.models import User
from turfs.models import (
    Sport, Amenity, Turf, TimeSlot, Booking, Review, HeroSlide,
    Organization, Branch, OrganizationRole, UserProfile
)

def seed():
    print("[*] Starting comprehensive database seeding for TurfBook...")

    # 1. Superuser
    sa_email = os.getenv('SUPERADMIN_EMAIL', 'superadmin@turfbook.com')
    sa_user_name = os.getenv('SUPERADMIN_USERNAME', 'admin')
    sa_pass = os.getenv('SUPERADMIN_PASSWORD', 'admin123')

    if not User.objects.filter(username=sa_user_name).exists():
        admin_user = User.objects.create_superuser(sa_user_name, sa_email, sa_pass)
        admin_user.first_name = "Super"
        admin_user.last_name = "Admin"
        admin_user.save()
        print(f"[OK] Superuser created: {sa_user_name} / {sa_pass} (email: {sa_email})")
    else:
        admin_user = User.objects.get(username=sa_user_name)
        admin_user.email = sa_email
        admin_user.set_password(sa_pass)
        admin_user.save()
        print(f"[OK] Superuser updated: {sa_email} / {sa_pass}")

    if hasattr(admin_user, 'profile'):
        admin_user.profile.role = 'SUPER_ADMIN'
        admin_user.profile.save()

    # 2. Sports
    sports_data = [
        {"name": "Cricket", "icon": "target", "image_url": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80", "description": "Box cricket and full ground turf practice nets with professional lighting."},
        {"name": "Football", "icon": "trophy", "image_url": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80", "description": "FIFA approved astro-turf courts for 5-a-side and 7-a-side football matches."},
        {"name": "Pickleball", "icon": "activity", "image_url": "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?auto=format&fit=crop&w=800&q=80", "description": "Cushioned acrylic pickleball courts with paddle rentals and coaching."},
        {"name": "Paddleball", "icon": "zap", "image_url": "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?auto=format&fit=crop&w=800&q=80", "description": "Fast paced enclosed paddleball courts with glass walls and night lighting."}
    ]

    sports_map = {}
    for data in sports_data:
        sport, _ = Sport.objects.get_or_create(name=data["name"], defaults=data)
        sports_map[sport.name] = sport
    print("[OK] Sports created:", list(sports_map.keys()))

    # 3. Amenities
    amenities_list = [
        "Floodlights", "Changing Rooms", "Parking", "Cafeteria", 
        "Indoor Courts", "Air Conditioning", "Equipment Rental", "Coaching Available"
    ]
    amenities_map = {}
    for a_name in amenities_list:
        amen, _ = Amenity.objects.get_or_create(name=a_name)
        amenities_map[a_name] = amen
    print("[OK] Amenities created:", list(amenities_map.keys()))

    # 4. Time Slots
    slots_data = [
        (time(6, 0), time(7, 0), "06:00 AM - 07:00 AM"),
        (time(7, 0), time(8, 0), "07:00 AM - 08:00 AM"),
        (time(8, 0), time(9, 0), "08:00 AM - 09:00 AM"),
        (time(9, 0), time(10, 0), "09:00 AM - 10:00 AM"),
        (time(10, 0), time(11, 0), "10:00 AM - 11:00 AM"),
        (time(11, 0), time(12, 0), "11:00 AM - 12:00 PM"),
        (time(16, 0), time(17, 0), "04:00 PM - 05:00 PM"),
        (time(17, 0), time(18, 0), "05:00 PM - 06:00 PM"),
        (time(18, 0), time(19, 0), "06:00 PM - 07:00 PM"),
        (time(19, 0), time(20, 0), "07:00 PM - 08:00 PM"),
        (time(20, 0), time(21, 0), "08:00 PM - 09:00 PM"),
        (time(21, 0), time(22, 0), "09:00 PM - 10:00 PM"),
    ]
    time_slots = []
    for start, end, label in slots_data:
        slot, _ = TimeSlot.objects.get_or_create(start_time=start, end_time=end, defaults={"label": label})
        time_slots.append(slot)
    print(f"[OK] {len(time_slots)} Time Slots configured.")

    # 5. Organizations & Branches
    org1, _ = Organization.objects.get_or_create(
        name="Apex Sports Arena Network",
        defaults={
            "email": "contact@apexsports.in",
            "phone": "+91 79 2685 1000",
            "address": "Sindhu Bhavan Road, Bodakdev, Ahmedabad",
            "description": "Ahmedabad's premier multi-sport turf and facility operator with 3 world-class centers across Gujarat."
        }
    )

    org2, _ = Organization.objects.get_or_create(
        name="Urban Kicks & Courts Group",
        defaults={
            "email": "hello@urbankicks.com",
            "phone": "+91 79 4001 8899",
            "address": "Vastrapur, Ahmedabad",
            "description": "Specialized indoor & astro-turf football and racket sports arenas."
        }
    )
    print(f"[OK] Organizations created: '{org1.name}' and '{org2.name}'.")

    # Branches for Org 1
    branch1_1, _ = Branch.objects.get_or_create(
        organization=org1,
        name="Apex Bodakdev Arena",
        defaults={
            "city": "Ahmedabad",
            "location": "Bodakdev, Ahmedabad",
            "address": "Plot 42, Near Rajpath Club, Bodakdev, Ahmedabad",
            "phone": "+91 98250 11223",
            "email": "bodakdev@apexsports.in"
        }
    )

    branch1_2, _ = Branch.objects.get_or_create(
        organization=org1,
        name="Apex Prahladnagar Complex",
        defaults={
            "city": "Ahmedabad",
            "location": "Prahladnagar, Ahmedabad",
            "address": "100ft Anandnagar Road, Prahladnagar, Ahmedabad",
            "phone": "+91 98250 44556",
            "email": "prahladnagar@apexsports.in"
        }
    )

    branch1_3, _ = Branch.objects.get_or_create(
        organization=org1,
        name="Apex Gandhinagar Hub",
        defaults={
            "city": "Gandhinagar",
            "location": "Sector 11, Gandhinagar",
            "address": "Koba Circle Sports Zone, Gandhinagar",
            "phone": "+91 98250 77889",
            "email": "gandhinagar@apexsports.in"
        }
    )

    # Branches for Org 2
    branch2_1, _ = Branch.objects.get_or_create(
        organization=org2,
        name="Urban Kicks Sindhu Bhavan",
        defaults={
            "city": "Ahmedabad",
            "location": "Sindhu Bhavan Road, Ahmedabad",
            "address": "SBR Sports Boulevard, Ahmedabad",
            "phone": "+91 99090 33445",
            "email": "sbr@urbankicks.com"
        }
    )

    branch2_2, _ = Branch.objects.get_or_create(
        organization=org2,
        name="Urban Kicks Vastrapur",
        defaults={
            "city": "Ahmedabad",
            "location": "Vastrapur, Ahmedabad",
            "address": "Near Vastrapur Lake, Ahmedabad",
            "phone": "+91 99090 66778",
            "email": "vastrapur@urbankicks.com"
        }
    )
    print("[OK] Branches created under organizations.")

    # 6. Custom Roles under Org 1
    role_mgr, _ = OrganizationRole.objects.get_or_create(
        organization=org1,
        name="General Manager",
        defaults={
            "description": "Full administrative command over daily branch operations, staff shifts, courts, and reports.",
            "can_manage_turfs": True,
            "can_manage_slots": True,
            "can_manage_bookings": True,
            "can_view_reports": True,
            "can_manage_staff": True
        }
    )

    role_staff, _ = OrganizationRole.objects.get_or_create(
        organization=org1,
        name="Operations Staff",
        defaults={
            "description": "Daily player check-in, court schedule monitoring, and on-ground management.",
            "can_manage_turfs": False,
            "can_manage_slots": True,
            "can_manage_bookings": True,
            "can_view_reports": False,
            "can_manage_staff": False
        }
    )

    role_cashier, _ = OrganizationRole.objects.get_or_create(
        organization=org1,
        name="Front Desk Cashier",
        defaults={
            "description": "Pass verification and offline payment collection.",
            "can_manage_turfs": False,
            "can_manage_slots": False,
            "can_manage_bookings": True,
            "can_view_reports": False,
            "can_manage_staff": False
        }
    )

    role_mgr_org2, _ = OrganizationRole.objects.get_or_create(
        organization=org2,
        name="General Manager",
        defaults={
            "description": "Full administrative command over daily branch operations, staff shifts, courts, and reports.",
            "can_manage_turfs": True,
            "can_manage_slots": True,
            "can_manage_bookings": True,
            "can_view_reports": True,
            "can_manage_staff": True
        }
    )

    role_staff_org2, _ = OrganizationRole.objects.get_or_create(
        organization=org2,
        name="Operations Staff",
        defaults={
            "description": "Daily player check-in, court schedule monitoring, and on-ground management.",
            "can_manage_turfs": False,
            "can_manage_slots": True,
            "can_manage_bookings": True,
            "can_view_reports": False,
            "can_manage_staff": False
        }
    )
    print(f"[OK] Custom Roles created under '{org1.name}' and '{org2.name}'.")

    # 7. Seed Turfs and link to Organizations & Branches
    turfs_seed = [
        {
            "name": "Green Field Cricket Academy",
            "primary_sport": sports_map["Cricket"],
            "sports": [sports_map["Cricket"]],
            "organization": org1,
            "branch": branch1_1,
            "location": "Bodakdev, Ahmedabad",
            "price_per_hour": 1200.00,
            "rating": 4.8,
            "rating_count": 38,
            "image_url": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1000&q=80",
            "description": "Green Field Cricket Academy offers state-of-the-art box cricket facilities with professional-grade artificial turf, high-lumen floodlights for evening play, and spacious changing rooms.",
            "amenities": ["Floodlights", "Changing Rooms", "Parking", "Equipment Rental", "Coaching Available"],
            "is_featured": True
        },
        {
            "name": "Premier Cricket Ground",
            "primary_sport": sports_map["Cricket"],
            "sports": [sports_map["Cricket"]],
            "organization": org1,
            "branch": branch1_2,
            "location": "Prahladnagar, Ahmedabad",
            "price_per_hour": 1100.00,
            "rating": 4.7,
            "rating_count": 31,
            "image_url": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1000&q=80",
            "description": "Top rated box cricket arena featuring imported Dutch synthetic turf, non-glare LED tower lighting, and electronic scoreboards.",
            "amenities": ["Floodlights", "Changing Rooms", "Parking"],
            "is_featured": True
        },
        {
            "name": "Urban Kicks Football Turf",
            "primary_sport": sports_map["Football"],
            "sports": [sports_map["Football"]],
            "organization": org2,
            "branch": branch2_1,
            "location": "Sindhu Bhavan Road, Ahmedabad",
            "price_per_hour": 1500.00,
            "rating": 4.9,
            "rating_count": 52,
            "image_url": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=1000&q=80",
            "description": "Ahmedabad's premier 5-a-side and 7-a-side football arena with FIFA Quality Pro certified 50mm monofilament turf.",
            "amenities": ["Floodlights", "Changing Rooms", "Parking", "Cafeteria", "Equipment Rental"],
            "is_featured": True
        },
        {
            "name": "Ace Pickleball Arena",
            "primary_sport": sports_map["Pickleball"],
            "sports": [sports_map["Pickleball"]],
            "organization": org2,
            "branch": branch2_2,
            "location": "Vastrapur, Ahmedabad",
            "price_per_hour": 700.00,
            "rating": 4.5,
            "rating_count": 22,
            "image_url": "https://images.unsplash.com/photo-1554068865-24cecd4e34b8?auto=format&fit=crop&w=1000&q=80",
            "description": "Conveniently located near Vastrapur lake, Ace Pickleball Arena is ideal for beginner and intermediate players seeking high quality courts at pocket-friendly rates.",
            "amenities": ["Indoor Courts", "Equipment Rental", "Coaching Available"],
            "is_featured": True
        }
    ]

    for t_data in turfs_seed:
        amenities_names = t_data.pop("amenities")
        sports_associated = t_data.pop("sports")
        turf, created = Turf.objects.get_or_create(name=t_data["name"], defaults=t_data)
        turf.organization = t_data["organization"]
        turf.branch = t_data["branch"]
        turf.location = t_data["location"]
        turf.sports.set(sports_associated)
        turf.amenities.set([amenities_map[a] for a in amenities_names if a in amenities_map])
        turf.save()
    print("[OK] All Turfs created, linked to sports, amenities, organizations, and branches.")

    # 8. User Accounts For All Levels (Unified login, validated strictly by email/account)
    
    # A. Super Admin (already configured as admin / superadmin@turfbook.com)
    
    # B. Organization Admin
    oa_email = os.getenv('ORG_ADMIN_EMAIL', 'admin.apex@turfbook.com')
    oa_pass = os.getenv('ORG_ADMIN_PASSWORD', 'password123')
    oa_user, _ = User.objects.get_or_create(
        username=oa_email,
        defaults={
            'email': oa_email,
            'first_name': 'Kavita',
            'last_name': 'Patel',
        }
    )
    oa_user.email = oa_email
    oa_user.set_password(oa_pass)
    oa_user.save()
    oa_profile, _ = UserProfile.objects.get_or_create(user=oa_user)
    oa_profile.role = 'ORG_ADMIN'
    oa_profile.organization = org1
    oa_profile.phone = '+91 98251 00001'
    oa_profile.save()
    print(f"[OK] Org Admin created: {oa_email} / {oa_pass}")

    # C. Manager
    mgr_email = os.getenv('MANAGER_EMAIL', 'manager.apex@turfbook.com')
    mgr_pass = os.getenv('MANAGER_PASSWORD', 'password123')
    mgr_user, _ = User.objects.get_or_create(
        username=mgr_email,
        defaults={
            'email': mgr_email,
            'first_name': 'Amit',
            'last_name': 'Shah',
        }
    )
    mgr_user.email = mgr_email
    mgr_user.set_password(mgr_pass)
    mgr_user.save()
    mgr_profile, _ = UserProfile.objects.get_or_create(user=mgr_user)
    mgr_profile.role = 'MANAGER'
    mgr_profile.organization = org1
    mgr_profile.branch = branch1_1
    mgr_profile.custom_role = role_mgr
    mgr_profile.phone = '+91 98251 00002'
    mgr_profile.save()
    print(f"[OK] Manager created: {mgr_email} / {mgr_pass}")

    # D. Staff
    stf_email = os.getenv('STAFF_EMAIL', 'staff.apex@turfbook.com')
    stf_pass = os.getenv('STAFF_PASSWORD', 'password123')
    stf_user, _ = User.objects.get_or_create(
        username=stf_email,
        defaults={
            'email': stf_email,
            'first_name': 'Ramesh',
            'last_name': 'Dave',
        }
    )
    stf_user.email = stf_email
    stf_user.set_password(stf_pass)
    stf_user.save()
    stf_profile, _ = UserProfile.objects.get_or_create(user=stf_user)
    stf_profile.role = 'STAFF'
    stf_profile.organization = org1
    stf_profile.branch = branch1_1
    stf_profile.custom_role = role_staff
    stf_profile.phone = '+91 98251 00003'
    stf_profile.save()
    print(f"[OK] Staff created: {stf_email} / {stf_pass}")

    # Helper function to create staff/manager
    def create_branch_user(email_env, default_email, pass_env, default_pass, first_name, last_name, role_type, org, branch, custom_role, phone):
        email = os.getenv(email_env, default_email)
        pwd = os.getenv(pass_env, default_pass)
        u, _ = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
        )
        u.email = email
        u.set_password(pwd)
        u.first_name = first_name
        u.last_name = last_name
        u.save()
        p, _ = UserProfile.objects.get_or_create(user=u)
        p.role = role_type
        p.organization = org
        p.branch = branch
        p.custom_role = custom_role
        p.phone = phone
        p.save()
        print(f"[OK] {role_type.title()} created: {email} / {pwd} ({branch.name if branch else org.name})")
        return u

    # Org 1: Additional Branch Accounts
    # Apex Prahladnagar Complex
    create_branch_user('APEX_PRAHLADNAGAR_MANAGER_EMAIL', 'manager.prahladnagar@turfbook.com', 'APEX_PRAHLADNAGAR_MANAGER_PASSWORD', 'password123', 'Rajesh', 'Vyas', 'MANAGER', org1, branch1_2, role_mgr, '+91 98251 00011')
    create_branch_user('APEX_PRAHLADNAGAR_STAFF_EMAIL', 'staff.prahladnagar@turfbook.com', 'APEX_PRAHLADNAGAR_STAFF_PASSWORD', 'password123', 'Sunil', 'Joshi', 'STAFF', org1, branch1_2, role_staff, '+91 98251 00012')

    # Apex Gandhinagar Hub
    create_branch_user('APEX_GANDHINAGAR_MANAGER_EMAIL', 'manager.gandhinagar@turfbook.com', 'APEX_GANDHINAGAR_MANAGER_PASSWORD', 'password123', 'Nirav', 'Panchal', 'MANAGER', org1, branch1_3, role_mgr, '+91 98251 00021')
    create_branch_user('APEX_GANDHINAGAR_STAFF_EMAIL', 'staff.gandhinagar@turfbook.com', 'APEX_GANDHINAGAR_STAFF_PASSWORD', 'password123', 'Hardik', 'Mehta', 'STAFF', org1, branch1_3, role_staff, '+91 98251 00022')

    # Org 2: Urban Kicks & Courts Group Accounts
    # Urban Kicks Org Admin
    create_branch_user('URBANKICKS_ADMIN_EMAIL', 'admin.urbankicks@turfbook.com', 'URBANKICKS_ADMIN_PASSWORD', 'password123', 'Manish', 'Trivedi', 'ORG_ADMIN', org2, None, None, '+91 99090 00001')

    # Urban Kicks Sindhu Bhavan (SBR)
    create_branch_user('URBANKICKS_SBR_MANAGER_EMAIL', 'manager.sbr@urbankicks.com', 'URBANKICKS_SBR_MANAGER_PASSWORD', 'password123', 'Devang', 'Thakar', 'MANAGER', org2, branch2_1, role_mgr_org2, '+91 99090 00011')
    create_branch_user('URBANKICKS_SBR_STAFF_EMAIL', 'staff.sbr@urbankicks.com', 'URBANKICKS_SBR_STAFF_PASSWORD', 'password123', 'Karan', 'Purohit', 'STAFF', org2, branch2_1, role_staff_org2, '+91 99090 00012')

    # Urban Kicks Vastrapur
    create_branch_user('URBANKICKS_VASTRAPUR_MANAGER_EMAIL', 'manager.vastrapur@urbankicks.com', 'URBANKICKS_VASTRAPUR_MANAGER_PASSWORD', 'password123', 'Snehal', 'Desai', 'MANAGER', org2, branch2_2, role_mgr_org2, '+91 99090 00021')
    create_branch_user('URBANKICKS_VASTRAPUR_STAFF_EMAIL', 'staff.vastrapur@urbankicks.com', 'URBANKICKS_VASTRAPUR_STAFF_PASSWORD', 'password123', 'Chirag', 'Modi', 'STAFF', org2, branch2_2, role_staff_org2, '+91 99090 00022')

    # E. Player
    plyr_email = os.getenv('PLAYER_EMAIL', 'player@example.com')
    plyr_pass = os.getenv('PLAYER_PASSWORD', 'password123')
    demo_user, _ = User.objects.get_or_create(
        username=plyr_email,
        defaults={
            'email': plyr_email,
            'first_name': 'Rahul',
            'last_name': 'Sharma',
        }
    )
    demo_user.email = plyr_email
    demo_user.set_password(plyr_pass)
    demo_user.save()
    demo_profile, _ = UserProfile.objects.get_or_create(user=demo_user)
    demo_profile.role = 'PLAYER'
    demo_profile.save()
    print(f"[OK] Player created: {plyr_email} / {plyr_pass}")

    # 9. Bookings: Today's bookings for fast check-in testing at Bodakdev branch
    turf_bodakdev = Turf.objects.filter(branch=branch1_1).first() or Turf.objects.first()
    today = date.today()

    # Booking 1: Confirmed today
    b1, _ = Booking.objects.get_or_create(
        user=demo_user,
        turf=turf_bodakdev,
        date=today,
        time_slot=time_slots[8], # 6-7 PM
        defaults={
            "total_price": turf_bodakdev.price_per_hour,
            "status": "CONFIRMED",
            "player_name": demo_user.get_full_name() or "Rahul Sharma",
            "player_phone": "+91 98765 43210"
        }
    )
    b1.status = "CONFIRMED"
    b1.save()

    # Booking 2: Another match today for check-in
    b2, _ = Booking.objects.get_or_create(
        user=demo_user,
        turf=turf_bodakdev,
        date=today,
        time_slot=time_slots[9], # 7-8 PM
        defaults={
            "total_price": turf_bodakdev.price_per_hour,
            "status": "CONFIRMED",
            "player_name": "Vikram Mehta",
            "player_phone": "+91 98980 12345"
        }
    )

    # 10. Hero Slides
    hero_slides_data = [
        {"title": "Footballs on Green Turf", "image_url": "https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=2000&q=80", "order": 1},
        {"title": "Soccer Ball on Turf Pitch", "image_url": "https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=2000&q=80", "order": 2},
        {"title": "Premier Football Arena", "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=2000&q=80", "order": 3},
    ]
    for hdata in hero_slides_data:
        HeroSlide.objects.get_or_create(title=hdata["title"], defaults=hdata)
    print("[OK] Hero background slider images configured.")

    print("\n" + "=" * 65)
    print("[SUCCESS] SYSTEM SEEDING COMPLETE!")
    print("Unified Login: All users log in via /login/ without any dropdown.")
    print("=" * 65)
    print("DEMO CREDENTIALS (Configured in .env):")
    print("  --- PLATFORM & SYSTEM ---")
    print("  1. SUPER ADMIN:           superadmin@turfbook.com (or 'admin') | admin123")
    print("     -> Routes to:          /super-admin/ (All Orgs & Branches)")
    print("  2. PLAYER / CUSTOMER:     player@example.com                   | password123")
    print("     -> Routes to:          /dashboard/ (My Bookings & Tickets)")
    print("  --- APEX SPORTS ARENA NETWORK (Org 1) ---")
    print("  3. ORG ADMIN:             admin.apex@turfbook.com              | password123 -> /org-admin/")
    print("  4. BODAKDEV MGR:          manager.apex@turfbook.com            | password123 -> /staff-portal/")
    print("  5. BODAKDEV STAFF:        staff.apex@turfbook.com              | password123 -> /staff-portal/")
    print("  6. PRAHLADNAGAR MGR:      manager.prahladnagar@turfbook.com    | password123 -> /staff-portal/")
    print("  7. PRAHLADNAGAR STAFF:    staff.prahladnagar@turfbook.com      | password123 -> /staff-portal/")
    print("  8. GANDHINAGAR MGR:       manager.gandhinagar@turfbook.com     | password123 -> /staff-portal/")
    print("  9. GANDHINAGAR STAFF:     staff.gandhinagar@turfbook.com       | password123 -> /staff-portal/")
    print("  --- URBAN KICKS & COURTS GROUP (Org 2) ---")
    print(" 10. ORG ADMIN:             admin.urbankicks@turfbook.com        | password123 -> /org-admin/")
    print(" 11. SINDHU BHAVAN MGR:     manager.sbr@urbankicks.com           | password123 -> /staff-portal/")
    print(" 12. SINDHU BHAVAN STAFF:   staff.sbr@urbankicks.com             | password123 -> /staff-portal/")
    print(" 13. VASTRAPUR MGR:         manager.vastrapur@urbankicks.com     | password123 -> /staff-portal/")
    print(" 14. VASTRAPUR STAFF:       staff.vastrapur@urbankicks.com       | password123 -> /staff-portal/")
    print("=" * 65)

if __name__ == '__main__':
    seed()
