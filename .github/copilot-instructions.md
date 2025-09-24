# Barbershop API - Copilot Instructions

This is a comprehensive Django REST API for barbershop operations with JWT authentication, caching, throttling, and extensive business logic.

## Architecture Overview

**Apps Structure**: Six modular Django apps with clear boundaries:

- `apps.auth` - JWT token management (obtain, refresh, verify, blacklist)
- `apps.user` - User management with role-based access (CLIENT, BARBER, ADMIN)
- `apps.barbershop` - Barbershop, Service, and BarbershopCustomer models
- `apps.appointment` - BarberSchedule and Appointment with complex business logic
- `apps.payment` - Payment processing with status tracking
- `apps.review` - Customer review system

**Key Domain Logic**: This is a multi-tenant barbershop system where:

- Barbershop owners (User.is_barbershop_owner=True) can own multiple barbershops
- Barbers work at specific barbershops with defined schedules (BarberSchedule)
- Complex appointment validation includes time slot availability and barber schedules
- All major models use UUID primary keys, not auto-incrementing integers

## Development Patterns

### Model Conventions

- All models use `id = models.UUIDField(primary_key=True, default=uuid4)`
- File uploads use encrypted filenames via `utils.file_uploads.encrypted_filename()`
- Models include business logic methods (e.g., `Barbershop.get_total_revenue()`)
- Custom user model extends AbstractUser with role-based permissions

### Serializer Patterns

- Multiple serializers per model: `UserSerializer`, `UserCreateSerializer`, `UserDetailSerializer`, `UserListSerializer`, `UserUpdateSerializer`
- Use `get_serializer_class()` to return appropriate serializer based on action
- Password validation with `django.contrib.auth.password_validation.validate_password`

### ViewSet Conventions

- All use `@extend_schema_view` with detailed OpenAPI documentation
- Custom permission classes: `IsOwnerOrAdmin`, `IsAdminOrReadOnly`, `IsBarber`, etc.
- Scoped throttling: `AuthThrottle`, `AppointmentThrottle`, `PaymentBurstThrottle`
- Standard filtering: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Custom actions use `@action(detail=True/False, methods=['post'])` with specific throttles

### Custom Infrastructure

**Cache System** (`utils.cache.cache_utils.py`):

- Organized cache keys: `CacheKeys.BARBERSHOP_LIST`, `CacheKeys.AVAILABLE_SLOTS`
- Configurable TTL: `CACHE_TTL.SHORT` (5 min), `CACHE_TTL.MEDIUM` (30 min), `CACHE_TTL.LONG` (2h)
- Two cache backends: 'default' for data, 'throttle' for rate limiting

**Custom Throttles** (`utils.throttles.custom_throttles.py`):

- Scoped throttles per endpoint type: 'auth', 'appointments', 'payments', 'reviews'
- Burst protection: 'auth_burst' (5/min), 'payment_burst' (3/min)
- Different rates for anon (50/hour) vs authenticated (500/hour) users

**API Tracking** (`middleware.api_tracking_middleware.py`):

- Comprehensive request monitoring with performance metrics
- Ignores static files and admin, tracks only `/api/v1/` routes
- JSON structured logging to separate files: `logs/api_usage.log`, `logs/api_errors.log`

## Configuration & Environment

**Settings Structure**:

- Environment variables via `django-environ` (.env file required)
- Brazilian locale: `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`
- Custom user model: `AUTH_USER_MODEL = "user.User"`
- JWT access tokens: 5 minutes, refresh tokens: 1 day

**Database**: SQLite for development (`db.sqlite3`), PostgreSQL production setup commented out

**API Documentation**:

- drf-spectacular with comprehensive Swagger/ReDoc setup
- Custom security schemes, servers, and tags configuration
- Available at `/api/schema/swagger-ui/` and `/api/schema/redoc/`

## Development Workflows

**Running the API**:

```bash
python manage.py runserver  # Development server at http://127.0.0.1:8000
python manage.py migrate    # Apply database migrations
python scripts/populate_db.py  # Seed database with realistic test data using Faker
```

**Testing**:

- Comprehensive test suites in each app's `tests.py` (1949+ lines in users alone)
- Base test classes like `UserAPITestCase` with common setup utilities
- JWT token authentication setup in test fixtures

**Cache Management**:

```bash
python manage.py createcachetable cache_table          # Create default cache table
python manage.py createcachetable throttle_cache_table # Create throttle cache table
```

## Common Patterns

**Adding New Endpoints**:

1. Create model with UUID primary key and business logic methods
2. Create multiple serializers for different use cases (list, detail, create, update)
3. Create custom permissions if needed (inherit from BasePermission)
4. Create ViewSet with `@extend_schema_view` documentation
5. Add appropriate throttle classes from `utils.throttles`
6. Register in `urls.py` with DefaultRouter
7. Add URL pattern to main `config/urls.py` under `/api/v1/`

**File Uploads**: Always use `encrypted_filename()` with proper subfolders based on model attributes

**Permissions**: Combine IsAuthenticated with role-specific permissions. Use object-level permissions for ownership checks.

**Caching**: Use CacheManager class with predefined TTL types. Implement cache invalidation in model save/delete methods.

This system prioritizes security (JWT, throttling, encrypted files), performance (aggressive caching), and maintainability (clean architecture, comprehensive tests).
