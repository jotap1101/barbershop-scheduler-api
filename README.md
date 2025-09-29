# 💈 Barbershop API

Uma API REST completa para gerenciamento de barbearias desenvolvida com Django REST Framework, incluindo autentica### 9. Popule o Banco com Dados de Teste (Opcional)

```bash
python scripts/populate_db.py
```

### 10. Inicie o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

A API estará disponível em: **http://127.0.0.1:8000**

## 🛠️ Gerenciamento do Redis

### Scripts Disponíveis

````bash
# Iniciar Redis
./scripts/redis-dev.sh start

# Verificar status
./scripts/redis-dev.sh status

# Ver logs
./scripts/redis-dev.sh logs

# Parar Redis
./scripts/redis-dev.sh stop

# Reiniciar Redis
./scripts/redis-dev.sh restart

# Limpar dados do Redis
./scripts/redis-dev.sh clean

# Testar cache
python scripts/test_cache.py
```damentos, pagamentos e sistema de avaliações.

## 📋 Sobre o Projeto

Esta é uma API robusta para sistemas de barbearia que oferece:

- **Gerenciamento Multi-tenant**: Suporte para múltiplas barbearias com proprietários independentes
- **Sistema de Agendamentos**: Agendamento inteligente com validação de disponibilidade de barbeiros
- **Processamento de Pagamentos**: Sistema completo de pagamentos com rastreamento de status
- **Sistema de Avaliações**: Avaliações e comentários de clientes
- **Autenticação JWT**: Sistema seguro de autenticação com tokens de acesso e refresh
- **Cache Inteligente**: Sistema de cache Redis em duas camadas para otimização de performance
- **Throttling Avançado**: Rate limiting personalizado por tipo de operação
- **Documentação Completa**: Swagger/ReDoc integrado

## 🏗️ Arquitetura

O projeto está organizado em 6 apps modulares:

- **`apps.auth`** - Gerenciamento de tokens JWT (obtain, refresh, verify, blacklist)
- **`apps.user`** - Gestão de usuários com controle de acesso baseado em roles (CLIENT, BARBER, ADMIN)
- **`apps.barbershop`** - Modelos de Barbershop, Service e BarbershopCustomer
- **`apps.appointment`** - BarberSchedule e Appointment com lógica de negócio complexa
- **`apps.payment`** - Processamento de pagamentos com rastreamento de status
- **`apps.review`** - Sistema de avaliações de clientes

## 🚀 Setup Local

### Pré-requisitos

- Python 3.11+
- pip
- Git
- Docker (para Redis)
- Docker Compose (para Redis)

### Observação: Utilize `python` se o sistema operacional for Windows, e `python3` se for macOS/Linux.

### 1. Clone o Repositório

```bash
git clone https://github.com/jotap1101/api.git
cd api
````

### 2. Crie e Ative um Ambiente Virtual

**Windows:**

```cmd
python -m venv .venv
cd .venv\Scripts
activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Django Settings
SECRET_KEY=sua-chave-secreta-aqui-muito-segura-e-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# Database Settings (SQLite para desenvolvimento)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Redis Settings (Cache)
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_THROTTLE_URL=redis://127.0.0.1:6379/1
REDIS_MAX_CONNECTIONS=20
REDIS_THROTTLE_MAX_CONNECTIONS=10
REDIS_KEY_PREFIX=barbershop_api
REDIS_THROTTLE_KEY_PREFIX=barbershop_throttle

# Para PostgreSQL (produção):
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=barbershop_db
# DB_USER=seu_usuario
# DB_PASSWORD=sua_senha
# DB_HOST=localhost
# DB_PORT=5432

# DockerHub settings
DOCKERHUB_USERNAME=
DOCKERHUB_TOKEN=
```

### 5. Execute as Migrações

```bash
python manage.py migrate
```

### 6. Configure o Redis

```bash
# Inicie o Redis com Docker Compose (Recomendado)
docker-compose -f docker-compose.redis.yml up -d

# Ou use o script de gerenciamento
chmod +x scripts/redis-dev.sh
./scripts/redis-dev.sh start

# Verifique se o Redis está funcionando
./scripts/redis-dev.sh status
```

### 7. Configure as Tabelas de Cache (OPCIONAL - Não necessário com Redis)

```bash
# O Redis é usado como cache principal
echo "Redis configurado como cache principal - sem necessidade de tabelas SQLite"
```

### 8. Crie um Superusuário (Opcional)

```bash
python manage.py createsuperuser
```

### 8. Popule o Banco com Dados de Teste (Opcional)

```bash
python scripts/populate_db.py
```

### 9. Inicie o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

A API estará disponível em: **http://127.0.0.1:8000**

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://127.0.0.1:8000/api/schema/swagger-ui/
- **ReDoc**: http://127.0.0.1:8000/api/schema/redoc/
- **Schema JSON**: http://127.0.0.1:8000/api/schema/

