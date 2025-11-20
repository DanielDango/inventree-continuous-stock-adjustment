"""Perform quick and intuitive stock adjustments by scanning barcodes to remove articles from stock"""

from plugin import InvenTreePlugin

from plugin.mixins import SettingsMixin, UrlsMixin, UserInterfaceMixin

from . import PLUGIN_VERSION

# Default values for plugin settings
DEFAULT_CONFIRMATION_THRESHOLD = 2.0
DEFAULT_QUANTITY = 1.0
DEFAULT_RESCAN_TIMEOUT = 3.0


class ContinouousStockAdjustment(SettingsMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin):

    """ContinouousStockAdjustment - custom InvenTree plugin."""

    # Plugin metadata
    TITLE = "Continouous Stock Adjustment"
    NAME = "ContinouousStockAdjustment"
    SLUG = "continouous-stock-adjustment"
    DESCRIPTION = "Perform quick and intuitive stock adjustments by scanning barcodes to remove articles from stock"
    VERSION = PLUGIN_VERSION

    # Additional project information
    AUTHOR = "Daniel Schwab"
    
    LICENSE = "MIT"

    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
    SETTINGS = {
        'CONFIRMATION_THRESHOLD': {
            'name': 'Confirmation Threshold',
            'description': 'Require confirmation when removing more than this quantity at once',
            'validator': float,
            'default': DEFAULT_CONFIRMATION_THRESHOLD,
        },
        'DEFAULT_QUANTITY': {
            'name': 'Default Quantity',
            'description': 'Default quantity to remove when using the quick removal button in confirmation dialog',
            'validator': float,
            'default': DEFAULT_QUANTITY,
        },
        'RESCAN_TIMEOUT': {
            'name': 'Re-scan Timeout',
            'description': 'Time window (in seconds) for detecting re-scans of the same barcode',
            'validator': float,
            'default': DEFAULT_RESCAN_TIMEOUT,
        },
    }

    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path
        from .views import BarcodeScanView, PluginSettingsView

        return [
            # Barcode scanning endpoint for stock removal
            path('scan/', BarcodeScanView.as_view(), name='barcode-scan'),
            # Plugin settings endpoint
            path('settings/', PluginSettingsView.as_view(), name='plugin-settings'),
        ]

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""
        # Scanning works independently of a concrete part/stock location
        # So we don't add panels to specific pages
        return []

    def get_ui_dashboard_items(self, request, context: dict, **kwargs):
        """Return a list of custom dashboard items to be rendered in the InvenTree user interface."""

        # Only display for authenticated users
        if not request.user or not request.user.is_authenticated:
            return []
        
        items = []

        items.append({
            'key': 'continouous-stock-adjustment-dashboard',
            'title': 'Quick Stock Removal',
            'description': 'Scan barcodes to quickly remove stock',
            'icon': 'ti:barcode:outline',
            'source': self.plugin_static_file('Dashboard.js:renderContinouousStockAdjustmentDashboardItem'),
        })

        return items
