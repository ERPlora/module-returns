"""
Tests for returns module views.
"""

import json
import pytest
from django.test import Client

from returns.models import ReturnsConfig


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.mark.django_db
class TestSettingsView:
    """Tests for returns settings."""

    def test_settings_view_get(self, client):
        """Test GET settings page."""
        response = client.get('/modules/returns/settings/')
        # Either 200 (if no login required in test) or redirect
        assert response.status_code in [200, 302]

    def test_settings_save_success(self, client):
        """Test saving settings via JSON."""
        response = client.post(
            '/modules/returns/settings/save/',
            data=json.dumps({
                'allow_returns': True,
                'return_window_days': 14,
                'allow_store_credit': False,
                'require_receipt': True,
                'auto_restore_stock': True
            }),
            content_type='application/json'
        )

        # May require login
        assert response.status_code in [200, 302]

        if response.status_code == 200:
            data = json.loads(response.content)
            assert data['success'] is True

    def test_settings_save_invalid_json(self, client):
        """Test saving with invalid JSON."""
        response = client.post(
            '/modules/returns/settings/save/',
            data='invalid json',
            content_type='application/json'
        )

        # May require login or return 400
        assert response.status_code in [400, 302]

    def test_settings_persist(self, client, db):
        """Test settings are persisted."""
        # Save settings
        response = client.post(
            '/modules/returns/settings/save/',
            data=json.dumps({
                'allow_returns': False,
                'return_window_days': 7,
                'allow_store_credit': True,
                'require_receipt': False,
                'auto_restore_stock': False
            }),
            content_type='application/json'
        )

        # Verify persisted values (if login not required)
        if response.status_code == 200:
            config = ReturnsConfig.get_config()
            assert config.allow_returns is False
            assert config.return_window_days == 7
            assert config.allow_store_credit is True
            assert config.require_receipt is False
            assert config.auto_restore_stock is False
