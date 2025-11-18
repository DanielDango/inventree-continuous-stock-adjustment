"""API views for the ContinouousStockAdjustment plugin."""

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BarcodeScanRequestSerializer, BarcodeScanResponseSerializer


class BarcodeScanView(APIView):
    """API view for scanning barcodes and removing stock.
    
    This view handles barcode scanning and performs stock removal operations
    similar to the functionality demonstrated in api_test.py.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BarcodeScanRequestSerializer

    def post(self, request, *args, **kwargs):
        """Handle barcode scan and stock removal."""
        from decimal import Decimal
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
            # Scan for matching barcode in Part and StockItem models
            part = None
            stock_item = None
            
            # Try Part first
            try:
                part = Part.objects.get(barcode=barcode)
            except (Part.DoesNotExist, AttributeError):
                pass
            
            # If no part, try StockItem
            if not part:
                try:
                    stock_item = StockItem.objects.get(barcode=barcode)
                    if stock_item:
                        part = stock_item.part
                except (StockItem.DoesNotExist, AttributeError):
                    pass
            
            if not part:
                # Scan succeeded but couldn't extract a valid part
                response_data = {
                    'success': False,
                    'message': 'Barcode not found or does not match a part'
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=404)
            
            # Get stock items for this part
            stock_items = StockItem.objects.filter(part=part, quantity__gt=0).order_by('id')
            
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
                supplier_parts = SupplierPart.objects.filter(part=part).first()
                if supplier_parts and supplier_parts.pack_quantity_native:
                    quantity = Decimal(supplier_parts.pack_quantity_native)

            quantity = Decimal(str(quantity))

            # Remove stock from available items
            quantity_removed = Decimal(0)
            remaining_quantity = quantity
            
            for stock_item in stock_items:
                if remaining_quantity <= 0:
                    break
                    
                if stock_item.quantity >= remaining_quantity:
                    # This item has enough stock
                    stock_item.remove_stock(
                        remaining_quantity,
                        request.user,
                        notes=f"Removed via barcode scan: {barcode}"
                    )
                    quantity_removed += remaining_quantity
                    remaining_quantity = Decimal(0)
                else:
                    # Remove all stock from this item and continue
                    item_quantity = stock_item.quantity
                    stock_item.remove_stock(
                        item_quantity,
                        request.user,
                        notes=f"Removed via barcode scan: {barcode}"
                    )
                    quantity_removed += item_quantity
                    remaining_quantity -= item_quantity

            # Calculate remaining stock
            remaining_stock = sum(item.quantity for item in StockItem.objects.filter(part=part))

            response_data = {
                'success': True,
                'message': f'Successfully removed {quantity_removed} {part.units} from stock',
                'part_id': part.pk,
                'part_name': part.name,
                'quantity_removed': float(quantity_removed),
                'remaining_stock': float(remaining_stock)
            }

            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data, status=200)

        except Part.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'Part not found'
            }
            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=404)
        except Exception as e:
            response_data = {
                'success': False,
                'message': f'Error processing barcode: {str(e)}'
            }
            response_serializer = BarcodeScanResponseSerializer(data=response_data)
            response_serializer.is_valid()
            return Response(response_serializer.data, status=500)
