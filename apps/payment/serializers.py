from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.appointment.models import Appointment
from apps.appointment.serializers import AppointmentListSerializer

from .models import Payment

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model with all fields"""

    appointment_details = AppointmentListSerializer(source="appointment", read_only=True)
    formatted_amount = serializers.CharField(source="get_formatted_amount", read_only=True)
    customer_name = serializers.CharField(source="get_customer_name", read_only=True)
    service_name = serializers.CharField(source="get_service_name", read_only=True)
    barbershop_name = serializers.CharField(source="get_barbershop_name", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    method_icon = serializers.CharField(source="get_method_display_icon", read_only=True)
    status_icon = serializers.CharField(source="get_status_display_icon", read_only=True)
    payment_age_days = serializers.IntegerField(source="get_payment_age_days", read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_refunded = serializers.BooleanField(read_only=True)
    is_card_payment = serializers.BooleanField(read_only=True)
    is_cash_payment = serializers.BooleanField(read_only=True)
    is_digital_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "appointment",
            "appointment_details",
            "amount",
            "formatted_amount",
            "method",
            "method_display",
            "method_icon",
            "status",
            "status_display",
            "status_icon",
            "transaction_id",
            "payment_date",
            "notes",
            "customer_name",
            "service_name",
            "barbershop_name",
            "payment_age_days",
            "is_paid",
            "is_pending",
            "is_refunded",
            "is_card_payment",
            "is_cash_payment",
            "is_digital_payment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "transaction_id", "created_at", "updated_at"]


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments with essential fields"""

    formatted_amount = serializers.CharField(source="get_formatted_amount", read_only=True)
    customer_name = serializers.CharField(source="get_customer_name", read_only=True)
    service_name = serializers.CharField(source="get_service_name", read_only=True)
    barbershop_name = serializers.CharField(source="get_barbershop_name", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    method_icon = serializers.CharField(source="get_method_display_icon", read_only=True)
    status_icon = serializers.CharField(source="get_status_display_icon", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "appointment",
            "amount",
            "formatted_amount",
            "method",
            "method_display",
            "method_icon",
            "status",
            "status_display",
            "status_icon",
            "payment_date",
            "customer_name",
            "service_name",
            "barbershop_name",
            "created_at",
        ]


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment detail view with comprehensive information"""

    appointment_details = AppointmentListSerializer(source="appointment", read_only=True)
    formatted_amount = serializers.CharField(source="get_formatted_amount", read_only=True)
    customer_name = serializers.CharField(source="get_customer_name", read_only=True)
    service_name = serializers.CharField(source="get_service_name", read_only=True)
    barbershop_name = serializers.CharField(source="get_barbershop_name", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    method_icon = serializers.CharField(source="get_method_display_icon", read_only=True)
    status_icon = serializers.CharField(source="get_status_display_icon", read_only=True)
    payment_age_days = serializers.IntegerField(source="get_payment_age_days", read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_refunded = serializers.BooleanField(read_only=True)
    is_card_payment = serializers.BooleanField(read_only=True)
    is_cash_payment = serializers.BooleanField(read_only=True)
    is_digital_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "appointment",
            "appointment_details",
            "amount",
            "formatted_amount",
            "method",
            "method_display",
            "method_icon",
            "status",
            "status_display",
            "status_icon",
            "transaction_id",
            "payment_date",
            "notes",
            "customer_name",
            "service_name",
            "barbershop_name",
            "payment_age_days",
            "is_paid",
            "is_pending",
            "is_refunded",
            "is_card_payment",
            "is_cash_payment",
            "is_digital_payment",
            "created_at",
            "updated_at",
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""

    class Meta:
        model = Payment
        fields = [
            "appointment",
            "amount",
            "method",
            "notes",
        ]

    def validate_appointment(self, value):
        """Validate that appointment doesn't already have a payment"""
        if hasattr(value, 'payment'):
            raise serializers.ValidationError(
                "Este agendamento já possui um pagamento associado."
            )
        return value

    def validate_amount(self, value):
        """Validate that amount is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "O valor do pagamento deve ser maior que zero."
            )
        return value

    def create(self, validated_data):
        """Create payment with automatic status setting"""
        # If method is cash, mark as paid immediately
        if validated_data.get('method') == Payment.Method.CASH:
            validated_data['status'] = Payment.Status.PAID
        
        return super().create(validated_data)


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payments"""

    class Meta:
        model = Payment
        fields = [
            "method",
            "notes",
        ]

    def validate(self, attrs):
        """Validate that paid payments cannot be modified extensively"""
        if self.instance and self.instance.is_paid():
            if 'method' in attrs and attrs['method'] != self.instance.method:
                raise serializers.ValidationError(
                    "Não é possível alterar o método de pagamento de um pagamento já realizado."
                )
        return attrs


class PaymentConfirmSerializer(serializers.Serializer):
    """Serializer for confirming payments"""

    transaction_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Mark payment as paid"""
        transaction_id = validated_data.get('transaction_id')
        notes = validated_data.get('notes', '')
        
        if notes:
            instance.notes = notes
        
        instance.mark_as_paid(transaction_id=transaction_id)
        return instance


class PaymentRefundSerializer(serializers.Serializer):
    """Serializer for refunding payments"""

    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate that only paid payments can be refunded"""
        if not self.instance.is_paid():
            raise serializers.ValidationError(
                "Apenas pagamentos realizados podem ser reembolsados."
            )
        return attrs

    def update(self, instance, validated_data):
        """Mark payment as refunded"""
        notes = validated_data.get('notes', '')
        
        if notes:
            if instance.notes:
                instance.notes += f"\n\nReembolso: {notes}"
            else:
                instance.notes = f"Reembolso: {notes}"
        
        instance.mark_as_refunded()
        return instance
