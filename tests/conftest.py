def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end test.")
    config.addinivalue_line("markers", "no_nox: skip test on nox.")
