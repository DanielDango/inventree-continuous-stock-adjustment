"""API views for the ContinouousStockAdjustment plugin."""

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BarcodeScanRequestSerializer, BarcodeScanResponseSerializer


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
        from stock.models import StockItem

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

        try:
            # Use InvenTree's barcode scanning helper to resolve the barcode
            from InvenTree.helpers import hash_barcode

            # Try to match barcode against stock items and parts
            barcode_hash = hash_barcode(barcode)

            part = None
            stock_item = None
            
            # First, try to find a stock item with this barcode
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

            # If not found in stock items, try parts
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
                
                # Try to find supplier part with pack quantity
                supplier_part = SupplierPart.objects.filter(part=part).first()
                if supplier_part and supplier_part.pack_quantity_native:
                    quantity = Decimal(supplier_part.pack_quantity_native)

            quantity = Decimal(str(quantity))

            # Remove stock from available items
            quantity_removed = Decimal(0)
            remaining_quantity = quantity
            
            with transaction.atomic():
                for item in stock_items:
                    if remaining_quantity <= 0:
                        break

                    available = item.quantity
                    to_remove = min(available, remaining_quantity)

                    # Update quantity directly
                    item.quantity -= to_remove
                    item.save()

                    # Add a simple note to the item
                    if hasattr(item, 'notes') and item.notes:
                        item.notes += f'\n[{request.user.username}] Removed {to_remove} via barcode scan: {barcode}'
                    else:
                        item.notes = f'[{request.user.username}] Removed {to_remove} via barcode scan: {barcode}'
                    item.save()

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
                'message': f'Successfully removed {quantity_removed} units of {part.name}',
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
                'message': f'Error processing barcode: {str(e)}\n{traceback.format_exc()}'
            }
            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=500)
