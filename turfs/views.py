from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import datetime, date, timedelta
import os
import json
import base64
import io
import qrcode

from django.db import models, transaction
from .models import Sport, Amenity, Turf, TimeSlot, Booking, Review, HeroSlide, Organization, Branch, OrganizationRole, UserProfile
from .validators import validate_email_format, clean_and_validate_mobile, validate_password_rules, validate_name
from .env_sync import save_credentials_to_env

def set_city(request, city):
    """
    Handle user switching their city anywhere on the site (like BookMyShow location popup).
    """
    clean_city = city.strip().title()
    request.session['selected_city'] = clean_city
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        request.user.profile.city = clean_city
        request.user.profile.save()
    next_url = request.GET.get('next')
    if next_url and not next_url.startswith('/set-city/'):
        return redirect(next_url)
    return redirect('home_city', city=clean_city.lower())

def home(request, city=None):
    if city:
        current_city = city.strip().title()
        request.session['selected_city'] = current_city
    else:
        current_city = request.session.get('selected_city', 'Rajkot')

    # City-specific turfs strictly filtered by current_city
    city_turfs = Turf.objects.filter(
        Q(city__iexact=current_city) | Q(location__icontains=current_city)
    ).prefetch_related('sports', 'amenities')
    
    has_city_turfs = city_turfs.exists()
    
    if has_city_turfs:
        featured_turfs = city_turfs.filter(is_featured=True)[:8]
        if not featured_turfs.exists():
            featured_turfs = city_turfs[:8]
        trending_turfs = city_turfs.order_by('-rating')[:8]
    else:
        # Strictly empty: never leak other cities when user selects a specific city with no venues
        featured_turfs = Turf.objects.none()
        trending_turfs = Turf.objects.none()

    # Suggested turfs from popular hubs to recommend when a city has 0 venues
    suggested_turfs = Turf.objects.filter(is_featured=True).prefetch_related('sports')[:6] if not has_city_turfs else Turf.objects.none()

    sports = Sport.objects.annotate(turf_count=models.Count('turfs', distinct=True))
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order', 'id')

    return render(request, 'turfs/home.html', {
        'featured_turfs': featured_turfs,
        'trending_turfs': trending_turfs,
        'suggested_turfs': suggested_turfs,
        'city_turfs': city_turfs,
        'has_city_turfs': has_city_turfs,
        'sports': sports,
        'hero_slides': hero_slides,
        'current_city': current_city,
    })

