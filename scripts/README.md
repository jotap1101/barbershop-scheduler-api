# Script de População do Banco de Dados

Este script utiliza a biblioteca **Faker** para popular todas as tabelas do sistema com dados fictícios realistas.

## 📁 Localização

```
scripts/populate_db.py
```

## 🎯 Funcionalidades

O script popula automaticamente as seguintes tabelas:

### 👥 Usuários (Users)

- **50 Clientes**: usuários com role `CLIENT`
- **15 Barbeiros**: usuários com role `BARBER` (5 deles são proprietários)
- **3 Administradores**: usuários com role `ADMIN`

### 🏪 Barbearias (Barbershops)

- Criadas automaticamente pelos barbeiros proprietários
- Dados realistas: nome, descrição, CNPJ, endereço, contato

### ✂️ Serviços (Services)

- 5 a 12 serviços por barbearia
- 20 tipos diferentes de serviços com preços e durações realistas
- Exemplos: Corte Masculino, Barba, Corte + Barba, etc.

### 🤝 Relacionamentos (BarbershopCustomer)

- Conecta clientes às barbearias
- Cada cliente pode ser cliente de 1 a 3 barbearias
- Inclui data da última visita quando aplicável

### 📅 Horários (BarberSchedule)

- Define os dias e horários que cada barbeiro trabalha
- Cada barbeiro trabalha 4 a 6 dias por semana
- Horários realistas de funcionamento (8h-20h)

### 📋 Agendamentos (Appointments)

- 200 agendamentos distribuídos entre os últimos 3 meses e próximo mês
- Status realistas: 60% completos, 25% confirmados, 10% pendentes, 5% cancelados
- Respeitam horários de trabalho dos barbeiros

### 💰 Pagamentos (Payments)

- Criados automaticamente para agendamentos confirmados/completos
- Métodos: 40% PIX, 30% Cartão de Crédito, 20% Dinheiro, 10% Cartão de Débito
- Status baseado no status do agendamento

### ⭐ Avaliações (Reviews)

- 70% dos agendamentos completos recebem avaliação
- Distribuição realista: mais avaliações 4 e 5 estrelas
- Comentários automáticos baseados na nota

## 🚀 Como Executar

### 1. Certifique-se que o Faker está instalado

```bash
pip install faker
```

### 2. Execute o script

```bash
python scripts/populate_db.py
```

### 3. Aguarde a conclusão

O script mostrará o progresso e estatísticas finais.

## ⚠️ Importante

- **O script apaga todos os dados existentes** antes de popular
- Use apenas em ambiente de desenvolvimento
- **NÃO execute em produção**

## 🔑 Credenciais de Teste

Após executar o script, você pode fazer login com:

| Tipo     | Username  | Senha  |
| -------- | --------- | ------ |
| Admin    | admin1    | 123456 |
| Barbeiro | barbeiro1 | 123456 |
| Cliente  | cliente1  | 123456 |

## 📊 Estatísticas Geradas

O script mostrará ao final:

- Tempo de execução
- Quantidade de registros criados por tabela
- Informações de login para teste

## 🛠️ Personalização

Para modificar as quantidades, edite os parâmetros na função `populate_all()`:

```python
# Exemplo: mais clientes e barbeiros
self.create_users(num_clients=100, num_barbers=25, num_admins=5)

# Exemplo: mais agendamentos
self.create_appointments(num_appointments=500)
```

## 🎭 Dados Fictícios Gerados

- **Nomes**: Brasileiros realistas
- **Emails**: Únicos e válidos
- **Telefones**: Formato brasileiro
- **CNPJs**: Válidos
- **Endereços**: Brasileiros
- **Preços**: Realistas para o mercado
- **Horários**: Dentro do horário comercial
- **Comentários**: Variados por nota

## 🔄 Executar Novamente

Para repopular o banco, simplesmente execute o script novamente. Ele limpará automaticamente os dados antigos e criará novos.
