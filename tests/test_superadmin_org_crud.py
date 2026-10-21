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
from turfs.models import Organization, Branch, OrganizationRole, UserProfile, Turf, Sport

def run_tests():
    print("==================================================")
    print("TESTING SUPER ADMIN ORGANIZATION UPDATE & DELETE")
    print("==================================================")

    client = Client()

    # 1. Login as Super Admin
    logged_in = client.login(username='admin', password='admin123')
    if not logged_in:
        logged_in = client.login(username='superadmin@turfbook.com', password='admin123')
    assert logged_in, "Super Admin login failed"
    print("[PASS] 1. Super Admin authenticated successfully.")

    # 2. Cleanup any leftover test organizations from previous runs
    Organization.objects.filter(name__in=['Test Org Alpha', 'Updated Alpha Sports Network', 'Conflict Target Org']).delete()

    # 3. Create test organization with a branch and custom role
    test_org = Organization.objects.create(
        name="Test Org Alpha",
        email="alpha@testorg.com",
        phone="9876543210",
        address="100 SG Highway, Ahmedabad",
        description="Initial test organization description",
        is_active=True
    )
    org_id = test_org.id

    test_branch = Branch.objects.create(
        organization=test_org,
        name="Alpha West Branch",
        location="SG Highway, Ahmedabad",
        city="Ahmedabad",
        phone="9876543210"
    )

    test_role = OrganizationRole.objects.create(
        organization=test_org,
        name="Alpha Shift Manager",
        can_manage_bookings=True
    )

    print(f"[OK] Test organization created: ID={org_id}, Name='{test_org.name}'")

    # 4. Check UI rendering on Super Admin dashboard and Org Detail
    dashboard_res = client.get('/super-admin/')
    assert dashboard_res.status_code == 200, f"Expected 200, got {dashboard_res.status_code}"
    dashboard_html = dashboard_res.content.decode('utf-8')
    assert "openEditOrgModal" in dashboard_html, "Edit Org modal handler missing from /super-admin/"
    assert "openDeleteOrgModal" in dashboard_html, "Delete Org modal handler missing from /super-admin/"
    assert "editOrgModal" in dashboard_html, "Edit Org modal HTML element missing from /super-admin/"
    assert "deleteOrgModal" in dashboard_html, "Delete Org modal HTML element missing from /super-admin/"
    print("[PASS] 2. /super-admin/ renders Edit and Delete Organization actions and modals.")

    detail_res = client.get(f'/super-admin/orgs/{org_id}/')
    assert detail_res.status_code == 200, f"Expected 200, got {detail_res.status_code}"
    detail_html = detail_res.content.decode('utf-8')
    assert "Edit Org" in detail_html, "'Edit Org' button missing from /super-admin/orgs/{id}/"
    assert "Delete Org" in detail_html, "'Delete Org' button missing from /super-admin/orgs/{id}/"
    print("[PASS] 3. /super-admin/orgs/{id}/ renders Edit and Delete Organization controls.")

    # 5. Test UPDATE Organization Details
    update_res = client.post(f'/super-admin/orgs/{org_id}/update/', {
        'name': 'Updated Alpha Sports Network',
        'email': 'updated.alpha@sportsnetwork.com',
        'phone': '9123456789',
        'address': 'Level 4, Alpha Tower, Bodakdev, Ahmedabad',
        'description': 'Premier multi-sport facilities and private turf courts.',
        'is_active': 'on',
    }, follow=False)

    assert update_res.status_code == 302, f"Expected 302 redirect on update, got {update_res.status_code}"
    test_org.refresh_from_db()
    assert test_org.name == 'Updated Alpha Sports Network', f"Expected updated name, got '{test_org.name}'"
    assert test_org.slug == 'updated-alpha-sports-network', f"Expected updated slug, got '{test_org.slug}'"
    assert test_org.email == 'updated.alpha@sportsnetwork.com'
    assert test_org.phone == '9123456789'
    assert test_org.is_active is True
    print("[PASS] 4. Super Admin successfully updated organization details and slug.")

    # 6. Test VALIDATION on Organization Update
    # 6.1 Duplicate Name check
    conflict_org = Organization.objects.create(name="Conflict Target Org", email="target@conflict.com")
    dup_res = client.post(f'/super-admin/orgs/{org_id}/update/', {
        'name': 'Conflict Target Org',
        'email': 'valid@org.com',
        'phone': '9876543210',
    }, follow=True)
    test_org.refresh_from_db()
    assert test_org.name == 'Updated Alpha Sports Network', "Org name should not change when duplicate name is provided"
    print("[PASS] 5.1 Rejected duplicate organization name collision.")

    # 6.2 Invalid Email check (missing dot)
    bad_email_res = client.post(f'/super-admin/orgs/{org_id}/update/', {
        'name': 'Updated Alpha Sports Network',
        'email': 'invalidemail@domain',
        'phone': '9876543210',
    }, follow=True)
    test_org.refresh_from_db()
    assert test_org.email == 'updated.alpha@sportsnetwork.com', "Org email should not change on invalid email format"
    print("[PASS] 5.2 Rejected invalid email format missing dot.")

    # 6.3 Invalid Phone check (< 10 digits)
    bad_phone_res = client.post(f'/super-admin/orgs/{org_id}/update/', {
        'name': 'Updated Alpha Sports Network',
        'email': 'updated.alpha@sportsnetwork.com',
        'phone': '12345',
    }, follow=True)
    test_org.refresh_from_db()
    assert test_org.phone == '9123456789', "Org phone should not change on non-10 digit input"
    print("[PASS] 5.3 Rejected invalid phone number with less than 10 digits.")

    # 7. SECURITY: Unauthorized player/customer blocked
    client.logout()
    player_user, _ = User.objects.get_or_create(username='test_player_crud@example.com', defaults={'email': 'test_player_crud@example.com'})
    player_user.set_password('PlayerPass123!')
    player_user.save()
    UserProfile.objects.update_or_create(user=player_user, defaults={'role': 'PLAYER'})
    
    player_logged = client.login(username='test_player_crud@example.com', password='PlayerPass123!')
    assert player_logged, "Player login failed"

    # Attempt update as player
    hack_update = client.post(f'/super-admin/orgs/{org_id}/update/', {'name': 'Hacked Org Name'})
    assert hack_update.status_code == 302, "Unauthorized player must be redirected"
    test_org.refresh_from_db()
    assert test_org.name == 'Updated Alpha Sports Network'

    # Attempt delete as player
    hack_delete = client.post(f'/super-admin/orgs/{org_id}/delete/')
    assert hack_delete.status_code == 302, "Unauthorized player must be redirected"
    assert Organization.objects.filter(id=org_id).exists(), "Org should still exist"
    print("[PASS] 6. Unauthorized player strictly blocked from updating or deleting organizations.")

    # 8. Test DELETE Organization as Super Admin
    client.logout()
    logged_in = client.login(username='admin', password='admin123')
    if not logged_in:
        logged_in = client.login(username='superadmin@turfbook.com', password='admin123')
    assert logged_in, "Super Admin re-login failed"

    delete_res = client.post(f'/super-admin/orgs/{org_id}/delete/', follow=False)
    assert delete_res.status_code == 302, f"Expected 302 redirect after delete, got {delete_res.status_code}"
    assert delete_res.url == '/super-admin/', f"Expected redirect to /super-admin/, got '{delete_res.url}'"

    # Verify organization and cascaded objects are deleted
    assert not Organization.objects.filter(id=org_id).exists(), "Organization should be deleted from DB"
    assert not Branch.objects.filter(name="Alpha West Branch").exists(), "Cascaded branch should be deleted from DB"
    assert not OrganizationRole.objects.filter(name="Alpha Shift Manager").exists(), "Cascaded role should be deleted from DB"
    print("[PASS] 7. Super Admin successfully deleted organization and cascaded branches/roles.")

    # Clean up conflict org
    conflict_org.delete()

    print("\n==================================================")
    print("ALL SUPER ADMIN ORGANIZATION UPDATE & DELETE TESTS PASSED!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
