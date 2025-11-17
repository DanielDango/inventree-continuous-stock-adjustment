"""API serializers for the ContinouousStockAdjustment plugin.

In practice, you would define your custom serializers here.

Ref: https://www.django-rest-framework.org/api-guide/serializers/
"""

from rest_framework import serializers


class ExampleSerializer(serializers.Serializer):
    """Example serializer for the ContinouousStockAdjustment plugin.
    
    This simply demonstrates how to create a serializer,
    with a few example fields of different types.
    """

    class Meta:
        """Meta options for this serializer."""
        fields = [
            'random_text',
            'part_count',
            'today',
        ]
    
    random_text = serializers.CharField(
        max_length=100,
        required=True,
        label="Random Text",
        help_text="A text field containing randomly generated data."
    )

    part_count = serializers.IntegerField(
        label="Number of Parts",
        help_text="Total number of parts in the InvenTree database.",
    )

    today = serializers.DateField(
        required=False,
        label="Today",
        help_text="The current date.",
    )


class BarcodeScanRequestSerializer(serializers.Serializer):
    """Serializer for barcode scan requests."""

    class Meta:
        """Meta options for this serializer."""
        fields = [
            'barcode',
            'quantity',
        ]

    barcode = serializers.CharField(
        required=True,
        label="Barcode",
        help_text="The barcode to scan and remove from stock."
    )

    quantity = serializers.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=5,
        allow_null=True,
        label="Quantity",
        help_text="Optional quantity to remove. If not provided, removes one package based on supplier part data."
    )


class BarcodeScanResponseSerializer(serializers.Serializer):
    """Serializer for barcode scan responses."""

    class Meta:
        """Meta options for this serializer."""
        fields = [
            'success',
            'message',
            'part_id',
            'part_name',
            'quantity_removed',
            'remaining_stock',
        ]

    success = serializers.BooleanField(
        label="Success",
        help_text="Whether the operation was successful."
    )

    message = serializers.CharField(
        label="Message",
        help_text="Status message describing the result."
    )

    part_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        label="Part ID",
        help_text="The ID of the part that was adjusted."
    )

    part_name = serializers.CharField(
        required=False,
        allow_null=True,
        label="Part Name",
        help_text="The name of the part that was adjusted."
    )

    quantity_removed = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=15,
        decimal_places=5,
        label="Quantity Removed",
        help_text="The quantity that was removed from stock."
    )

    remaining_stock = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=15,
        decimal_places=5,
        label="Remaining Stock",
        help_text="The total remaining stock quantity for this part."
    )
