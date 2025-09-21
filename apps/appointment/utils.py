from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from .models import Appointment, BarberSchedule

User = get_user_model()


def get_available_barbers_for_datetime(barbershop, datetime_obj):
    """
    Retorna lista de barbeiros disponíveis para um determinado horário
    """
    weekday = datetime_obj.weekday()
    time = datetime_obj.time()

    # Buscar horários disponíveis para o dia e horário
    schedules = BarberSchedule.objects.filter(
        barbershop=barbershop,
        weekday=weekday,
        start_time__lte=time,
        end_time__gt=time,
        is_available=True,
    ).select_related("barber")

    available_barbers = []
    for schedule in schedules:
        # Verificar se o barbeiro não tem agendamento neste horário
        if not schedule.has_appointment_at(datetime_obj):
            available_barbers.append(schedule.barber)

    return available_barbers


def get_available_slots_for_barber(
    barber, barbershop, date_obj, service_duration_minutes=30
):
    """
    Retorna horários disponíveis para um barbeiro em uma data específica
    """
    try:
        schedule = BarberSchedule.objects.get(
            barber=barber,
            barbershop=barbershop,
            weekday=date_obj.weekday(),
            is_available=True,
        )
        return [
            datetime.combine(date_obj, slot)
            for slot in schedule.get_available_slots(date_obj, service_duration_minutes)
        ]
    except BarberSchedule.DoesNotExist:
        return []


def get_all_available_slots(barbershop, date_obj, service=None, barber=None):
    """
    Retorna todos os horários disponíveis para uma barbearia em uma data
    Organizado por barbeiro
    """
    service_duration = 30  # Default
    if service:
        service_duration = service.get_duration_in_minutes()

    available_slots = {}

    # Se barbeiro específico foi fornecido, buscar apenas para ele
    if barber:
        barbers = [barber]
    else:
        # Buscar todos os barbeiros que trabalham nesta barbearia neste dia
        weekday = date_obj.weekday()
        schedules = BarberSchedule.objects.filter(
            barbershop=barbershop, weekday=weekday, is_available=True
        ).select_related("barber")
        barbers = [schedule.barber for schedule in schedules]

    for barber_obj in barbers:
        slots = get_available_slots_for_barber(
            barber_obj, barbershop, date_obj, service_duration
        )

        if slots:
            available_slots[barber_obj.get_full_name()] = [
                {
                    "barber_id": str(barber_obj.id),
                    "barber_name": barber_obj.get_full_name(),
                    "datetime": slot.strftime("%Y-%m-%d %H:%M:%S"),
                    "time": slot.strftime("%H:%M"),
                }
                for slot in slots
            ]

    return available_slots


def validate_appointment_datetime(
    barber, barbershop, start_datetime, end_datetime, appointment_id=None
):
    """
    Valida se um horário de agendamento é válido
    Retorna dicionário com 'valid' (bool) e 'errors' (list)
    """
    errors = []

    # Verificar se é no passado
    if start_datetime < timezone.now():
        errors.append("Não é possível agendar para uma data passada")

    # Verificar se início é antes do fim
    if start_datetime >= end_datetime:
        errors.append(
            "A data e hora de início devem ser antes da data e hora de término"
        )

    # Verificar se o barbeiro trabalha neste dia e horário
    weekday = start_datetime.weekday()
    time = start_datetime.time()

    try:
        schedule = BarberSchedule.objects.get(
            barber=barber,
            barbershop=barbershop,
            weekday=weekday,
            start_time__lte=time,
            end_time__gt=end_datetime.time(),
            is_available=True,
        )
    except BarberSchedule.DoesNotExist:
        errors.append("O barbeiro não está disponível neste horário")
        return {"valid": False, "errors": errors}

    # Verificar conflitos com outros agendamentos
    conflicting_appointment = Appointment.objects.filter(
        barber=barber,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    )

    if appointment_id:
        conflicting_appointment = conflicting_appointment.exclude(id=appointment_id)

    conflicting_appointment = conflicting_appointment.first()

    if conflicting_appointment:
        errors.append(
            f"Já existe um agendamento neste horário: {conflicting_appointment.formatted_datetime}"
        )

    return {"valid": len(errors) == 0, "errors": errors}


