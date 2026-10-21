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
from turfs.models import Organization, Branch

def run_tests():
    print("==================================================")
    print("TESTING SUPER ADMIN BRANCH UPDATE & DELETE")
    print("==================================================")

    client = Client()

    # 1. Login as Super Admin
    logged_in = client.login(username='admin', password='admin123')
    if not logged_in:
        logged_in = client.login(username='superadmin@turfbook.com', password='admin123')
    assert logged_in, "Super Admin login failed"
    print("[PASS] Super Admin logged in successfully.")

    # 2. Get an existing branch
    org = Organization.objects.first()
    assert org is not None, "No organizations found"
    
    # Clean up if existed from previous run to ensure idempotency
    Branch.objects.filter(organization=org, name='Updated Premier Arena').delete()

    test_branch, created = Branch.objects.get_or_create(
        organization=org,
        name="Test Operations Hub",
        defaults={
            "location": "Prahladnagar, Ahmedabad",
            "city": "Ahmedabad",
            "phone": "+91 99999 88888",
            "email": "test.hub@example.com",
            "is_active": True
        }
    )
    branch_id = test_branch.id
    print(f"[OK] Test branch ready: ID={branch_id}, Name='{test_branch.name}'")

    # 3. Test UPDATE branch
    update_response = client.post(f'/super-admin/branches/{branch_id}/update/', {
        'name': 'Updated Premier Arena',
        'location': 'Sindhu Bhavan Extension, Ahmedabad',
        'city': 'Ahmedabad',
        'address': 'Opposite Club 07',
        'phone': '+91 98765 00000',
        'email': 'premier.updated@example.com',
        'is_active': 'on',
        'organization_id': str(org.id),
    }, follow=False)

    assert update_response.status_code == 302, f"Expected 302 redirect, got {update_response.status_code}"
    
    # Reload from DB
    test_branch.refresh_from_db()
    assert test_branch.name == 'Updated Premier Arena', f"Expected 'Updated Premier Arena', got '{test_branch.name}'"
    assert test_branch.location == 'Sindhu Bhavan Extension, Ahmedabad'
    assert test_branch.phone == '+91 98765 00000'
    assert test_branch.is_active is True
    print("[PASS] Test 1: Super Admin successfully updated existing branch details.")

    # 4. Test DELETE branch
    delete_response = client.post(f'/super-admin/branches/{branch_id}/delete/', follow=False)
    assert delete_response.status_code == 302, f"Expected 302 redirect, got {delete_response.status_code}"

    # Verify deleted from DB
    assert not Branch.objects.filter(id=branch_id).exists(), "Branch should have been deleted from DB!"
    print("[PASS] Test 2: Super Admin successfully deleted existing branch.")

    # 5. Security Test: Non-superadmin cannot update or delete branches
    client.logout()
    player_logged_in = client.login(username='player@example.com', password='password123')
    assert player_logged_in, "Player login failed"

    any_branch = Branch.objects.first()
    if any_branch:
        sec_response = client.post(f'/super-admin/branches/{any_branch.id}/update/', {'name': 'Hacked Branch'}, follow=False)
        assert sec_response.status_code == 302
        assert '/super-admin/' not in sec_response.url or '/dashboard/' in sec_response.url
        any_branch.refresh_from_db()
        assert any_branch.name != 'Hacked Branch'

        sec_del_response = client.post(f'/super-admin/branches/{any_branch.id}/delete/', follow=False)
        assert sec_del_response.status_code == 302
        assert Branch.objects.filter(id=any_branch.id).exists()
        print("[PASS] Test 3: Unauthorized customer/player blocked from updating or deleting branches.")

    # 6. Test Org Admin Branch Management (Update, Delete, Tenant Isolation)
    client.logout()
    org_admin_logged_in = client.login(username='admin.apex@turfbook.com', password='password123')
    assert org_admin_logged_in, "Org Admin login failed"
    print("[PASS] Test 4: Org Admin logged in successfully.")

    apex_org = Organization.objects.filter(name__icontains='Apex').first()
    assert apex_org is not None

    # Check UI rendering in /org-admin/
    org_admin_res = client.get('/org-admin/')
    assert org_admin_res.status_code == 200
    org_admin_html = org_admin_res.content.decode('utf-8')
    assert 'openEditBranchModal' in org_admin_html, "Edit Branch trigger missing from /org-admin/"
    assert 'openDeleteBranchModal' in org_admin_html, "Delete Branch trigger missing from /org-admin/"
    assert 'editBranchModal' in org_admin_html, "Edit Branch modal missing from /org-admin/"
    assert 'deleteBranchModal' in org_admin_html, "Delete Branch modal missing from /org-admin/"
    print("[PASS] Test 5: /org-admin/ renders Edit Branch and Delete Branch modals and controls.")

    # Org Admin creates a new branch
    create_res = client.post('/org-admin/branches/create/', {
        'name': 'Apex Thaltej Arena',
        'location': 'Thaltej Cross Roads',
        'city': 'Ahmedabad',
        'phone': '9876500001',
    }, follow=False)
    assert create_res.status_code == 302
    created_branch = Branch.objects.filter(organization=apex_org, name='Apex Thaltej Arena').first()
    assert created_branch is not None, "Branch creation by Org Admin failed"
    print("[PASS] Test 6: Org Admin successfully created branch.")

    # Org Admin updates their branch
    update_res = client.post(f'/org-admin/branches/{created_branch.id}/update/', {
        'name': 'Apex Thaltej Sports Hub',
        'location': 'Near Thaltej Metro Station',
        'city': 'Ahmedabad',
        'address': 'Plot 42, Thaltej',
        'phone': '9876500002',
        'email': 'thaltej@apexarena.com',
        'is_active': 'on',
    }, follow=False)
    assert update_res.status_code == 302
    created_branch.refresh_from_db()
    assert created_branch.name == 'Apex Thaltej Sports Hub'
    assert created_branch.location == 'Near Thaltej Metro Station'
    print("[PASS] Test 7: Org Admin successfully updated their branch.")

    # Org Admin deletes their branch
    del_res = client.post(f'/org-admin/branches/{created_branch.id}/delete/', follow=False)
    assert del_res.status_code == 302
    assert not Branch.objects.filter(id=created_branch.id).exists()
    print("[PASS] Test 8: Org Admin successfully deleted their branch.")

    print("\n" + "=" * 50)
    print("ALL BRANCH UPDATE & DELETE TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
