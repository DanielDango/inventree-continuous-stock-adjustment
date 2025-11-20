"""API serializers for the ContinouousStockAdjustment plugin."""

from rest_framework import serializers


class BarcodeScanRequestSerializer(serializers.Serializer):
    """Serializer for barcode scan requests."""

    class Meta:
        """Meta options for this serializer."""
        fields = [
            'barcode',
            'quantity',
            'confirmed',
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

    confirmed = serializers.BooleanField(
        required=False,
        default=False,
        label="Confirmed",
        help_text="Whether the user has confirmed the action for large quantity removals."
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
            'confirmation_required',
            'quantity_to_remove',
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

    confirmation_required = serializers.BooleanField(
        required=False,
        default=False,
        label="Confirmation Required",
        help_text="Whether confirmation is required before proceeding."
    )

    quantity_to_remove = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=15,
        decimal_places=5,
        label="Quantity to Remove",
        help_text="The quantity that will be removed if confirmed."
    )

