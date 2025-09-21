from datetime import date

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.appointment.models import Appointment, BarberSchedule
from apps.barbershop.models import Barbershop, Service

User = get_user_model()


class BarberScheduleSerializer(serializers.ModelSerializer):
    """Serializer para BarberSchedule com todos os campos"""

    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    weekday_display = serializers.CharField(
        source="get_weekday_display", read_only=True
    )
    work_duration_hours = serializers.DecimalField(
        source="get_work_duration_hours", max_digits=4, decimal_places=2, read_only=True
    )
    work_duration_minutes = serializers.IntegerField(read_only=True)
    is_working_now = serializers.BooleanField(read_only=True)
    appointments_count_today = serializers.IntegerField(
        source="get_appointments_count_today", read_only=True
    )

    class Meta:
        model = BarberSchedule
        fields = [
            "id",
            "barber",
            "barber_name",
            "barbershop",
            "barbershop_name",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_available",
            "work_duration_hours",
            "work_duration_minutes",
            "is_working_now",
            "appointments_count_today",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Validar se a hora de início é antes da hora de término"""
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError(
                    "A hora de início deve ser antes da hora de término"
                )
        return data


class BarberScheduleDetailSerializer(BarberScheduleSerializer):
    """Serializer detalhado para BarberSchedule"""

    barber_email = serializers.EmailField(source="barber.email", read_only=True)
    barber_phone = serializers.CharField(source="barber.phone", read_only=True)
    barbershop_address = serializers.CharField(
        source="barbershop.address", read_only=True
    )
    is_fully_booked_today = serializers.SerializerMethodField()
    next_available_slot = serializers.SerializerMethodField()

    class Meta(BarberScheduleSerializer.Meta):
        fields = BarberScheduleSerializer.Meta.fields + [
            "barber_email",
            "barber_phone",
            "barbershop_address",
            "is_fully_booked_today",
            "next_available_slot",
        ]

    def get_is_fully_booked_today(self, obj):
        """Verifica se está totalmente ocupado hoje"""
        return obj.is_fully_booked_today()

    def get_next_available_slot(self, obj):
        """Retorna próximo horário disponível"""
        slot = obj.get_next_available_slot()
        return slot.strftime("%Y-%m-%d %H:%M:%S") if slot else None


class BarberScheduleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de horários"""

    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    weekday_display = serializers.CharField(
        source="get_weekday_display", read_only=True
    )
    work_duration_hours = serializers.DecimalField(
        source="get_work_duration_hours", max_digits=4, decimal_places=2, read_only=True
    )
    is_working_now = serializers.BooleanField(read_only=True)

    class Meta:
        model = BarberSchedule
        fields = [
            "id",
            "barber_name",
            "barbershop_name",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_available",
            "work_duration_hours",
            "is_working_now",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer para Appointment com todos os campos"""

    customer_name = serializers.CharField(
        source="customer.customer.get_full_name", read_only=True
    )
    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    barbershop_name = serializers.CharField(source="barbershop.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    duration_hours = serializers.DecimalField(
        source="get_duration_hours", max_digits=4, decimal_places=2, read_only=True
    )
    formatted_datetime = serializers.CharField(read_only=True)
    formatted_date = serializers.CharField(read_only=True)
    formatted_time = serializers.CharField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_in_progress = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    can_be_confirmed = serializers.BooleanField(read_only=True)
    can_be_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "customer_name",
            "barber",
            "barber_name",
            "service",
            "service_name",
            "barbershop",
            "barbershop_name",
            "start_datetime",
            "end_datetime",
            "status",
            "status_display",
            "final_price",
            "created_at",
            "updated_at",
            "duration_minutes",
            "duration_hours",
            "formatted_datetime",
            "formatted_date",
            "formatted_time",
            "is_today",
            "is_past",
            "is_upcoming",
            "is_in_progress",
            "can_be_cancelled",
            "can_be_confirmed",
            "can_be_completed",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "final_price"]

    def validate(self, data):
        """Validações customizadas para agendamento"""
        start_datetime = data.get("start_datetime")
        end_datetime = data.get("end_datetime")
        service = data.get("service")
        barber = data.get("barber")
        barbershop = data.get("barbershop")

        # Validar se data/hora de início é antes do fim
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise serializers.ValidationError(
                    "A data e hora de início devem ser antes da data e hora de término"
                )

        # Validar se o agendamento é no passado
        if start_datetime and start_datetime < timezone.now():
            raise serializers.ValidationError(
                "Não é possível agendar para uma data passada"
            )

        # Validar se o serviço pertence à barbearia
        if service and barbershop and service.barbershop != barbershop:
            raise serializers.ValidationError(
                "O serviço deve pertencer à barbearia selecionada"
            )

        # Validar se o barbeiro trabalha na barbearia
        if barber and barbershop:
            has_schedule = BarberSchedule.objects.filter(
                barber=barber, barbershop=barbershop, is_available=True
            ).exists()
            if not has_schedule:
                raise serializers.ValidationError(
                    "O barbeiro não trabalha nesta barbearia ou não está disponível"
                )

        # Validar se o barbeiro está disponível no horário
        if start_datetime and barber and barbershop:
            weekday = start_datetime.weekday()  # 0=Monday
            time = start_datetime.time()

            schedule = BarberSchedule.objects.filter(
                barber=barber,
                barbershop=barbershop,
                weekday=weekday,
                start_time__lte=time,
                end_time__gt=time,
                is_available=True,
            ).first()

            if not schedule:
                raise serializers.ValidationError(
                    "O barbeiro não está disponível neste horário"
                )

            # Verificar conflito com outros agendamentos
            conflicting_appointment = (
                Appointment.objects.filter(
                    barber=barber,
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime,
                    status__in=[
                        Appointment.Status.PENDING,
                        Appointment.Status.CONFIRMED,
                    ],
                )
                .exclude(id=self.instance.id if self.instance else None)
                .first()
            )

            if conflicting_appointment:
                raise serializers.ValidationError(
                    f"Já existe um agendamento neste horário: {conflicting_appointment.formatted_datetime}"
                )

        return data


class AppointmentDetailSerializer(AppointmentSerializer):
    """Serializer detalhado para Appointment"""

    customer_phone = serializers.CharField(
        source="customer.customer.phone", read_only=True
    )
    customer_email = serializers.EmailField(
        source="customer.customer.email", read_only=True
    )
    barber_phone = serializers.CharField(source="barber.phone", read_only=True)
    service_price = serializers.DecimalField(
        source="service.price", max_digits=10, decimal_places=2, read_only=True
    )
    service_duration = serializers.DurationField(
        source="service.duration", read_only=True
    )
    barbershop_address = serializers.CharField(
        source="barbershop.address", read_only=True
    )
    barbershop_phone = serializers.CharField(source="barbershop.phone", read_only=True)
    time_until_appointment = serializers.SerializerMethodField()

    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + [
            "customer_phone",
            "customer_email",
            "barber_phone",
            "service_price",
            "service_duration",
            "barbershop_address",
            "barbershop_phone",
            "time_until_appointment",
        ]

    def get_time_until_appointment(self, obj):
        """Retorna o tempo até o agendamento"""
        time_until = obj.get_time_until_appointment()
        if time_until:
            total_seconds = int(time_until.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            if days > 0:
                return f"{days} dias, {hours} horas"
            elif hours > 0:
                return f"{hours} horas, {minutes} minutos"
            else:
                return f"{minutes} minutos"
        return None


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos"""

    customer_name = serializers.CharField(
        source="customer.customer.get_full_name", read_only=True
    )
    barber_name = serializers.CharField(source="barber.get_full_name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    formatted_datetime = serializers.CharField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer_name",
            "barber_name",
            "service_name",
            "start_datetime",
            "status",
            "status_display",
            "final_price",
            "formatted_datetime",
            "is_today",
            "can_be_cancelled",
        ]


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para criação de agendamentos"""

    class Meta:
        model = Appointment
        fields = [
            "customer",
            "barber",
            "service",
            "barbershop",
            "start_datetime",
            "end_datetime",
        ]

    def validate(self, data):
        """Reutilizar validações do AppointmentSerializer"""
        return AppointmentSerializer().validate(data)

    def create(self, validated_data):
        """Criar agendamento com preço final baseado no serviço"""
        service = validated_data["service"]
        appointment = Appointment.objects.create(
            final_price=service.price, **validated_data
        )
        return appointment


class AvailableSlotsSerializer(serializers.Serializer):
    """Serializer para consultar horários disponíveis"""

    barbershop_id = serializers.UUIDField(required=True)
    barber_id = serializers.UUIDField(required=False)
    service_id = serializers.UUIDField(required=False)
    date = serializers.DateField(required=True)

    def validate_date(self, value):
        """Validar se a data não é no passado"""
        if value < date.today():
            raise serializers.ValidationError("A data não pode ser no passado")
        return value

    def validate_barbershop_id(self, value):
        """Validar se a barbearia existe"""
        try:
            Barbershop.objects.get(id=value)
        except Barbershop.DoesNotExist:
            raise serializers.ValidationError("Barbearia não encontrada")
        return value

    def validate_barber_id(self, value):
        """Validar se o barbeiro existe"""
        if value:
            try:
                User.objects.get(id=value, role__in=[User.Role.BARBER, User.Role.ADMIN])
            except User.DoesNotExist:
                raise serializers.ValidationError("Barbeiro não encontrado")
        return value

    def validate_service_id(self, value):
        """Validar se o serviço existe"""
        if value:
            try:
                Service.objects.get(id=value)
            except Service.DoesNotExist:
                raise serializers.ValidationError("Serviço não encontrado")
        return value
