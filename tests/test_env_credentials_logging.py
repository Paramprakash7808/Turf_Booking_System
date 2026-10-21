"""
Test Suite: Environment Credentials Auto-Logging (.env persistence)
Verifies that whenever a new user, admin, manager, or staff member is created
or registered (or updates their password), their credentials (email, username,
plaintext password, and role) are automatically persisted into the project .env file.
"""
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
from turfs.models import Organization, Branch, UserProfile
from turfs.env_sync import get_env_file_path, sanitize_identifier

def run_tests():
    print("\n" + "=" * 50)
    print("RUNNING .ENV CREDENTIALS LOGGING TEST SUITE")
    print("=" * 50)

    env_path = get_env_file_path()
    assert env_path.exists(), f".env file must exist at {env_path}"

    # Backup original .env content to ensure zero side-effects
    original_env_content = env_path.read_text(encoding='utf-8')

    client = Client()

    try:
        # ----------------------------------------------------
        # Test 1: Customer / Player Registration via /register/
        # ----------------------------------------------------
        test_player_email = "test.env.player@example.com"
        test_player_pass = "PlayerPass999!"

        # Remove existing user if any
        User.objects.filter(email=test_player_email).delete()

        reg_resp = client.post('/register/', {
            'first_name': 'TestEnv',
            'last_name': 'Player',
            'email': test_player_email,
            'phone': '9876543210',
            'password': test_player_pass,
            'confirm_password': test_player_pass,
        }, follow=True)

        assert reg_resp.status_code == 200, f"Registration failed with code {reg_resp.status_code}"
        assert User.objects.filter(email=test_player_email).exists(), "User should exist in database"

        # Verify .env contents
        env_text = env_path.read_text(encoding='utf-8')
        player_ident = sanitize_identifier(test_player_email)

        assert f"USER_{player_ident}_EMAIL={test_player_email}" in env_text, \
            f"Expected USER_{player_ident}_EMAIL={test_player_email} in .env"
        assert f"USER_{player_ident}_PASSWORD={test_player_pass}" in env_text, \
            f"Expected USER_{player_ident}_PASSWORD={test_player_pass} in .env"
        assert f"USER_{player_ident}_ROLE=PLAYER" in env_text, \
            f"Expected USER_{player_ident}_ROLE=PLAYER in .env"
        assert f"LATEST_CREATED_USER_EMAIL={test_player_email}" in env_text, \
            "Expected LATEST_CREATED_USER_EMAIL to be updated"
        assert f"NEW_ACCOUNT_EMAIL={test_player_email}" in env_text, \
            "Expected NEW_ACCOUNT_EMAIL to be updated"
        print("[PASS] Test 1: Player registration automatically recorded email, password, and role in .env")

        # ----------------------------------------------------
        # Test 2: Super Admin creates Org & Org Admin
        # ----------------------------------------------------
        sa_user = User.objects.filter(is_superuser=True).first()
        if not sa_user:
            sa_user = User.objects.create_superuser('test_sa', 'test_sa@turfbook.com', 'admin123')
        client.force_login(sa_user)

        test_oa_email = "test.env.oa@example.com"
        test_oa_pass = "OrgAdminPass888!"
        User.objects.filter(email=test_oa_email).delete()

        org_resp = client.post('/super-admin/orgs/create/', {
            'name': 'Test Env Arena Network',
            'location': 'Rajkot',
            'admin_name': 'Test OA Admin',
            'admin_email': test_oa_email,
            'admin_password': test_oa_pass,
            'phone': '9876543211',
        }, follow=True)

        assert org_resp.status_code == 200, f"Org creation failed with {org_resp.status_code}"
        env_text = env_path.read_text(encoding='utf-8')
        oa_ident = sanitize_identifier(test_oa_email)

        assert f"ORG_ADMIN_{oa_ident}_EMAIL={test_oa_email}" in env_text, \
            f"Expected ORG_ADMIN_{oa_ident}_EMAIL in .env"
        assert f"ORG_ADMIN_{oa_ident}_PASSWORD={test_oa_pass}" in env_text, \
            f"Expected ORG_ADMIN_{oa_ident}_PASSWORD in .env"
        assert f"ORG_ADMIN_{oa_ident}_ROLE=ORG_ADMIN" in env_text, \
            f"Expected ORG_ADMIN_{oa_ident}_ROLE=ORG_ADMIN in .env"
        print("[PASS] Test 2: Super Admin creating Org Admin automatically recorded in .env")

        # ----------------------------------------------------
        # Test 3: Super Admin creates Staff Member
        # ----------------------------------------------------
        test_org = Organization.objects.filter(name='Test Env Arena Network').first()
        test_staff_email = "test.env.staff@example.com"
        test_staff_pass = "StaffSecret777!"
        User.objects.filter(email=test_staff_email).delete()

        staff_resp = client.post('/super-admin/team/create/', {
            'organization_id': test_org.id,
            'first_name': 'TestEnv',
            'last_name': 'Staff',
            'email': test_staff_email,
            'phone': '9876543212',
            'password': test_staff_pass,
            'role': 'STAFF',
        }, follow=True)

        assert staff_resp.status_code == 200, f"Staff creation failed with {staff_resp.status_code}"
        env_text = env_path.read_text(encoding='utf-8')
        staff_ident = sanitize_identifier(test_staff_email)

        assert f"STAFF_{staff_ident}_EMAIL={test_staff_email}" in env_text, \
            f"Expected STAFF_{staff_ident}_EMAIL in .env"
        assert f"STAFF_{staff_ident}_PASSWORD={test_staff_pass}" in env_text, \
            f"Expected STAFF_{staff_ident}_PASSWORD in .env"
        assert f"STAFF_{staff_ident}_ROLE=STAFF" in env_text, \
            f"Expected STAFF_{staff_ident}_ROLE=STAFF in .env"
        print("[PASS] Test 3: Super Admin creating Staff member automatically recorded in .env")

        # ----------------------------------------------------
        # Test 4: Org Admin creates Manager Team Member
        # ----------------------------------------------------
        oa_user = User.objects.get(email=test_oa_email)
        client.force_login(oa_user)

        test_mgr_email = "test.env.mgr@example.com"
        test_mgr_pass = "ManagerSecret666!"
        User.objects.filter(email=test_mgr_email).delete()

        mgr_resp = client.post('/org-admin/team/create/', {
            'first_name': 'TestEnv',
            'last_name': 'Manager',
            'email': test_mgr_email,
            'phone': '9876543213',
            'password': test_mgr_pass,
            'system_role': 'MANAGER',
        }, follow=True)

        assert mgr_resp.status_code == 200, f"Manager creation failed with {mgr_resp.status_code}"
        env_text = env_path.read_text(encoding='utf-8')
        mgr_ident = sanitize_identifier(test_mgr_email)

        assert f"MANAGER_{mgr_ident}_EMAIL={test_mgr_email}" in env_text, \
            f"Expected MANAGER_{mgr_ident}_EMAIL in .env"
        assert f"MANAGER_{mgr_ident}_PASSWORD={test_mgr_pass}" in env_text, \
            f"Expected MANAGER_{mgr_ident}_PASSWORD in .env"
        assert f"MANAGER_{mgr_ident}_ROLE=MANAGER" in env_text, \
            f"Expected MANAGER_{mgr_ident}_ROLE=MANAGER in .env"
        print("[PASS] Test 4: Org Admin creating Manager team member automatically recorded in .env")

        # ----------------------------------------------------
        # Test 5: Password update reflection in .env
        # ----------------------------------------------------
        player_user = User.objects.get(email=test_player_email)
        client.force_login(player_user)

        new_player_pass = "NewPlayerPassUpdated321!"
        pw_resp = client.post('/profile/password/', {
            'current_password': test_player_pass,
            'new_password': new_player_pass,
            'confirm_password': new_player_pass,
        }, follow=True)

        assert pw_resp.status_code == 200, f"Password change failed with {pw_resp.status_code}"
        env_text = env_path.read_text(encoding='utf-8')

        assert f"USER_{player_ident}_PASSWORD={new_player_pass}" in env_text, \
            "Expected updated password in .env for player"
        print("[PASS] Test 5: User password change successfully updated credentials in .env")

    finally:
        # Clean up database test objects
        User.objects.filter(email__in=[
            "test.env.player@example.com",
            "test.env.oa@example.com",
            "test.env.staff@example.com",
            "test.env.mgr@example.com"
        ]).delete()
        Organization.objects.filter(name='Test Env Arena Network').delete()

        # Restore pristine original .env
        env_path.write_text(original_env_content, encoding='utf-8')
        print("[OK] Test cleanup complete: pristine .env restored.")

    print("=" * 50)
    print("ALL 5 .ENV CREDENTIALS LOGGING TESTS PASSED!")
    print("=" * 50 + "\n")

if __name__ == '__main__':
    run_tests()
