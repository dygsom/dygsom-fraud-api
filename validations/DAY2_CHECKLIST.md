# Day 2 Setup & Verification Guide

## Checklist del Día 2

### ✅ Código
- [x] Repository layer completo
- [x] Service layer básico  
- [x] DTOs con validación
- [x] Seed script funcionando
- [x] Sin errores de linter
- [x] Sin prohibidos (any, print, etc.)

### 🗄️ Database
- [ ] Schema Prisma completo (4+ tablas)
- [ ] Migraciones ejecutadas
- [ ] 1000 transacciones seed en DB

### ⚙️ Funcionalidad
- [ ] Puedes crear transacciones via repository
- [ ] Service.score_transaction retorna algo (aunque sea básico)
- [ ] DTOs validan correctamente

---

## Setup Rápido (Docker)

### 1. Levantar servicios
```bash
docker-compose up -d
```

### 2. Instalar dependencias
```bash
docker-compose exec api pip install -r requirements.txt
```

### 3. Ejecutar setup completo (dentro del container)
```bash
docker-compose exec api bash scripts/setup_day2.sh
```

O en Windows PowerShell (fuera del container):
```powershell
docker-compose exec api pwsh scripts/setup_day2.ps1
```

### 4. Verificar checklist
```bash
docker-compose exec api python scripts/verify_day2.py
```

---

## Setup Manual (Paso a Paso)

### 1. Generar Prisma Client
```bash
docker-compose exec api prisma generate
```

### 2. Push schema a database
```bash
docker-compose exec api prisma db push --skip-generate
```

### 3. Instalar Faker
```bash
docker-compose exec api pip install faker==22.0.0
```

### 4. Ejecutar seed script
```bash
docker-compose exec api python -m src.scripts.seed_transactions
```

### 5. Verificar resultados
```bash
docker-compose exec api python scripts/verify_day2.py
```

---

## Verificación de Componentes

### Repository Layer
Métodos implementados:
- `find_by_id()` - Buscar por ID
- `find_all()` - Listar con paginación
- `create()` - Crear transacción
- `update()` - Actualizar transacción
- `delete()` - Eliminar transacción
- `find_by_transaction_id()` - Buscar por transaction_id
- `get_customer_history()` - Historial de cliente
- `get_ip_history()` - Historial de IP
- `get_transactions_by_date_range()` - Rango de fechas

**Archivo**: `src/repositories/transaction_repository.py`

### Service Layer
Métodos implementados:
- `score_transaction()` - Scoring de fraude principal
- `_extract_velocity_features()` - Extracción de features de velocidad
- `_calculate_fraud_score()` - Cálculo de score (rule-based)
- `_calculate_risk_level()` - Determinar nivel de riesgo
- `_generate_recommendation()` - Generar recomendación
- `get_transaction_by_id()` - Obtener transacción
- `get_risk_statistics()` - Estadísticas de riesgo

**Archivo**: `src/services/fraud_service.py`

### DTOs con Validación
Clases implementadas:
- `CustomerData` - Validación de email, IP, phone
- `PaymentMethodData` - Validación de tarjeta
- `CreateTransactionDto` - Validación de transacción completa
- `TransactionResponseDto` - Response model

**Validaciones**:
- Email regex
- IP address válida (no privadas)
- Phone number cleaning
- Amount > 0 y <= 1,000,000
- Card BIN (6 dígitos)
- Card last4 (4 dígitos)

**Archivo**: `src/schemas/transaction_schemas.py`

### Database Schema
Tablas implementadas:
1. **Transaction** - Transacciones principales
2. **FraudFeatures** - Features de detección de fraude
3. **Blocklist** - Lista de emails/IPs/BINs bloqueados
4. **ApiKey** - Autenticación API

**Archivo**: `prisma/schema.prisma`

### Seed Script
Genera 1000 transacciones:
- 800 legítimas (fraud_score < 0.3)
- 150 sospechosas (0.3 <= fraud_score < 0.8)
- 50 fraudulentas (fraud_score >= 0.8)

Usa **Faker** para datos realistas:
- Emails variados (legítimos vs disposable)
- IPs de Perú vs VPNs
- Tarjetas Visa/Mastercard/Amex
- Timestamps últimos 30 días

**Archivo**: `src/scripts/seed_transactions.py`

---

## Troubleshooting

### Error: "prisma: command not found"
```bash
docker-compose exec api pip install prisma
docker-compose exec api prisma generate
```

### Error: "No module named 'faker'"
```bash
docker-compose exec api pip install faker==22.0.0
```

### Error: "Database connection failed"
Verificar que PostgreSQL esté corriendo:
```bash
docker-compose ps
docker-compose logs postgres
```

### Error: "Table does not exist"
Ejecutar push de schema:
```bash
docker-compose exec api prisma db push --skip-generate
```

### Limpiar y reiniciar todo
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec api bash scripts/setup_day2.sh
```

---

## Próximos Pasos (Día 3)

1. **FastAPI Endpoints**
   - POST `/api/v1/fraud/score`
   - GET `/api/v1/transactions/{id}`
   - GET `/health`

2. **ML Model Integration**
   - Cargar modelo XGBoost
   - Feature extraction completo
   - Reemplazar rule-based scoring

3. **Redis Cache**
   - Cache de scores
   - Rate limiting
   - Session management

4. **Testing**
   - Unit tests
   - Integration tests
   - E2E tests

---

## Recursos

- **Prisma Docs**: https://www.prisma.io/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Faker Docs**: https://faker.readthedocs.io
- **Roadmap**: Ver `DYGSOM_Roadmap_Detallado_Dias_1-10.md`
