"""Pytest configuration."""

import pytest
from models.invoice import SellerProfile
import services.seller_store as seller_store

# Pre-seed a demo seller profile for all test session IDs used in the test suite.
# This prevents existing tests from hitting the setup flow instead of the invoice flow.
_TEST_PROFILE = SellerProfile(name="Test Seller Pvt Ltd", gstin="27AADCB2230M1ZT")
_TEST_SESSION_IDS = ["test-1", "test-2", "test-3", "test-4", "test-5",
                     "test-6", "test-7", "test-8", "test-9"]


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: tests that call real external APIs")
    for sid in _TEST_SESSION_IDS:
        seller_store.save(sid, _TEST_PROFILE)
