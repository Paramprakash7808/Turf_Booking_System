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
from django.utils import timezone
from datetime import timedelta
from turfs.models import Organization, Branch, Turf, TimeSlot, Booking, UserProfile
from turfs.validators import validate_email_format, clean_and_validate_mobile, validate_password_rules, validate_name

def run_tests():
    print("==================================================")
    print("RUNNING COMPREHENSIVE INPUT VALIDATION TEST SUITE")
    print("==================================================")

    # -------------------------------------------------------------------------
    # UNIT TEST 1: Email Validation Function
    # -------------------------------------------------------------------------
    valid_emails = ["alex@gmail.com", "user.name+tag@sub.domain.co", "admin@turfbook.in"]
    for ve in valid_emails:
        ok, err, cleaned = validate_email_format(ve)
        assert ok is True, f"Expected {ve} to be valid, got error: {err}"
    print("[PASS] Test 1.1: Valid email formats accepted correctly.")

    invalid_emails = [
        ("noatsign.domain.com", "missing @"),
        ("user@nodomaindot", "missing domain dot ."),
        ("user@.com", "missing domain name"),
        ("@domain.com", "missing local part"),
        ("user@domain.", "trailing dot"),
        ("", "empty email"),
    ]
    for ie, reason in invalid_emails:
        ok, err, _ = validate_email_format(ie)
        assert ok is False, f"Expected {ie} ({reason}) to fail validation!"
    print("[PASS] Test 1.2: Invalid email formats strictly rejected (both '@' and '.' enforced).")

    # -------------------------------------------------------------------------
    # UNIT TEST 2: Mobile Number (10 Digits) Validation Function
    # -------------------------------------------------------------------------
    valid_mobiles = [
        ("9876543210", "9876543210"),
        ("+91 98765 43210", "9876543210"),
        ("+91-9876543210", "9876543210"),
        ("09876543210", "9876543210"),
        ("919876543210", "9876543210"),
    ]
    for raw_m, expected_10 in valid_mobiles:
        ok, err, cleaned = clean_and_validate_mobile(raw_m, required=True)
        assert ok is True, f"Expected {raw_m} to be valid, got: {err}"
        assert cleaned == expected_10, f"Expected {expected_10}, got {cleaned}"
    print("[PASS] Test 2.1: 10-digit mobile numbers with/without formatting accepted and normalized.")

    invalid_mobiles = [
        ("12345", "too short - 5 digits"),
        ("98765432109999", "too long - 14 digits"),
        ("98765abcde", "contains letters"),
        ("", "empty mobile when required"),
    ]
    for raw_m, reason in invalid_mobiles:
        ok, err, _ = clean_and_validate_mobile(raw_m, required=True)
        assert ok is False, f"Expected {raw_m} ({reason}) to fail validation!"
    print("[PASS] Test 2.2: Mobile numbers not matching exactly 10 digits strictly rejected.")

    # -------------------------------------------------------------------------
    # UNIT TEST 3: Password Length Validation Function (Min 8 Characters)
    # -------------------------------------------------------------------------
    assert validate_password_rules("12345678")[0] is True
    assert validate_password_rules("superSecretPass123")[0] is True
    assert validate_password_rules("short")[0] is False
    assert validate_password_rules("1234567")[0] is False
    assert validate_password_rules("")[0] is False
    print("[PASS] Test 3: Password minimum 8 characters rule validated.")

    # -------------------------------------------------------------------------
    # INTEGRATION TEST 4: Register View Validation
    # -------------------------------------------------------------------------
    client = Client()

    # 4.1: Register with missing '.' in email -> Should fail
    res = client.post('/register/', {
        'first_name': 'TestUser',
        'last_name': 'Validation',
        'email': 'bademail@domain',  # Missing dot .
        'phone': '9876543210',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert res.status_code == 200
    assert not User.objects.filter(username='bademail@domain').exists()
    print("[PASS] Test 4.1: /register/ rejected email without domain dot.")

    # 4.2: Register with invalid mobile (only 6 digits) -> Should fail
    res = client.post('/register/', {
        'first_name': 'TestUser',
        'last_name': 'Validation',
        'email': 'validuser1@example.com',
        'phone': '123456',  # 6 digits
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert res.status_code == 200
    assert not User.objects.filter(email='validuser1@example.com').exists()
    print("[PASS] Test 4.2: /register/ rejected phone with less than 10 digits.")

    # 4.3: Register with short password (< 8 chars) -> Should fail
    res = client.post('/register/', {
        'first_name': 'TestUser',
        'last_name': 'Validation',
        'email': 'validuser2@example.com',
        'phone': '9876543210',
        'password': 'short',  # 5 chars
        'confirm_password': 'short'
    })
    assert res.status_code == 200
    assert not User.objects.filter(email='validuser2@example.com').exists()
    print("[PASS] Test 4.3: /register/ rejected password under 8 characters.")

    # 4.4: Register with password mismatch -> Should fail
    res = client.post('/register/', {
        'first_name': 'TestUser',
        'last_name': 'Validation',
        'email': 'validuser3@example.com',
        'phone': '9876543210',
        'password': 'password123',
        'confirm_password': 'mismatchPassword456'
    })
    assert res.status_code == 200
    assert not User.objects.filter(email='validuser3@example.com').exists()
    print("[PASS] Test 4.4: /register/ rejected mismatched passwords.")

    # 4.5: Successful Registration with all validations passed!
    valid_reg_email = "newplayer.valid@turfbook.com"
    User.objects.filter(email=valid_reg_email).delete()

    res = client.post('/register/', {
        'first_name': 'Kavya',
        'last_name': 'Patel',
        'email': valid_reg_email,
        'phone': '+91 98765 11111',  # Formatted 10-digit mobile
        'password': 'safePassword2026',
        'confirm_password': 'safePassword2026'
    }, follow=False)

    assert res.status_code == 302, f"Expected 302 redirect, got {res.status_code}"
    assert res.url == '/dashboard/'
    created_user = User.objects.filter(email=valid_reg_email).first()
    assert created_user is not None
    assert created_user.profile.phone == '9876511111', f"Expected cleaned 10 digits '9876511111', got '{created_user.profile.phone}'"
    print(f"[PASS] Test 4.5: Successful registration created user with normalized 10-digit phone ({created_user.profile.phone}) and logged in.")

    # -------------------------------------------------------------------------
    # INTEGRATION TEST 5: Login View Validation
    # -------------------------------------------------------------------------
    client.logout()

    # 5.1: Login with invalid email syntax (missing @)
    res_no_at = client.post('/login/', {
        'email': 'noatsign.com',
        'password': 'password123'
    })
    assert res_no_at.status_code == 200
    print("[PASS] Test 5.1a: /login/ rejected email missing '@'")

    # 5.1b: Login with invalid email syntax (contains @ but no dot .)
    res = client.post('/login/', {
        'email': 'invalidemail@nodot',
        'password': 'password123'
    })
    assert res.status_code == 200
    print("[PASS] Test 5.1b: /login/ rejected email missing dot '.'")

    # 5.2: Login with short password (< 8 chars)
    res = client.post('/login/', {
        'email': valid_reg_email,
        'password': '123'  # 3 chars
    })
    assert res.status_code == 200
    print("[PASS] Test 5.2: /login/ rejected password with less than 8 characters.")

    # 5.3: Valid login with valid credentials
    res = client.post('/login/', {
        'email': valid_reg_email,
        'password': 'safePassword2026'
    }, follow=False)
    assert res.status_code == 302
    assert res.url == '/dashboard/'
    print("[PASS] Test 5.3: /login/ successfully authenticated valid user with >= 8 char password.")

    # -------------------------------------------------------------------------
    # INTEGRATION TEST 6: Booking View Phone Validation
    # -------------------------------------------------------------------------
    turf = Turf.objects.first()
    assert turf is not None
    slot = TimeSlot.objects.first()
    assert slot is not None
    test_date = (timezone.localdate() + timedelta(days=2)).isoformat()

    # 6.1: Booking with invalid phone (e.g. 5 digits) -> Should fail and redirect back
    booking_count_before = Booking.objects.count()
    res = client.post(f'/booking/{turf.id}/', {
        'date': test_date,
        'slot_ids': [str(slot.id)],
        'player_name': 'Kavya Patel',
        'player_phone': '98765',  # Invalid: only 5 digits
    }, follow=False)
    assert Booking.objects.count() == booking_count_before, "Booking should NOT be created with invalid 5-digit phone!"
    print("[PASS] Test 6.1: /booking/ rejected invalid mobile number with only 5 digits.")

    # 6.2: Booking with valid 10-digit mobile -> Confirms booking and saves 10-digit phone
    # Clear any conflicting booking for this slot
    Booking.objects.filter(turf=turf, date=test_date, time_slot=slot).delete()

    res = client.post(f'/booking/{turf.id}/', {
        'date': test_date,
        'slot_ids': [str(slot.id)],
        'player_name': 'Kavya Patel',
        'player_phone': '+91 98222 33333',  # Valid 10-digit phone
    }, follow=False)

    assert res.status_code == 302, f"Expected 302 redirect to ticket, got {res.status_code}"
    new_booking = Booking.objects.filter(turf=turf, date=test_date, time_slot=slot).first()
    assert new_booking is not None
    assert new_booking.player_phone == '9822233333', f"Expected cleaned 10 digits '9822233333', got '{new_booking.player_phone}'"
    print(f"[PASS] Test 6.2: /booking/ confirmed booking and saved normalized 10-digit mobile '{new_booking.player_phone}'.")

    print("\n" + "=" * 50)
    print("ALL INPUT VALIDATION TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
