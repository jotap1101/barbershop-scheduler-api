from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.appointment.models import Appointment
from apps.barbershop.models import Barbershop, BarbershopCustomer, Service
from apps.payment.models import Payment
from apps.review.models import Review
from apps.user.models import User


def get_dashboard_overview() -> Dict:
    """
    Retorna dados gerais para o dashboard administrativo.
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # Contadores gerais
    total_barbershops = Barbershop.objects.count()
    total_users = User.objects.count()
    active_barbers = User.objects.filter(role=User.Role.BARBER, is_active=True).count()

    # Agendamentos hoje
    appointments_today = Appointment.objects.filter(start_datetime__date=today).count()

    # Agendamentos pendentes
    pending_appointments = Appointment.objects.filter(
        status=Appointment.Status.PENDING
    ).count()

    # Receita hoje
    revenue_today = Payment.objects.filter(
        payment_date=today, status=Payment.Status.PAID
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Agendamentos este mês
    appointments_this_month = Appointment.objects.filter(
        start_datetime__date__gte=start_of_month
    ).count()

    # Receita este mês
    revenue_this_month = Payment.objects.filter(
        payment_date__gte=start_of_month, status=Payment.Status.PAID
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    return {
        "total_barbershops": total_barbershops,
        "total_users": total_users,
        "total_appointments_today": appointments_today,
        "total_revenue_today": revenue_today,
        "total_appointments_this_month": appointments_this_month,
        "total_revenue_this_month": revenue_this_month,
        "active_barbers": active_barbers,
        "pending_appointments": pending_appointments,
    }


def get_barbershop_analytics(barbershop_id: str) -> Optional[Dict]:
    """
    Retorna analytics específicas de uma barbearia.
    """
    try:
        barbershop = Barbershop.objects.get(id=barbershop_id)
    except Barbershop.DoesNotExist:
        return None

    start_of_month = timezone.now().date().replace(day=1)

    # Métricas básicas
    total_customers = barbershop.get_total_customers()
    total_appointments = barbershop.get_total_appointments()
    total_revenue = barbershop.get_total_revenue()

    # Agendamentos e receita deste mês
    appointments_this_month = Appointment.objects.filter(
        barbershop=barbershop, start_datetime__date__gte=start_of_month
    ).count()

    revenue_this_month = Payment.objects.filter(
        appointment__barbershop=barbershop,
        payment_date__gte=start_of_month,
        status=Payment.Status.PAID,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Avaliação média
    average_rating = Review.objects.filter(barbershop=barbershop).aggregate(
        avg=Avg("rating")
    )["avg"] or Decimal("0.00")

    # Serviço mais popular
    popular_service = (
        Service.objects.filter(barbershop=barbershop)
        .annotate(appointment_count=Count("appointments"))
        .order_by("-appointment_count")
        .first()
    )

    # Barbeiro mais popular
    popular_barber = (
        User.objects.filter(
            barber_appointments__barbershop=barbershop, role=User.Role.BARBER
        )
        .annotate(appointment_count=Count("barber_appointments"))
        .order_by("-appointment_count")
        .first()
    )

    return {
        "barbershop_id": barbershop.id,
        "barbershop_name": barbershop.name,
        "total_customers": total_customers,
        "total_appointments": total_appointments,
        "total_revenue": total_revenue,
        "average_rating": (
            round(average_rating, 2) if average_rating else Decimal("0.00")
        ),
        "appointments_this_month": appointments_this_month,
        "revenue_this_month": revenue_this_month,
        "top_service": popular_service.name if popular_service else None,
        "most_popular_barber": (
            popular_barber.get_full_name() if popular_barber else None
        ),
    }


def get_barber_performance(barber_id: str) -> Optional[Dict]:
    """
    Retorna métricas de performance de um barbeiro.
    """
    try:
        barber = User.objects.get(id=barber_id, role=User.Role.BARBER)
    except User.DoesNotExist:
        return None

    start_of_month = timezone.now().date().replace(day=1)

    # Agendamentos totais
    total_appointments = Appointment.objects.filter(barber=barber).count()

    # Agendamentos deste mês
    appointments_this_month = Appointment.objects.filter(
        barber=barber, start_datetime__date__gte=start_of_month
    ).count()

    # Receita total
    total_revenue = Payment.objects.filter(
        appointment__barber=barber, status=Payment.Status.PAID
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Receita deste mês
    revenue_this_month = Payment.objects.filter(
        appointment__barber=barber,
        payment_date__gte=start_of_month,
        status=Payment.Status.PAID,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Avaliação média
    average_rating = Review.objects.filter(barber=barber).aggregate(avg=Avg("rating"))[
        "avg"
    ] or Decimal("0.00")

    # Taxa de conclusão
    completed_appointments = Appointment.objects.filter(
        barber=barber, status=Appointment.Status.COMPLETED
    ).count()

    completion_rate = Decimal("0.00")
    if total_appointments > 0:
        completion_rate = (
            Decimal(completed_appointments) / Decimal(total_appointments)
        ) * 100

    return {
        "barber_id": barber.id,
        "barber_name": barber.get_full_name(),
        "total_appointments": total_appointments,
        "total_revenue": total_revenue,
        "average_rating": (
            round(average_rating, 2) if average_rating else Decimal("0.00")
        ),
        "appointments_this_month": appointments_this_month,
        "revenue_this_month": revenue_this_month,
        "completion_rate": round(completion_rate, 2),
    }


def get_revenue_analytics(period: str = "daily", days: int = 30) -> List[Dict]:
    """
    Retorna analytics de receita por período.
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    analytics = []

    if period == "daily":
        current_date = start_date
        while current_date <= end_date:
            payments = Payment.objects.filter(
                payment_date=current_date, status=Payment.Status.PAID
            )

            revenue = payments.aggregate(total=Sum("amount"))["total"] or Decimal(
                "0.00"
            )
            appointments_count = payments.count()
            average_ticket = (
                revenue / appointments_count
                if appointments_count > 0
                else Decimal("0.00")
            )

            analytics.append(
                {
                    "period": "daily",
                    "date": current_date,
                    "revenue": revenue,
                    "appointments_count": appointments_count,
                    "average_ticket": round(average_ticket, 2),
                }
            )

            current_date += timedelta(days=1)

    return analytics


