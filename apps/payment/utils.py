from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db import models
from django.utils import timezone

from apps.appointment.models import Appointment

from .models import Payment


def validate_payment_creation(appointment: Appointment) -> Tuple[bool, str]:
    """
    Valida se um pagamento pode ser criado para um agendamento.
    
    Args:
        appointment: O agendamento para criar o pagamento
    
    Returns:
        Tupla com (is_valid, error_message)
    """
    # Verificar se já existe pagamento para este agendamento
    if hasattr(appointment, 'payment'):
        return False, "Este agendamento já possui um pagamento associado."
    
    # Verificar se o agendamento está confirmado ou concluído
    if appointment.status not in [Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED]:
        return False, "Apenas agendamentos confirmados ou concluídos podem ter pagamentos criados."
    
    # Verificar se o agendamento tem um preço final
    if not appointment.final_price or appointment.final_price <= 0:
        return False, "O agendamento deve ter um preço final válido."
    
    return True, ""


def validate_payment_confirmation(payment: Payment) -> Tuple[bool, str]:
    """
    Valida se um pagamento pode ser confirmado.
    
    Args:
        payment: O pagamento a ser confirmado
    
    Returns:
        Tupla com (is_valid, error_message)
    """
    # Verificar se já está pago
    if payment.is_paid():
        return False, "Este pagamento já foi confirmado."
    
    # Verificar se foi reembolsado
    if payment.is_refunded():
        return False, "Não é possível confirmar um pagamento reembolsado."
    
    return True, ""


def validate_payment_refund(payment: Payment) -> Tuple[bool, str]:
    """
    Valida se um pagamento pode ser reembolsado.
    
    Args:
        payment: O pagamento a ser reembolsado
    
    Returns:
        Tupla com (is_valid, error_message)
    """
    # Verificar se está pago
    if not payment.is_paid():
        return False, "Apenas pagamentos realizados podem ser reembolsados."
    
    # Verificar se já foi reembolsado
    if payment.is_refunded():
        return False, "Este pagamento já foi reembolsado."
    
    return True, ""


def calculate_payment_statistics(
    payments_queryset: models.QuerySet = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> Dict:
    """
    Calcula estatísticas detalhadas dos pagamentos.
    
    Args:
        payments_queryset: QuerySet de pagamentos (opcional, usa todos se não fornecido)
        start_date: Data de início para filtro
        end_date: Data de fim para filtro
    
    Returns:
        Dicionário com estatísticas
    """
    if payments_queryset is None:
        payments_queryset = Payment.objects.all()
    
    # Aplicar filtros de data se fornecidos
    if start_date:
        payments_queryset = payments_queryset.filter(created_at__date__gte=start_date)
    if end_date:
        payments_queryset = payments_queryset.filter(created_at__date__lte=end_date)
    
    # Estatísticas gerais
    total_payments = payments_queryset.count()
    paid_payments = payments_queryset.filter(status=Payment.Status.PAID)
    pending_payments = payments_queryset.filter(status=Payment.Status.PENDING)
    refunded_payments = payments_queryset.filter(status=Payment.Status.REFUNDED)
    
    # Receita total
    total_revenue = paid_payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    refunded_amount = refunded_payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    net_revenue = total_revenue - refunded_amount
    
    # Receita por método de pagamento
    revenue_by_method = paid_payments.values('method').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount'),
        avg_amount=models.Avg('amount')
    ).order_by('-total_amount')
    
    # Estatísticas por status
    status_stats = payments_queryset.values('status').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    )
    
    return {
        'total_payments': total_payments,
        'paid_count': paid_payments.count(),
        'pending_count': pending_payments.count(),
        'refunded_count': refunded_payments.count(),
        'total_revenue': total_revenue,
        'refunded_amount': refunded_amount,
        'net_revenue': net_revenue,
        'average_payment': total_revenue / paid_payments.count() if paid_payments.count() > 0 else Decimal('0'),
        'revenue_by_method': list(revenue_by_method),
        'status_distribution': list(status_stats),
    }


