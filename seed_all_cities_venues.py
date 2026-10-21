import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.utils.text import slugify
from turfs.models import Turf, Sport, Amenity, Organization, Branch

def seed_all_cities():
    print("Seeding dummy turfs for all cities in POPULAR_CITIES...")

    # Get sports
    cricket = Sport.objects.filter(slug='cricket').first()
    football = Sport.objects.filter(slug='football').first()
    pickleball = Sport.objects.filter(slug='pickleball').first()
    paddleball = Sport.objects.filter(slug='paddleball').first()
    all_sports = list(Sport.objects.all())

    # Get amenities
    amenities = list(Amenity.objects.all())

    # Organizations
    apex_org = Organization.objects.filter(name__icontains='Apex').first()
    urban_org = Organization.objects.filter(name__icontains='Urban').first()
    saurashtra_org = Organization.objects.filter(name__icontains='Saurashtra').first()
    default_org = apex_org or urban_org or saurashtra_org

    # Venue Data Dictionary
    CITY_VENUES = [
        # MUMBAI
        {
            'city': 'Mumbai',
            'venues': [
                {
                    'name': 'Bandra Kickoff Astro Arena',
                    'location': 'Bandra West, Mumbai',
                    'address': 'Near Carter Road Promenade, Bandra West, Mumbai 400050',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket, pickleball],
                    'price': 1400.0,
                    'rating': 4.9,
                    'rating_count': 142,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'Premier FIFA-grade synthetic turf situated in heart of Bandra West with marine breeze and international lighting.'
                },
                {
                    'name': 'Juhu Beachside Sports Club',
                    'location': 'Juhu, Mumbai',
                    'address': 'Opposite Juhu Beach, J.W. Marriott Lane, Juhu, Mumbai 400049',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, paddleball],
                    'price': 1500.0,
                    'rating': 4.8,
                    'rating_count': 118,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Iconic Mumbai seaside box cricket and football facility with premium lounge and night floodlighting.'
                },
                {
                    'name': 'Powai Central Multi-Turf Hub',
                    'location': 'Hiranandani Gardens, Powai, Mumbai',
                    'address': 'High Street, Hiranandani Gardens, Powai, Mumbai 400076',
                    'sport': football or all_sports[0],
                    'secondary_sports': [pickleball],
                    'price': 1300.0,
                    'rating': 4.7,
                    'rating_count': 94,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
                    'description': 'Spacious multi-sport arena serving Powai with European shock-pad grass, locker rooms, and coaching facilities.'
                },
                {
                    'name': 'Andheri West Pro Sports Turf',
                    'location': 'Lokhandwala, Andheri West, Mumbai',
                    'address': 'Back Road, Lokhandwala Complex, Andheri West, Mumbai 400053',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football],
                    'price': 1200.0,
                    'rating': 4.8,
                    'rating_count': 160,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=800&q=80',
                    'description': 'High-rebound box cricket and 5-a-side football court with ultra-bright LED towers and player cafeteria.'
                }
            ]
        },

        # DELHI-NCR
        {
            'city': 'Delhi-NCR',
            'venues': [
                {
                    'name': 'Gurugram CyberHub Champions Turf',
                    'location': 'Cyber City, Gurugram, Delhi-NCR',
                    'address': 'DLF Phase 2, Adjacent CyberHub, Gurugram 122002',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket, pickleball],
                    'price': 1500.0,
                    'rating': 4.9,
                    'rating_count': 156,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=800&q=80',
                    'description': 'Top-tier corporate and club sporting complex featuring all-weather turf and corporate tournament facilities.'
                },
                {
                    'name': 'Saket South Delhi Football Ground',
                    'location': 'Saket, Delhi-NCR',
                    'address': 'Near Select CityWalk, Saket District Centre, New Delhi 110017',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1400.0,
                    'rating': 4.8,
                    'rating_count': 130,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=800&q=80',
                    'description': 'Expansive South Delhi 7v7 and 5v5 football arena with full perimeter netting and pro player benches.'
                },
                {
                    'name': 'Noida Sector 62 Astro Park',
                    'location': 'Sector 62, Noida, Delhi-NCR',
                    'address': 'Electronic City Road, Sector 62, Noida 201309',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [paddleball, football],
                    'price': 1100.0,
                    'rating': 4.7,
                    'rating_count': 88,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'High-density synthetic grass complex offering high-speed box cricket matches and corporate night leagues.'
                },
                {
                    'name': 'Vasant Kunj Elite Arena',
                    'location': 'Vasant Kunj, Delhi-NCR',
                    'address': 'Pocket 2, Sector B, Vasant Kunj, New Delhi 110070',
                    'sport': pickleball or all_sports[0],
                    'secondary_sports': [cricket, football],
                    'price': 1300.0,
                    'rating': 4.8,
                    'rating_count': 104,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1626248801379-51a0748a5f96?auto=format&fit=crop&w=800&q=80',
                    'description': 'Premier pickleball and cricket sports enclave in Vasant Kunj with air-conditioned lounge and showers.'
                }
            ]
        },

        # BENGALURU
        {
            'city': 'Bengaluru',
            'venues': [
                {
                    'name': 'Indiranagar Premier Turf Arena',
                    'location': '100 Feet Road, Indiranagar, Bengaluru',
                    'address': 'HAL 2nd Stage, Indiranagar, Bengaluru 560038',
                    'sport': football or all_sports[0],
                    'secondary_sports': [pickleball, cricket],
                    'price': 1450.0,
                    'rating': 4.9,
                    'rating_count': 175,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'Bengaluru central hub for 5-a-side football and weekend box cricket leagues with premium acoustic turf.'
                },
                {
                    'name': 'Koramangala Smashers & Kickers',
                    'location': 'Koramangala 4th Block, Bengaluru',
                    'address': '80 Feet Road, Koramangala 4th Block, Bengaluru 560034',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, pickleball],
                    'price': 1350.0,
                    'rating': 4.8,
                    'rating_count': 148,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Vibrant Koramangala community sports facility with LED stadium towers, juice bar, and changing rooms.'
                },
                {
                    'name': 'Whitefield Tech Sports Park',
                    'location': 'ITPL Main Road, Whitefield, Bengaluru',
                    'address': 'Near Hope Farm Junction, Whitefield, Bengaluru 560066',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1200.0,
                    'rating': 4.7,
                    'rating_count': 112,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
                    'description': 'Large-scale synthetic surface arena serving tech corridors of Whitefield with abundant parking.'
                },
                {
                    'name': 'HSR Layout Astro Court',
                    'location': 'Sector 2, HSR Layout, Bengaluru',
                    'address': '27th Main Road, Sector 2, HSR Layout, Bengaluru 560102',
                    'sport': pickleball or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1250.0,
                    'rating': 4.8,
                    'rating_count': 92,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1626248801379-51a0748a5f96?auto=format&fit=crop&w=800&q=80',
                    'description': 'Dedicated professional pickleball and compact cricket courts in HSR Layout with automated booking.'
                }
            ]
        },

        # HYDERABAD
        {
            'city': 'Hyderabad',
            'venues': [
                {
                    'name': 'Gachibowli Titans Sports Hub',
                    'location': 'Financial District, Gachibowli, Hyderabad',
                    'address': 'Near Wipro Circle, Gachibowli, Hyderabad 500032',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket, pickleball],
                    'price': 1300.0,
                    'rating': 4.9,
                    'rating_count': 135,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=800&q=80',
                    'description': 'State-of-the-art arena in Hyderabad Financial District with international standard turf and live scores.'
                },
                {
                    'name': 'HITEC City Box Cricket Arena',
                    'location': 'Madhapur, HITEC City, Hyderabad',
                    'address': 'Behind Inorbit Mall, Madhapur, Hyderabad 500081',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football],
                    'price': 1200.0,
                    'rating': 4.8,
                    'rating_count': 164,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Popular floodlit box cricket venue with premium grass, boundary netting, and spectator bleachers.'
                },
                {
                    'name': 'Jubilee Hills Sports Pavilion',
                    'location': 'Road No. 36, Jubilee Hills, Hyderabad',
                    'address': 'Jubilee Hills Road 36, Hyderabad 500033',
                    'sport': football or all_sports[0],
                    'secondary_sports': [pickleball],
                    'price': 1400.0,
                    'rating': 4.8,
                    'rating_count': 98,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=800&q=80',
                    'description': 'Exclusive sports facility offering pristine turf courts, luxury shower facilities, and cafe.'
                }
            ]
        },

        # SURAT
        {
            'city': 'Surat',
            'venues': [
                {
                    'name': 'Vesu Diamond City Sports Turf',
                    'location': 'VIP Road, Vesu, Surat',
                    'address': 'Opposite Shyam Mandir, VIP Road, Vesu, Surat 395007',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, pickleball],
                    'price': 1100.0,
                    'rating': 4.9,
                    'rating_count': 152,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Surats premier all-weather cricket turf with lush green synthetic surface and bright evening lights.'
                },
                {
                    'name': 'Piplod Riverview Astro Arena',
                    'location': 'Dumas Road, Piplod, Surat',
                    'address': 'Near VR Mall, Dumas Road, Piplod, Surat 395007',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1000.0,
                    'rating': 4.8,
                    'rating_count': 120,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'Spacious multi-sport arena near VR Mall offering high-rebound turf and comfortable player seating.'
                },
                {
                    'name': 'Adajan Champions Ground',
                    'location': 'LP Savani Road, Adajan, Surat',
                    'address': 'Near LP Savani Circle, Adajan, Surat 395009',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [pickleball],
                    'price': 950.0,
                    'rating': 4.7,
                    'rating_count': 98,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
                    'description': 'Affordable and top-maintained box cricket destination with equipment rental and ample parking.'
                }
            ]
        },

        # VADODARA
        {
            'city': 'Vadodara',
            'venues': [
                {
                    'name': 'Alkapuri Heritage Sports Turf',
                    'location': 'RC Dutt Road, Alkapuri, Vadodara',
                    'address': 'Near Alkapuri Club, RC Dutt Road, Vadodara 390007',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, pickleball],
                    'price': 1050.0,
                    'rating': 4.9,
                    'rating_count': 128,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Centrally located luxury turf court in Alkapuri, offering non-marking synthetic turf and chilled amenities.'
                },
                {
                    'name': 'Gotri Green Field Arena',
                    'location': 'Gotri Road, Vadodara',
                    'address': 'Opposite Yash Complex, Gotri Road, Vadodara 390021',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 950.0,
                    'rating': 4.8,
                    'rating_count': 110,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'High-spec synthetic turf for fast-paced football games and community cricket tournaments.'
                },
                {
                    'name': 'Vasna Sports Enclave',
                    'location': 'Vasna-Bhayli Road, Vadodara',
                    'address': 'Near Waves Club, Vasna-Bhayli Road, Vadodara 391410',
                    'sport': pickleball or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 900.0,
                    'rating': 4.7,
                    'rating_count': 84,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1626248801379-51a0748a5f96?auto=format&fit=crop&w=800&q=80',
                    'description': 'Fresh open-air court facility specializing in pickleball and youth sports leagues in Bhayli.'
                }
            ]
        },

        # PUNE
        {
            'city': 'Pune',
            'venues': [
                {
                    'name': 'Koregaon Park Astro Arena',
                    'location': 'North Main Road, Koregaon Park, Pune',
                    'address': 'Lane 5, North Main Road, Koregaon Park, Pune 411001',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket, pickleball],
                    'price': 1300.0,
                    'rating': 4.9,
                    'rating_count': 146,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'Punes most popular football and cricket hub in KP, with lush canopy and high-intensity LED floodlights.'
                },
                {
                    'name': 'Baner High-Street Sports Turf',
                    'location': 'Baner Road, Pune',
                    'address': 'Behind Balewadi High Street, Baner, Pune 411045',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football],
                    'price': 1200.0,
                    'rating': 4.8,
                    'rating_count': 134,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Top-choice sports turf for IT professionals near Balewadi, with showers and online instant booking.'
                },
                {
                    'name': 'Viman Nagar PlayZone Turf',
                    'location': 'Viman Nagar, Pune',
                    'address': 'Near Phoenix Marketcity, Viman Nagar, Pune 411014',
                    'sport': football or all_sports[0],
                    'secondary_sports': [paddleball],
                    'price': 1150.0,
                    'rating': 4.7,
                    'rating_count': 98,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
                    'description': 'Energetic sports zone near the airport corridor with high safety netting and cafeteria.'
                }
            ]
        },

        # CHANDIGARH
        {
            'city': 'Chandigarh',
            'venues': [
                {
                    'name': 'Sector 17 City Center Pro Turf',
                    'location': 'Sector 17, Chandigarh',
                    'address': 'Near Parade Ground, Sector 17, Chandigarh 160017',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, pickleball],
                    'price': 1100.0,
                    'rating': 4.9,
                    'rating_count': 114,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Centrally situated synthetic court in Sector 17 with tournament-ready pitch and change facilities.'
                },
                {
                    'name': 'Mohali Stadium Turf Complex',
                    'location': 'Phase 7, Mohali, Chandigarh',
                    'address': 'Near PCA Stadium, Phase 7, Mohali, Punjab 160062',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1200.0,
                    'rating': 4.8,
                    'rating_count': 140,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'World-class astro turf in Mohali for aspiring cricketers and soccer players with evening lighting.'
                },
                {
                    'name': 'Panchkula Elite Sports Arena',
                    'location': 'Sector 5, Panchkula, Chandigarh',
                    'address': 'Near Town Park, Sector 5, Panchkula, Haryana 134109',
                    'sport': pickleball or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1050.0,
                    'rating': 4.7,
                    'rating_count': 82,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1626248801379-51a0748a5f96?auto=format&fit=crop&w=800&q=80',
                    'description': 'Family-friendly sports complex with modern pickleball courts and indoor badminton facilities.'
                }
            ]
        },

        # CHENNAI
        {
            'city': 'Chennai',
            'venues': [
                {
                    'name': 'OMR Express Champions Turf',
                    'location': 'Thoraipakkam, OMR, Chennai',
                    'address': 'IT Expressway, Thoraipakkam, Chennai 600097',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket, pickleball],
                    'price': 1250.0,
                    'rating': 4.9,
                    'rating_count': 138,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=800&q=80',
                    'description': 'Premier IT corridor sports court along OMR featuring international monofilament grass.'
                },
                {
                    'name': 'Nungambakkam Box Cricket Club',
                    'location': 'Nungambakkam High Road, Chennai',
                    'address': 'Opposite Taj Coromandel, Nungambakkam, Chennai 600034',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football],
                    'price': 1300.0,
                    'rating': 4.8,
                    'rating_count': 122,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Central Chennai premier venue for weekend box cricket matches and night tournaments.'
                },
                {
                    'name': 'Anna Nagar Sports Arena',
                    'location': '2nd Avenue, Anna Nagar, Chennai',
                    'address': 'Near Roundana, Anna Nagar East, Chennai 600102',
                    'sport': football or all_sports[0],
                    'secondary_sports': [pickleball],
                    'price': 1150.0,
                    'rating': 4.7,
                    'rating_count': 96,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=800&q=80',
                    'description': 'Well-lit artificial grass turf with dedicated coaching programs and comfortable player dugout.'
                }
            ]
        },

        # KOLKATA
        {
            'city': 'Kolkata',
            'venues': [
                {
                    'name': 'Salt Lake Kickers Arena',
                    'location': 'Sector V, Salt Lake, Kolkata',
                    'address': 'Near College More, Sector V, Salt Lake, Kolkata 700091',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1150.0,
                    'rating': 4.9,
                    'rating_count': 160,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80',
                    'description': 'Passion-fueled Kolkata soccer and cricket turf in Sector V tech hub with professional coaching staff.'
                },
                {
                    'name': 'New Town Eco-Sports Park',
                    'location': 'Action Area 1, New Town, Kolkata',
                    'address': 'Near Eco Park Gate 2, New Town, Kolkata 700156',
                    'sport': cricket or all_sports[0],
                    'secondary_sports': [football, pickleball],
                    'price': 1200.0,
                    'rating': 4.8,
                    'rating_count': 130,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
                    'description': 'Scenic sports arena adjacent to Eco Park with high-speed synthetic outfield and cafeteria.'
                },
                {
                    'name': 'Park Street Heritage Turf',
                    'location': 'Park Street, Kolkata',
                    'address': 'Near Mullick Bazaar, Park Street, Kolkata 700016',
                    'sport': football or all_sports[0],
                    'secondary_sports': [cricket],
                    'price': 1100.0,
                    'rating': 4.7,
                    'rating_count': 102,
                    'is_featured': True,
                    'image': 'https://images.unsplash.com/photo-1529900748604-07564a03e7a6?auto=format&fit=crop&w=800&q=80',
                    'description': 'Central Kolkata box cricket & football court equipped with player locker rooms and water stations.'
                }
            ]
        }
    ]

    total_added = 0
    for city_data in CITY_VENUES:
        city_name = city_data['city']
        for v in city_data['venues']:
            base_slug = slugify(f"{v['name']}-{city_name}")
            slug = base_slug
            counter = 1
            while Turf.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            turf, created = Turf.objects.get_or_create(
                name=v['name'],
                city=city_name,
                defaults={
                    'slug': slug,
                    'location': v['location'],
                    'address': v['address'],
                    'price_per_hour': v['price'],
                    'primary_sport': v['sport'],
                    'rating': v['rating'],
                    'rating_count': v['rating_count'],
                    'is_featured': v['is_featured'],
                    'image_url': v['image'],
                    'description': v['description'],
                    'organization': default_org,
                }
            )

            if created:
                total_added += 1
                # Add sports
                sports_to_add = [v['sport']] + [s for s in v['secondary_sports'] if s]
                turf.sports.set(sports_to_add)
                # Add sample amenities
                if amenities:
                    turf.amenities.set(amenities[:5])
                print(f"[CREATED] {turf.name} ({city_name}) - Rs.{turf.price_per_hour}")
            else:
                print(f"[EXISTS] {turf.name} ({city_name})")

    print(f"\nDone! Added {total_added} new realistic venues across all popular cities.")

if __name__ == '__main__':
    seed_all_cities()
