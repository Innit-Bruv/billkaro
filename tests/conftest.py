"""Pytest configuration."""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: tests that call real external APIs")
