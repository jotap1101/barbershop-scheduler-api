from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.appointment.models import Appointment
from apps.barbershop.models import Barbershop, BarbershopCustomer
from apps.review.models import Review
from apps.user.models import User


def validate_review_creation(barbershop_customer, barber, service, barbershop):
    """
    Valida se uma avaliação pode ser criada com os parâmetros fornecidos.
    
    Args:
        barbershop_customer: Instância de BarbershopCustomer
        barber: Instância de User (barbeiro)
        service: Instância de Service
        barbershop: Instância de Barbershop
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Verificar se o serviço pertence à barbearia
    if service.barbershop != barbershop:
        return False, "O serviço deve pertencer à barbearia informada."
    
    # Verificar se o cliente pertence à barbearia
    if barbershop_customer.barbershop != barbershop:
        return False, "O cliente deve pertencer à barbearia informada."
    
    # Verificar se já existe uma avaliação com essa combinação
    if Review.objects.filter(
        barbershop_customer=barbershop_customer,
        barber=barber,
        service=service,
        barbershop=barbershop
    ).exists():
        return False, "Já existe uma avaliação para esta combinação."
    
    # Verificar se existe um agendamento confirmado ou finalizado
    appointment_exists = Appointment.objects.filter(
        customer=barbershop_customer,
        barber=barber,
        service=service,
        barbershop=barbershop,
        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED]
    ).exists()
    
    if not appointment_exists:
        return False, "Só é possível avaliar após ter um agendamento confirmado ou finalizado."
    
    return True, "Validação passou com sucesso."


def can_user_review(user, barbershop_customer, barber, service, barbershop):
    """
    Verifica se um usuário pode criar uma avaliação específica.
    
    Args:
        user: Usuário que deseja fazer a avaliação
        barbershop_customer: Cliente da barbearia
        barber: Barbeiro a ser avaliado
        service: Serviço a ser avaliado
        barbershop: Barbearia
        
    Returns:
        tuple: (can_review: bool, reason: str)
    """
    # Verificar se o usuário é o cliente da avaliação
    if barbershop_customer.customer != user:
        return False, "Usuário não é o cliente desta barbearia."
    
    # Verificar se o usuário é realmente um cliente
    if not (hasattr(user, 'role') and user.role == 'CLIENT'):
        return False, "Usuário deve ter role de cliente."
    
    # Usar validação padrão
    is_valid, message = validate_review_creation(
        barbershop_customer, barber, service, barbershop
    )
    
    if not is_valid:
        return False, message
    
    return True, "Usuário pode criar a avaliação."


def calculate_review_statistics(queryset=None, barbershop=None, barber=None, service=None):
    """
    Calcula estatísticas detalhadas de avaliações.
    
    Args:
        queryset: QuerySet de reviews (opcional)
        barbershop: Filtrar por barbearia específica (opcional)
        barber: Filtrar por barbeiro específico (opcional)
        service: Filtrar por serviço específico (opcional)
        
    Returns:
        dict: Estatísticas das avaliações
    """
    if queryset is None:
        queryset = Review.objects.all()
    
    # Aplicar filtros se fornecidos
    if barbershop:
        queryset = queryset.filter(barbershop=barbershop)
    if barber:
        queryset = queryset.filter(barber=barber)
    if service:
        queryset = queryset.filter(service=service)
    
    # Estatísticas básicas
    total_reviews = queryset.count()
    
    if total_reviews == 0:
        return {
            'total_reviews': 0,
            'average_rating': Decimal('0.00'),
            'rating_distribution': {i: 0 for i in range(1, 6)},
            'positive_reviews': 0,
            'negative_reviews': 0,
            'neutral_reviews': 0,
            'reviews_with_comments': 0,
            'recent_reviews': 0,
            'percentage_positive': Decimal('0.00'),
            'percentage_negative': Decimal('0.00'),
            'percentage_with_comments': Decimal('0.00')
        }
    
    # Média de avaliações
    avg_rating = queryset.aggregate(avg=Avg('rating'))['avg'] or Decimal('0.00')
    avg_rating = Decimal(str(round(avg_rating, 2)))
    
    # Distribuição por rating
    rating_distribution = {}
    for rating in range(1, 6):
        count = queryset.filter(rating=rating).count()
        rating_distribution[rating] = count
    
    # Contadores por tipo
    positive_reviews = queryset.filter(rating__gte=4).count()
    negative_reviews = queryset.filter(rating__lte=2).count()
    neutral_reviews = queryset.filter(rating=3).count()
    
    # Reviews com comentários
    reviews_with_comments = queryset.exclude(
        Q(comment__isnull=True) | Q(comment__exact='')
    ).count()
    
    # Reviews recentes (últimos 7 dias)
    recent_date = timezone.now() - timedelta(days=7)
    recent_reviews = queryset.filter(created_at__gte=recent_date).count()
    
    # Percentuais
    percentage_positive = Decimal(str(round((positive_reviews / total_reviews) * 100, 2)))
    percentage_negative = Decimal(str(round((negative_reviews / total_reviews) * 100, 2)))
    percentage_with_comments = Decimal(str(round((reviews_with_comments / total_reviews) * 100, 2)))
    
    return {
        'total_reviews': total_reviews,
        'average_rating': avg_rating,
        'rating_distribution': rating_distribution,
        'positive_reviews': positive_reviews,
        'negative_reviews': negative_reviews,
        'neutral_reviews': neutral_reviews,
        'reviews_with_comments': reviews_with_comments,
        'recent_reviews': recent_reviews,
        'percentage_positive': percentage_positive,
        'percentage_negative': percentage_negative,
        'percentage_with_comments': percentage_with_comments
    }


def get_top_rated_barbers(limit=10, barbershop=None):
    """
    Retorna os barbeiros com melhor avaliação.
    
    Args:
        limit: Número máximo de resultados
        barbershop: Filtrar por barbearia específica (opcional)
        
    Returns:
        QuerySet: Barbeiros ordenados por avaliação média
    """
    queryset = User.objects.filter(role=User.Role.BARBER)
    
    if barbershop:
        queryset = queryset.filter(reviews__barbershop=barbershop)
    
    return queryset.annotate(
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).filter(
        total_reviews__gt=0  # Apenas barbeiros com pelo menos uma avaliação
    ).order_by('-avg_rating', '-total_reviews')[:limit]


def get_top_rated_services(limit=10, barbershop=None):
    """
    Retorna os serviços com melhor avaliação.
    
    Args:
        limit: Número máximo de resultados
        barbershop: Filtrar por barbearia específica (opcional)
        
    Returns:
        QuerySet: Serviços ordenados por avaliação média
    """
    from apps.barbershop.models import Service
    
    queryset = Service.objects.filter(available=True)
    
    if barbershop:
        queryset = queryset.filter(barbershop=barbershop)
    
    return queryset.annotate(
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).filter(
        total_reviews__gt=0  # Apenas serviços com pelo menos uma avaliação
    ).order_by('-avg_rating', '-total_reviews')[:limit]


def get_top_rated_barbershops(limit=10):
    """
    Retorna as barbearias com melhor avaliação.
    
    Args:
        limit: Número máximo de resultados
        
    Returns:
        QuerySet: Barbearias ordenadas por avaliação média
    """
    return Barbershop.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).filter(
        total_reviews__gt=0  # Apenas barbearias com pelo menos uma avaliação
    ).order_by('-avg_rating', '-total_reviews')[:limit]


def get_review_trends(days=30, barbershop=None):
    """
    Retorna tendências de avaliações nos últimos X dias.
    
    Args:
        days: Número de dias para análise
        barbershop: Filtrar por barbearia específica (opcional)
        
    Returns:
        dict: Dados de tendência
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    queryset = Review.objects.filter(created_at__range=[start_date, end_date])
    
    if barbershop:
        queryset = queryset.filter(barbershop=barbershop)
    
    total_period = queryset.count()
    avg_rating_period = queryset.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Compara com período anterior
    previous_start = start_date - timedelta(days=days)
    previous_queryset = Review.objects.filter(
        created_at__range=[previous_start, start_date]
    )
    
    if barbershop:
        previous_queryset = previous_queryset.filter(barbershop=barbershop)
    
    total_previous = previous_queryset.count()
    avg_rating_previous = previous_queryset.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Calcular tendências
    volume_change = total_period - total_previous
    rating_change = avg_rating_period - avg_rating_previous
    
    return {
        'period_days': days,
        'current_period': {
            'total_reviews': total_period,
            'average_rating': round(avg_rating_period, 2)
        },
        'previous_period': {
            'total_reviews': total_previous,
            'average_rating': round(avg_rating_previous, 2)
        },
        'changes': {
            'volume_change': volume_change,
            'rating_change': round(rating_change, 2)
        }
    }


