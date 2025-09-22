from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointment.models import Appointment
from apps.barbershop.models import Barbershop, BarbershopCustomer, Service
from apps.review.models import Review
from apps.review.permissions import (CanCreateReview, CanDeleteReview,
                                     CanUpdateOwnReview,
                                     IsReviewOwnerOrBarbershopOwnerOrAdmin)
from apps.review.serializers import (ReviewCreateSerializer,
                                     ReviewDetailSerializer,
                                     ReviewListSerializer,
                                     ReviewUpdateSerializer)
from apps.review.utils import (calculate_review_statistics,
                               can_user_delete_review, can_user_review,
                               can_user_update_review,
                               validate_review_creation)
from apps.user.models import User


class ReviewModelTests(TestCase):
    """Testes para o modelo Review"""
    
    def setUp(self):
        """Configura dados de teste"""
        # Criar usuários
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        # Criar barbearia
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        # Criar serviço
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        # Criar customer relationship
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
    
    def test_review_creation(self):
        """Testa a criação de uma avaliação"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5,
            comment="Excelente serviço!"
        )
        
        self.assertIsNotNone(review.id)
        self.assertEqual(review.barbershop_customer, self.customer)
        self.assertEqual(review.barber, self.barber_user)
        self.assertEqual(review.service, self.service)
        self.assertEqual(review.barbershop, self.barbershop)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Excelente serviço!")
    
    def test_review_str(self):
        """Testa a representação string da avaliação"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=4,
            comment="Bom atendimento"
        )
        
        expected_str = f"{self.customer} - {self.barber_user} - {self.service} - 4 - Bom atendimento - {review.created_at}"
        self.assertEqual(str(review), expected_str)
    
    def test_review_type_methods(self):
        """Testa os métodos de verificação de tipo de avaliação"""
        # Avaliação positiva (5 estrelas)
        positive_review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5
        )
        
        self.assertTrue(positive_review.is_positive_review())
        self.assertFalse(positive_review.is_negative_review())
        self.assertFalse(positive_review.is_neutral_review())
        
        # Criar outra combinação para teste negativo
        client2 = User.objects.create_user(
            username="client2@test.com",
            email="client2@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        customer2 = BarbershopCustomer.objects.create(
            customer=client2,
            barbershop=self.barbershop
        )
        
        # Avaliação negativa (2 estrelas)
        negative_review = Review.objects.create(
            barbershop_customer=customer2,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=2
        )
        
        self.assertFalse(negative_review.is_positive_review())
        self.assertTrue(negative_review.is_negative_review())
        self.assertFalse(negative_review.is_neutral_review())
    
    def test_has_comment(self):
        """Testa verificação de comentário"""
        review_with_comment = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5,
            comment="Ótimo!"
        )
        
        self.assertTrue(review_with_comment.has_comment())
    
    def test_get_rating_stars(self):
        """Testa a exibição de estrelas"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=4
        )
        
        self.assertEqual(review.get_rating_stars(), "⭐⭐⭐⭐")
    
    def test_get_names(self):
        """Testa os métodos de obtenção de nomes"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5
        )
        
        self.assertEqual(review.get_customer_name(), self.client_user.get_display_name())
        self.assertEqual(review.get_barber_name(), self.barber_user.get_display_name())
        self.assertEqual(review.get_service_name(), self.service.name)
        self.assertEqual(review.get_barbershop_name(), self.barbershop.name)
    
    def test_is_recent_review(self):
        """Testa verificação de avaliação recente"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5
        )
        
        # Avaliação recém criada deve ser recente
        self.assertTrue(review.is_recent_review())


class ReviewSerializerTests(APITestCase):
    """Testes para os serializers de Review"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento para validação
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        self.review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5,
            comment="Excelente serviço!"
        )
    
    def test_review_create_serializer_valid(self):
        """Testa criação de avaliação com dados válidos"""
        # Criar outro cliente para evitar unique constraint
        client2 = User.objects.create_user(
            username="client2@test.com",
            email="client2@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        customer2 = BarbershopCustomer.objects.create(
            customer=client2,
            barbershop=self.barbershop
        )
        
        # Criar agendamento para o novo cliente
        Appointment.objects.create(
            customer=customer2,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=2),
            end_datetime=timezone.now() + timedelta(hours=2, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        data = {
            'barbershop_customer_id': customer2.id,
            'barber_id': self.barber_user.id,
            'service_id': self.service.id,
            'barbershop_id': self.barbershop.id,
            'rating': 4,
            'comment': 'Bom serviço!'
        }
        
        serializer = ReviewCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        review = serializer.save()
        
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Bom serviço!')
    
    def test_review_create_serializer_invalid_rating(self):
        """Testa validação de rating inválido"""
        data = {
            'barbershop_customer_id': self.customer.id,
            'barber_id': self.barber_user.id,
            'service_id': self.service.id,
            'barbershop_id': self.barbershop.id,
            'rating': 6,  # Rating inválido
            'comment': 'Teste'
        }
        
        serializer = ReviewCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rating', serializer.errors)
    
    def test_review_create_serializer_duplicate(self):
        """Testa validação de avaliação duplicada"""
        data = {
            'barbershop_customer_id': self.customer.id,
            'barber_id': self.barber_user.id,
            'service_id': self.service.id,
            'barbershop_id': self.barbershop.id,
            'rating': 3,
            'comment': 'Teste duplicado'
        }
        
        serializer = ReviewCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_review_update_serializer_valid(self):
        """Testa atualização de avaliação com dados válidos"""
        data = {
            'rating': 4,
            'comment': 'Atualizado!'
        }
        
        serializer = ReviewUpdateSerializer(self.review, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_review = serializer.save()
        
        self.assertEqual(updated_review.rating, 4)
        self.assertEqual(updated_review.comment, 'Atualizado!')


class ReviewUtilsTests(TestCase):
    """Testes para as funções utilitárias de Review"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento confirmado
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
    
    def test_validate_review_creation_valid(self):
        """Testa validação de criação de avaliação válida"""
        is_valid, message = validate_review_creation(
            self.customer,
            self.barber_user,
            self.service,
            self.barbershop
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Validação passou com sucesso.")
    
    def test_validate_review_creation_duplicate(self):
        """Testa validação com avaliação já existente"""
        # Criar uma avaliação primeiro
        Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5
        )
        
        is_valid, message = validate_review_creation(
            self.customer,
            self.barber_user,
            self.service,
            self.barbershop
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Já existe uma avaliação", message)
    
    def test_can_user_review_valid(self):
        """Testa se usuário pode criar avaliação"""
        can_review, reason = can_user_review(
            self.client_user,
            self.customer,
            self.barber_user,
            self.service,
            self.barbershop
        )
        
        self.assertTrue(can_review)
        self.assertEqual(reason, "Usuário pode criar a avaliação.")
    
    def test_calculate_review_statistics(self):
        """Testa cálculo de estatísticas de avaliações"""
        # Criar algumas avaliações
        Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5,
            comment="Excelente!"
        )
        
        stats = calculate_review_statistics()
        
        self.assertEqual(stats['total_reviews'], 1)
        self.assertEqual(stats['positive_reviews'], 1)
        self.assertEqual(stats['average_rating'], Decimal('5.00'))
        self.assertEqual(stats['reviews_with_comments'], 1)
    
    def test_can_user_update_review(self):
        """Testa se usuário pode atualizar avaliação"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=4
        )
        
        # Cliente que criou pode atualizar
        self.assertTrue(can_user_update_review(self.client_user, review))
        
        # Outro usuário não pode
        self.assertFalse(can_user_update_review(self.barber_user, review))
    
    def test_can_user_delete_review(self):
        """Testa se usuário pode deletar avaliação"""
        review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=4
        )
        
        # Cliente que criou pode deletar
        self.assertTrue(can_user_delete_review(self.client_user, review))
        
        # Dono da barbearia pode deletar
        self.assertTrue(can_user_delete_review(self.owner_user, review))
        
        # Barbeiro não pode deletar (apenas ver)
        self.assertFalse(can_user_delete_review(self.barber_user, review))