def get_service_popularity(barbershop_id: Optional[str] = None) -> List[Dict]:
    """
    Retorna popularidade dos serviços.
    """
    services = Service.objects.all()

    if barbershop_id:
        try:
            barbershop = Barbershop.objects.get(id=barbershop_id)
            services = services.filter(barbershop=barbershop)
        except Barbershop.DoesNotExist:
            return []

    services = services.annotate(
        appointment_count=Count("appointments"),
        total_revenue=Sum(
            "appointments__payment__amount",
            filter=Q(appointments__payment__status=Payment.Status.PAID),
        ),
        avg_rating=Avg("reviews__rating"),
    ).order_by("-appointment_count")

    total_appointments = sum(service.appointment_count for service in services)

    popularity_data = []
    for service in services:
        booking_percentage = Decimal("0.00")
        if total_appointments > 0:
            booking_percentage = (
                Decimal(service.appointment_count) / Decimal(total_appointments)
            ) * 100

        popularity_data.append(
            {
                "service_id": service.id,
                "service_name": service.name,
                "barbershop_name": service.barbershop.name,
                "appointments_count": service.appointment_count,
                "total_revenue": service.total_revenue or Decimal("0.00"),
                "average_rating": (
                    round(service.avg_rating, 2)
                    if service.avg_rating
                    else Decimal("0.00")
                ),
                "booking_percentage": round(booking_percentage, 2),
            }
        )

    return popularity_data


def get_customer_insights(barbershop_id: Optional[str] = None) -> Dict:
    """
    Retorna insights sobre clientes.
    """
    start_of_month = timezone.now().date().replace(day=1)

    if barbershop_id:
        try:
            barbershop = Barbershop.objects.get(id=barbershop_id)
            customers = BarbershopCustomer.objects.filter(barbershop=barbershop)
        except Barbershop.DoesNotExist:
            return {}
    else:
        customers = BarbershopCustomer.objects.all()

    total_customers = customers.count()

    # Novos clientes este mês (baseado na data de criação dos agendamentos)
    new_customers_this_month = (
        customers.filter(appointments__start_datetime__date__gte=start_of_month)
        .distinct()
        .count()
    )

    # Clientes que retornaram (têm mais de um agendamento)
    returning_customers = (
        customers.annotate(appointment_count=Count("appointments"))
        .filter(appointment_count__gt=1)
        .count()
    )

    # Média de agendamentos por cliente
    total_appointments = customers.aggregate(total=Count("appointments"))["total"] or 0
    avg_appointments = (
        Decimal(total_appointments) / Decimal(total_customers)
        if total_customers > 0
        else Decimal("0.00")
    )

    # Taxa de retenção (clientes com mais de 1 visita)
    retention_rate = (
        (Decimal(returning_customers) / Decimal(total_customers)) * 100
        if total_customers > 0
        else Decimal("0.00")
    )

    # Cliente mais frequente (baseado no número de agendamentos)
    frequent_customer = (
        customers.annotate(appointment_count=Count("appointments"))
        .order_by("-appointment_count")
        .first()
    )

    return {
        "total_customers": total_customers,
        "new_customers_this_month": new_customers_this_month,
        "returning_customers": returning_customers,
        "average_appointments_per_customer": round(avg_appointments, 2),
        "customer_retention_rate": round(retention_rate, 2),
        "most_frequent_customer": (
            frequent_customer.customer.get_full_name() if frequent_customer else None
        ),
    }
