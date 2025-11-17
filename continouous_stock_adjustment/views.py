"""API views for the ContinouousStockAdjustment plugin.

In practice, you would define your custom views here.

Ref: https://www.django-rest-framework.org/api-guide/views/
"""

from datetime import date
import random
import string

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ExampleSerializer, BarcodeScanRequestSerializer, BarcodeScanResponseSerializer


class ExampleView(APIView):
    """Example API view for the ContinouousStockAdjustment plugin.
    
    This view returns some very simple example data,
    but the concept can be extended to include more complex logic.
    """

    # You can control which users can access this view using DRF permissions
    permission_classes = [permissions.IsAuthenticated]

    # Control how the response is formatted
    serializer_class = ExampleSerializer

    def get(self, request, *args, **kwargs):
        """Override the GET method to return example data."""

        from part.models import Part

        response_serializer = self.serializer_class(data={
            'random_text': ''.join(random.choices(string.ascii_letters, k=50)),
            'part_count': Part.objects.count(),
            'today': date.today()
        })

        # Serializer must be validated before it can be returned to the client
        response_serializer.is_valid(raise_exception=True)

        return Response(
            response_serializer.data,
            status=200
        )


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
            # Scan the barcode to find the associated item
            from plugin.registry import registry
            barcode_data = registry.scan_barcode(barcode)

            if not barcode_data or 'part' not in barcode_data:
                response_data = {
                    'success': False,
                    'message': 'Barcode not found or does not match a part'
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=404)

            # Get the part
            part_id = barcode_data['part'].get('pk')
            if not part_id:
                response_data = {
                    'success': False,
                    'message': 'Invalid part data in barcode'
                }
                response_serializer = BarcodeScanResponseSerializer(data=response_data)
                response_serializer.is_valid()
                return Response(response_serializer.data, status=400)

            part = Part.objects.get(pk=part_id)
            
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
