"""API views for the ContinouousStockAdjustment plugin."""

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from stock.status_codes import StockHistoryCode
from .serializers import BarcodeScanRequestSerializer, BarcodeScanResponseSerializer
from .core import DEFAULT_CONFIRMATION_THRESHOLD, DEFAULT_QUANTITY, DEFAULT_RESCAN_TIMEOUT


class PluginSettingsView(APIView):
    """API view to retrieve plugin settings."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return plugin settings."""
        from plugin import registry

        try:
            plugin = registry.get_plugin('continouous-stock-adjustment')
            if plugin:
                confirmation_threshold = plugin.get_setting('CONFIRMATION_THRESHOLD', DEFAULT_CONFIRMATION_THRESHOLD)
                default_quantity = plugin.get_setting('DEFAULT_QUANTITY', DEFAULT_QUANTITY)
                rescan_timeout = plugin.get_setting('RESCAN_TIMEOUT', DEFAULT_RESCAN_TIMEOUT)
                return Response({
                    'confirmation_threshold': float(confirmation_threshold),
                    'default_quantity': float(default_quantity),
                    'rescan_timeout': float(rescan_timeout)
                })
            else:
                return Response({
                    'confirmation_threshold': DEFAULT_CONFIRMATION_THRESHOLD,
                    'default_quantity': DEFAULT_QUANTITY,
                    'rescan_timeout': DEFAULT_RESCAN_TIMEOUT
                })
        except Exception:
            return Response({
                'confirmation_threshold': DEFAULT_CONFIRMATION_THRESHOLD,
                'default_quantity': DEFAULT_QUANTITY,
                'rescan_timeout': DEFAULT_RESCAN_TIMEOUT
            })


