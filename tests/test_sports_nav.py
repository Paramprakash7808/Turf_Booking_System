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

def run_tests():
    print("==================================================")
    print("TESTING SPORTS NAVBAR LINK & FILTERING")
    print("==================================================")

    client = Client()

    # TEST 1: Navbar sports link
    response = client.get('/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'href="/sports/"' in content or 'href="/sports"' in content, "Sports navbar link missing"
    assert 'sportsDropdownMenu' not in content, "VIOLATION: sportsDropdownMenu still present in navbar"
    assert 'sportsDropdownBtn' not in content, "VIOLATION: sportsDropdownBtn still present in navbar"
    print("[PASS] Test 1: In navbar, Sports is a direct link (no dropdown, no submenu).")

    # TEST 2: /sports/ page renders all sports and filter sidebar
    response = client.get('/sports/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Cricket' in content
    assert 'Football' in content
    assert 'Pickleball' in content
    assert 'Paddleball' in content
    assert 'name="sport"' in content, "Missing sport filter dropdown in sidebar"
    print("[PASS] Test 2: /sports/ displays all sports categories and the filter sidebar.")

    # TEST 3: Filter by cricket
    response = client.get('/sports/?sport=cricket')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Green Field Cricket Academy' in content
    print("[PASS] Test 3: /sports/?sport=cricket displays filtered cricket venues.")

    # TEST 4: Filter by football
    response = client.get('/sports/?sport=football')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Urban Kicks Football Turf' in content
    print("[PASS] Test 4: /sports/?sport=football displays filtered football venues.")

    # TEST 5: Filter by pickleball
    response = client.get('/sports/?sport=pickleball')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'Ace Pickleball Arena' in content
    print("[PASS] Test 5: /sports/?sport=pickleball displays filtered pickleball venues.")

    print("\n" + "=" * 50)
    print("ALL 5 SPORTS NAVIGATION & FILTER TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
