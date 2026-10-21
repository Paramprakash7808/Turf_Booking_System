import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from turfs.models import UserProfile, Organization, Branch, Turf, Sport, TimeSlot, Booking

def run_tests():
    print("=" * 50)
    print("TESTING FULL PLATFORM RESPONSIVENESS")
    print("=" * 50)

    client = Client()

    # Test 1: Base template contains viewport meta tag & mobile drawer elements
    response = client.get('/')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content = response.content.decode('utf-8')
    assert 'name="viewport"' in content, "Missing viewport meta tag in base.html"
    assert 'id="mobileMenuBtn"' in content, "Missing mobileMenuBtn in base.html"
    assert 'id="mobileMenu"' in content, "Missing mobileMenu in base.html"
    assert 'overflow-x-hidden' in content, "Missing overflow-x-hidden on body in base.html"
    print("[PASS] Test 1: base.html contains mobile viewport, menu drawer, and touch-friendly navigation.")

    # Test 2: Turf List contains mobile filter drawer toggle & scrollable pills
    response = client.get('/turfs/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'id="toggleMobileFilterBtn"' in content, "Missing toggleMobileFilterBtn in turf_list.html"
    assert 'id="closeMobileFilterBtn"' in content, "Missing closeMobileFilterBtn in turf_list.html"
    assert 'id="filterSidebar"' in content, "Missing filterSidebar in turf_list.html"
    assert 'touch-scroll' in content, "Missing touch-scroll for sports pills in turf_list.html"
    print("[PASS] Test 2: /turfs/ contains mobile filter drawer toggle and touch-scrollable sports pills.")

    # Test 3: Sports List contains mobile filter drawer toggle & scrollable pills
    response = client.get('/sports/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'id="toggleSportsMobileFilterBtn"' in content, "Missing toggleSportsMobileFilterBtn in sports_list.html"
    assert 'id="closeSportsMobileFilterBtn"' in content, "Missing closeSportsMobileFilterBtn in sports_list.html"
    assert 'id="sportsFilterSidebar"' in content, "Missing sportsFilterSidebar in sports_list.html"
    assert 'touch-scroll' in content, "Missing touch-scroll for sports pills in sports_list.html"
    print("[PASS] Test 3: /sports/ contains mobile filter drawer toggle and touch-scrollable sports pills.")

    # Test 4: Turf Detail contains mobile floating sticky booking bar & responsive media aspect ratio
    turf = Turf.objects.first()
    if turf:
        response = client.get(f'/turfs/{turf.slug}/')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'sm:aspect-[21/9]' in content or 'aspect-[16/10]' in content, "Missing responsive banner aspect ratio in turf_detail.html"
        assert 'lg:hidden' in content and 'Book Slot' in content, "Missing mobile floating booking CTA in turf_detail.html"
        print("[PASS] Test 4: /turfs/<slug>/ contains mobile floating booking bar and responsive media banner.")

    # Test 5: Booking view contains mobile sticky summary bottom bar
    if turf:
        response = client.get(f'/booking/{turf.id}/')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'id="mobileBookingBar"' in content, "Missing mobileBookingBar in booking.html"
        assert 'id="mobileSelectedCount"' in content, "Missing mobileSelectedCount in booking.html"
        assert 'id="mobileTotalPrice"' in content, "Missing mobileTotalPrice in booking.html"
        assert 'slotsGrid' in content, "Missing slotsGrid in booking.html"
        print("[PASS] Test 5: /booking/<id>/ contains mobile sticky bottom summary bar and responsive slot grid.")

    # Test 6: Super Admin portal contains horizontally scrollable tabs & min-width tables
    super_user = User.objects.filter(is_superuser=True).first()
    if not super_user:
        super_user = User.objects.create_superuser('resp_super', 'resp_super@turfbook.com', 'password123')
    client.force_login(super_user)
    response = client.get('/super-admin/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'overflow-x-auto' in content and 'touch-scroll' in content, "Missing touch-scroll in super_admin tabs"
    assert 'shrink-0' in content and 'whitespace-nowrap' in content, "Missing shrink-0 on tab buttons in super_admin"
    assert 'min-w-' in content, "Missing min-w on tables in super_admin"
    print("[PASS] Test 6: /super-admin/ contains touch-scrollable tabs and responsive data tables.")

    # Test 7: Org Admin portal contains horizontally scrollable tabs, min-width tables & scrollable modals
    org_admin_user = User.objects.filter(profile__role='ORG_ADMIN').first()
    if org_admin_user:
        client.force_login(org_admin_user)
        response = client.get('/org-admin/')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'touch-scroll' in content, "Missing touch-scroll in org_admin tabs"
        assert 'shrink-0' in content and 'whitespace-nowrap' in content, "Missing shrink-0 on tabs in org_admin"
        assert 'min-w-[640px]' in content or 'min-w-[700px]' in content, "Missing min-w on tables in org_admin"
        assert 'max-h-[90vh]' in content and 'overflow-y-auto' in content, "Missing modal scrollable viewport in org_admin"
        print("[PASS] Test 7: /org-admin/ contains touch-scrollable tabs, responsive tables, and scrollable modal sheets.")

    # Test 8: Staff portal contains horizontally scrollable branch filters & min-width manifest table
    staff_user = User.objects.filter(profile__role__in=['MANAGER', 'STAFF']).first()
    if staff_user:
        client.force_login(staff_user)
        response = client.get('/staff-portal/')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'touch-scroll' in content, "Missing touch-scroll in staff portal"
        assert 'min-w-[780px]' in content, "Missing min-w on manifest table in staff portal"
        print("[PASS] Test 8: /staff-portal/ contains touch-scrollable branch tabs and responsive manifest table.")

    print("\n" + "=" * 50)
    print("ALL PLATFORM RESPONSIVENESS TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