## 🔑 Endpoints Principais

### Autenticação

- `POST /api/v1/token/` - Obter token de acesso
- `POST /api/v1/token/refresh/` - Renovar token
- `POST /api/v1/token/verify/` - Verificar token
- `POST /api/v1/token/blacklist/` - Blacklist do token

### Usuários

- `GET /api/v1/users/` - Listar usuários
- `POST /api/v1/users/` - Criar usuário
- `GET /api/v1/users/{id}/` - Detalhar usuário
- `PUT /api/v1/users/{id}/` - Atualizar usuário
- `DELETE /api/v1/users/{id}/` - Deletar usuário

### Barbearias

- `GET /api/v1/barbershops/` - Listar barbearias
- `POST /api/v1/barbershops/` - Criar barbearia
- `GET /api/v1/barbershops/{id}/` - Detalhar barbearia

### Agendamentos

- `GET /api/v1/appointments/` - Listar agendamentos
- `POST /api/v1/appointments/` - Criar agendamento
- `GET /api/v1/appointments/{id}/` - Detalhar agendamento

## 🧪 Executando os Testes

```bash
# Executar todos os testes
python manage.py test

# Executar testes de um app específico
python manage.py test apps.user

# Executar com verbose
python manage.py test --verbosity=2

# Executar com coverage (instale python-coverage primeiro)
coverage run --source='.' manage.py test
coverage report
```

## 🔧 Ferramentas de Desenvolvimento

### Django Extensions

```bash
# Listar todas as URLs
python manage.py show_urls

# Shell Plus com imports automáticos
python manage.py shell_plus

# Visualizar modelo de dados
python manage.py graph_models -a -o models.png
```

### Logs

Os logs são salvos em:

- `logs/api_usage.log` - Logs de uso da API
- `logs/api_errors.log` - Logs de erros
- `logs/django.log` - Logs gerais do Django

## 🏷️ Roles e Permissões

### Tipos de Usuário:

- **CLIENT** - Cliente das barbearias
- **BARBER** - Barbeiro que trabalha nas barbearias
- **ADMIN** - Administrador do sistema

### Permissões Customizadas:

- `IsOwnerOrAdmin` - Proprietário do objeto ou admin
- `IsAdminOrReadOnly` - Admin pode editar, outros só visualizar
- `IsBarber` - Apenas barbeiros
- `IsClient` - Apenas clientes

## 📈 Sistema de Cache

### Configuração Redis:

- **Cache Primário**: Redis Database 0 - Dados da aplicação
- **Cache de Throttle**: Redis Database 1 - Rate limiting
- **TTL Configurável**: SHORT (5min), MEDIUM (30min), LONG (2h), LISTING (15min)
- **Recursos Avançados**: JSON serialization, compressão Zlib, connection pooling

### Invalidação:

O cache é automaticamente invalidado quando os dados são modificados através dos signals do Django.

## 🚦 Rate Limiting

### Limits por Usuário:

- **Anônimos**: 50 requisições/hora
- **Autenticados**: 500 requisições/hora

### Limits por Escopo:

- **Autenticação**: 10/hora (5/min burst)
- **Agendamentos**: 30/hora
- **Pagamentos**: 20/hora (3/min burst)
- **Avaliações**: 15/hora

## 🔒 Segurança

- **JWT Tokens**: Access token (5 min), Refresh token (1 dia)
- **Upload Seguro**: Nomes de arquivos criptografados
- **CORS Configurado**: Para desenvolvimento e produção
- **Throttling**: Proteção contra abuso
- **Logs de Segurança**: Monitoramento de tentativas de acesso
- **Cache Redis**: Proteção contra falha rápida se Redis não disponível

## 📁 Estrutura de Arquivos

```
barbershop-scheduler-api/
├── apps/                          # Apps da aplicação
│   ├── auth/                      # Autenticação JWT
│   ├── user/                      # Gestão de usuários
│   ├── barbershop/                # Barbearias e serviços
│   ├── appointment/               # Agendamentos
│   ├── payment/                   # Pagamentos
│   └── review/                    # Avaliações
├── config/                        # Configurações Django
├── middleware/                    # Middlewares customizados
├── utils/                         # Utilitários
│   ├── cache/                     # Sistema de cache
│   ├── throttles/                 # Rate limiting
│   └── file_uploads.py            # Upload seguro
├── scripts/                       # Scripts utilitários
├── logs/                          # Arquivos de log
├── media/                         # Uploads de usuários
├── static/                        # Arquivos estáticos
└── requirements.txt               # Dependências
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [`LICENSE`](LICENSE) para mais detalhes.

## 👤 Autor

**João Pedro** - [jotap1101](https://github.com/jotap1101)

📧 Email: jotap1101.joaopedro@gmail.com

---

⭐️ Se este projeto te ajudou, deixe uma estrela!
