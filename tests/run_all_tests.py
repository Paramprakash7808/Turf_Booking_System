"""
Master test runner to execute all test modules inside the tests/ directory.
Usage:
    python tests/run_all_tests.py
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tests.test_validation_rules import run_tests as test_validation
from tests.test_roles_auth import run_tests as test_auth
from tests.test_superadmin_role_staff import run_tests as test_superadmin
from tests.test_branch_crud import run_tests as test_branch
from tests.test_sports_nav import run_tests as test_sports
from tests.test_profile_section import run_tests as test_profile
from tests.test_superadmin_org_crud import run_tests as test_org_crud
from tests.test_branch_display import run_tests as test_branch_display
from tests.test_responsiveness import run_tests as test_responsiveness
from tests.test_payment_methods import run_tests as test_payments
from tests.test_city_selection_data import run_tests as test_city_data
from tests.test_env_credentials_logging import run_tests as test_env_logging

def main():
    test_suites = [
        ("Input Validation Rules Suite", test_validation),
        ("Role Hierarchy & Auth Suite", test_auth),
        ("Super Admin & Staff Suite", test_superadmin),
        ("Branch CRUD & Security Suite", test_branch),
        ("Organization CRUD & Security Suite", test_org_crud),
        ("Sports Navigation & Filter Suite", test_sports),
        ("User Profile & Avatar Suite", test_profile),
        ("Branch Display & Direct Navigation Suite", test_branch_display),
        ("Platform Responsiveness Suite", test_responsiveness),
        ("Payment Methods (Razorpay & Cash) Suite", test_payments),
        ("City Selection & Data Integrity Suite", test_city_data),
        ("Environment Credentials (.env) Persistence Suite", test_env_logging),
    ]

    print("\n" + "#" * 60)
    print("STARTING FULL TURFBOOK AUTOMATED TEST RUNNER")
    print("#" * 60 + "\n")

    passed = 0
    failed = 0

    for name, suite in test_suites:
        try:
            print(f"\n>>> Running: {name}")
            suite()
            passed += 1
        except Exception as e:
            print(f"[FAIL] Error in {name}: {e}")
            failed += 1

    print("\n" + "#" * 60)
    print(f"SUMMARY: {passed}/{len(test_suites)} test suites passed successfully! (Failed: {failed})")
    print("#" * 60 + "\n")

    if failed > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
