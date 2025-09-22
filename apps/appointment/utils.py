from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from django.db import models
from django.utils import timezone

from .models import Appointment, BarberSchedule


def get_available_time_slots(
    barber_schedule: BarberSchedule,
    date: datetime.date,
    service_duration_minutes: int = 30,
    exclude_appointment: Optional[Appointment] = None,
) -> List[datetime.time]:
    """
    Retorna uma lista de horários disponíveis para um barbeiro em uma data específica.
    
    Args:
        barber_schedule: A agenda do barbeiro
        date: A data para verificar disponibilidade
        service_duration_minutes: Duração do serviço em minutos
        exclude_appointment: Agendamento a ser excluído da verificação (útil para reagendamentos)
    
    Returns:
        Lista de horários disponíveis como objetos time
    """
    if not barber_schedule.is_available or date.weekday() != barber_schedule.weekday:
        return []

    # Buscar agendamentos existentes para esse dia
    existing_appointments = Appointment.objects.filter(
        barber=barber_schedule.barber,
        barbershop=barber_schedule.barbershop,
        start_datetime__date=date,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    )

    # Excluir agendamento específico se fornecido
    if exclude_appointment:
        existing_appointments = existing_appointments.exclude(id=exclude_appointment.id)

    existing_appointments = existing_appointments.order_by("start_datetime")

    slots = []
    current_time = datetime.combine(date, barber_schedule.start_time)
    end_time = datetime.combine(date, barber_schedule.end_time)
    slot_duration = timedelta(minutes=service_duration_minutes)

    for appointment in existing_appointments:
        # Adicionar slots até o início do agendamento
        while current_time + slot_duration <= appointment.start_datetime:
            slots.append(current_time.time())
            current_time += slot_duration

        # Pular para depois do agendamento
        current_time = appointment.end_datetime

    # Adicionar slots restantes até o fim do horário
    while current_time + slot_duration <= end_time:
        slots.append(current_time.time())
        current_time += slot_duration

    return slots


def check_appointment_conflict(
    barber,
    barbershop,
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_appointment: Optional[Appointment] = None,
) -> bool:
    """
    Verifica se há conflito de horário para um agendamento.
    
    Args:
        barber: O barbeiro
        barbershop: A barbearia
        start_datetime: Data e hora de início
        end_datetime: Data e hora de término
        exclude_appointment: Agendamento a ser excluído da verificação
    
    Returns:
        True se houver conflito, False caso contrário
    """
    conflicting_appointments = Appointment.objects.filter(
        barber=barber,
        barbershop=barbershop,
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
    ).filter(
        # Verificar sobreposição de horários
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    )

    # Excluir agendamento específico se fornecido
    if exclude_appointment:
        conflicting_appointments = conflicting_appointments.exclude(
            id=exclude_appointment.id
        )

    return conflicting_appointments.exists()


def get_next_available_appointment_slot(
    barber,
    barbershop,
    service_duration_minutes: int = 30,
    days_ahead: int = 30,
) -> Optional[Tuple[datetime, datetime]]:
    """
    Encontra o próximo slot disponível para um agendamento.
    
    Args:
        barber: O barbeiro
        barbershop: A barbearia
        service_duration_minutes: Duração do serviço em minutos
        days_ahead: Número de dias à frente para procurar
    
    Returns:
        Tupla com (start_datetime, end_datetime) ou None se não encontrar
    """
    schedules = BarberSchedule.objects.filter(
        barber=barber,
        barbershop=barbershop,
        is_available=True,
    )

    today = timezone.now().date()
    
    for i in range(days_ahead):
        check_date = today + timedelta(days=i)
        weekday = check_date.weekday()
        
        # Buscar agenda para este dia da semana
        schedule = schedules.filter(weekday=weekday).first()
        if not schedule:
            continue
        
        # Obter slots disponíveis
        available_slots = get_available_time_slots(
            schedule, check_date, service_duration_minutes
        )
        
        if available_slots:
            # Retornar o primeiro slot disponível
            start_time = available_slots[0]
            start_datetime = timezone.make_aware(
                datetime.combine(check_date, start_time)
            )
            end_datetime = start_datetime + timedelta(minutes=service_duration_minutes)
            return (start_datetime, end_datetime)
    
    return None


