"""Repeatable Local-only Phase 1 verification; no production configuration used.

Set CREDIT_TEST_DATABASE_URL to local PostgreSQL database moobaan_credit_test.
Run: python -B run_payin_integrity_checks.py --results <local-result.json>
"""
import argparse
import importlib
import inspect
import json
import logging
import os
import unittest
from pathlib import Path
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path)
    args = parser.parse_args()
    raw = os.environ.get('CREDIT_TEST_DATABASE_URL', '')
    url = make_url(raw)
    if (url.get_backend_name() != 'postgresql' or url.host not in ('localhost', '127.0.0.1')
            or url.database != 'moobaan_credit_test'):
        raise RuntimeError('Only localhost/moobaan_credit_test is allowed')
    # Override app configuration before importing any app/test module.
    os.environ['DATABASE_URL'] = raw
    os.environ['ENV'] = 'local'
    os.environ['OTP_PROVIDER'] = 'mock'
    for key in ('R2_ENDPOINT', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME'):
        os.environ[key] = ''
    logging.disable(logging.CRITICAL)
    suite = unittest.TestSuite()
    counts = {}
    modules = ['test_payin_integrity_postgres', 'test_credit_settlement_postgres',
               'test_automatic_allocation_postgres', 'test_accounting_reads_postgres',
               'test_r2_postgres', 'test_invoice_read_access_postgres']
    for name in modules:
        module = importlib.import_module(name)
        counts[name] = 0
        for cls in vars(module).values():
            if inspect.isclass(cls) and issubclass(cls, unittest.TestCase) and cls.__module__ == name:
                cases = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                counts[name] += cases.countTestCases()
                suite.addTests(cases)
    for name in ['test_invoice_paid_at', 'test_invoice_settlement_status', 'test_report_export']:
        module = importlib.import_module(name)
        functions = [fn for key, fn in vars(module).items() if key.startswith('test_') and inspect.isfunction(fn)]
        counts[name] = len(functions)
        suite.addTests(unittest.FunctionTestCase(fn) for fn in functions)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    report = dict(passed=result.wasSuccessful(), total=result.testsRun,
                  counts=counts, failures=len(result.failures), errors=len(result.errors),
                  local_only=True, synthetic_data=True)
    if args.results:
        args.results.parent.mkdir(parents=True, exist_ok=True)
        args.results.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