def get_payment_trends(
    payments_queryset: models.QuerySet = None,
    period_days: int = 30
) -> Dict:
    """
    Analisa tendências de pagamentos em um período.
    
    Args:
        payments_queryset: QuerySet de pagamentos
        period_days: Número de dias para análise de tendência
    
    Returns:
        Dicionário com dados de tendência
    """
    if payments_queryset is None:
        payments_queryset = Payment.objects.all()
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=period_days)
    
    # Filtrar para o período
    period_payments = payments_queryset.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    # Pagamentos por dia
    daily_payments = period_payments.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount', filter=models.Q(status=Payment.Status.PAID))
    ).order_by('day')
    
    # Métodos de pagamento mais usados
    popular_methods = period_payments.values('method').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Taxa de conversão (pendente para pago)
    total_created = period_payments.count()
    total_paid = period_payments.filter(status=Payment.Status.PAID).count()
    conversion_rate = (total_paid / total_created * 100) if total_created > 0 else 0
    
    return {
        'period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': period_days
        },
        'daily_payments': list(daily_payments),
        'popular_methods': list(popular_methods),
        'conversion_rate': conversion_rate,
        'total_created': total_created,
        'total_paid': total_paid,
    }


def get_overdue_payments(days_overdue: int = 7) -> models.QuerySet:
    """
    Retorna pagamentos pendentes há mais de X dias.
    
    Args:
        days_overdue: Número de dias para considerar como atrasado
    
    Returns:
        QuerySet de pagamentos em atraso
    """
    cutoff_date = timezone.now() - timedelta(days=days_overdue)
    
    return Payment.objects.filter(
        status=Payment.Status.PENDING,
        created_at__lt=cutoff_date
    ).select_related('appointment', 'appointment__customer', 'appointment__service')


def create_payment_from_appointment(appointment: Appointment, **kwargs) -> Tuple[Optional[Payment], str]:
    """
    Cria um pagamento a partir de um agendamento.
    
    Args:
        appointment: O agendamento base
        **kwargs: Argumentos adicionais para o pagamento (method, notes, etc.)
    
    Returns:
        Tupla com (payment_instance, error_message)
    """
    # Validar se pode criar pagamento
    is_valid, error_msg = validate_payment_creation(appointment)
    if not is_valid:
        return None, error_msg
    
    try:
        # Criar pagamento com dados do agendamento
        payment_data = {
            'appointment': appointment,
            'amount': appointment.final_price,
            'method': kwargs.get('method', Payment.Method.PIX),
            'notes': kwargs.get('notes', ''),
        }
        
        # Se for dinheiro, marcar como pago imediatamente
        if payment_data['method'] == Payment.Method.CASH:
            payment_data['status'] = Payment.Status.PAID
            payment_data['payment_date'] = timezone.now()
        
        payment = Payment.objects.create(**payment_data)
        return payment, ""
        
    except Exception as e:
        return None, f"Erro ao criar pagamento: {str(e)}"


def get_user_payment_summary(user, start_date: Optional[datetime.date] = None) -> Dict:
    """
    Retorna resumo de pagamentos para um usuário específico.
    
    Args:
        user: O usuário (cliente, barbeiro ou dono de barbearia)
        start_date: Data de início para filtro
    
    Returns:
        Dicionário com resumo dos pagamentos
    """
    # Determinar qual filtro usar baseado no tipo de usuário
    if user.is_client():
        payments = Payment.objects.filter(appointment__customer=user)
    elif user.is_barber():
        payments = Payment.objects.filter(appointment__barber=user)
    elif user.is_barbershop_owner:
        payments = Payment.objects.filter(appointment__barbershop__owner=user)
    elif hasattr(user, 'role') and user.role == "ADMIN":
        payments = Payment.objects.all()
    else:
        return {}
    
    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)
    
    return calculate_payment_statistics(payments)
