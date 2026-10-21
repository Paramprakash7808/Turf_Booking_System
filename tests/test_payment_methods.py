import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from turfs.models import Turf, TimeSlot, Booking, UserProfile, Organization, Branch

def run_tests():
    print("\n" + "=" * 50)
    print("RUNNING PAYMENT METHODS (RAZORPAY & CASH) TEST SUITE")
    print("=" * 50)

    # 1. Setup test user, turf, and slot
    user, _ = User.objects.get_or_create(username='payment_tester@turfbook.com', email='payment_tester@turfbook.com')
    user.set_password('pass1234')
    user.save()
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user, phone='9876543210', role='PLAYER')
    else:
        user.profile.phone = '9876543210'
        user.profile.save()

    turf = Turf.objects.first()
    assert turf is not None, "No turf found in database."
    slot = TimeSlot.objects.first()
    assert slot is not None, "No time slot found."

    client = Client()
    logged_in = client.login(username='payment_tester@turfbook.com', password='pass1234')
    assert logged_in, "Failed to log in test user."

    target_date = timezone.localdate() + timedelta(days=20)
    target_date_str = target_date.isoformat()

    # Clean up any preexisting test booking on this date & slot
    Booking.objects.filter(turf=turf, date=target_date, time_slot=slot).delete()

    # Test 1: Verify booking page renders Razorpay & Cash on Counter payment options
    res_page = client.get(f'/booking/{turf.id}/?date={target_date_str}')
    assert res_page.status_code == 200, f"Booking page failed: {res_page.status_code}"
    content = res_page.content.decode()
    assert 'Select Payment Method' in content, "Step 4 Select Payment Method missing on booking page."
    assert 'Razorpay Online' in content, "Razorpay option missing on booking page."
    assert 'Cash on Counter' in content, "Cash on Counter option missing on booking page."
    assert 'razorpayModal' in content, "Razorpay simulation checkout modal missing."
    assert 'name="payment_method"' in content, "Hidden input payment_method missing in form."
    print("[PASS] Test 1: /booking/ renders Step 4 with Razorpay, Cash on Counter, and Checkout Modal.")

    # Test 2: Book slot with Razorpay Online
    razorpay_mock_id = 'pay_rzp_test_12345678'
    res_rzp = client.post(f'/booking/{turf.id}/', {
        'date': target_date_str,
        'slot_ids': [slot.id],
        'player_name': 'Razorpay Player',
        'player_phone': '9876543210',
        'payment_method': 'RAZORPAY',
        'razorpay_payment_id': razorpay_mock_id,
        'notes': 'Online paid slot'
    }, follow=True)
    assert res_rzp.status_code == 200, f"Razorpay booking failed: {res_rzp.status_code}"

    rzp_booking = Booking.objects.filter(
        turf=turf,
        date=target_date,
        time_slot=slot,
        user=user
    ).first()
    assert rzp_booking is not None, "Razorpay booking was not created."
    assert rzp_booking.payment_method == 'RAZORPAY', f"Expected RAZORPAY, got {rzp_booking.payment_method}"
    assert rzp_booking.payment_status == 'PAID', f"Expected PAID, got {rzp_booking.payment_status}"
    assert rzp_booking.razorpay_payment_id == razorpay_mock_id, f"Expected {razorpay_mock_id}, got {rzp_booking.razorpay_payment_id}"
    print("[PASS] Test 2: Razorpay booking recorded with payment_method='RAZORPAY', payment_status='PAID', and razorpay_payment_id.")

    # Test 3: Check Ticket pass for Razorpay booking
    res_ticket = client.get(f'/booking/{rzp_booking.id}/ticket/')
    assert res_ticket.status_code == 200
    ticket_content = res_ticket.content.decode()
    assert 'Razorpay Online Settled' in ticket_content or 'Razorpay Online (Settled)' in ticket_content, "Ticket missing Razorpay settled badge."
    assert razorpay_mock_id in ticket_content, "Ticket missing Razorpay transaction ID."
    print("[PASS] Test 3: Digital ticket displays Razorpay Online Settled badge and payment reference ID.")

    # Clean up Razorpay booking to free slot for Cash test
    rzp_booking.delete()

    # Test 4: Book slot with Cash on Counter
    res_cash = client.post(f'/booking/{turf.id}/', {
        'date': target_date_str,
        'slot_ids': [slot.id],
        'player_name': 'Cash Player',
        'player_phone': '9876543210',
        'payment_method': 'CASH',
        'notes': 'Will pay at counter'
    }, follow=True)
    assert res_cash.status_code == 200, f"Cash booking failed: {res_cash.status_code}"

    cash_booking = Booking.objects.filter(
        turf=turf,
        date=target_date,
        time_slot=slot,
        user=user
    ).first()
    assert cash_booking is not None, "Cash booking was not created."
    assert cash_booking.payment_method == 'CASH', f"Expected CASH, got {cash_booking.payment_method}"
    assert cash_booking.payment_status == 'PENDING_AT_COUNTER', f"Expected PENDING_AT_COUNTER, got {cash_booking.payment_status}"
    assert cash_booking.razorpay_payment_id is None, "razorpay_payment_id should be None for Cash booking."
    print("[PASS] Test 4: Cash booking recorded with payment_method='CASH', payment_status='PENDING_AT_COUNTER'.")

    # Test 5: Check Ticket pass for Cash booking
    res_cash_ticket = client.get(f'/booking/{cash_booking.id}/ticket/')
    assert res_cash_ticket.status_code == 200
    cash_ticket_content = res_cash_ticket.content.decode()
    assert 'Cash on Counter' in cash_ticket_content, "Ticket missing Cash on Counter notice."
    assert 'Pay at Venue Counter' in cash_ticket_content or 'Due at Counter' in cash_ticket_content, "Ticket missing Pay at Venue instructions."
    print("[PASS] Test 5: Digital ticket displays Cash on Counter notice and counter payment guidelines.")

    # Test 6: Check User Dashboard displays Cash on Counter and Razorpay badges
    res_dash = client.get('/dashboard/')
    assert res_dash.status_code == 200
    dash_content = res_dash.content.decode()
    assert 'Cash on Counter' in dash_content, "Dashboard missing Cash on Counter badge."
    assert 'Due at Counter' in dash_content, "Dashboard missing Due at Counter label."
    print("[PASS] Test 6: Dashboard displays Cash on Counter payment status badge.")

    # Test 7: Staff Portal check-in marks Counter Payment as PAID
    staff_user, _ = User.objects.get_or_create(username='staff_cash_checker@turfbook.com', email='staff_cash_checker@turfbook.com')
    staff_user.set_password('pass1234')
    staff_user.is_staff = True
    staff_user.save()
    if not hasattr(staff_user, 'profile'):
        UserProfile.objects.create(user=staff_user, phone='9876543211', role='STAFF')
    else:
        staff_user.profile.role = 'STAFF'
        staff_user.profile.save()

    client.login(username='staff_cash_checker@turfbook.com', password='pass1234')
    res_checkin = client.post(f'/staff-portal/checkin/{cash_booking.id}/', follow=True)
    assert res_checkin.status_code == 200

    cash_booking.refresh_from_db()
    assert cash_booking.status == 'COMPLETED', "Booking status should be COMPLETED after check-in."
    assert cash_booking.payment_status == 'PAID', "Counter booking payment_status should be updated to PAID on check-in."
    print("[PASS] Test 7: Staff check-in successfully marks counter booking payment_status as PAID.")

    # Clean up test records
    cash_booking.delete()

    print("\n" + "=" * 50)
    print("ALL 7 PAYMENT METHODS TESTS PASSED PERFECTLY!")
    print("=" * 50 + "\n")

if __name__ == '__main__':
    run_tests()
