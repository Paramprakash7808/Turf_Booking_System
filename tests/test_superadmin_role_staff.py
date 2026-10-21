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
    print("TESTING SUPER ADMIN CREATE ROLE & ADD STAFF/MEMBER")
    print("==================================================")

    client = Client()

    # 1. Super Admin Login
    logged_in = client.login(username='admin', password='admin123')
    if not logged_in:
        logged_in = client.login(username='superadmin@turfbook.com', password='admin123')
    assert logged_in, "Super Admin login failed"
    print("[PASS] 1. Super Admin authenticated successfully.")

    # Get or create an organization for testing
    org = Organization.objects.first()
    assert org is not None, "No organization found"
    branch = org.branches.first()
    print(f"[OK] Using Organization: '{org.name}', Branch: '{branch.name if branch else 'None'}'")

    # 2. Test Super Admin: CREATE ROLE
    role_name = "Master Turf Supervisor"
    role_desc = "Supervises all courts, slots, and field operations."
    
    # Remove if existed
    OrganizationRole.objects.filter(organization=org, name=role_name).delete()

    response = client.post('/super-admin/roles/create/', {
        'organization_id': str(org.id),
        'name': role_name,
        'description': role_desc,
        'can_manage_turfs': 'on',
        'can_manage_slots': 'on',
        'can_manage_bookings': 'on',
        'can_manage_staff': 'on',
        'can_view_reports': 'on',
        'next': f'/super-admin/orgs/{org.id}/',
    }, follow=False)

    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == f'/super-admin/orgs/{org.id}/', f"Expected redirect to org detail, got {response.url}"

    created_role = OrganizationRole.objects.filter(organization=org, name=role_name).first()
    assert created_role is not None, "Role was not created in database!"
    assert created_role.can_manage_turfs is True
    assert created_role.can_manage_slots is True
    assert created_role.can_manage_bookings is True
    assert created_role.can_manage_staff is True
    assert created_role.can_view_reports is True
    print(f"[PASS] 2. Super Admin created role '{created_role.name}' with all permissions.")

    # 3. Test Super Admin: ADD STAFF / MEMBER
    staff_email = "newstaff.superadmin@turfbook.com"
    staff_pass = "staffpass123"

    # Remove if existed
    User.objects.filter(email=staff_email).delete()

    response = client.post('/super-admin/team/create/', {
        'organization_id': str(org.id),
        'first_name': 'Rohan',
        'last_name': 'Desai',
        'email': staff_email,
        'password': staff_pass,
        'phone': '+91 91234 56789',
        'system_role': 'STAFF',
        'custom_role_id': str(created_role.id),
        'branch_id': str(branch.id) if branch else '',
        'next': f'/super-admin/orgs/{org.id}/',
    }, follow=False)

    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.url == f'/super-admin/orgs/{org.id}/'

    staff_user = User.objects.filter(email=staff_email).first()
    assert staff_user is not None, "Staff user was not created in database!"
    assert staff_user.first_name == 'Rohan'
    assert staff_user.last_name == 'Desai'

    staff_profile = getattr(staff_user, 'profile', None)
    assert staff_profile is not None, "UserProfile not created for staff!"
    assert staff_profile.role == 'STAFF'
    assert staff_profile.organization == org
    assert staff_profile.custom_role == created_role
    if branch:
        assert staff_profile.branch == branch
    print(f"[PASS] 3. Super Admin added staff member '{staff_user.email}' linked to '{org.name}' and role '{created_role.name}'.")

    # 4. Test Unified Login for newly created staff member
    client.logout()
    login_resp = client.post('/login/', {
        'email': staff_email,
        'password': staff_pass,
    }, follow=False)

    assert login_resp.status_code == 302, f"Expected 302 redirect from login, got {login_resp.status_code}"
    assert login_resp.url == '/staff-portal/', f"Expected redirect to /staff-portal/, got {login_resp.url}"
    print(f"[PASS] 4. Newly created staff '{staff_email}' logged in successfully via unified /login/ and routed directly to '{login_resp.url}'.")

    # Access Staff Portal
    portal_resp = client.get('/staff-portal/')
    assert portal_resp.status_code == 200, f"Expected 200 on staff portal, got {portal_resp.status_code}"
    portal_html = portal_resp.content.decode('utf-8')
    assert 'Rapid Desk Check-In Station' in portal_html
    print("[PASS] 5. Staff portal loaded with active check-in station.")

    # 6. Test Super Admin: ADD ORG ADMIN MEMBER
    client.logout()
    if not client.login(username='admin', password='admin123'):
        client.login(username='superadmin@turfbook.com', password='admin123')

    org_admin_email = "newadmin.superadmin@turfbook.com"
    User.objects.filter(email=org_admin_email).delete()

    resp = client.post('/super-admin/team/create/', {
        'organization_id': str(org.id),
        'first_name': 'Pooja',
        'last_name': 'Mehta',
        'email': org_admin_email,
        'password': 'adminpass123',
        'system_role': 'ORG_ADMIN',
    }, follow=False)
    assert resp.status_code == 302, f"Expected 302, got {resp.status_code}"

    client.logout()
    oa_login_resp = client.post('/login/', {
        'email': org_admin_email,
        'password': 'adminpass123',
    }, follow=False)
    assert oa_login_resp.status_code == 302
    assert oa_login_resp.url == '/org-admin/', f"Expected redirect to /org-admin/, got {oa_login_resp.url}"
    print(f"[PASS] 6. Super Admin added Org Admin '{org_admin_email}', logged in via unified /login/ and routed directly to '{oa_login_resp.url}'.")

    # 7. Check UI Pages Render properly
    client.logout()
    if not client.login(username='admin', password='admin123'):
        client.login(username='superadmin@turfbook.com', password='admin123')

    sa_resp = client.get('/super-admin/')
    assert sa_resp.status_code == 200
    sa_html = sa_resp.content.decode('utf-8')
    assert 'Create Role' in sa_html
    assert 'Add Staff / Member' in sa_html
    assert 'teamTab' in sa_html
    assert 'Staff &amp; Roles' in sa_html or 'Staff & Roles' in sa_html
    assert 'Master Turf Supervisor' in sa_html
    print("[PASS] 7. /super-admin/ renders Staff & Roles tab, Create Role and Add Staff modals.")

    detail_resp = client.get(f'/super-admin/orgs/{org.id}/')
    assert detail_resp.status_code == 200
    detail_html = detail_resp.content.decode('utf-8')
    assert 'Operational Custom Roles' in detail_html
    assert 'Master Turf Supervisor' in detail_html
    assert 'Add Staff / Member' in detail_html
    assert 'Create Role' in detail_html
    print(f"[PASS] 8. /super-admin/orgs/{org.id}/ renders Operational Roles and Add Staff actions.")

    print("\nALL SUPER ADMIN ROLE & STAFF MANAGEMENT TESTS PASSED PERFECTLY!\n")

if __name__ == '__main__':
    run_tests()
