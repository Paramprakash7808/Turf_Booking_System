from .models import Turf, Sport

POPULAR_CITIES = [
    {'name': 'Rajkot', 'icon': 'map-pin', 'state': 'Gujarat', 'popular': True},
    {'name': 'Ahmedabad', 'icon': 'building', 'state': 'Gujarat', 'popular': True},
    {'name': 'Mumbai', 'icon': 'building-2', 'state': 'Maharashtra', 'popular': True},
    {'name': 'Delhi-NCR', 'icon': 'landmark', 'state': 'Delhi', 'popular': True},
    {'name': 'Bengaluru', 'icon': 'cpu', 'state': 'Karnataka', 'popular': True},
    {'name': 'Hyderabad', 'icon': 'gem', 'state': 'Telangana', 'popular': True},
    {'name': 'Surat', 'icon': 'sun', 'state': 'Gujarat', 'popular': True},
    {'name': 'Vadodara', 'icon': 'compass', 'state': 'Gujarat', 'popular': True},
    {'name': 'Pune', 'icon': 'coffee', 'state': 'Maharashtra', 'popular': True},
    {'name': 'Chandigarh', 'icon': 'trees', 'state': 'Punjab', 'popular': True},
    {'name': 'Chennai', 'icon': 'anchor', 'state': 'Tamil Nadu', 'popular': True},
    {'name': 'Kolkata', 'icon': 'tram', 'state': 'West Bengal', 'popular': True},
]

ALL_CITIES_LIST = [
    'Rajkot', 'Ahmedabad', 'Surat', 'Vadodara', 'Gandhinagar', 'Bhavnagar', 'Jamnagar', 'Junagadh',
    'Mumbai', 'Pune', 'Nagpur', 'Nashik',
    'Delhi-NCR', 'Noida', 'Gurugram', 'Faridabad',
    'Bengaluru', 'Mysuru', 'Mangaluru',
    'Hyderabad', 'Warangal',
    'Chennai', 'Coimbatore', 'Madurai',
    'Kolkata', 'Howrah',
    'Chandigarh', 'Jaipur', 'Udaipur', 'Indore', 'Bhopal', 'Lucknow', 'Kanpur', 'Patna', 'Kochi', 'Goa'
]

def city_context(request):
    """
    Global BookMyShow-style city and navigation context processor.
    Defaults active city to 'Rajkot' as requested, but seamlessly allows switching
    to any city via session, query parameters, or URL routing.
    """
    # 1. Determine active city
    active_city = request.session.get('selected_city')
    
    # Check if city is passed in GET params e.g. ?city=Rajkot
    get_city = request.GET.get('city')
    if get_city and get_city.strip():
        active_city = get_city.strip().title()
        request.session['selected_city'] = active_city

    # Check resolver kwargs if present e.g. /explore/home/<city>/
    if not active_city:
        if hasattr(request, 'resolver_match') and request.resolver_match:
            url_city = request.resolver_match.kwargs.get('city')
            if url_city:
                active_city = url_city.title()
                request.session['selected_city'] = active_city

    # Fallback to User profile city or default 'Rajkot'
    if not active_city:
        if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.city:
            active_city = request.user.profile.city.title()
        else:
            active_city = 'Rajkot'
        request.session['selected_city'] = active_city

    # 2. Get all distinct cities from DB merged with popular list
    try:
        db_cities = list(Turf.objects.values_list('city', flat=True).distinct())
    except Exception:
        db_cities = []

    combined_cities = sorted(list(set(ALL_CITIES_LIST + [c for c in db_cities if c])))

    # 3. Quick Sports list for BookMyShow category menu
    try:
        nav_sports = Sport.objects.all()[:8]
    except Exception:
        nav_sports = []

    return {
        'current_city': active_city,
        'current_city_lower': active_city.lower(),
        'popular_cities': POPULAR_CITIES,
        'all_cities_list': combined_cities,
        'nav_sports': nav_sports,
    }
