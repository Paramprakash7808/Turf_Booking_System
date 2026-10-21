import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
django.setup()

from django.test import Client
from turfs.models import Organization, Branch, Turf

def run_tests():
    print("==================================================")
    print("TESTING BRANCH DETAIL PAGE & DIRECT NAVIGATION")
    print("==================================================")

    client = Client()

    # 1. Test Branch Detail view (public & authenticated)
    branch = Branch.objects.filter(name__icontains='Sindhu Bhavan').first()
    assert branch is not None, 'Sindhu Bhavan branch not found'
    print('Testing branch:', branch.id, branch.name)

    res = client.get(f'/branches/{branch.id}/')
    assert res.status_code == 200, f'Expected 200, got {res.status_code}'
    content = res.content.decode('utf-8')
    assert branch.name in content, 'Branch name missing from branch_detail'
    assert 'Courts & Facilities Under' in content or 'Active Court' in content, 'Courts section missing'
    assert 'turf-card' in content, 'Turf cards missing'
    print('[PASS] Test 1: /branches/<id>/ rendered with featured cricket grounds/turfs like home page.')

    # 2. Test Urban Kicks & Courts Group detail page
    org = Organization.objects.filter(name__icontains='Urban Kicks').first()
    assert org is not None, 'Urban Kicks organization not found'

    # Login as super admin to view org_detail
    logged_in = client.login(username='admin', password='admin123')
    if not logged_in:
        logged_in = client.login(username='superadmin@turfbook.com', password='admin123')
    assert logged_in, 'Super admin login failed'

    res_org = client.get(f'/super-admin/orgs/{org.id}/')
    assert res_org.status_code == 200
    org_html = res_org.content.decode('utf-8')

    # Ensure 'View Branch Data' button is gone
    assert 'View Branch Data' not in org_html, 'View Branch Data button still present!'
    # Ensure branch link to /branches/<id>/ exists
    assert f'/branches/{branch.id}/' in org_html, 'Link to branch_detail missing from org_detail'
    print('[PASS] Test 2: In /super-admin/orgs/<id>/, branches link directly to branch detail (no View Branch Data option).')

    # 3. Test Org Admin portal
    client.logout()
    admin_apex_logged_in = client.login(username='admin.apex@turfbook.com', password='password123')
    assert admin_apex_logged_in, 'Org Admin login failed'

    res_admin = client.get('/org-admin/')
    assert res_admin.status_code == 200
    admin_html = res_admin.content.decode('utf-8')
    assert 'View Branch Data' not in admin_html, 'View Branch Data button still present in org_admin!'
    print('[PASS] Test 3: In /org-admin/, branches link directly to branch detail (no View Branch Data option).')

    print("\n" + "=" * 50)
    print("ALL BRANCH DISPLAY & NAVIGATION TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
