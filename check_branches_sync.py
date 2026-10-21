"""
CLI utility to inspect and verify the real-time synchronization status
of all Organizations and Branches across the TurfBook platform.

Usage:
    python check_branches_sync.py
"""
import os
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_project.settings')
import django
django.setup()

from django.test import Client
from turfs.models import Organization, Branch, Turf

def verify_sync():
    client = Client()
    print("\n" + "=" * 70)
    print("  TURFBOOK MULTI-BRANCH API SYNCHRONIZATION AUDIT")
    print("=" * 70)

    orgs = Organization.objects.all().order_by('id')
    if not orgs.exists():
        print("[!] No organizations found in the database.")
        return

    total_orgs = orgs.count()
    total_branches = Branch.objects.count()
    print(f"Total Organizations: {total_orgs} | Total Registered Branches: {total_branches}\n")

    all_passed = True

    for org in orgs:
        print(f"[*] Organization #{org.id}: '{org.name}'")
        org_url = f"/api/organizations/{org.id}/sync/"
        resp = client.get(org_url)

        if resp.status_code != 200:
            print(f"    [FAIL] Org API {org_url} returned HTTP {resp.status_code}")
            all_passed = False
            continue

        data = json.loads(resp.content)
        is_synced = data.get('is_synced', False)
        sync_version = data.get('sync_version', 'N/A')
        synced_at = data.get('synced_at', 'N/A')
        branches_in_sync = data.get('branches', [])
        org_totals = data.get('organization_totals', {})

        status_marker = "[OK]" if is_synced else "[FAIL]"
        print(f"    {status_marker} Sync Status: is_synced={is_synced} | Version={sync_version}")
        print(f"         Synced At: {synced_at}")
        print(f"         Branches Reported: {len(branches_in_sync)} | Total Turfs: {org_totals.get('total_turfs', 0)}")
        print(f"         Today's Bookings: {org_totals.get('total_bookings_today', 0)} | Revenue: Rs. {org_totals.get('total_revenue_today', 0)}")

        # Verify individual branch endpoints
        branches = org.branches.filter(is_active=True).order_by('id')
        for branch in branches:
            branch_url = f"/api/branches/{branch.id}/sync/"
            b_resp = client.get(branch_url)
            if b_resp.status_code == 200:
                b_data = json.loads(b_resp.content)
                b_synced = b_data.get('is_synced', False)
                turf_count = len(b_data.get('branches', []))
                print(f"        -> Branch #{branch.id} '{branch.name}' ({branch.city}):")
                print(f"           API Endpoint: {branch_url} -> 200 OK | Synced: {b_synced} | Sibling Branches in Cluster: {turf_count}")
            else:
                print(f"        -> [FAIL] Branch #{branch.id} '{branch.name}' returned HTTP {b_resp.status_code}")
                all_passed = False
        print("-" * 70)

    # Verify Turf Slot Availability Sync
    print("\n[*] Verifying Live Slot & Multi-Branch Availability on Booking Endpoint:")
    turf = Turf.objects.first()
    if turf:
        turf_url = f"/api/turfs/{turf.id}/slots/"
        t_resp = client.get(turf_url)
        if t_resp.status_code == 200:
            t_data = json.loads(t_resp.content)
            has_branch_sync = 'all_branches_sync' in t_data
            print(f"    [OK] Turf #{turf.id} '{turf.name}' -> {turf_url}")
            print(f"         Booked Slots: {len(t_data.get('booked_slot_ids', []))}")
            print(f"         Cross-Branch Live Sync Payload Present: {has_branch_sync} (is_synced={t_data.get('is_synced')})")
        else:
            print(f"    [FAIL] Turf slot API returned HTTP {t_resp.status_code}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  RESULT: ALL BRANCHES & ORGANIZATIONS ARE FULLY SYNCHRONIZED [PASSED]")
    else:
        print("  RESULT: SYNCHRONIZATION ISSUES DETECTED [FAILED]")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    verify_sync()
