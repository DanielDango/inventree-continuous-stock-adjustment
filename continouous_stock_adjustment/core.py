"""Perform quick and intuitive stock adjustments by scanning barcodes to remove articles from stock"""

from plugin import InvenTreePlugin

from plugin.mixins import SettingsMixin, UrlsMixin, UserInterfaceMixin

from . import PLUGIN_VERSION


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

    # Optionally specify supported InvenTree versions
    # MIN_VERSION = '0.18.0'
    # MAX_VERSION = '2.0.0'

    # Render custom UI elements to the plugin settings page
    ADMIN_SOURCE = "Settings.js:renderPluginSettings"

    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
    SETTINGS = {
        # Define your plugin settings here...
        'CUSTOM_VALUE': {
            'name': 'Custom Value',
            'description': 'A custom value',
            'validator': int,
            'default': 42,
        }
    }

    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path
        from .views import ExampleView, BarcodeScanView

        return [
            # Provide path to a simple custom view - replace this with your own views
            path('example/', ExampleView.as_view(), name='example-view'),
            # Barcode scanning endpoint for stock removal
            path('scan/', BarcodeScanView.as_view(), name='barcode-scan'),
        ]

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/

    # Custom UI panels
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""

        panels = []

        # Only display this panel for the 'part' target
        if context.get('target_model') == 'part':
            panels.append({
                'key': 'continouous-stock-adjustment-panel',
                'title': 'Continouous Stock Adjustment',
                'description': 'Custom panel description',
                'icon': 'ti:mood-smile:outline',
                'source': self.plugin_static_file('Panel.js:renderContinouousStockAdjustmentPanel'),
                'context': {
                    # Provide additional context data to the panel
                    'settings': self.get_settings_dict(),
                    'foo': 'bar'
                }
            })

        return panels

    # Custom dashboard items
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
            'context': {
                # Provide additional context data to the dashboard item
                'settings': self.get_settings_dict(),
            }
        })

        return items
