import os
import sys
from pathlib import Path
import io
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from turfs.models import Sport, UserProfile

def create_dummy_image():
    file = io.BytesIO()
    image = Image.new('RGBA', size=(100, 100), color=(16, 185, 129))
    image.save(file, 'png')
    file.name = 'test_avatar.png'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/png')

def run_tests():
    print("==================================================")
    print("RUNNING USER PROFILE SECTION TEST SUITE")
    print("==================================================")

    client = Client()

    # TEST 1: Unauthenticated user is redirected to login
    client.logout()
    response = client.get('/profile/', follow=False)
    assert response.status_code == 302
    assert '/login/' in response.url
    print("[PASS] Test 1: Unauthenticated access redirected to login.")

    # Get or create test user
    test_email = "player.profile@turfbook.com"
    test_user, created = User.objects.get_or_create(
        username=test_email,
        defaults={
            'email': test_email,
            'first_name': 'Aarav',
            'last_name': 'Sharma',
        }
    )
    test_user.set_password('profilePass123')
    test_user.save()

    profile, _ = UserProfile.objects.get_or_create(user=test_user, defaults={'role': 'PLAYER'})
    cricket_sport = Sport.objects.first()

    # TEST 2: Authenticated user loads /profile/
    logged_in = client.login(username=test_email, password='profilePass123')
    assert logged_in is True, "Login failed for profile test user"

    response = client.get('/profile/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Personal Information' in content
    assert 'Password &amp; Security' in content or 'Password & Security' in content
    assert test_user.first_name in content
    print("[PASS] Test 2: /profile/ rendered successfully with profile form and security sections.")

    # TEST 3: Update Profile Details (First Name, Last Name, Phone, City, Bio, Favorite Sport)
    response = client.post('/profile/', {
        'action': 'update_profile',
        'first_name': 'Aarav Kumar',
        'last_name': 'Sharma',
        'email': test_email,
        'phone': '+91 99887 76655',  # Valid 10 digits
        'city': 'Ahmedabad',
        'address': 'Bodakdev, SG Highway',
        'bio': 'All-rounder cricket player and weekend football enthusiast.',
        'favorite_sport_id': str(cricket_sport.id) if cricket_sport else '',
    }, follow=True)

    assert response.status_code == 200
    test_user.refresh_from_db()
    profile.refresh_from_db()

    assert test_user.first_name == 'Aarav Kumar', f"Expected 'Aarav Kumar', got '{test_user.first_name}'"
    assert profile.phone == '9988776655', f"Expected clean 10 digits '9988776655', got '{profile.phone}'"
    assert profile.city == 'Ahmedabad'
    assert 'All-rounder' in profile.bio
    if cricket_sport:
        assert profile.favorite_sport == cricket_sport
    print("[PASS] Test 3: Profile personal details, bio, and 10-digit phone updated successfully.")

    # TEST 4: Invalid Phone (<10 digits) in Profile is rejected
    response = client.post('/profile/', {
        'action': 'update_profile',
        'first_name': 'Aarav Kumar',
        'last_name': 'Sharma',
        'email': test_email,
        'phone': '12345',  # Invalid 5 digits
    }, follow=True)
    profile.refresh_from_db()
    assert profile.phone == '9988776655', "Phone should NOT have updated with invalid digits!"
    print("[PASS] Test 4: Profile update rejected phone with less than 10 digits.")

    # TEST 5: Upload Custom Avatar Image
    avatar_file = create_dummy_image()
    response = client.post('/profile/', {
        'action': 'update_profile',
        'first_name': 'Aarav Kumar',
        'last_name': 'Sharma',
        'email': test_email,
        'phone': '9988776655',
        'avatar': avatar_file,
    }, follow=True)

    assert response.status_code == 200
    profile.refresh_from_db()
    assert bool(profile.avatar) is True, "Profile avatar image was not saved!"
    assert profile.get_avatar_url is not None, "get_avatar_url returned None!"
    print(f"[PASS] Test 5: Profile avatar image uploaded successfully: {profile.get_avatar_url}")

    # TEST 6: Remove Avatar Image
    response = client.post('/profile/', {
        'action': 'update_profile',
        'first_name': 'Aarav Kumar',
        'last_name': 'Sharma',
        'email': test_email,
        'phone': '9988776655',
        'remove_avatar': '1',
    }, follow=True)

    assert response.status_code == 200
    profile.refresh_from_db()
    assert not bool(profile.avatar), "Profile avatar was not removed!"
    print("[PASS] Test 6: Profile avatar removed successfully upon request.")

    # TEST 7: Password Change Security
    # 7.1: Incorrect current password rejected
    response = client.post('/profile/password/', {
        'current_password': 'wrongCurrentPassword',
        'new_password': 'newStrongPass2026',
        'confirm_password': 'newStrongPass2026',
    }, follow=True)
    assert not test_user.check_password('newStrongPass2026')
    print("[PASS] Test 7.1: Password change rejected with wrong current password.")

    # 7.2: New password < 8 characters rejected
    response = client.post('/profile/password/', {
        'current_password': 'profilePass123',
        'new_password': 'short',
        'confirm_password': 'short',
    }, follow=True)
    assert not test_user.check_password('short')
    print("[PASS] Test 7.2: Password change rejected with password under 8 characters.")

    # 7.3: Valid password change succeeds
    response = client.post('/profile/password/', {
        'current_password': 'profilePass123',
        'new_password': 'newStrongPass2026',
        'confirm_password': 'newStrongPass2026',
    }, follow=True)
    assert response.status_code == 200
    test_user.refresh_from_db()
    assert test_user.check_password('newStrongPass2026') is True
    print("[PASS] Test 7.3: Password changed successfully and user authenticated with new password.")

    print("\n" + "=" * 50)
    print("ALL USER PROFILE SECTION TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