class BarcodeScanView(APIView):
    """API view for scanning barcodes and removing stock.
    
    This view handles barcode scanning and performs stock removal operations
    using InvenTree's built-in barcode scanning API.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BarcodeScanRequestSerializer

    def post(self, request, *args, **kwargs):
        """Handle barcode scan and stock removal."""
        from decimal import Decimal
        from django.db import transaction
        from company.models import SupplierPart
        from part.models import Part
        from stock.models import StockItem, StockItemTracking
        from plugin import registry

        # Validate input
        request_serializer = self.serializer_class(data=request.data)
        if not request_serializer.is_valid():
            response_data = {
                'success': False,
                'message': f"Invalid request: {request_serializer.errors}"
            }
            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=400)

        barcode = request_serializer.validated_data['barcode']
        quantity = request_serializer.validated_data.get('quantity')
        confirmed = request_serializer.validated_data.get('confirmed', False)

        try:
            import json

            from InvenTree.helpers import hash_barcode

            part = None
            stock_item = None

            # 1) Try to parse as InvenTree internal barcode format (JSON like {"stockitem": 123})
            try:
                barcode_json = json.loads(barcode)
                if isinstance(barcode_json, dict):
                    if 'stockitem' in barcode_json:
                        try:
                            stock_item = StockItem.objects.get(pk=int(barcode_json['stockitem']))
                            part = stock_item.part
                        except (StockItem.DoesNotExist, ValueError, TypeError):
                            pass

                    if not part and 'part' in barcode_json:
                        try:
                            part = Part.objects.get(pk=int(barcode_json['part']))
                        except (Part.DoesNotExist, ValueError, TypeError):
                            pass

            except (json.JSONDecodeError, ValueError):
                # Not JSON - continue with hash-based lookup
                pass

            # 2) Fall back to hash-based lookup for custom/external barcodes
            if not part:
                barcode_hash = hash_barcode(barcode)

                # First, try to find a stock item with this barcode hash
                try:
                    stock_item = StockItem.objects.get(barcode_hash=barcode_hash, barcode_data=barcode)
                    part = stock_item.part
                except StockItem.DoesNotExist:
                    pass
                except StockItem.MultipleObjectsReturned:
                    # If multiple items, just get the first one
                    stock_item = StockItem.objects.filter(barcode_hash=barcode_hash, barcode_data=barcode).first()
                    if stock_item:
                        part = stock_item.part

                # If still not found, try parts via hash
                if not part:
                    try:
                        part = Part.objects.get(barcode_hash=barcode_hash, barcode_data=barcode)
                    except Part.DoesNotExist:
                        pass
                    except Part.MultipleObjectsReturned:
                        part = Part.objects.filter(barcode_hash=barcode_hash, barcode_data=barcode).first()

            if not part:
                response_data = {
                    'success': False,
                    'message': 'Barcode not found or does not match any part or stock item'
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=404)
            
            # Get stock items for this part with OK status only (status=10)
            stock_items = StockItem.objects.filter(
                part=part,
                quantity__gt=0,
                status=10  # OK/available stock status
            ).order_by('id')

            if not stock_items.exists():
                response_data = {
                    'success': False,
                    'message': f'No stock available for part: {part.name}',
                    'part_id': part.pk,
                    'part_name': part.name
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=400)

            # Determine quantity to remove
            if quantity is None or quantity == 0:
                # Try to get package quantity from supplier part
                quantity = Decimal(1)  # Default to 1 if no supplier part data
                
                # Find all supplier parts with pack quantity and select the smallest
                supplier_parts = SupplierPart.objects.filter(
                    part=part,
                    pack_quantity_native__isnull=False
                ).order_by('pack_quantity_native')

                if supplier_parts.exists():
                    # Get the smallest package size
                    smallest_supplier_part = supplier_parts.first()
                    quantity = Decimal(smallest_supplier_part.pack_quantity_native)

            quantity = Decimal(str(quantity))

            # Get plugin settings
            plugin = registry.get_plugin('continouous-stock-adjustment')
            confirmation_threshold = Decimal(str(plugin.get_setting('CONFIRMATION_THRESHOLD', DEFAULT_CONFIRMATION_THRESHOLD))) if plugin else Decimal(str(DEFAULT_CONFIRMATION_THRESHOLD))

            # Check if confirmation is needed
            if quantity > confirmation_threshold and not confirmed:
                response_data = {
                    'success': False,
                    'confirmation_required': True,
                    'message': f'Confirmation required to remove {float(quantity)} units',
                    'part_id': part.pk,
                    'part_name': part.name,
                    'quantity_to_remove': float(quantity),
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=200)

            # Remove stock from available items
            quantity_removed = Decimal(0)
            remaining_quantity = quantity
            
            with transaction.atomic():
                for item in stock_items:
                    if remaining_quantity <= 0:
                        break

                    available = item.quantity
                    to_remove = min(available, remaining_quantity)

                    # Store old quantity before update for tracking
                    old_quantity = item.quantity
                    new_quantity = old_quantity - to_remove

                    # Update stock quantity
                    item.quantity = new_quantity
                    item.save()

                    # Create tracking entry for transaction history
                    try:
                        StockItemTracking.objects.create(
                            item=item,
                            tracking_type=StockHistoryCode.STOCK_REMOVE,
                            user=request.user,
                            notes=f'Removed via barcode scan: {barcode}',
                            deltas={
                                'removed': float(to_remove),
                                'quantity': float(new_quantity)
                            }
                        )
                    except Exception as tracking_error:
                        # If tracking fails for any reason, log it but don't fail the operation
                        # This ensures stock removal still succeeds even if tracking fails
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to create tracking entry for stock item {item.pk}: {tracking_error}')

                        # Still try to create a minimal tracking entry without deltas
                        try:
                            StockItemTracking.objects.create(
                                item=item,
                                tracking_type=32,
                                user=request.user,
                                notes=f'Removed via barcode scan: {barcode}'
                            )
                        except Exception:
                            # If even minimal tracking fails, continue with the operation
                            pass

                    # Check if stock item is now empty and should be deleted
                    # InvenTree may have a setting to auto-delete empty stock items
                    if new_quantity <= 0:
                        try:
                            # Check InvenTree's stock settings for auto-deletion
                            from common.models import InvenTreeSetting
                            delete_empty = InvenTreeSetting.get_setting('STOCK_DELETE_DEPLETED_DEFAULT', False)

                            if delete_empty:
                                item.delete()
                        except Exception as delete_error:
                            # If deletion check/execution fails, log but continue
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f'Failed to check/delete empty stock item {item.pk}: {delete_error}')

                    quantity_removed += to_remove
                    remaining_quantity -= to_remove

            # Calculate remaining stock for this part (OK status=10 only)
            total_remaining = sum(
                si.quantity for si in StockItem.objects.filter(
                    part=part,
                    status=10  # Only count OK/available stock
                )
            )

            response_data = {
                'success': True,
                'message': f'Successfully removed {round(quantity_removed, 2)} units of {part.name}',
                'part_id': part.pk,
                'part_name': part.name,
                'quantity_removed': float(quantity_removed),
                'remaining_stock': float(total_remaining)
            }

            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data)

        except Exception as e:
            import traceback
            response_data = {
                'success': False,
                'message': f'Error processing barcode: {str(e)}\n{traceback.format_exc()}'
            }
            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=500)