def get_barber_appointments_for_period(barber, start_date, end_date, barbershop=None):
    """
    Retorna agendamentos de um barbeiro para um período
    """
    queryset = Appointment.objects.filter(
        barber=barber,
        start_datetime__date__gte=start_date,
        start_datetime__date__lte=end_date,
    ).select_related("customer__customer", "service", "barbershop")

    if barbershop:
        queryset = queryset.filter(barbershop=barbershop)

    return queryset.order_by("start_datetime")


def get_barbershop_appointments_for_period(
    barbershop, start_date, end_date, status=None
):
    """
    Retorna agendamentos de uma barbearia para um período
    """
    queryset = Appointment.objects.filter(
        barbershop=barbershop,
        start_datetime__date__gte=start_date,
        start_datetime__date__lte=end_date,
    ).select_related("customer__customer", "barber", "service")

    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by("start_datetime")


def calculate_appointment_revenue(barbershop, start_date, end_date):
    """
    Calcula receita de agendamentos para um período
    """
    appointments = get_barbershop_appointments_for_period(
        barbershop, start_date, end_date, Appointment.Status.COMPLETED
    )

    total_revenue = (
        appointments.aggregate(total=models.Sum("final_price"))["total"] or 0
    )

    appointments_count = appointments.count()

    average_price = total_revenue / appointments_count if appointments_count > 0 else 0

    return {
        "total_revenue": total_revenue,
        "appointments_count": appointments_count,
        "average_price": average_price,
        "period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        },
    }


def get_barber_stats(barber, barbershop=None, period_days=30):
    """
    Retorna estatísticas de um barbeiro
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)

    appointments = get_barber_appointments_for_period(
        barber, start_date, end_date, barbershop
    )

    completed_appointments = appointments.filter(status=Appointment.Status.COMPLETED)
    pending_appointments = appointments.filter(status=Appointment.Status.PENDING)
    confirmed_appointments = appointments.filter(status=Appointment.Status.CONFIRMED)
    cancelled_appointments = appointments.filter(status=Appointment.Status.CANCELLED)

    total_revenue = (
        completed_appointments.aggregate(total=models.Sum("final_price"))["total"] or 0
    )

    return {
        "barber_name": barber.get_full_name(),
        "period_days": period_days,
        "total_appointments": appointments.count(),
        "completed_appointments": completed_appointments.count(),
        "pending_appointments": pending_appointments.count(),
        "confirmed_appointments": confirmed_appointments.count(),
        "cancelled_appointments": cancelled_appointments.count(),
        "total_revenue": total_revenue,
        "average_appointment_value": (
            total_revenue / completed_appointments.count()
            if completed_appointments.count() > 0
            else 0
        ),
    }


def find_next_available_appointment_slot(
    barbershop, service, preferred_barber=None, preferred_date=None
):
    """
    Encontra o próximo horário disponível para um serviço
    """
    start_date = preferred_date or date.today()
    service_duration = service.get_duration_in_minutes()

    # Buscar por até 14 dias
    for i in range(14):
        check_date = start_date + timedelta(days=i)

        if preferred_barber:
            slots = get_available_slots_for_barber(
                preferred_barber, barbershop, check_date, service_duration
            )
            if slots:
                return {
                    "barber_id": str(preferred_barber.id),
                    "barber_name": preferred_barber.get_full_name(),
                    "datetime": slots[0].strftime("%Y-%m-%d %H:%M:%S"),
                    "date": check_date.strftime("%Y-%m-%d"),
                    "time": slots[0].strftime("%H:%M"),
                }
        else:
            all_slots = get_all_available_slots(barbershop, check_date, service)
            if all_slots:
                # Retornar primeiro barbeiro com horário disponível
                for barber_name, barber_slots in all_slots.items():
                    if barber_slots:
                        return barber_slots[0]

    return None


def bulk_create_barber_schedules(barber, barbershop, schedules_data):
    """
    Cria múltiplos horários de barbeiro de uma vez
    """
    schedules = []

    for schedule_data in schedules_data:
        schedule = BarberSchedule(barber=barber, barbershop=barbershop, **schedule_data)
        schedules.append(schedule)

    return BarberSchedule.objects.bulk_create(schedules)


def get_conflicting_appointments(
    barber, start_datetime, end_datetime, exclude_appointment_id=None
):
    """
    Retorna agendamentos que conflitam com um horário específico
    """
    queryset = Appointment.objects.filter(
        barber=barber,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    )

    if exclude_appointment_id:
        queryset = queryset.exclude(id=exclude_appointment_id)

    return queryset
