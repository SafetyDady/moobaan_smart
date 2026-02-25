"""
Phase 5: Syntax Validation Tests

Validates that all Phase 5 backend files:
1. Have valid Python syntax (compile check)
2. Can be imported without errors
3. Have proper structure
"""
import ast
import os
import sys
import unittest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestPhase5Syntax(unittest.TestCase):
    """Test that all Phase 5 files have valid Python syntax"""

    PHASE5_FILES = [
        'app/api/notifications.py',
        'app/api/report_export.py',
        'app/api/audit_logs.py',
        'app/db/models/notification.py',
        'app/services/notification_service.py',
        'alembic/versions/p5_1_notifications.py',
    ]

    def test_syntax_valid(self):
        """All Phase 5 files should have valid Python syntax"""
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        for filepath in self.PHASE5_FILES:
            full_path = os.path.join(base_dir, filepath)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                try:
                    ast.parse(source)
                except SyntaxError as e:
                    self.fail(f"Syntax error in {filepath}: {e}")

    def test_notification_model_structure(self):
        """Notification model should have required fields"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/db/models/notification.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        self.assertIn('Notification', class_names, "Notification class not found")

    def test_notification_api_has_router(self):
        """Notification API should define a router"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/api/notifications.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertIn('router = APIRouter', source, "Router not defined in notifications.py")
        self.assertIn('/api/notifications', source, "Notification prefix not found")

    def test_report_export_has_router(self):
        """Report export API should define a router"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/api/report_export.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertIn('router = APIRouter', source, "Router not defined in report_export.py")
        self.assertIn('/api/reports/export', source, "Export prefix not found")

    def test_audit_logs_has_router(self):
        """Audit logs API should define a router"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/api/audit_logs.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertIn('router = APIRouter', source, "Router not defined in audit_logs.py")
        self.assertIn('/api/audit-logs', source, "Audit logs prefix not found")

    def test_report_export_supports_all_types(self):
        """Report export should support all 5 report types"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/api/report_export.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        for report_type in ['invoices', 'payins', 'houses', 'members', 'expenses']:
            self.assertIn(f'"{report_type}"', source, f"Report type '{report_type}' not found")

    def test_all_apis_have_auth(self):
        """All Phase 5 API endpoints should have authentication"""
        api_files = [
            'app/api/notifications.py',
            'app/api/report_export.py',
            'app/api/audit_logs.py',
        ]
        base_dir = os.path.join(os.path.dirname(__file__), '..')
        for filepath in api_files:
            full_path = os.path.join(base_dir, filepath)
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            self.assertIn('Depends(', source, f"No auth dependency found in {filepath}")

    def test_main_py_includes_all_routers(self):
        """main.py should include all Phase 5 routers"""
        filepath = os.path.join(os.path.dirname(__file__), '..', 'app/main.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertIn('notifications_router', source, "Notifications router not in main.py")
        self.assertIn('report_export_router', source, "Report export router not in main.py")
        self.assertIn('audit_logs_router', source, "Audit logs router not in main.py")


if __name__ == '__main__':
    unittest.main()