def turf_list(request, city=None):
    if city:
        current_city = city.strip().title()
        request.session['selected_city'] = current_city
    else:
        current_city = request.session.get('selected_city', 'Rajkot')

    city_param = request.GET.get('city', '').strip()
    show_all_cities = request.GET.get('all_cities') == '1' or city_param.lower() == 'all'
    
    if city_param and city_param.lower() != 'all':
        active_city_filter = city_param.title()
        request.session['selected_city'] = active_city_filter
        current_city = active_city_filter
    elif show_all_cities:
        active_city_filter = None
    elif city:
        active_city_filter = current_city
    else:
        active_city_filter = current_city

    query = request.GET.get('q', '').strip()
    sport_filter = request.GET.get('sport', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    selected_amenities = request.GET.getlist('amenity')

    turfs = Turf.objects.all().prefetch_related('sports', 'amenities')

    # Strictly apply city filter if not 'all cities'
    if active_city_filter:
        turfs = turfs.filter(
            Q(city__iexact=active_city_filter) | 
            Q(location__icontains=active_city_filter)
        )

    if query:
        turfs = turfs.filter(
            Q(name__icontains=query) | 
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    if sport_filter:
        turfs = turfs.filter(sports__slug=sport_filter)

    if min_price:
        try:
            turfs = turfs.filter(price_per_hour__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            turfs = turfs.filter(price_per_hour__lte=float(max_price))
        except ValueError:
            pass

    if selected_amenities:
        for amen in selected_amenities:
            turfs = turfs.filter(amenities__name__iexact=amen)

    sports = Sport.objects.annotate(turf_count=models.Count('turfs', distinct=True))
    amenities = Amenity.objects.all()

    return render(request, 'turfs/turf_list.html', {
        'turfs': turfs.distinct(),
        'sports': sports,
        'amenities': amenities,
        'selected_sport': sport_filter,
        'search_query': query,
        'min_price': min_price or 500,
        'max_price': max_price or 2500,
        'selected_amenities': selected_amenities,
        'total_all_turfs': Turf.objects.count(),
        'active_city_filter': active_city_filter,
        'current_city': current_city,
        'show_all_cities': show_all_cities,
    })

def sports_list(request):
    """
    Dedicated Sports Directory & Filtering Hub:
    - Displays all sports prominently (Cricket, Football, Pickleball, Paddleball) with icons, counts, and descriptions.
    - Quick-filter pills and filter sidebar allowing instant filtering by sport, price, amenities, and keywords.
    """
    query = request.GET.get('q', '').strip()
    sport_filter = request.GET.get('sport', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    selected_amenities = request.GET.getlist('amenity')

    sports = Sport.objects.annotate(turf_count=models.Count('turfs', distinct=True))
    turfs = Turf.objects.all().prefetch_related('sports', 'amenities')

    if query:
        turfs = turfs.filter(
            Q(name__icontains=query) | 
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    if sport_filter:
        turfs = turfs.filter(sports__slug=sport_filter)

    if min_price:
        try:
            turfs = turfs.filter(price_per_hour__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            turfs = turfs.filter(price_per_hour__lte=float(max_price))
        except ValueError:
            pass

    if selected_amenities:
        for amen in selected_amenities:
            turfs = turfs.filter(amenities__name__iexact=amen)

    amenities = Amenity.objects.all()
    active_sport_obj = Sport.objects.filter(slug=sport_filter).first() if sport_filter else None
    turfs_list = turfs.distinct()

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        html = render_to_string('turfs/sports_turfs_partial.html', {
            'turfs': turfs_list,
            'active_sport_obj': active_sport_obj,
            'selected_sport': sport_filter,
            'search_query': query,
            'selected_amenities': selected_amenities,
        }, request=request)
        return JsonResponse({
            'html': html,
            'count': turfs_list.count(),
            'selected_sport': sport_filter,
            'sport_name': active_sport_obj.name if active_sport_obj else '',
            'hero_title': f"{active_sport_obj.name} <span class=\"text-brand-500\">Turfs & Courts</span>" if active_sport_obj else "Explore By <span class=\"text-brand-500\">Sport Category</span>",
        })

    return render(request, 'turfs/sports_list.html', {
        'turfs': turfs_list,
        'sports': sports,
        'amenities': amenities,
        'selected_sport': sport_filter,
        'active_sport_obj': active_sport_obj,
        'search_query': query,
        'min_price': min_price or 500,
        'max_price': max_price or 2500,
        'selected_amenities': selected_amenities,
        'total_all_turfs': Turf.objects.count(),
    })

def turf_detail(request, slug):
    turf = get_object_or_404(Turf.objects.prefetch_related('sports', 'amenities', 'reviews__user'), slug=slug)
    related_turfs = Turf.objects.filter(primary_sport=turf.primary_sport).exclude(id=turf.id)[:3]
    return render(request, 'turfs/turf_detail.html', {
        'turf': turf,
        'related_turfs': related_turfs,
    })

def branch_detail(request, branch_id=None, slug=None):
    if branch_id:
        branch = get_object_or_404(
            Branch.objects.select_related('organization').prefetch_related(
                'turfs__sports', 
                'turfs__amenities'
            ), 
            id=branch_id
        )
    elif slug:
        branch = get_object_or_404(
            Branch.objects.select_related('organization').prefetch_related(
                'turfs__sports', 
                'turfs__amenities'
            ), 
            slug=slug
        )
    else:
        return redirect('home')

    turfs = branch.turfs.prefetch_related('sports', 'amenities').all()
    staff_members = UserProfile.objects.filter(branch=branch).select_related('user', 'custom_role')

    can_manage = False
    is_super_admin = False
    is_org_admin = False

    if request.user.is_authenticated:
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN'):
            can_manage = True
            is_super_admin = True
        elif hasattr(request.user, 'profile') and request.user.profile.organization == branch.organization:
            if request.user.profile.role == 'ORG_ADMIN':
                can_manage = True
                is_org_admin = True
            elif request.user.profile.role in ['MANAGER', 'STAFF']:
                can_manage = False

    return render(request, 'turfs/branch_detail.html', {
        'branch': branch,
        'organization': branch.organization,
        'turfs': turfs,
        'staff_members': staff_members,
        'can_manage': can_manage,
        'is_super_admin': is_super_admin,
        'is_org_admin': is_org_admin,
    })


def booking_view(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    time_slots = TimeSlot.objects.all().order_by('start_time')
    
    # Selected date defaults to today
    selected_date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()

    if selected_date < timezone.localdate():
        selected_date = timezone.localdate()

    # Find already booked slots for this turf and date
    booked_slot_ids = list(
        Booking.objects.filter(
            turf=turf, 
            date=selected_date, 
            status='CONFIRMED'
        ).values_list('time_slot_id', flat=True)
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to confirm your booking.")
            return redirect(f"/login/?next=/booking/{turf.id}/")

        booking_date_str = request.POST.get('date')
        player_name = request.POST.get('player_name', '').strip() or request.user.get_full_name() or request.user.username
        player_phone = request.POST.get('player_phone', '').strip()
        notes = request.POST.get('notes', '').strip()

        # Validation: Player Name (at least 2 characters)
        pname_valid, pname_err, clean_pname = validate_name(player_name, field_name="Player Name", min_length=2, required=True)
        if not pname_valid:
            messages.error(request, pname_err)
            return redirect(f"/booking/{turf.id}/?date={booking_date_str or ''}")

        # Validation: Contact Phone (exactly 10 digits)
        ph_valid, ph_err, clean_phone = clean_and_validate_mobile(player_phone, required=True)
        if not ph_valid:
            messages.error(request, ph_err)
            return redirect(f"/booking/{turf.id}/?date={booking_date_str or ''}")

        # Support both 'slot_ids' list and legacy/comma-separated 'slot_id'
        slot_ids = request.POST.getlist('slot_ids')
        if not slot_ids:
            raw_slots = request.POST.get('slot_id', '') or request.POST.get('slot_ids', '')
            if raw_slots:
                slot_ids = [s.strip() for s in raw_slots.split(',') if s.strip()]

        if not slot_ids:
            messages.error(request, "Please select at least one time slot to book.")
            return redirect(f"/booking/{turf.id}/?date={booking_date_str or ''}")

        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid booking date.")
            return redirect(request.path)

        if booking_date < timezone.localdate():
            messages.error(request, "Cannot book slots in the past.")
            return redirect(request.path)

        # Parse and retrieve all selected TimeSlot records
        try:
            slot_id_ints = [int(s) for s in slot_ids]
        except (ValueError, TypeError):
            messages.error(request, "Invalid time slot selected.")
            return redirect(f"/booking/{turf.id}/?date={booking_date.isoformat()}")

        slots = list(TimeSlot.objects.filter(id__in=slot_id_ints).order_by('start_time'))
        if not slots or len(slots) != len(set(slot_id_ints)):
            messages.error(request, "One or more selected time slots could not be found.")
            return redirect(f"/booking/{turf.id}/?date={booking_date.isoformat()}")

        # Concurrency safety: check if any slot is already booked inside a transaction
        with transaction.atomic():
            clashes = list(Booking.objects.filter(
                turf=turf,
                date=booking_date,
                time_slot__in=slots,
                status='CONFIRMED'
            ).select_related('time_slot'))

            if clashes:
                clash_labels = ", ".join([b.time_slot.label for b in clashes])
                messages.error(request, f"Sorry, slot(s) {clash_labels} are already reserved for {booking_date}. Please select other available slots.")
                return redirect(f"/booking/{turf.id}/?date={booking_date.isoformat()}")

            # Payment Method & Status Selection (Razorpay vs Cash on Counter)
            raw_pay_method = request.POST.get('payment_method', 'RAZORPAY').strip().upper()
            if raw_pay_method == 'CASH':
                payment_method = 'CASH'
                payment_status = 'PENDING_AT_COUNTER'
                razorpay_payment_id = None
            else:
                payment_method = 'RAZORPAY'
                payment_status = 'PAID'
                razorpay_payment_id = request.POST.get('razorpay_payment_id') or f"pay_rzp_{timezone.now().strftime('%Y%m%d%H%M%S')}_{request.user.id}"

            created_bookings = []
            for slot in slots:
                booking = Booking.objects.create(
                    user=request.user,
                    turf=turf,
                    date=booking_date,
                    time_slot=slot,
                    total_price=turf.price_per_hour,
                    status='CONFIRMED',
                    player_name=clean_pname,
                    player_phone=clean_phone,
                    payment_method=payment_method,
                    payment_status=payment_status,
                    razorpay_payment_id=razorpay_payment_id,
                    notes=notes
                )
                created_bookings.append(booking)

            # Auto-save phone number to user profile if not previously set
            if hasattr(request.user, 'profile') and not request.user.profile.phone:
                request.user.profile.phone = clean_phone
                request.user.profile.save()

            total_hours = len(created_bookings)
            total_price = total_hours * turf.price_per_hour
            slot_labels = ", ".join([s.label for s in slots])

            if payment_method == 'RAZORPAY':
                messages.success(
                    request,
                    f"🎉 Payment Successful via Razorpay ({razorpay_payment_id})! {total_hours} slot(s) reserved for {turf.name} on {booking_date}: {slot_labels}. Your match pass is ready below!"
                )
            else:
                messages.success(
                    request,
                    f"🎉 Booking Confirmed (Cash on Counter)! {total_hours} slot(s) reserved for {turf.name} on {booking_date}: {slot_labels}. Please pay ₹{total_price:,.0f} at venue counter before kickoff."
                )
            return redirect('booking_ticket', booking_id=created_bookings[0].id)

    return render(request, 'turfs/booking.html', {
        'turf': turf,
        'time_slots': time_slots,
        'selected_date': selected_date,
        'selected_date_str': selected_date.isoformat(),
        'booked_slot_ids': booked_slot_ids,
        'today_str': timezone.localdate().isoformat(),
    })

def get_org_sync_data(org, target_date=None):
    """
    Centralized synchronization service: Aggregates real-time slot occupancy,
    recent bookings manifest, and metrics across all branches of an organization.
    """
    if not org:
        return {}

    if isinstance(target_date, str):
        try:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            target_date = timezone.localdate()
    elif not target_date:
        target_date = timezone.localdate()

    time_slots = list(TimeSlot.objects.all().order_by('start_time'))
    time_slots_count = len(time_slots)

    branches = org.branches.filter(is_active=True).prefetch_related('turfs__primary_sport')
    all_org_bookings = Booking.objects.filter(
        Q(turf__organization=org) | Q(turf__branch__organization=org),
        date=target_date
    ).select_related('turf', 'turf__branch', 'time_slot', 'user').order_by('-created_at')

    branches_data = []
    org_total_bookings_today = 0
    org_checked_in_today = 0
    org_total_revenue_today = 0

    for branch in branches:
        branch_bookings = [b for b in all_org_bookings if b.turf.branch_id == branch.id]
        branch_confirmed = [b for b in branch_bookings if b.status == 'CONFIRMED']
        branch_completed = [b for b in branch_bookings if b.status == 'COMPLETED']
        branch_revenue = sum(float(b.total_price) for b in branch_bookings if b.status != 'CANCELLED')

        org_total_bookings_today += len(branch_bookings)
        org_checked_in_today += len(branch_completed)
        org_total_revenue_today += branch_revenue

        turfs_data = []
        for t in branch.turfs.all():
            t_booked_slots = [b.time_slot_id for b in branch_confirmed if b.turf_id == t.id]
            turfs_data.append({
                'id': t.id,
                'name': t.name,
                'slug': t.slug,
                'sport': t.primary_sport.name if t.primary_sport else "Multi-Sport",
                'price_per_hour': float(t.price_per_hour),
                'booked_slot_ids': t_booked_slots,
                'booked_count': len(t_booked_slots),
                'available_count': max(0, time_slots_count - len(t_booked_slots)),
                'is_fully_booked': len(t_booked_slots) >= time_slots_count if time_slots_count else False
            })

        branches_data.append({
            'id': branch.id,
            'name': branch.name,
            'slug': branch.slug,
            'city': branch.city,
            'location': branch.location,
            'phone': branch.phone,
            'turfs': turfs_data,
            'turfs_count': len(turfs_data),
            'bookings_count': len(branch_bookings),
            'checked_in_count': len(branch_completed),
            'pending_count': len(branch_confirmed),
            'revenue_today': branch_revenue,
        })

    recent_bookings = []
    for b in all_org_bookings[:25]:
        recent_bookings.append({
            'id': b.id,
            'pass_code': b.pass_code,
            'player_name': b.player_name,
            'player_phone': b.player_phone,
            'turf_id': b.turf.id,
            'turf_name': b.turf.name,
            'branch_id': b.turf.branch.id if b.turf.branch else None,
            'branch_name': b.turf.branch.name if b.turf.branch else "Main Branch",
            'date': b.date.isoformat(),
            'slot_id': b.time_slot_id,
            'slot_label': b.time_slot.label if b.time_slot else "Standard Slot",
            'total_price': float(b.total_price),
            'status': b.status,
            'created_at': b.created_at.strftime('%H:%M:%S'),
        })

    latest_b = all_org_bookings.first()
    sync_version = f"{latest_b.id if latest_b else 0}-{len(all_org_bookings)}-{len(branches_data)}"

    return {
        'organization': {
            'id': org.id,
            'name': org.name,
            'slug': org.slug,
            'branches_count': len(branches_data),
        },
        'date': target_date.isoformat(),
        'branches': branches_data,
        'organization_totals': {
            'total_branches': len(branches_data),
            'total_turfs': sum(b['turfs_count'] for b in branches_data),
            'total_bookings_today': org_total_bookings_today,
            'total_checked_in_today': org_checked_in_today,
            'pending_checkins_today': max(0, org_total_bookings_today - org_checked_in_today),
            'total_revenue_today': org_total_revenue_today,
        },
        'recent_bookings': recent_bookings,
        'sync_version': sync_version,
        'synced_at': timezone.now().isoformat(),
        'is_synced': True,
    }

def api_check_slots(request, turf_id):
    """
    Returns real-time booked slots for a given turf AND dynamically syncs
    the live availability status across all sibling branches in the same organization.
    """
    turf = get_object_or_404(Turf.objects.select_related('organization', 'branch__organization'), id=turf_id)
    date_str = request.GET.get('date')
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.localdate()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)

    booked_ids = list(
        Booking.objects.filter(
            turf=turf,
            date=check_date,
            status='CONFIRMED'
        ).values_list('time_slot_id', flat=True)
    )

    org = turf.organization or (turf.branch.organization if turf.branch else None)
    response_data = {
        'turf_id': turf.id,
        'turf_name': turf.name,
        'date': check_date.isoformat(),
        'booked_slot_ids': booked_ids,
        'timestamp': timezone.now().isoformat(),
    }

    if org:
        org_sync = get_org_sync_data(org, check_date)
        response_data.update({
            'organization': org_sync.get('organization'),
            'current_branch': {
                'id': turf.branch.id if turf.branch else None,
                'name': turf.branch.name if turf.branch else None,
                'location': turf.branch.location if turf.branch else None,
            },
            'all_branches_sync': org_sync.get('branches', []),
            'organization_totals': org_sync.get('organization_totals', {}),
            'sync_version': org_sync.get('sync_version'),
            'synced_at': org_sync.get('synced_at'),
            'is_synced': True,
        })

    return JsonResponse(response_data)

def api_organization_sync(request, org_id):
    """
    Direct endpoint for real-time dynamic sync across all branches of an organization.
    """
    org = get_object_or_404(Organization, id=org_id)
    target_date_str = request.GET.get('date')
    sync_data = get_org_sync_data(org, target_date_str)
    return JsonResponse(sync_data)

def api_branch_sync(request, branch_id):
    """
    Returns real-time sync for a branch and all its sibling branches within the organization.
    """
    branch = get_object_or_404(Branch.objects.select_related('organization'), id=branch_id)
    target_date_str = request.GET.get('date')
    sync_data = get_org_sync_data(branch.organization, target_date_str)
    sync_data['selected_branch_id'] = branch.id
    sync_data['selected_branch_name'] = branch.name
    return JsonResponse(sync_data)

def api_staff_live_sync(request):
    """
    Live background polling endpoint for the Staff Portal.
    Syncs live bookings across all 3 branches in real-time.
    """
    profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=404)

    target_date_str = request.GET.get('date')
    branch_filter = request.GET.get('branch', '').strip()

    sync_data = get_org_sync_data(org, target_date_str)

    if branch_filter and branch_filter != 'all' and branch_filter.isdigit():
        b_id = int(branch_filter)
        sync_data['filtered_recent_bookings'] = [b for b in sync_data.get('recent_bookings', []) if b['branch_id'] == b_id]
        sync_data['active_branch_id'] = b_id
    else:
        sync_data['filtered_recent_bookings'] = sync_data.get('recent_bookings', [])
        sync_data['active_branch_id'] = 'all'

    return JsonResponse(sync_data)

def api_org_admin_live_sync(request):
    """
    Live background polling endpoint for the Organization Admin Portal.
    Syncs metrics and reservations across all 3 branches in real-time.
    """
    profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=404)

    target_date_str = request.GET.get('date')
    sync_data = get_org_sync_data(org, target_date_str)
    return JsonResponse(sync_data)


@login_required
def dashboard(request):
    today = timezone.localdate()
    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        date__gte=today,
        status='CONFIRMED'
    ).select_related('turf', 'time_slot').order_by('date', 'time_slot__start_time')

    past_bookings = Booking.objects.filter(
        Q(user=request.user) & (Q(date__lt=today) | Q(status__in=['COMPLETED', 'CANCELLED']))
    ).select_related('turf', 'time_slot').order_by('-date')

    return render(request, 'turfs/dashboard.html', {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    })

@login_required
def profile_view(request):
    """
    User Profile Management:
    - View and update personal information (names, email, 10-digit mobile, city, address, bio).
    - Upload / replace / remove custom profile avatar image.
    - Select favorite sport.
    - View player activity statistics.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    sports = Sport.objects.all().order_by('name')

    today = timezone.localdate()
    total_bookings = Booking.objects.filter(user=user).count()
    completed_bookings = Booking.objects.filter(user=user, status='COMPLETED').count()
    active_bookings = Booking.objects.filter(user=user, status='CONFIRMED', date__gte=today).count()

    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')

        if action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            city = request.POST.get('city', '').strip()
            address = request.POST.get('address', '').strip()
            bio = request.POST.get('bio', '').strip()
            favorite_sport_id = request.POST.get('favorite_sport_id')

            # 1. First Name Validation
            fn_valid, fn_err, clean_first_name = validate_name(first_name, field_name="First Name", min_length=2, required=True)
            if not fn_valid:
                messages.error(request, fn_err)
                return redirect('profile')

            # 2. Email Validation (@ and . must)
            em_valid, em_err, clean_email = validate_email_format(email)
            if not em_valid:
                messages.error(request, em_err)
                return redirect('profile')

            # Check if email taken by someone else
            if User.objects.filter(Q(email__iexact=clean_email) | Q(username__iexact=clean_email)).exclude(id=user.id).exists():
                messages.error(request, "This email address is already registered to another account.")
                return redirect('profile')

            # 3. Phone Validation (10 digits if provided)
            clean_phone = ""
            if phone:
                ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
                if not ph_valid:
                    messages.error(request, ph_err)
                    return redirect('profile')
                clean_phone = verified_phone

            # 4. Avatar File Handling
            if request.POST.get('remove_avatar') == '1':
                if profile.avatar:
                    profile.avatar.delete(save=False)
                profile.avatar = None
            elif 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']
                # Max 5MB file size
                if avatar_file.size > 5 * 1024 * 1024:
                    messages.error(request, "Profile picture size must not exceed 5MB.")
                    return redirect('profile')

                allowed_exts = ['.jpg', '.jpeg', '.png', '.webp']
                ext = os.path.splitext(avatar_file.name)[1].lower()
                if ext not in allowed_exts:
                    messages.error(request, f"Invalid image format. Allowed formats: {', '.join(allowed_exts)}")
                    return redirect('profile')

                if profile.avatar:
                    profile.avatar.delete(save=False)
                profile.avatar = avatar_file

            # 5. Favorite Sport
            fav_sport = None
            if favorite_sport_id:
                fav_sport = Sport.objects.filter(id=favorite_sport_id).first()

            # Update User fields
            user.first_name = clean_first_name
            user.last_name = last_name
            user.email = clean_email
            user.username = clean_email
            user.save()

            # Update Profile fields
            profile.phone = clean_phone
            profile.city = city or 'Ahmedabad'
            profile.address = address
            profile.bio = bio[:500]
            profile.favorite_sport = fav_sport
            profile.save()

            messages.success(request, "Your profile details have been saved successfully!")
            return redirect('profile')

    return render(request, 'turfs/profile.html', {
        'profile': profile,
        'sports': sports,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'active_bookings': active_bookings,
    })

@login_required
def change_password_view(request):
    """
    Secure password update handler from Profile section.
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, "Incorrect current password. Please try again.")
            return redirect('profile')

        pw_valid, pw_err = validate_password_rules(new_password, min_length=8)
        if not pw_valid:
            messages.error(request, pw_err)
            return redirect('profile')

        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return redirect('profile')

        request.user.set_password(new_password)
        request.user.save()
        # Re-authenticate so session remains active
        login(request, request.user)

        user_role = 'PLAYER'
        if hasattr(request.user, 'profile') and request.user.profile.role:
            user_role = request.user.profile.role
        elif request.user.is_superuser:
            user_role = 'SUPERADMIN'
        save_credentials_to_env(
            email=request.user.email or request.user.username,
            password=new_password,
            role=user_role,
            username=request.user.username,
            name=request.user.get_full_name() or request.user.username
        )

        messages.success(request, "Your password has been changed successfully!")
        return redirect('profile')

    return redirect('profile')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save()
        messages.info(request, f"Booking #{booking.id} for {booking.turf.name} has been cancelled.")
    return redirect('dashboard')

@login_required
def booking_ticket(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('turf', 'turf__primary_sport', 'time_slot', 'user'),
        id=booking_id
    )

    is_staff_or_admin = (
        request.user.is_staff or 
        request.user.is_superuser or 
        (hasattr(request.user, 'profile') and request.user.profile.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'MANAGER', 'STAFF'])
    )
    if booking.user != request.user and not is_staff_or_admin:
        messages.error(request, "You do not have permission to view this ticket.")
        return redirect('dashboard')

    # Find companion bookings made in the same checkout session (same user, turf, date within 2 minutes)
    time_window_start = booking.created_at - timedelta(minutes=2)
    time_window_end = booking.created_at + timedelta(minutes=2)
    related_bookings = list(Booking.objects.filter(
        user=booking.user,
        turf=booking.turf,
        date=booking.date,
        created_at__gte=time_window_start,
        created_at__lte=time_window_end,
    ).select_related('time_slot').order_by('time_slot__start_time'))

    if not related_bookings:
        related_bookings = [booking]

    all_slots = [b.time_slot for b in related_bookings]
    total_amount = sum(b.total_price for b in related_bookings)
    total_hours = len(related_bookings)
    ticket_code = f"TB-{booking.date.strftime('%Y%m%d')}-{booking.id:04d}"

    # Generate high-resolution scannable QR Code as base64 PNG data URL
    qr_data_url = ""
    try:
        qr_payload = f"TURFBOOK-PASS:{ticket_code}|TURF:{booking.turf.name}|PLAYER:{booking.player_name}|DATE:{booking.date}|STATUS:{booking.status}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(qr_payload)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf)
        qr_b64 = base64.b64encode(qr_buf.getvalue()).decode()
        qr_data_url = f"data:image/png;base64,{qr_b64}"
    except Exception as e:
        print("QR generation error:", e)

    return render(request, 'turfs/ticket.html', {
        'booking': booking,
        'related_bookings': related_bookings,
        'all_slots': all_slots,
        'total_amount': total_amount,
        'total_hours': total_hours,
        'ticket_code': ticket_code,
        'qr_data_url': qr_data_url,
    })

def ticket_hub(request):
    """
    Navbar Ticket shortcut:
    - If user is logged in, redirects to their most recent match ticket.
    - If user is staff and has no personal booking, displays the latest system booking.
    - If user has no bookings, prompts user to explore turfs.
    - If unauthenticated, prompts to log in.
    """
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view and download your Match Ticket.")
        return redirect(f"{reverse('login')}?next={reverse('ticket')}")

    # Prioritize active or upcoming confirmed bookings
    today = timezone.localdate()
    booking = (
        Booking.objects.filter(user=request.user, status='CONFIRMED', date__gte=today)
        .order_by('date', 'time_slot__start_time')
        .first()
    )
    if not booking:
        booking = (
            Booking.objects.filter(user=request.user)
            .order_by('-date', '-created_at')
            .first()
        )

    # For staff/admin convenience during testing
    if not booking and request.user.is_staff:
        booking = Booking.objects.order_by('-date', '-created_at').first()

    if booking:
        return redirect('booking_ticket', booking_id=booking.id)

    messages.info(request, "You haven't booked any turf yet. Reserve your turf to generate your VIP Match Ticket!")
    return redirect('turf_list')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
        }

        # 1. First Name Validation
        fn_valid, fn_err, clean_first_name = validate_name(first_name, field_name="First Name", min_length=2, required=True)
        if not fn_valid:
            messages.error(request, fn_err)
            return render(request, 'turfs/register.html', {'form_data': form_data})

        # 2. Email Validation (Must contain '@' and '.')
        em_valid, em_err, clean_email = validate_email_format(email)
        if not em_valid:
            messages.error(request, em_err)
            return render(request, 'turfs/register.html', {'form_data': form_data})

        # 3. Mobile Number Validation (Must be exactly 10 digits)
        ph_valid, ph_err, clean_phone = clean_and_validate_mobile(phone, required=True)
        if not ph_valid:
            messages.error(request, ph_err)
            return render(request, 'turfs/register.html', {'form_data': form_data})

        # 4. Password Validation (Must be at least 8 characters)
        pw_valid, pw_err = validate_password_rules(password, min_length=8)
        if not pw_valid:
            messages.error(request, pw_err)
            return render(request, 'turfs/register.html', {'form_data': form_data})

        # 5. Confirm Password Match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'turfs/register.html', {'form_data': form_data})

        # 6. Check for existing registered account
        if User.objects.filter(username__iexact=clean_email).exists() or User.objects.filter(email__iexact=clean_email).exists():
            messages.error(request, "An account with this email already exists. Please sign in.")
            return render(request, 'turfs/register.html', {'form_data': form_data})

        user = User.objects.create_user(
            username=clean_email,
            email=clean_email,
            password=password,
            first_name=clean_first_name,
            last_name=last_name
        )

        # Store phone on user profile
        if hasattr(user, 'profile'):
            user.profile.phone = clean_phone
            user.profile.save()
        else:
            UserProfile.objects.create(user=user, role='PLAYER', phone=clean_phone)

        # Auto-persist newly registered account credentials to .env
        save_credentials_to_env(
            email=clean_email,
            password=password,
            role='PLAYER',
            username=clean_email,
            name=f"{clean_first_name} {last_name}".strip()
        )

        login(request, user)
        messages.success(request, f"Welcome to TurfBook, {clean_first_name}!")
        return redirect('dashboard')

    return render(request, 'turfs/register.html')

def get_user_dashboard_url(user):
    """
    Intelligently determines the landing portal based on user role:
    - Super Admin -> super_admin_dashboard (/super-admin/)
    - Org Admin -> org_admin_dashboard (/org-admin/)
    - Manager / Staff -> staff_portal (/staff-portal/)
    - Customer / Player -> dashboard (/dashboard/)
    """
    if not user.is_authenticated:
        return 'home'
    if user.is_superuser:
        return 'super_admin_dashboard'
    try:
        profile = user.profile
        if profile.role == 'SUPER_ADMIN':
            return 'super_admin_dashboard'
        elif profile.role == 'ORG_ADMIN':
            return 'org_admin_dashboard'
        elif profile.role in ['MANAGER', 'STAFF']:
            return 'staff_portal'
        else:
            return 'dashboard'
    except Exception:
        if user.is_staff:
            return 'super_admin_dashboard'
        return 'dashboard'

def super_admin_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        is_super = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN')
        if not is_super:
            messages.error(request, "Access restricted to Super Administrators.")
            return redirect(get_user_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped

def org_admin_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        is_super = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN')
        is_org_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ORG_ADMIN' and request.user.profile.organization
        if not (is_super or is_org_admin):
            messages.error(request, "Access restricted to Organization Administrators.")
            return redirect(get_user_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped

def staff_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        is_super = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'SUPER_ADMIN')
        is_org_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ORG_ADMIN'
        is_staff_role = hasattr(request.user, 'profile') and request.user.profile.role in ['MANAGER', 'STAFF']
        if not (is_super or is_org_admin or is_staff_role):
            messages.error(request, "Access restricted to Staff and Managers.")
            return redirect(get_user_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped

def login_view(request):
    """
    Unified Login View:
    - Zero dropdowns, pure Email/Username + Password.
    - System automatically detects if user is Super Admin, Org Admin, Manager, Staff, or Player based on their account/email.
    - Redirects each user to their designated portal automatically.
    - Validates email format and password length requirements.
    """
    if request.user.is_authenticated:
        return redirect(get_user_dashboard_url(request.user))

    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        email_or_user = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email_or_user:
            messages.error(request, "Please enter your email or username.")
            return render(request, 'turfs/login.html', {'next': next_url, 'email': email_or_user})

        # Enforce email format (@ and .) unless logging in as default 'admin' superuser
        if email_or_user.lower() != 'admin':
            em_valid, em_err, clean_email = validate_email_format(email_or_user)
            if not em_valid:
                messages.error(request, em_err)
                return render(request, 'turfs/login.html', {'next': next_url, 'email': email_or_user})
            email_or_user = clean_email

        if not password:
            messages.error(request, "Please enter your password.")
            return render(request, 'turfs/login.html', {'next': next_url, 'email': email_or_user})

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'turfs/login.html', {'next': next_url, 'email': email_or_user})
        
        # 1. Try standard authentication by username
        user = authenticate(request, username=email_or_user, password=password)
        
        # 2. If not found, try looking up User by email address
        if user is None:
            matched_user = User.objects.filter(Q(email__iexact=email_or_user) | Q(username__iexact=email_or_user)).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)

        if user is not None:
            login(request, user)
            
            # Determine role badge for welcome message
            role_title = "Customer"
            if user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'SUPER_ADMIN'):
                role_title = "Super Admin"
            elif hasattr(user, 'profile'):
                role_title = user.profile.role_display_name
                
            messages.success(request, f"Welcome back, {user.first_name or user.username}! Logged in as {role_title}.")
            
            # Redirect to explicit next URL if requested, otherwise route automatically based on role
            if next_url and next_url not in ['dashboard', '/dashboard/', '']:
                return redirect(next_url)
            return redirect(get_user_dashboard_url(user))
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'turfs/login.html', {'next': next_url, 'email': email_or_user})

    return render(request, 'turfs/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# -------------------------------------------------------------
# 1. SUPER ADMIN PORTAL VIEWS
# -------------------------------------------------------------

@super_admin_required
def super_admin_dashboard(request):
    organizations = Organization.objects.annotate(
        branch_count=models.Count('branches', distinct=True),
        turf_count=models.Count('turfs', distinct=True),
    ).order_by('-created_at')

    all_branches = Branch.objects.select_related('organization').annotate(
        turf_count=models.Count('turfs', distinct=True)
    ).order_by('organization__name', 'name')

    all_turfs = Turf.objects.select_related('organization', 'branch', 'primary_sport').order_by('-created_at')

    recent_bookings = Booking.objects.select_related('turf', 'turf__organization', 'turf__branch', 'user', 'time_slot').order_by('-created_at')[:20]

    total_revenue = Booking.objects.filter(status__in=['CONFIRMED', 'COMPLETED']).aggregate(total=models.Sum('total_price'))['total'] or 0

    all_roles = OrganizationRole.objects.select_related('organization').annotate(
        assigned_count=models.Count('assigned_users', distinct=True)
    ).order_by('organization__name', 'name')

    all_team_members = UserProfile.objects.filter(
        role__in=['ORG_ADMIN', 'MANAGER', 'STAFF']
    ).select_related('user', 'organization', 'branch', 'custom_role').order_by('-created_at')

    return render(request, 'portals/super_admin.html', {
        'organizations': organizations,
        'all_branches': all_branches,
        'all_turfs': all_turfs,
        'all_roles': all_roles,
        'all_team_members': all_team_members,
        'recent_bookings': recent_bookings,
        'total_organizations': organizations.count(),
        'total_branches': all_branches.count(),
        'total_turfs': all_turfs.count(),
        'total_roles': all_roles.count(),
        'total_team_members': all_team_members.count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': total_revenue,
    })

@super_admin_required
def super_admin_create_org(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Org Admin account details
        admin_name = request.POST.get('admin_name', '').strip()
        admin_email = request.POST.get('admin_email', '').strip()
        admin_password = request.POST.get('admin_password', '').strip() or 'password123'
        
        if not name or not admin_email:
            messages.error(request, "Organization name and Admin Email are required.")
            return redirect('super_admin_dashboard')

        # Validate Admin Email (must contain '@' and '.')
        em_valid, em_err, clean_admin_email = validate_email_format(admin_email)
        if not em_valid:
            messages.error(request, f"Admin Email: {em_err}")
            return redirect('super_admin_dashboard')

        # Validate Admin Password (must be >= 8 chars)
        pw_valid, pw_err = validate_password_rules(admin_password, min_length=8)
        if not pw_valid:
            messages.error(request, f"Admin Password: {pw_err}")
            return redirect('super_admin_dashboard')

        # Validate Organization Phone if provided (10 digits)
        clean_org_phone = phone
        if phone:
            ph_valid, ph_err, clean_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Organization Phone: {ph_err}")
                return redirect('super_admin_dashboard')
            clean_org_phone = clean_phone

        # Validate Organization Email if provided
        clean_org_email = email or clean_admin_email
        if email:
            oem_valid, oem_err, verified_org_email = validate_email_format(email)
            if not oem_valid:
                messages.error(request, f"Organization Email: {oem_err}")
                return redirect('super_admin_dashboard')
            clean_org_email = verified_org_email
            
        org, _ = Organization.objects.get_or_create(
            name=name,
            defaults={
                'email': clean_org_email,
                'phone': clean_org_phone,
                'address': address,
                'description': description,
            }
        )
        
        # Create or update Org Admin user
        admin_user, u_created = User.objects.get_or_create(
            username=clean_admin_email,
            defaults={
                'email': clean_admin_email,
                'first_name': admin_name or name + " Admin",
            }
        )
        if u_created:
            admin_user.set_password(admin_password)
            admin_user.save()
        elif admin_password and admin_password != 'password123':
            admin_user.set_password(admin_password)
            admin_user.save()
            
        # Ensure user profile is set as ORG_ADMIN for this organization
        profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        profile.role = 'ORG_ADMIN'
        profile.organization = org
        profile.phone = phone
        profile.save()

        # Auto-persist newly created Org Admin credentials to .env
        save_credentials_to_env(
            email=clean_admin_email,
            password=admin_password,
            role='ORG_ADMIN',
            username=clean_admin_email,
            name=admin_name or f"{name} Admin",
            organization=org.name
        )
        
        messages.success(request, f"Organization '{org.name}' and Org Admin account '{admin_email}' created successfully!")
        return redirect('super_admin_org_detail', org_id=org.id)
    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_org_detail(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    branches = org.branches.annotate(turf_count=models.Count('turfs', distinct=True)).all()
    turfs = org.turfs.select_related('branch', 'primary_sport').all()
    team_members = UserProfile.objects.filter(organization=org).select_related('user', 'custom_role', 'branch')
    custom_roles = org.custom_roles.all()
    bookings = Booking.objects.filter(turf__organization=org).select_related('turf', 'user', 'time_slot').order_by('-date')[:25]
    
    org_revenue = Booking.objects.filter(turf__organization=org, status__in=['CONFIRMED', 'COMPLETED']).aggregate(total=models.Sum('total_price'))['total'] or 0

    return render(request, 'portals/org_detail.html', {
        'org': org,
        'branches': branches,
        'turfs': turfs,
        'team_members': team_members,
        'custom_roles': custom_roles,
        'bookings': bookings,
        'org_revenue': org_revenue,
    })

@super_admin_required
def super_admin_update_org(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('super_admin_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        description = request.POST.get('description', '').strip()
        logo_url = request.POST.get('logo_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            messages.error(request, "Organization name is required.")
            return redirect(next_url)

        # Unique name validation among other organizations
        if Organization.objects.filter(name=name).exclude(id=org.id).exists():
            messages.error(request, f"Another organization with the name '{name}' already exists.")
            return redirect(next_url)

        clean_phone = phone
        if phone:
            ph_valid, ph_err, clean_p = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Organization Phone: {ph_err}")
                return redirect(next_url)
            clean_phone = clean_p

        clean_email = email
        if email:
            em_valid, em_err, verified_email = validate_email_format(email)
            if not em_valid:
                messages.error(request, f"Organization Email: {em_err}")
                return redirect(next_url)
            clean_email = verified_email

        org.name = name
        org.slug = slugify(name)
        org.email = clean_email
        org.phone = clean_phone
        org.address = address
        org.description = description
        if logo_url:
            org.logo_url = logo_url
        org.is_active = is_active
        org.save()

        messages.success(request, f"Organization '{org.name}' updated successfully!")
        return redirect(next_url)

    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_delete_org(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if request.method == 'POST':
        org_name = org.name

        # Demote or unassign any user profiles attached to this organization
        UserProfile.objects.filter(organization=org).update(
            role='PLAYER',
            organization=None,
            branch=None,
            custom_role=None
        )

        # Delete turfs belonging to this organization (cascades bookings & reviews)
        org.turfs.all().delete()

        # Delete the organization (cascades branches & custom roles)
        org.delete()

        messages.success(request, f"Organization '{org_name}' and all associated branches, roles, and courts have been deleted.")
        return redirect('super_admin_dashboard')

    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_create_branch(request):
    if request.method == 'POST':
        org_id = request.POST.get('organization_id')
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', 'Ahmedabad').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        org = get_object_or_404(Organization, id=org_id)
        if not name or not location:
            messages.error(request, "Branch name and location are required.")
            return redirect('super_admin_org_detail', org_id=org.id)

        clean_branch_phone = phone
        if phone:
            ph_valid, ph_err, clean_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Branch Phone: {ph_err}")
                return redirect('super_admin_org_detail', org_id=org.id)
            clean_branch_phone = clean_phone

        branch = Branch.objects.create(
            organization=org,
            name=name,
            location=location,
            city=city,
            address=address,
            phone=clean_branch_phone
        )
        messages.success(request, f"Branch '{branch.name}' created under '{org.name}'!")
        return redirect('super_admin_org_detail', org_id=org.id)
    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_update_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('super_admin_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', 'Ahmedabad').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        org_id = request.POST.get('organization_id')

        if not name or not location:
            messages.error(request, "Branch name and location are required.")
            return redirect(next_url)

        clean_phone = phone
        if phone:
            ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Branch Phone: {ph_err}")
                return redirect(next_url)
            clean_phone = phone

        clean_email = email
        if email:
            em_valid, em_err, verified_email = validate_email_format(email)
            if not em_valid:
                messages.error(request, f"Branch Email: {em_err}")
                return redirect(next_url)
            clean_email = verified_email

        branch.name = name
        branch.location = location
        branch.city = city
        branch.address = address
        branch.phone = clean_phone
        branch.email = clean_email
        branch.is_active = is_active

        if org_id:
            new_org = Organization.objects.filter(id=org_id).first()
            if new_org:
                branch.organization = new_org

        branch.save()
        messages.success(request, f"Branch '{branch.name}' updated successfully!")
        return redirect(next_url)

    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_delete_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('super_admin_dashboard')
    
    if request.method == 'POST':
        branch_name = branch.name
        org_name = branch.organization.name
        branch.delete()
        messages.success(request, f"Branch '{branch_name}' ({org_name}) has been deleted successfully.")
        return redirect(next_url)

    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_create_role(request):
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('super_admin_dashboard')
    if request.method == 'POST':
        org_id = request.POST.get('organization_id')
        if not org_id:
            messages.error(request, "Organization is required to create a role.")
            return redirect(next_url)

        org = get_object_or_404(Organization, id=org_id)
        role_name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        can_manage_turfs = request.POST.get('can_manage_turfs') == 'on'
        can_manage_slots = request.POST.get('can_manage_slots') == 'on'
        can_manage_bookings = request.POST.get('can_manage_bookings') == 'on'
        can_view_reports = request.POST.get('can_view_reports') == 'on'
        can_manage_staff = request.POST.get('can_manage_staff') == 'on'

        if not role_name:
            messages.error(request, "Role title cannot be empty.")
            return redirect(next_url)

        role, created = OrganizationRole.objects.get_or_create(
            organization=org,
            name=role_name,
            defaults={
                'description': description,
                'can_manage_turfs': can_manage_turfs,
                'can_manage_slots': can_manage_slots,
                'can_manage_bookings': can_manage_bookings,
                'can_view_reports': can_view_reports,
                'can_manage_staff': can_manage_staff,
            }
        )
        if not created:
            role.description = description
            role.can_manage_turfs = can_manage_turfs
            role.can_manage_slots = can_manage_slots
            role.can_manage_bookings = can_manage_bookings
            role.can_view_reports = can_view_reports
            role.can_manage_staff = can_manage_staff
            role.save()

        action_str = "created" if created else "updated"
        messages.success(request, f"Role '{role_name}' {action_str} successfully for '{org.name}'!")
        return redirect(next_url)

    return redirect('super_admin_dashboard')

@super_admin_required
def super_admin_create_team_member(request):
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('super_admin_dashboard')
    if request.method == 'POST':
        org_id = request.POST.get('organization_id')
        if not org_id:
            messages.error(request, "Organization is required to add a staff / member.")
            return redirect(next_url)

        org = get_object_or_404(Organization, id=org_id)
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip() or 'password123'
        phone = request.POST.get('phone', '').strip()
        custom_role_id = request.POST.get('custom_role_id')
        branch_id = request.POST.get('branch_id')
        system_role = request.POST.get('system_role', 'STAFF').strip().upper()
        if system_role not in ['ORG_ADMIN', 'MANAGER', 'STAFF']:
            system_role = 'STAFF'

        # First Name Validation
        fn_valid, fn_err, clean_fname = validate_name(first_name, field_name="First Name", min_length=2, required=True)
        if not fn_valid:
            messages.error(request, fn_err)
            return redirect(next_url)

        # Email Validation (Must contain '@' and '.')
        em_valid, em_err, clean_email = validate_email_format(email)
        if not em_valid:
            messages.error(request, em_err)
            return redirect(next_url)

        # Password Validation (At least 8 characters)
        pw_valid, pw_err = validate_password_rules(password, min_length=8)
        if not pw_valid:
            messages.error(request, pw_err)
            return redirect(next_url)

        # Phone Validation (10 digits if provided)
        clean_phone = phone
        if phone:
            ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, ph_err)
                return redirect(next_url)
            clean_phone = verified_phone

        custom_role = None
        if custom_role_id:
            custom_role = OrganizationRole.objects.filter(id=custom_role_id, organization=org).first()

        branch = None
        if branch_id:
            branch = Branch.objects.filter(id=branch_id, organization=org).first()

        user, created = User.objects.get_or_create(
            username=clean_email,
            defaults={
                'email': clean_email,
                'first_name': clean_fname,
                'last_name': last_name,
            }
        )
        if created:
            user.set_password(password)
            user.save()
        else:
            if clean_fname:
                user.first_name = clean_fname
            if last_name:
                user.last_name = last_name
            if password and password != 'password123':
                user.set_password(password)
            user.save()

        user_prof, _ = UserProfile.objects.get_or_create(user=user)
        user_prof.role = system_role
        user_prof.organization = org
        user_prof.branch = branch
        user_prof.custom_role = custom_role
        user_prof.phone = clean_phone
        user_prof.save()

        # Auto-persist newly created team member credentials to .env
        save_credentials_to_env(
            email=clean_email,
            password=password,
            role=system_role,
            username=clean_email,
            name=f"{clean_fname} {last_name}".strip(),
            organization=org.name if org else None,
            branch=branch.name if branch else None
        )

        display_role = custom_role.name if custom_role else user_prof.get_role_display()
        messages.success(request, f"Team member '{user.email}' added to '{org.name}' as {display_role}!")
        return redirect(next_url)

    return redirect('super_admin_dashboard')

# -------------------------------------------------------------
# 2. ORGANIZATION ADMIN PORTAL VIEWS
# -------------------------------------------------------------

@org_admin_required
def org_admin_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if request.user.is_superuser and (not profile or not profile.organization):
        org = Organization.objects.first()
    else:
        org = profile.organization

    if not org:
        messages.error(request, "No organization assigned to your account.")
        return redirect('dashboard')

    branches = org.branches.annotate(turf_count=models.Count('turfs', distinct=True)).all()
    turfs = org.turfs.select_related('branch', 'primary_sport').all()
    custom_roles = org.custom_roles.all()
    team_members = UserProfile.objects.filter(organization=org).select_related('user', 'custom_role', 'branch')
    recent_bookings = Booking.objects.filter(turf__organization=org).select_related('turf', 'user', 'time_slot').order_by('-date', '-created_at')[:25]
    
    total_revenue = Booking.objects.filter(turf__organization=org, status__in=['CONFIRMED', 'COMPLETED']).aggregate(total=models.Sum('total_price'))['total'] or 0

    return render(request, 'portals/org_admin.html', {
        'org': org,
        'branches': branches,
        'turfs': turfs,
        'custom_roles': custom_roles,
        'team_members': team_members,
        'recent_bookings': recent_bookings,
        'total_revenue': total_revenue,
        'sports': Sport.objects.all(),
    })

@org_admin_required
def org_admin_create_role(request):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if request.method == 'POST' and org:
        role_name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        can_manage_turfs = request.POST.get('can_manage_turfs') == 'on'
        can_manage_slots = request.POST.get('can_manage_slots') == 'on'
        can_manage_bookings = request.POST.get('can_manage_bookings') == 'on'
        can_view_reports = request.POST.get('can_view_reports') == 'on'
        can_manage_staff = request.POST.get('can_manage_staff') == 'on'
        
        if role_name:
            role, created = OrganizationRole.objects.get_or_create(
                organization=org,
                name=role_name,
                defaults={
                    'description': description,
                    'can_manage_turfs': can_manage_turfs,
                    'can_manage_slots': can_manage_slots,
                    'can_manage_bookings': can_manage_bookings,
                    'can_view_reports': can_view_reports,
                    'can_manage_staff': can_manage_staff,
                }
            )
            if not created:
                role.description = description
                role.can_manage_turfs = can_manage_turfs
                role.can_manage_slots = can_manage_slots
                role.can_manage_bookings = can_manage_bookings
                role.can_view_reports = can_view_reports
                role.can_manage_staff = can_manage_staff
                role.save()
            messages.success(request, f"Role '{role_name}' created successfully with permissions!")
    return redirect('org_admin_dashboard')

@org_admin_required
def org_admin_create_team_member(request):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if request.method == 'POST' and org:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip() or 'password123'
        phone = request.POST.get('phone', '').strip()
        custom_role_id = request.POST.get('custom_role_id')
        branch_id = request.POST.get('branch_id')
        system_role = request.POST.get('system_role', 'STAFF') # 'MANAGER' or 'STAFF'

        # First Name Validation
        fn_valid, fn_err, clean_fname = validate_name(first_name, field_name="First Name", min_length=2, required=True)
        if not fn_valid:
            messages.error(request, fn_err)
            return redirect('org_admin_dashboard')

        # Email Validation (Must contain '@' and '.')
        em_valid, em_err, clean_email = validate_email_format(email)
        if not em_valid:
            messages.error(request, em_err)
            return redirect('org_admin_dashboard')

        # Password Validation (At least 8 characters)
        pw_valid, pw_err = validate_password_rules(password, min_length=8)
        if not pw_valid:
            messages.error(request, pw_err)
            return redirect('org_admin_dashboard')

        # Phone Validation (10 digits if provided)
        clean_phone = phone
        if phone:
            ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, ph_err)
                return redirect('org_admin_dashboard')
            clean_phone = verified_phone
            
        custom_role = None
        if custom_role_id:
            custom_role = OrganizationRole.objects.filter(id=custom_role_id, organization=org).first()
            
        branch = None
        if branch_id:
            branch = Branch.objects.filter(id=branch_id, organization=org).first()
            
        user, created = User.objects.get_or_create(
            username=clean_email,
            defaults={
                'email': clean_email,
                'first_name': clean_fname,
                'last_name': last_name,
            }
        )
        if created:
            user.set_password(password)
            user.save()
        else:
            if clean_fname:
                user.first_name = clean_fname
            if last_name:
                user.last_name = last_name
            if password and password != 'password123':
                user.set_password(password)
            user.save()
            
        user_prof, _ = UserProfile.objects.get_or_create(user=user)
        user_prof.role = system_role
        user_prof.organization = org
        user_prof.branch = branch
        user_prof.custom_role = custom_role
        user_prof.phone = clean_phone
        user_prof.save()

        # Auto-persist newly created team member credentials to .env
        save_credentials_to_env(
            email=clean_email,
            password=password,
            role=system_role,
            username=clean_email,
            name=f"{clean_fname} {last_name}".strip(),
            organization=org.name if org else None,
            branch=branch.name if branch else None
        )
        
        messages.success(request, f"Team member '{user.email}' added successfully as {custom_role.name if custom_role else system_role}!")
    return redirect('org_admin_dashboard')

@org_admin_required
def org_admin_create_branch(request):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if request.method == 'POST' and org:
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', 'Ahmedabad').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not name or not location:
            messages.error(request, "Branch name and location are required.")
            return redirect('org_admin_dashboard')

        clean_phone = phone
        if phone:
            ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Branch Phone: {ph_err}")
                return redirect('org_admin_dashboard')
            clean_phone = verified_phone
        
        Branch.objects.create(
            organization=org,
            name=name,
            location=location,
            city=city,
            address=address,
            phone=clean_phone
        )
        messages.success(request, f"Branch '{name}' created for {org.name}!")
    return redirect('org_admin_dashboard')

@org_admin_required
def org_admin_update_branch(request, branch_id):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    branch = get_object_or_404(Branch, id=branch_id, organization=org)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        city = request.POST.get('city', 'Ahmedabad').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name or not location:
            messages.error(request, "Branch name and location are required.")
            return redirect('org_admin_dashboard')

        clean_phone = phone
        if phone:
            ph_valid, ph_err, verified_phone = clean_and_validate_mobile(phone, required=False)
            if not ph_valid:
                messages.error(request, f"Branch Phone: {ph_err}")
                return redirect('org_admin_dashboard')
            clean_phone = verified_phone

        clean_email = email
        if email:
            em_valid, em_err, verified_email = validate_email_format(email)
            if not em_valid:
                messages.error(request, f"Branch Email: {em_err}")
                return redirect('org_admin_dashboard')
            clean_email = verified_email

        branch.name = name
        branch.location = location
        branch.city = city
        branch.address = address
        branch.phone = clean_phone
        branch.email = clean_email
        branch.is_active = is_active
        branch.save()
        messages.success(request, f"Branch '{branch.name}' updated successfully!")
    return redirect('org_admin_dashboard')

@org_admin_required
def org_admin_delete_branch(request, branch_id):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    branch = get_object_or_404(Branch, id=branch_id, organization=org)
    
    if request.method == 'POST':
        branch_name = branch.name
        branch.delete()
        messages.success(request, f"Branch '{branch_name}' has been deleted successfully.")
    return redirect('org_admin_dashboard')

@org_admin_required
def org_admin_create_turf(request):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    if request.method == 'POST' and org:
        name = request.POST.get('name', '').strip()
        branch_id = request.POST.get('branch_id')
        sport_id = request.POST.get('primary_sport_id')
        price_per_hour = request.POST.get('price_per_hour', 1200)
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        
        branch = Branch.objects.filter(id=branch_id, organization=org).first() if branch_id else None
        sport = Sport.objects.filter(id=sport_id).first() if sport_id else Sport.objects.first()
        
        turf = Turf.objects.create(
            name=name,
            organization=org,
            branch=branch,
            primary_sport=sport,
            price_per_hour=price_per_hour,
            location=location or (branch.location if branch else 'Ahmedabad'),
            description=description or f"Premier sports facility by {org.name}",
            image_url=image_url or "https://images.unsplash.com/photo-1575361204480-aadea25e6e68?auto=format&fit=crop&w=1000&q=80"
        )
        if sport:
            turf.sports.add(sport)
        messages.success(request, f"Turf court '{turf.name}' created successfully!")
    return redirect('org_admin_dashboard')

# -------------------------------------------------------------
# 3. STAFF / MANAGER PORTAL VIEWS
# -------------------------------------------------------------

@staff_required
def staff_portal(request):
    profile = getattr(request.user, 'profile', None)
    org = profile.organization if (profile and profile.organization) else Organization.objects.first()
    
    today = timezone.localdate()
    all_org_branches = org.branches.filter(is_active=True).annotate(turf_count=models.Count('turfs')) if org else []
    
    # Selected branch filter from query params; defaults to staff's assigned branch if any, or 'all'
    requested_branch = request.GET.get('branch')
    if requested_branch:
        selected_branch_id = requested_branch
    elif profile and profile.branch:
        selected_branch_id = str(profile.branch.id)
    else:
        selected_branch_id = 'all'

    active_branch = None
    if selected_branch_id != 'all' and selected_branch_id.isdigit():
        active_branch = Branch.objects.filter(id=int(selected_branch_id), organization=org).first()

    if active_branch:
        turfs = Turf.objects.filter(branch=active_branch)
        branch_bookings = Booking.objects.filter(turf__branch=active_branch, date=today).select_related('turf', 'turf__branch', 'user', 'time_slot').order_by('time_slot__start_time')
    elif org:
        turfs = Turf.objects.filter(Q(organization=org) | Q(branch__organization=org))
        branch_bookings = Booking.objects.filter(Q(turf__organization=org) | Q(turf__branch__organization=org), date=today).select_related('turf', 'turf__branch', 'user', 'time_slot').order_by('time_slot__start_time')
    else:
        turfs = Turf.objects.all()
        branch_bookings = Booking.objects.filter(date=today).select_related('turf', 'turf__branch', 'user', 'time_slot').order_by('time_slot__start_time')
        
    verify_code = request.GET.get('verify_code', '').strip()
    verified_booking = None
    if verify_code:
        booking_id = None
        if verify_code.startswith('TB-'):
            parts = verify_code.split('-')
            if len(parts) >= 3 and parts[-1].isdigit():
                booking_id = int(parts[-1])
        elif verify_code.isdigit():
            booking_id = int(verify_code)
            
        if booking_id:
            # Multi-branch pass lookup across entire organization network
            verified_booking = Booking.objects.filter(
                id=booking_id
            ).filter(
                Q(turf__organization=org) | Q(turf__branch__organization=org) if org else Q()
            ).select_related('turf', 'turf__branch', 'user', 'time_slot').first()
            
            if not verified_booking:
                # Fallback to any booking if super admin or org not restricting
                verified_booking = Booking.objects.filter(id=booking_id).select_related('turf', 'turf__branch', 'user', 'time_slot').first()

            if not verified_booking:
                messages.warning(request, f"No booking found matching Pass Code: {verify_code}")
        else:
            messages.warning(request, f"Invalid pass code format: {verify_code}")

    checked_in_count = branch_bookings.filter(status='COMPLETED').count()
    pending_checkin_count = branch_bookings.filter(status='CONFIRMED').count()
    org_sync = get_org_sync_data(org, today) if org else {}

    return render(request, 'portals/staff_portal.html', {
        'profile': profile,
        'org': org,
        'branch': active_branch or (profile.branch if profile else None),
        'all_org_branches': all_org_branches,
        'selected_branch_id': selected_branch_id,
        'turfs': turfs,
        'branch_bookings': branch_bookings,
        'checked_in_count': checked_in_count,
        'pending_checkin_count': pending_checkin_count,
        'verified_booking': verified_booking,
        'verify_code': verify_code,
        'today': today,
        'org_sync': org_sync,
    })

@staff_required
def staff_checkin_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.status = 'COMPLETED'
        if booking.payment_method == 'CASH' and booking.payment_status == 'PENDING_AT_COUNTER':
            booking.payment_status = 'PAID'
            booking.save()
            messages.success(request, f"Pass Verified! Received ₹{booking.total_price:,.0f} cash at counter and checked in player {booking.player_name} for {booking.turf.name}.")
        else:
            booking.save()
            messages.success(request, f"Pass Verified! Player {booking.player_name} checked in successfully for {booking.turf.name}.")
    return redirect('staff_portal')

