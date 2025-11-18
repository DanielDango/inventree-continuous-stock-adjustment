"""Perform quick and intuitive stock adjustments by scanning barcodes to remove articles from stock"""

from plugin import InvenTreePlugin

from plugin.mixins import ActionMixin, AppMixin, NavigationMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin

from . import PLUGIN_VERSION


class ContinouousStockAdjustment(ActionMixin, AppMixin, NavigationMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin):

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
        # Plugin settings can be defined here if needed in the future
    }

    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path
        from .views import BarcodeScanView

        return [
            # Barcode scanning endpoint for stock removal
            path('scan/', BarcodeScanView.as_view(), name='barcode-scan'),
        ]

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/

    # Custom UI panels
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""
        # Scanning works independently of a concrete part/stock location
        # So we don't add panels to specific pages
        return []

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

    # Custom UI features (from UserInterfaceMixin)
    def get_ui_features(self, request, feature_type, context, **kwargs):
        """Return custom UI features for creating standalone pages."""
        
        features = []
        
        # Add a custom "app" page for stock removal
        if feature_type == 'app':
            features.append({
                'key': 'stock-removal',
                'title': 'Stock Removal',
                'description': 'Quick barcode scanning for stock removal',
                'icon': 'ti:barcode:outline',
                'source': self.plugin_static_file('StockRemovalPage.js:renderStockRemovalPage'),
            })
        
        return features

    # Custom actions (from ActionMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/action/
    def get_custom_actions(self, model=None):
        """Return custom actions for stock items."""
        actions = []
        
        # Only provide actions for StockItem model
        if model == 'stockitem':
            actions.append({
                'name': 'remove_package',
                'title': 'Remove Package',
                'description': 'Remove one package quantity from stock',
                'icon': 'ti:package-minus:outline',
            })
        
        return actions

    def perform_custom_action(self, action, model, instances, **kwargs):
        """Perform a custom action on selected instances."""
        from decimal import Decimal
        from company.models import SupplierPart
        
        if action == 'remove_package' and model == 'stockitem':
            results = []
            for stock_item in instances:
                try:
                    # Get package quantity from supplier part
                    quantity = Decimal(1)  # Default to 1
                    
                    part = stock_item.part
                    supplier_parts = SupplierPart.objects.filter(part=part).first()
                    if supplier_parts and supplier_parts.pack_quantity_native:
                        quantity = Decimal(supplier_parts.pack_quantity_native)
                    
                    # Check if enough stock is available
                    if stock_item.quantity >= quantity:
                        stock_item.remove_stock(
                            quantity,
                            kwargs.get('user'),
                            notes='Removed one package via plugin action'
                        )
                        results.append({
                            'success': True,
                            'message': f'Removed {quantity} from stock item {stock_item.pk}'
                        })
                    else:
                        results.append({
                            'success': False,
                            'message': f'Insufficient stock (need {quantity}, have {stock_item.quantity})'
                        })
                except Exception as e:
                    results.append({
                        'success': False,
                        'message': f'Error: {str(e)}'
                    })
            
            return results
        
        return []

    # Custom navigation items (from NavigationMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/navigation/
    def get_navigation_items(self, request, **kwargs):
        """Return custom navigation items for quick access."""
        
        # Only display for authenticated users
        if not request.user or not request.user.is_authenticated:
            return []
        
        return [
            {
                'name': 'Stock Removal',
                'description': 'Quick barcode stock removal',
                'link': '/app/plugin/continouous-stock-adjustment/stock-removal/',
                'icon': 'ti:barcode:outline',
            }
        ]