def calculate_appointment_end_time(
    start_datetime: datetime, service_duration_minutes: int
) -> datetime:
    """
    Calcula o horário de término de um agendamento.
    
    Args:
        start_datetime: Data e hora de início
        service_duration_minutes: Duração do serviço em minutos
    
    Returns:
        Data e hora de término
    """
    return start_datetime + timedelta(minutes=service_duration_minutes)


def is_barber_available(
    barber, barbershop, start_datetime: datetime, end_datetime: datetime
) -> bool:
    """
    Verifica se um barbeiro está disponível em um horário específico.
    
    Args:
        barber: O barbeiro
        barbershop: A barbearia
        start_datetime: Data e hora de início
        end_datetime: Data e hora de término
    
    Returns:
        True se estiver disponível, False caso contrário
    """
    # Verificar se há agenda para o dia da semana
    weekday = start_datetime.weekday()
    schedule = BarberSchedule.objects.filter(
        barber=barber,
        barbershop=barbershop,
        weekday=weekday,
        is_available=True,
    ).first()

    if not schedule:
        return False

    # Verificar se o horário está dentro do período de trabalho
    start_time = start_datetime.time()
    end_time = end_datetime.time()

    if start_time < schedule.start_time or end_time > schedule.end_time:
        return False

    # Verificar conflitos com outros agendamentos
    return not check_appointment_conflict(
        barber, barbershop, start_datetime, end_datetime
    )


def get_appointment_statistics(barbershop=None, start_date=None, end_date=None):
    """
    Retorna estatísticas de agendamentos.
    
    Args:
        barbershop: Filtrar por barbearia específica
        start_date: Data de início do período
        end_date: Data de fim do período
    
    Returns:
        Dicionário com estatísticas
    """
    queryset = Appointment.objects.all()

    if barbershop:
        queryset = queryset.filter(barbershop=barbershop)

    if start_date:
        queryset = queryset.filter(start_datetime__date__gte=start_date)

    if end_date:
        queryset = queryset.filter(start_datetime__date__lte=end_date)

    total_appointments = queryset.count()
    
    stats = {
        "total_appointments": total_appointments,
        "pending": queryset.filter(status=Appointment.Status.PENDING).count(),
        "confirmed": queryset.filter(status=Appointment.Status.CONFIRMED).count(),
        "completed": queryset.filter(status=Appointment.Status.COMPLETED).count(),
        "cancelled": queryset.filter(status=Appointment.Status.CANCELLED).count(),
    }

    if total_appointments > 0:
        stats.update({
            "completion_rate": (stats["completed"] / total_appointments) * 100,
            "cancellation_rate": (stats["cancelled"] / total_appointments) * 100,
        })

    # Receita total (apenas agendamentos concluídos)
    total_revenue = queryset.filter(
        status=Appointment.Status.COMPLETED
    ).aggregate(total=models.Sum("final_price"))["total"] or 0

    stats["total_revenue"] = total_revenue

    return stats


def validate_appointment_datetime(start_datetime: datetime, end_datetime: datetime) -> List[str]:
    """
    Valida as datas e horários de um agendamento.
    
    Args:
        start_datetime: Data e hora de início
        end_datetime: Data e hora de término
    
    Returns:
        Lista de erros de validação
    """
    errors = []
    
    # Verificar se as datas são válidas
    if start_datetime >= end_datetime:
        errors.append("A data e hora de início devem ser antes da data e hora de término")
    
    # Verificar se o agendamento é no passado
    if start_datetime < timezone.now():
        errors.append("Não é possível agendar no passado")
    
    # Verificar se o agendamento é no mesmo dia
    if start_datetime.date() != end_datetime.date():
        errors.append("O agendamento deve começar e terminar no mesmo dia")
    
    return errors