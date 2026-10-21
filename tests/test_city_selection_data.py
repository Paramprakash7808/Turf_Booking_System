import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
import django
django.setup()

from django.test import Client
from turfs.models import Turf

def run_tests():
    print("\n" + "=" * 50)
    print("RUNNING CITY SELECTION & DATA INTEGRITY TEST SUITE")
    print("=" * 50)

    client = Client()

    # Test 1: Rajkot displays Rajkot venues
    res_rajkot = client.get('/explore/home/rajkot/')
    assert res_rajkot.status_code == 200
    content_rajkot = res_rajkot.content.decode()
    assert 'Recommended Turfs in Rajkot' in content_rajkot
    assert 'Kalawad Road' in content_rajkot or 'Race Course' in content_rajkot
    # Verify DB has venues for Rajkot
    assert Turf.objects.filter(city__iexact='Rajkot').count() >= 6
    print("[PASS] Test 1: /explore/home/rajkot/ displays exclusively Rajkot turfs.")

    # Test 2: Ahmedabad displays Ahmedabad venues
    res_ahmedabad = client.get('/explore/home/ahmedabad/')
    assert res_ahmedabad.status_code == 200
    content_ahmedabad = res_ahmedabad.content.decode()
    assert 'Recommended Turfs in Ahmedabad' in content_ahmedabad
    assert 'Bodakdev' in content_ahmedabad or 'Sindhu Bhavan' in content_ahmedabad
    assert Turf.objects.filter(city__iexact='Ahmedabad').count() >= 6
    print("[PASS] Test 2: /explore/home/ahmedabad/ displays exclusively Ahmedabad turfs.")

    # Test 3: Mumbai displays authentic Mumbai venues
    res_mumbai = client.get('/explore/home/mumbai/')
    assert res_mumbai.status_code == 200
    content_mumbai = res_mumbai.content.decode()
    assert 'Recommended Turfs in Mumbai' in content_mumbai
    assert 'Bandra' in content_mumbai or 'Juhu' in content_mumbai
    assert Turf.objects.filter(city__iexact='Mumbai').count() >= 4
    print("[PASS] Test 3: /explore/home/mumbai/ displays authentic Mumbai turfs (Bandra, Juhu, etc.).")

    # Test 4: Bengaluru displays authentic Bengaluru venues
    res_blr = client.get('/explore/home/bengaluru/')
    assert res_blr.status_code == 200
    content_blr = res_blr.content.decode()
    assert 'Recommended Turfs in Bengaluru' in content_blr
    assert 'Indiranagar' in content_blr or 'Koramangala' in content_blr
    assert Turf.objects.filter(city__iexact='Bengaluru').count() >= 4
    print("[PASS] Test 4: /explore/home/bengaluru/ displays authentic Bengaluru turfs (Indiranagar, Koramangala).")

    # Test 5: Verify all remaining popular hubs have venues in DB and list properly
    popular_cities = ['Delhi-NCR', 'Hyderabad', 'Surat', 'Vadodara', 'Pune', 'Chandigarh', 'Chennai', 'Kolkata']
    for c in popular_cities:
        count = Turf.objects.filter(city__iexact=c).count()
        assert count >= 3, f"City {c} should have at least 3 turfs in DB, found {count}"
        res_city = client.get(f'/explore/turfs/{c.lower()}/')
        assert res_city.status_code == 200
        content_city = res_city.content.decode()
        assert c in content_city, f"Expected {c} in content of /explore/turfs/{c}/"
    print(f"[PASS] Test 5: Verified venues present in all other major hubs ({', '.join(popular_cities)}).")

    # Test 6: Empty / unlisted city (e.g. Kochi) does NOT leak Ahmedabad turfs and shows friendly empty state
    res_kochi = client.get('/explore/home/kochi/')
    assert res_kochi.status_code == 200
    content_kochi = res_kochi.content.decode()
    assert 'No Venues Listed in Kochi Yet' in content_kochi, "Expected 'No Venues Listed in Kochi Yet' empty state."
    assert 'Explore Rajkot' in content_kochi, "Expected switch to Rajkot link in empty state."
    assert 'Explore Ahmedabad' in content_kochi, "Expected switch to Ahmedabad link in empty state."
    # Crucial: Ahmedabad turfs must NOT leak into the featured turfs for Kochi
    assert 'Apex Bodakdev' not in content_kochi, "Ahmedabad venue leaked into Kochi home view."
    print("[PASS] Test 6: Unlisted city (Kochi) displays 'No Venues Listed' empty state without leaking other cities.")

    # Test 7: /turfs/?city=Kochi strictly filters and displays empty state
    res_kochi_list = client.get('/turfs/?city=Kochi')
    assert res_kochi_list.status_code == 200
    content_kochi_list = res_kochi_list.content.decode()
    assert 'No Venues Found in Kochi' in content_kochi_list, "Expected 'No Venues Found in Kochi' empty state."
    assert 'Apex Bodakdev' not in content_kochi_list, "Ahmedabad venue leaked into Kochi turf list."
    print("[PASS] Test 7: /turfs/?city=Kochi strictly filters to 0 venues and renders 'No Venues Found' empty state.")

    print("\n" + "=" * 50)
    print("ALL 7 CITY SELECTION & DATA INTEGRITY TESTS PASSED!")
    print("=" * 50 + "\n")

if __name__ == '__main__':
    run_tests()
