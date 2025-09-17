from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from apps.barbershops.models import Barbershop, Service, Barber, BarbershopCustomer
from apps.appointments.models import Appointment, BarberSchedule
from apps.payments.models import Payment
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates fake data for testing purposes'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker('pt_BR')
        # Store created instances for relationships
        self.users = {
            'owners': [],
            'barbers': [],
            'clients': []
        }
        self.barbershops = []
        self.services = []
        self.barber_profiles = []

    def handle(self, *args, **options):
        self.stdout.write('Cleaning existing data...')
        self._clean_data()
        
        self.stdout.write('Creating users...')
        self._create_users()
        
        self.stdout.write('Creating barbershops...')
        self._create_barbershops()
        
        self.stdout.write('Creating services...')
        self._create_services()
        
        self.stdout.write('Creating barber profiles...')
        self._create_barber_profiles()
        
        self.stdout.write('Creating barber schedules...')
        self._create_barber_schedules()
        
        self.stdout.write('Creating barbershop customers...')
        self._create_barbershop_customers()
        
        self.stdout.write('Creating appointments...')
        self._create_appointments()
        
        self.stdout.write('Creating payments...')
        self._create_payments()
        
        self.stdout.write(self.style.SUCCESS('Fake data generated successfully!'))

    def _clean_data(self):
        Payment.objects.all().delete()
        Appointment.objects.all().delete()
        BarberSchedule.objects.all().delete()
        BarbershopCustomer.objects.all().delete()
        Service.objects.all().delete()
        Barber.objects.all().delete()
        Barbershop.objects.all().delete()
        User.objects.exclude(username='admin').delete()

    def _create_users(self):
        # Create owners
        for _ in range(5):
            user = User.objects.create_user(
                username=self.fake.user_name(),
                email=self.fake.email(),
                password='password123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                role='OWNER',
                phone=self.fake.phone_number(),
                birth_date=self.fake.date_of_birth(minimum_age=25, maximum_age=60)
            )
            self.users['owners'].append(user)

        # Create barbers
        for _ in range(15):
            user = User.objects.create_user(
                username=self.fake.user_name(),
                email=self.fake.email(),
                password='password123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                role='BARBER',
                phone=self.fake.phone_number(),
                birth_date=self.fake.date_of_birth(minimum_age=20, maximum_age=50)
            )
            self.users['barbers'].append(user)

        # Create clients
        for _ in range(50):
            user = User.objects.create_user(
                username=self.fake.user_name(),
                email=self.fake.email(),
                password='password123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                role='CLIENT',
                phone=self.fake.phone_number(),
                birth_date=self.fake.date_of_birth(minimum_age=16, maximum_age=80)
            )
            self.users['clients'].append(user)

    def _create_barbershops(self):
        for owner in self.users['owners']:
            barbershop = Barbershop.objects.create(
                name=f"{self.fake.company()} Barbearia",
                address=self.fake.address(),
                phone=self.fake.phone_number(),
                owner=owner,
                description=self.fake.paragraph()
            )
            self.barbershops.append(barbershop)

    def _create_services(self):
        service_templates = [
            ('Corte de Cabelo', 'Corte tradicional ou moderno', 40, 30),
            ('Barba', 'Aparar e modelar a barba', 30, 20),
            ('Corte + Barba', 'Pacote completo', 65, 45),
            ('Design de Sobrancelha', 'Modelagem de sobrancelha', 25, 15),
            ('Coloração', 'Pintura de cabelo', 80, 60),
            ('Hidratação', 'Tratamento capilar', 50, 40)
        ]

        for barbershop in self.barbershops:
            for name, desc, price, duration in service_templates:
                # Add some price variation
                final_price = price + random.randint(-5, 15)
                service = Service.objects.create(
                    barbershop=barbershop,
                    name=name,
                    description=desc,
                    price=final_price,
                    duration=duration
                )
                self.services.append(service)

    def _create_barber_profiles(self):
        specialties = [
            'Cortes modernos', 'Barbas', 'Coloração', 
            'Cortes clássicos', 'Desenhos', 'Tratamentos capilares'
        ]

        for barber_user in self.users['barbers']:
            barber = Barber.objects.create(
                user=barber_user,
                specialties=', '.join(random.sample(specialties, k=random.randint(2, 4))),
                experience_years=random.randint(1, 20)
            )
            # Assign to 1-3 random barbershops
            assigned_barbershops = random.sample(self.barbershops, k=random.randint(1, 3))
            barber.barbershops.set(assigned_barbershops)
            self.barber_profiles.append(barber)

    def _create_barber_schedules(self):
        for barber in self.barber_profiles:
            for barbershop in barber.barbershops.all():
                # Create schedules for weekdays
                for weekday in range(0, 6):  # Monday to Saturday
                    if random.random() > 0.2:  # 80% chance of working each day
                        start_hour = random.choice([8, 9, 10])
                        BarberSchedule.objects.create(
                            barber=barber.user,
                            barbershop=barbershop,
                            weekday=weekday,
                            start_time=f'{start_hour:02d}:00',
                            end_time=f'{start_hour+9:02d}:00',
                            is_available=True
                        )

    def _create_barbershop_customers(self):
        for client in self.users['clients']:
            # Each client is registered in 1-3 random barbershops
            for barbershop in random.sample(self.barbershops, k=random.randint(1, 3)):
                BarbershopCustomer.objects.create(
                    customer=client,
                    barbershop=barbershop,
                    loyalty_points=random.randint(0, 1000),
                    last_visit=self.fake.date_time_between(
                        start_date='-1y',
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    )
                )

    def _create_appointments(self):
        statuses = ['COMPLETED', 'CANCELLED', 'PENDING', 'CONFIRMED']
        weights = [60, 10, 15, 15]  # More completed appointments

        # Get all barbershop customers
        customers = BarbershopCustomer.objects.all()

        for customer in customers:
            # Create 1-5 appointments for each customer
            for _ in range(random.randint(1, 5)):
                barbershop = customer.barbershop
                # Get a random barber from this barbershop
                barber = random.choice(
                    Barber.objects.filter(barbershops=barbershop)
                ).user
                service = random.choice(
                    Service.objects.filter(barbershop=barbershop)
                )
                
                status = random.choices(statuses, weights=weights)[0]
                
                # Generate appointment datetime
                if status in ['PENDING', 'CONFIRMED']:
                    start_datetime = self.fake.date_time_between(
                        start_date='now',
                        end_date='+30d',
                        tzinfo=timezone.get_current_timezone()
                    )
                else:
                    start_datetime = self.fake.date_time_between(
                        start_date='-1y',
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    )

                appointment = Appointment.objects.create(
                    customer=customer,
                    barber=barber,
                    service=service,
                    barbershop=barbershop,
                    start_datetime=start_datetime,
                    end_datetime=start_datetime + timedelta(minutes=service.duration),
                    status=status,
                    final_price=service.price,
                    notes=self.fake.sentence() if random.random() > 0.7 else ''
                )

                # Create payment for completed appointments
                if status == 'COMPLETED':
                    self._create_payment_for_appointment(appointment)

    def _create_payment_for_appointment(self, appointment):
        payment_methods = ['PIX', 'CARD', 'CASH']
        weights = [50, 30, 20]  # More PIX payments

        Payment.objects.create(
            appointment=appointment,
            amount=appointment.final_price,
            method=random.choices(payment_methods, weights=weights)[0],
            status='PAID',
            transaction_id=self.fake.uuid4() if random.random() > 0.3 else '',
            payment_date=appointment.start_datetime + timedelta(minutes=appointment.service.duration),
            notes=self.fake.sentence() if random.random() > 0.8 else ''
        )

    def _create_payments(self):
        # Create payments for pending appointments (30% chance)
        pending_appointments = Appointment.objects.filter(status='PENDING')
        for appointment in pending_appointments:
            if random.random() < 0.3:
                Payment.objects.create(
                    appointment=appointment,
                    amount=appointment.final_price,
                    method='PIX',
                    status='PENDING',
                    transaction_id='',
                    notes='Pagamento antecipado'
                )