def format_rating_display(rating):
    """
    Formata a exibição de uma avaliação.
    
    Args:
        rating: Valor da avaliação (1-5)
        
    Returns:
        str: Avaliação formatada com estrelas
    """
    stars = "⭐" * rating
    empty_stars = "☆" * (5 - rating)
    return f"{stars}{empty_stars} ({rating}/5)"


def can_user_update_review(user, review):
    """
    Verifica se um usuário pode atualizar uma avaliação específica.
    
    Args:
        user: Usuário
        review: Instância de Review
        
    Returns:
        bool: Se pode atualizar
    """
    # Apenas o cliente que criou a avaliação pode editá-la
    return review.barbershop_customer.customer == user


def can_user_delete_review(user, review):
    """
    Verifica se um usuário pode deletar uma avaliação específica.
    
    Args:
        user: Usuário
        review: Instância de Review
        
    Returns:
        bool: Se pode deletar
    """
    # Admins podem deletar qualquer avaliação
    if hasattr(user, 'role') and user.role == 'ADMIN':
        return True
    
    # Donos de barbearia podem deletar avaliações de sua barbearia
    if hasattr(user, 'is_barbershop_owner') and user.is_barbershop_owner:
        if review.barbershop.owner == user:
            return True
    
    # Cliente que fez a avaliação pode deletá-la
    if review.barbershop_customer.customer == user:
        return True
    
    return False
