#!/usr/bin/env python
"""
Script para popular o banco de dados com dados fictícios
Utiliza a biblioteca Faker para gerar dados realistas

Uso:
    python scripts/populate_db.py
"""

import os
import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import django
from faker import Faker
from faker.providers import BaseProvider

# Configuração do Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.appointment.models import Appointment, BarberSchedule
from apps.barbershop.models import Barbershop, BarbershopCustomer, Service
from apps.payment.models import Payment
from apps.review.models import Review

User = get_user_model()

# Configurar Faker em português brasileiro
fake = Faker("pt_BR")


# Provider customizado para dados específicos de barbearia
class BarbershopProvider(BaseProvider):
    """Provider customizado para dados de barbearia"""

    barbershop_names = [
        "Barbearia Clássica",
        "Corte & Arte",
        "The Barber Shop",
        "Estilo Masculino",
        "Barbearia Moderna",
        "Barbeiro Real",
        "Corte Perfeito",
        "Barbearia Vintage",
        "Mestre Barbeiro",
        "Corte & Estilo",
        "Barbershop Elite",
        "Barbearia Urbana",
        "Corte Imperial",
        "Barbeiro Master",
        "Estilo & Classe",
        "Barbearia Premium",
        "Corte Tradicional",
        "Barbeiro Profissional",
        "Barbearia dos Amigos",
        "Corte & Barba",
        "Barbershop Deluxe",
        "Barbearia Fashion",
        "Estilo Único",
        "Corte Royal",
        "Barbeiro Especialista",
        "Barbearia Top",
        "Corte & Charme",
        "Barbershop Premium",
        "Barbearia Exclusiva",
        "Corte & Beleza",
    ]

    service_names = [
        "Corte Masculino",
        "Barba",
        "Bigode",
        "Sobrancelha",
        "Lavagem",
        "Corte + Barba",
        "Corte Degradê",
        "Corte Social",
        "Corte Moderno",
        "Barba Completa",
        "Aparar Barba",
        "Design de Barba",
        "Corte Infantil",
        "Corte com Navalha",
        "Tratamento Capilar",
        "Massagem Capilar",
        "Relaxamento",
        "Hidratação",
        "Corte Americano",
        "Corte Europeu",
    ]

    service_descriptions = [
        "Corte profissional com acabamento perfeito",
        "Serviço completo de barbearia tradicional",
        "Corte moderno seguindo as tendências atuais",
        "Acabamento refinado para ocasiões especiais",
        "Serviço personalizado conforme seu estilo",
        "Experiência premium de barbearia",
        "Técnica tradicional com toque moderno",
        "Atendimento especializado e diferenciado",
    ]

    def barbershop_name(self):
        return self.random_element(self.barbershop_names)

    def service_name(self):
        return self.random_element(self.service_names)

    def service_description(self):
        return self.random_element(self.service_descriptions)


# Adicionar provider customizado
fake.add_provider(BarbershopProvider)


