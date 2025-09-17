from rest_framework import serializers
from .models import Payment
from apps.appointments.serializers import AppointmentSerializer

class PaymentSerializer(serializers.ModelSerializer):
    appointment_details = AppointmentSerializer(source='appointment', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'appointment', 'appointment_details', 'amount', 'method',
                'status', 'transaction_id', 'payment_date', 'notes',
                'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('status') == Payment.Status.PAID and not data.get('payment_date'):
            raise serializers.ValidationError(
                "Payment date is required when status is PAID"
            )
        return data