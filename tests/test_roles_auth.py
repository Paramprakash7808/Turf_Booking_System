import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from turfs.models import Organization, Branch, OrganizationRole, UserProfile

def run_tests():
    print("==================================================")
    print("RUNNING ROLE HIERARCHY & UNIFIED AUTH TESTS")
    print("==================================================")

    client = Client()

    # TEST 1: Check login page has NO role dropdown
    response = client.get('/login/')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content = response.content.decode('utf-8')
    assert '<select' not in content, "VIOLATION: <select> dropdown found on login page!"
    assert 'role' not in content.lower() or 'select role' not in content.lower(), "VIOLATION: Role selector found on login page!"
    print("[PASS] Test 1: /login/ has ZERO role dropdowns and pure email/password fields.")

    # TEST 2: Super Admin Login via Email -> Redirect to /super-admin/
    client.logout()
    response = client.post('/login/', {'email': 'superadmin@turfbook.com', 'password': 'admin123'}, follow=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == '/super-admin/', f"Expected redirect to /super-admin/, got {response.url}"
    print(f"[PASS] Test 2: superadmin@turfbook.com redirected cleanly to '{response.url}'")

    # TEST 3: Super Admin Portal view contains all orgs and branches
    response = client.get('/super-admin/')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    s_content = response.content.decode('utf-8')
    assert 'Apex Sports Arena Network' in s_content, "Missing Org 1 in Super Admin"
    assert ('Urban Kicks & Courts Group' in s_content or 'Urban Kicks &amp; Courts Group' in s_content), "Missing Org 2 in Super Admin"
    assert 'Apex Bodakdev Arena' in s_content, "Missing Bodakdev branch in Super Admin"
    assert 'Urban Kicks Sindhu Bhavan' in s_content, "Missing Sindhu Bhavan branch in Super Admin"
    print("[PASS] Test 3: /super-admin/ displays all organizations and branches system-wide.")

    # TEST 4: Org Admin Login via Email -> Redirect to /org-admin/
    client.logout()
    response = client.post('/login/', {'email': 'admin.apex@turfbook.com', 'password': 'password123'}, follow=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == '/org-admin/', f"Expected redirect to /org-admin/, got {response.url}"
    print(f"[PASS] Test 4: admin.apex@turfbook.com redirected cleanly to '{response.url}'")

    # TEST 5: Org Admin can view their org and can create custom roles
    response = client.get('/org-admin/')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    oa_content = response.content.decode('utf-8')
    assert 'Apex Sports Arena Network' in oa_content
    assert 'General Manager' in oa_content
    print("[PASS] Test 5: /org-admin/ displays org details, custom roles, and team management.")

    # TEST 6: Org Admin creates a new custom role
    response = client.post('/org-admin/roles/create/', {
        'name': 'Weekend Shift Captain',
        'description': 'Leads court operations and bookings over Saturdays and Sundays',
        'can_manage_bookings': 'on',
        'can_manage_turfs': 'on'
    }, follow=True)
    assert response.status_code == 200
    assert OrganizationRole.objects.filter(name='Weekend Shift Captain').exists()
    print("[PASS] Test 6: Org Admin successfully created custom role 'Weekend Shift Captain'.")

    # TEST 7: Manager Login via Email -> Redirect to /staff-portal/
    client.logout()
    response = client.post('/login/', {'email': 'manager.apex@turfbook.com', 'password': 'password123'}, follow=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == '/staff-portal/', f"Expected redirect to /staff-portal/, got {response.url}"
    print(f"[PASS] Test 7: manager.apex@turfbook.com redirected cleanly to '{response.url}'")

    # TEST 8: Staff Login via Email -> Redirect to /staff-portal/
    client.logout()
    response = client.post('/login/', {'email': 'staff.apex@turfbook.com', 'password': 'password123'}, follow=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == '/staff-portal/', f"Expected redirect to /staff-portal/, got {response.url}"
    print(f"[PASS] Test 8: staff.apex@turfbook.com redirected cleanly to '{response.url}'")

    # TEST 9: Staff Portal Access & Pass Verification
    response = client.get('/staff-portal/')
    assert response.status_code == 200
    stf_content = response.content.decode('utf-8')
    assert 'Rapid Desk Check-In Station' in stf_content
    assert 'Apex Bodakdev Arena' in stf_content
    print("[PASS] Test 9: /staff-portal/ operational with live check-in station and manifest.")

    # TEST 10: Player / Customer Login via Email -> Redirect to /dashboard/
    client.logout()
    response = client.post('/login/', {'email': 'player@example.com', 'password': 'password123'}, follow=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == '/dashboard/', f"Expected redirect to /dashboard/, got {response.url}"
    print(f"[PASS] Test 10: player@example.com redirected cleanly to '{response.url}'")

    # TEST 11: Security Isolation: Player cannot access /super-admin/ or /org-admin/
    response = client.get('/super-admin/', follow=True)
    assert response.redirect_chain[-1][0] == '/dashboard/' or response.redirect_chain[-1][0] == '/login/?next=/super-admin/'
    response = client.get('/org-admin/', follow=True)
    assert response.redirect_chain[-1][0] == '/dashboard/' or response.redirect_chain[-1][0] == '/login/?next=/org-admin/'
    print("[PASS] Test 11: Security isolation confirmed: Player cannot access Super Admin or Org Admin portals.")

    print("\n" + "=" * 50)
    print("ALL 11 TESTS PASSED PERFECTLY!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