class DatabasePopulator:
    """Classe principal para popular o banco de dados"""

    def __init__(self):
        self.users = []
        self.barbershops = []
        self.services = []
        self.barbershop_customers = []
        self.barber_schedules = []
        self.appointments = []
        self.payments = []
        self.reviews = []

    def clear_database(self):
        """Limpa todas as tabelas do banco de dados"""
        print("🗑️  Limpando banco de dados...")

        Review.objects.all().delete()
        Payment.objects.all().delete()
        Appointment.objects.all().delete()
        BarberSchedule.objects.all().delete()
        BarbershopCustomer.objects.all().delete()
        Service.objects.all().delete()
        Barbershop.objects.all().delete()
        User.objects.all().delete()

        print("✅ Banco de dados limpo com sucesso!")

    def create_users(self, num_clients=50, num_barbers=15, num_admins=3):
        """Cria usuários (clientes, barbeiros e administradores)"""
        print(
            f"👥 Criando usuários ({num_clients} clientes, {num_barbers} barbeiros, {num_admins} admins)..."
        )

        used_emails = set()
        used_usernames = set()

        def get_unique_email():
            email = fake.email()
            while email in used_emails:
                email = fake.email()
            used_emails.add(email)
            return email

        def get_unique_username(base):
            username = base
            counter = 1
            while username in used_usernames:
                username = f"{base}{counter}"
                counter += 1
            used_usernames.add(username)
            return username

        # Criar administradores
        for i in range(num_admins):
            username = get_unique_username(f"admin{i+1}")
            user = User.objects.create_user(
                username=username,
                email=get_unique_email(),
                password="123456",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=User.Role.ADMIN,
                phone=fake.phone_number(),
                birth_date=fake.date_of_birth(minimum_age=25, maximum_age=60),
                bio=fake.text(max_nb_chars=200),
                is_staff=True,
                is_superuser=True,
            )
            self.users.append(user)

        # Criar barbeiros (alguns serão donos de barbearia)
        for i in range(num_barbers):
            is_owner = i < (num_barbers // 3)  # 1/3 dos barbeiros serão donos
            username = get_unique_username(f"barbeiro{i+1}")
            user = User.objects.create_user(
                username=username,
                email=get_unique_email(),
                password="123456",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=User.Role.BARBER,
                is_barbershop_owner=is_owner,
                phone=fake.phone_number(),
                birth_date=fake.date_of_birth(minimum_age=20, maximum_age=55),
                bio=f"Barbeiro profissional com experiência em {fake.text(max_nb_chars=150)}",
            )
            self.users.append(user)

        # Criar clientes
        for i in range(num_clients):
            username = get_unique_username(f"cliente{i+1}")
            user = User.objects.create_user(
                username=username,
                email=get_unique_email(),
                password="123456",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=User.Role.CLIENT,
                phone=fake.phone_number() if random.choice([True, False]) else None,
                birth_date=(
                    fake.date_of_birth(minimum_age=16, maximum_age=70)
                    if random.choice([True, False])
                    else None
                ),
                bio=(
                    fake.text(max_nb_chars=100)
                    if random.choice([True, False])
                    else None
                ),
            )
            self.users.append(user)

        print(f"✅ {len(self.users)} usuários criados com sucesso!")

    def create_barbershops(self):
        """Cria barbearias"""
        print("🏪 Criando barbearias...")

        # Obter barbeiros que são donos
        barber_owners = [
            user
            for user in self.users
            if user.role == User.Role.BARBER and user.is_barbershop_owner
        ]

        used_names = set()
        used_emails = set()
        used_cnpjs = set()

        for i, owner in enumerate(barber_owners):
            # Garantir nome único
            base_name = fake.barbershop_name()
            name = base_name
            counter = 1
            while name in used_names:
                name = f"{base_name} {counter}"
                counter += 1
            used_names.add(name)

            # Garantir email único se fornecido
            email = None
            if random.choice([True, False]):
                email = fake.email()
                while email in used_emails:
                    email = fake.email()
                used_emails.add(email)

            # Garantir CNPJ único se fornecido
            cnpj = None
            if random.choice([True, False]):
                cnpj = fake.cnpj()
                while cnpj in used_cnpjs:
                    cnpj = fake.cnpj()
                used_cnpjs.add(cnpj)

            barbershop = Barbershop.objects.create(
                name=name,
                description=fake.text(max_nb_chars=300),
                cnpj=cnpj,
                address=fake.address(),
                email=email,
                phone=fake.phone_number() if random.choice([True, False]) else None,
                website=fake.url() if random.choice([True, False]) else None,
                owner=owner,
            )
            self.barbershops.append(barbershop)

        print(f"✅ {len(self.barbershops)} barbearias criadas com sucesso!")

    def create_services(self):
        """Cria serviços para as barbearias"""
        print("✂️ Criando serviços...")

        service_prices = {
            "Corte Masculino": (25.00, 45.00),
            "Barba": (15.00, 35.00),
            "Bigode": (10.00, 20.00),
            "Sobrancelha": (8.00, 18.00),
            "Lavagem": (5.00, 15.00),
            "Corte + Barba": (35.00, 70.00),
            "Corte Degradê": (30.00, 50.00),
            "Corte Social": (28.00, 48.00),
            "Corte Moderno": (32.00, 55.00),
            "Barba Completa": (25.00, 45.00),
            "Aparar Barba": (12.00, 25.00),
            "Design de Barba": (20.00, 40.00),
            "Corte Infantil": (15.00, 35.00),
            "Corte com Navalha": (40.00, 80.00),
            "Tratamento Capilar": (30.00, 60.00),
            "Massagem Capilar": (20.00, 40.00),
            "Relaxamento": (25.00, 50.00),
            "Hidratação": (35.00, 65.00),
            "Corte Americano": (35.00, 60.00),
            "Corte Europeu": (40.00, 75.00),
        }

        service_durations = {
            "Corte Masculino": 30,
            "Barba": 25,
            "Bigode": 15,
            "Sobrancelha": 10,
            "Lavagem": 15,
            "Corte + Barba": 45,
            "Corte Degradê": 35,
            "Corte Social": 30,
            "Corte Moderno": 40,
            "Barba Completa": 35,
            "Aparar Barba": 20,
            "Design de Barba": 30,
            "Corte Infantil": 25,
            "Corte com Navalha": 50,
            "Tratamento Capilar": 40,
            "Massagem Capilar": 25,
            "Relaxamento": 35,
            "Hidratação": 45,
            "Corte Americano": 40,
            "Corte Europeu": 45,
        }

        for barbershop in self.barbershops:
            # Cada barbearia terá entre 5 e 12 serviços
            num_services = random.randint(5, min(12, len(service_prices)))
            available_services = list(service_prices.keys())
            random.shuffle(available_services)
            selected_services = available_services[:num_services]

            for service_name in selected_services:
                min_price, max_price = service_prices[service_name]
                price = round(random.uniform(min_price, max_price), 2)
                duration_minutes = service_durations[service_name]

                service = Service.objects.create(
                    barbershop=barbershop,
                    name=service_name,
                    description=fake.service_description(),
                    price=Decimal(str(price)),
                    duration=timedelta(minutes=duration_minutes),
                    available=random.choice(
                        [True, True, True, False]
                    ),  # 75% disponíveis
                )
                self.services.append(service)

        print(f"✅ {len(self.services)} serviços criados com sucesso!")

    def create_barbershop_customers(self):
        """Cria relacionamentos entre clientes e barbearias"""
        print("🤝 Criando relacionamentos cliente-barbearia...")

        clients = [user for user in self.users if user.role == User.Role.CLIENT]

        for client in clients:
            # Cada cliente pode ser cliente de 1 a 3 barbearias
            num_barbershops = random.randint(1, min(3, len(self.barbershops)))
            selected_barbershops = random.sample(self.barbershops, num_barbershops)

            for barbershop in selected_barbershops:
                last_visit = None
                if random.choice([True, False]):  # 50% têm última visita
                    last_visit = fake.date_time_between(
                        start_date="-6months", end_date="now"
                    )
                    # Tornar timezone-aware usando UTC
                    if last_visit.tzinfo is None:
                        last_visit = timezone.make_aware(last_visit)

                barbershop_customer = BarbershopCustomer.objects.create(
                    customer=client, barbershop=barbershop, last_visit=last_visit
                )
                self.barbershop_customers.append(barbershop_customer)

        print(
            f"✅ {len(self.barbershop_customers)} relacionamentos cliente-barbearia criados!"
        )

    def create_barber_schedules(self):
        """Cria horários de trabalho dos barbeiros"""
        print("📅 Criando horários dos barbeiros...")

        barbers = [user for user in self.users if user.role == User.Role.BARBER]

        for barber in barbers:
            # Barbeiros podem trabalhar em 1 ou 2 barbearias
            barber_barbershops = []
            if barber.is_barbershop_owner:
                # Se é dono, trabalha na própria barbearia
                owner_barbershop = next(
                    (b for b in self.barbershops if b.owner == barber), None
                )
                if owner_barbershop:
                    barber_barbershops.append(owner_barbershop)
            else:
                # Se não é dono, pode trabalhar em outras barbearias
                num_barbershops = random.randint(1, min(2, len(self.barbershops)))
                barber_barbershops = random.sample(self.barbershops, num_barbershops)

            for barbershop in barber_barbershops:
                # Definir dias da semana que trabalha (pelo menos 4 dias)
                working_days = random.sample(range(1, 8), random.randint(4, 6))

                for weekday in working_days:
                    # Horários típicos de barbearia
                    start_hour = random.choice([8, 9, 10])
                    end_hour = random.choice([17, 18, 19, 20])

                    schedule = BarberSchedule.objects.create(
                        barber=barber,
                        barbershop=barbershop,
                        weekday=weekday,
                        start_time=time(start_hour, 0),
                        end_time=time(end_hour, 0),
                        is_available=random.choice(
                            [True, True, True, False]
                        ),  # 75% disponíveis
                    )
                    self.barber_schedules.append(schedule)

        print(f"✅ {len(self.barber_schedules)} horários de barbeiros criados!")

    def create_appointments(self, num_appointments=200):
        """Cria agendamentos"""
        print("📋 Criando agendamentos...")

        if not self.barbershop_customers or not self.barber_schedules:
            print(
                "❌ Erro: É necessário ter clientes e horários de barbeiros antes de criar agendamentos"
            )
            return

        statuses = [
            Appointment.Status.COMPLETED,  # 60%
            Appointment.Status.CONFIRMED,  # 25%
            Appointment.Status.PENDING,  # 10%
            Appointment.Status.CANCELLED,  # 5%
        ]

        status_weights = [0.6, 0.25, 0.10, 0.05]
        created_appointments = []
        attempts = 0
        max_attempts = (
            num_appointments * 3
        )  # Limite de tentativas para evitar loop infinito

        while len(created_appointments) < num_appointments and attempts < max_attempts:
            attempts += 1

            # Selecionar cliente aleatório
            customer = random.choice(self.barbershop_customers)
            barbershop = customer.barbershop

            # Selecionar barbeiro que trabalha nesta barbearia
            barbershop_schedules = [
                s
                for s in self.barber_schedules
                if s.barbershop == barbershop and s.is_available
            ]
            if not barbershop_schedules:
                continue

            schedule = random.choice(barbershop_schedules)
            barber = schedule.barber

            # Selecionar serviço da barbearia
            barbershop_services = [
                s for s in self.services if s.barbershop == barbershop and s.available
            ]
            if not barbershop_services:
                continue

            service = random.choice(barbershop_services)

            # Gerar data/hora do agendamento
            start_date = fake.date_between(start_date="-3months", end_date="+1month")

            # Verificar se o barbeiro trabalha neste dia
            if start_date.weekday() + 1 != schedule.weekday:
                continue

            # Gerar horário dentro do horário de trabalho
            work_start = datetime.combine(start_date, schedule.start_time)
            work_end = datetime.combine(start_date, schedule.end_time)

            # Calcular horário de início possível (considerando duração do serviço)
            service_duration = service.duration
            latest_start = work_end - service_duration

            if work_start >= latest_start:
                continue

            # Gerar horário aleatório
            try:
                start_datetime = fake.date_time_between(
                    start_date=work_start, end_date=latest_start
                )
                # Tornar timezone-aware usando UTC
                if start_datetime.tzinfo is None:
                    start_datetime = timezone.make_aware(start_datetime)
            except ValueError:
                continue

            end_datetime = start_datetime + service_duration

            # Verificar se já existe agendamento no mesmo horário para o mesmo barbeiro
            conflict = any(
                apt
                for apt in created_appointments
                if apt.barber == barber
                and (
                    (apt.start_datetime <= start_datetime < apt.end_datetime)
                    or (start_datetime <= apt.start_datetime < end_datetime)
                )
            )

            if conflict:
                continue

            # Definir status
            status = random.choices(statuses, weights=status_weights)[0]

            try:
                appointment = Appointment.objects.create(
                    customer=customer,
                    barber=barber,
                    service=service,
                    barbershop=barbershop,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    status=status,
                    final_price=service.price
                    + Decimal(str(random.uniform(-5, 10))),  # Variação no preço
                )
                created_appointments.append(appointment)
                self.appointments.append(appointment)
            except Exception as e:
                print(f"⚠️  Erro ao criar agendamento: {e}")
                continue

        print(f"✅ {len(self.appointments)} agendamentos criados com sucesso!")
        if attempts >= max_attempts:
            print(
                "⚠️  Atingido limite de tentativas. Nem todos os agendamentos foram criados."
            )

    def create_payments(self):
        """Cria pagamentos para os agendamentos"""
        print("💰 Criando pagamentos...")

        payment_methods = [
            Payment.Method.PIX,  # 40%
            Payment.Method.CREDIT_CARD,  # 30%
            Payment.Method.CASH,  # 20%
            Payment.Method.DEBIT_CARD,  # 10%
        ]
        method_weights = [0.4, 0.3, 0.2, 0.1]

        for appointment in self.appointments:
            # Apenas agendamentos confirmados e completos têm pagamentos
            if appointment.status not in [
                Appointment.Status.CONFIRMED,
                Appointment.Status.COMPLETED,
            ]:
                continue

            method = random.choices(payment_methods, weights=method_weights)[0]

            # Status do pagamento baseado no status do agendamento
            if appointment.status == Appointment.Status.COMPLETED:
                status = Payment.Status.PAID
                payment_date = appointment.end_datetime + timedelta(
                    minutes=random.randint(-30, 60)
                )
            else:
                status = random.choice([Payment.Status.PENDING, Payment.Status.PAID])
                payment_date = None
                if status == Payment.Status.PAID:
                    payment_date = appointment.start_datetime + timedelta(
                        minutes=random.randint(-60, 30)
                    )

            payment = Payment.objects.create(
                appointment=appointment,
                amount=appointment.final_price,
                method=method,
                status=status,
                payment_date=payment_date,
                notes=(
                    fake.text(max_nb_chars=100)
                    if random.choice([True, False])
                    else None
                ),
            )
            self.payments.append(payment)

        print(f"✅ {len(self.payments)} pagamentos criados com sucesso!")

    def create_reviews(self):
        """Cria avaliações para agendamentos completos"""
        print("⭐ Criando avaliações...")

        completed_appointments = [
            a for a in self.appointments if a.status == Appointment.Status.COMPLETED
        ]

        # Nem todos os agendamentos completos terão avaliações (70%)
        appointments_to_review = random.sample(
            completed_appointments, int(len(completed_appointments) * 0.7)
        )

        rating_weights = [0.05, 0.1, 0.15, 0.35, 0.35]  # Mais avaliações 4 e 5 estrelas

        for appointment in appointments_to_review:
            rating = random.choices(
                list(Review.Rating.choices), weights=rating_weights
            )[0][0]

            # Comentários baseados na avaliação
            comment = None
            if rating >= 4:
                comments = [
                    "Excelente serviço! Recomendo muito!",
                    "Barbeiro muito profissional, adorei o resultado.",
                    "Sempre saio satisfeito daqui. Ótimo atendimento!",
                    "Corte perfeito, como sempre. Parabéns!",
                    "Ambiente agradável e serviço de qualidade.",
                    "Superou minhas expectativas. Voltarei sempre!",
                ]
            elif rating == 3:
                comments = [
                    "Serviço bom, mas pode melhorar.",
                    "Atendimento ok, nada excepcional.",
                    "Satisfeito com o resultado final.",
                    "Preço justo pelo serviço prestado.",
                ]
            else:
                comments = [
                    "Não ficou como esperava.",
                    "Atendimento deixou a desejar.",
                    "Esperava mais pela reputação do local.",
                    "Pode melhorar bastante.",
                ]

            if random.choice([True, False]):  # 50% têm comentário
                comment = random.choice(comments)

            review = Review.objects.create(
                barbershop_customer=appointment.customer,
                barber=appointment.barber,
                service=appointment.service,
                barbershop=appointment.barbershop,
                rating=rating,
                comment=comment,
            )
            self.reviews.append(review)

        print(f"✅ {len(self.reviews)} avaliações criadas com sucesso!")

    def populate_all(self):
        """Executa todo o processo de população do banco"""
        print("🚀 Iniciando população completa do banco de dados...")
        print("=" * 60)

        start_time = datetime.now()

        try:
            # Limpar banco
            self.clear_database()

            # Popular em ordem de dependência
            self.create_users()
            self.create_barbershops()
            self.create_services()
            self.create_barbershop_customers()
            self.create_barber_schedules()
            self.create_appointments()
            self.create_payments()
            self.create_reviews()

            # Estatísticas finais
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "=" * 60)
            print("🎉 POPULAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print(f"⏱️  Tempo total: {duration}")
            print(f"👥 Usuários criados: {len(self.users)}")
            print(f"🏪 Barbearias criadas: {len(self.barbershops)}")
            print(f"✂️  Serviços criados: {len(self.services)}")
            print(
                f"🤝 Relacionamentos cliente-barbearia: {len(self.barbershop_customers)}"
            )
            print(f"📅 Horários de barbeiros: {len(self.barber_schedules)}")
            print(f"📋 Agendamentos criados: {len(self.appointments)}")
            print(f"💰 Pagamentos criados: {len(self.payments)}")
            print(f"⭐ Avaliações criadas: {len(self.reviews)}")
            print("=" * 60)

            # Informações de login
            print("\n🔑 INFORMAÇÕES DE LOGIN:")
            print("=" * 30)
            print("Admin: admin1 / 123456")
            print("Barbeiro: barbeiro1 / 123456")
            print("Cliente: cliente1 / 123456")
            print("=" * 30)

        except Exception as e:
            print(f"\n❌ Erro durante a população: {str(e)}")
            print("🔧 Tentando limpeza do banco de dados...")
            try:
                self.clear_database()
                print("✅ Banco limpo após erro")
            except Exception as cleanup_error:
                print(f"❌ Erro na limpeza: {str(cleanup_error)}")
            raise e


def main():
    """Função principal"""
    print("🎭 SCRIPT DE POPULAÇÃO DO BANCO DE DADOS")
    print("=" * 60)

    try:
        populator = DatabasePopulator()
        populator.populate_all()
    except Exception as e:
        print(f"\n❌ Erro durante a população: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
