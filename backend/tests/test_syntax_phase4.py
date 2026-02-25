"""
Phase 4: Syntax validation for all modified backend files.
Ensures no import errors or syntax issues.
"""
import ast
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, BACKEND_DIR)

MODIFIED_FILES = [
    'app/core/pagination.py',
    'app/api/invoices.py',
    'app/api/payins.py',
    'app/api/houses.py',
    'app/api/members.py',
    'app/api/expenses_v2.py',
    'app/api/health.py',
]


def test_syntax():
    """Verify all modified files have valid Python syntax"""
    errors = []
    for filepath in MODIFIED_FILES:
        full_path = os.path.join(BACKEND_DIR, filepath)
        if not os.path.exists(full_path):
            errors.append(f"❌ {filepath}: FILE NOT FOUND")
            continue
        try:
            with open(full_path, 'r') as f:
                source = f.read()
            ast.parse(source)
            print(f"✅ {filepath}: syntax OK")
        except SyntaxError as e:
            errors.append(f"❌ {filepath}: {e}")
    
    if errors:
        print("\n--- ERRORS ---")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\n🎉 All files have valid syntax!")


def test_pagination_imports():
    """Verify pagination utility is importable"""
    from app.core.pagination import paginate_list, paginate_query, PaginatedResponse
    assert callable(paginate_list)
    assert callable(paginate_query)
    print("✅ pagination imports OK")


def test_health_imports():
    """Verify health module structure"""
    full_path = os.path.join(BACKEND_DIR, 'app/api/health.py')
    with open(full_path, 'r') as f:
        source = f.read()
    
    # Check key function definitions exist
    assert 'def health_check' in source
    assert 'def readiness_check' in source
    assert 'def system_status' in source
    assert '/api/system/status' in source
    print("✅ health.py structure OK")


def test_blocking_check_endpoint():
    """Verify blocking-check endpoint exists in payins.py"""
    full_path = os.path.join(BACKEND_DIR, 'app/api/payins.py')
    with open(full_path, 'r') as f:
        source = f.read()
    
    assert '/blocking-check' in source
    assert 'def check_blocking_payin' in source
    assert 'has_blocking' in source
    assert 'blocking_payin' in source
    print("✅ payins.py blocking-check endpoint OK")


def test_pagination_params_in_endpoints():
    """Verify all list endpoints have page/page_size params"""
    endpoints = {
        'app/api/invoices.py': 'list_invoices',
        'app/api/payins.py': 'list_payin_reports',
        'app/api/houses.py': 'list_houses',
        'app/api/members.py': 'list_members',
        'app/api/expenses_v2.py': 'list_expenses',
    }
    
    for filepath, func_name in endpoints.items():
        full_path = os.path.join(BACKEND_DIR, filepath)
        with open(full_path, 'r') as f:
            source = f.read()
        
        assert f'def {func_name}' in source, f"{filepath}: missing {func_name}"
        assert 'page: Optional[int]' in source, f"{filepath}: missing page param"
        assert 'page_size: int' in source, f"{filepath}: missing page_size param"
        assert 'paginate_' in source, f"{filepath}: missing paginate_ call"
        print(f"✅ {filepath}: pagination params OK")


if __name__ == "__main__":
    test_syntax()
    test_pagination_imports()
    test_health_imports()
    test_blocking_check_endpoint()
    test_pagination_params_in_endpoints()
    print("\n🎉 All Phase 4 validation tests passed!")