class ReviewViewSetTests(APITestCase):
    """Testes para o ViewSet de Review"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.client_user = User.objects.create_user(
            username="client@test.com",
            email="client@test.com",
            password="testpass123",
            role=User.Role.CLIENT
        )
        
        self.barber_user = User.objects.create_user(
            username="barber@test.com",
            email="barber@test.com",
            password="testpass123",
            role=User.Role.BARBER
        )
        
        self.owner_user = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123",
            role=User.Role.CLIENT,
            is_barbershop_owner=True
        )
        
        self.barbershop = Barbershop.objects.create(
            name="Test Barbershop",
            owner=self.owner_user,
            address="Test Address",
            phone="123456789"
        )
        
        self.service = Service.objects.create(
            name="Corte de Cabelo",
            barbershop=self.barbershop,
            price=Decimal('30.00'),
            duration=timedelta(minutes=30)
        )
        
        self.customer = BarbershopCustomer.objects.create(
            customer=self.client_user,
            barbershop=self.barbershop
        )
        
        # Criar agendamento para validação
        self.appointment = Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=1),
            end_datetime=timezone.now() + timedelta(hours=1, minutes=30),
            final_price=Decimal('30.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        # Criar avaliação de teste
        self.review = Review.objects.create(
            barbershop_customer=self.customer,
            barber=self.barber_user,
            service=self.service,
            barbershop=self.barbershop,
            rating=5,
            comment="Excelente serviço!"
        )
    
    def test_list_reviews_unauthenticated(self):
        """Testa listagem de avaliações sem autenticação"""
        response = self.client.get('/api/v1/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_reviews_as_client(self):
        """Testa listagem de avaliações como cliente"""
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.get('/api/v1/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_review_as_client(self):
        """Testa criação de avaliação como cliente"""
        self.client.force_authenticate(user=self.client_user)
        
        # Criar outro serviço para evitar unique constraint
        service2 = Service.objects.create(
            name="Barba",
            barbershop=self.barbershop,
            price=Decimal('20.00'),
            duration=timedelta(minutes=20)
        )
        
        # Criar agendamento para novo serviço
        Appointment.objects.create(
            customer=self.customer,
            barber=self.barber_user,
            service=service2,
            barbershop=self.barbershop,
            start_datetime=timezone.now() + timedelta(hours=2),
            end_datetime=timezone.now() + timedelta(hours=2, minutes=20),
            final_price=Decimal('20.00'),
            status=Appointment.Status.CONFIRMED
        )
        
        data = {
            'barbershop_customer_id': self.customer.id,
            'barber_id': self.barber_user.id,
            'service_id': service2.id,
            'barbershop_id': self.barbershop.id,
            'rating': 4,
            'comment': 'Bom serviço!'
        }
        
        response = self.client.post('/api/v1/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.filter(service=service2).count(), 1)
    
    def test_update_review_as_owner(self):
        """Testa atualização de avaliação como dono"""
        self.client.force_authenticate(user=self.client_user)
        
        data = {
            'rating': 4,
            'comment': 'Atualizado!'
        }
        
        response = self.client.patch(f'/api/v1/reviews/{self.review.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.comment, 'Atualizado!')
    
    def test_delete_review_as_owner(self):
        """Testa exclusão de avaliação como dono"""
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.delete(f'/api/v1/reviews/{self.review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())
    
    def test_my_reviews_action(self):
        """Testa ação my-reviews"""
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.get('/api/v1/reviews/my_reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_statistics_action(self):
        """Testa ação statistics"""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/v1/reviews/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reviews', response.data)
        self.assertIn('average_rating', response.data)
    
    def test_top_rated_action(self):
        """Testa ação top-rated"""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.get('/api/v1/reviews/top_rated/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_barbers', response.data)
        self.assertIn('top_services', response.data)
