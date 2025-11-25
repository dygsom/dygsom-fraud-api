# Plantilla Base para Desarrollo de APIs Backend

> **Sistema de Diseño de Prompts para Asistentes de IA**
> **Framework agnóstico - Especializado en APIs REST modernas**

---

## 🎯 Propósito de Esta Plantilla

Esta plantilla estandariza el desarrollo de APIs backend usando asistentes de IA (Claude, Copilot, ChatGPT, etc.) para:

1. ✅ **Consistencia**: Mismo estilo de código en todo el proyecto
2. ✅ **Calidad**: Guardrails que previenen malas prácticas
3. ✅ **Eficiencia**: Acelera desarrollo sin sacrificar calidad
4. ✅ **Contexto**: Mantiene a la IA alineada con el negocio
5. ✅ **Mantenibilidad**: Código legible y bien estructurado

---

## 📦 Stack Tecnológico (OBLIGATORIO)

### Runtime y Lenguaje

```yaml
Runtime: Node.js 20 LTS (iron)
Lenguaje: TypeScript 5.3+
Package Manager: npm (package-lock.json obligatorio)
```

**Razón**: LTS garantiza soporte a largo plazo, TypeScript previene errores en tiempo de compilación.

### Framework Backend

Elige UNO según tu caso de uso:

| Framework | Cuándo Usar | Versión |
|-----------|-------------|---------|
| **NestJS 10+** | Proyectos enterprise, multi-tenant, arquitectura modular | ⭐ Recomendado |
| **Fastify 4+** | Performance crítico, APIs simples, microservicios | Alta performance |
| **Express 4.18+** | Proyectos legacy, migración gradual | Solo si es necesario |

**Recomendación**: NestJS para nuevos proyectos (TypeScript nativo, decorators, DI automático).

### ORM / Query Builder

```yaml
ORM Recomendado: Prisma 5+
Alternativa: TypeORM 0.3+ (solo si hay requerimiento específico)
```

**Prisma ventajas:**
- Type-safe en tiempo de compilación
- Migraciones declarativas
- Mejor DX (Developer Experience)
- Auto-completion excelente

### Base de Datos

```yaml
Primary: PostgreSQL 15+ (mejor para producción)
Development: PostgreSQL en Docker (consistencia dev/prod)
Testing: PostgreSQL en memoria (testcontainers)
```

**Prohibido**: SQLite en producción, MySQL para nuevos proyectos (excepto requerimiento específico).

### Cache

```yaml
Cache: Redis 7+
Session Store: Redis
Queue: BullMQ 4+ (basado en Redis)
```

### Validación

```yaml
Schema Validation: Zod 3+ o class-validator 0.14+
Runtime Validation: Obligatorio en TODOS los inputs
```

### Testing

```yaml
Framework: Vitest 1.0+ o Jest 29+
Coverage Objetivo: >80%
E2E: Supertest para APIs
```

### Logging

```yaml
Logger: winston 3+ o pino 8+
Prohibido: console.log en producción
```

### Documentación

```yaml
API Docs: OpenAPI 3.1 (Swagger)
Auto-generación: Obligatoria
```

---

## 🚫 Guardrails de Seguridad (PROHIBICIONES)

### ❌ Prohibido Type-Unsafe

```typescript
// ❌ PROHIBIDO: any type
function processData(data: any) { }

// ❌ PROHIBIDO: as any
const result = apiResponse as any

// ❌ PROHIBIDO: @ts-ignore sin justificación
// @ts-ignore
const value = obj.property

// ✅ CORRECTO: Type-safe
interface UserData {
  id: string
  email: string
}

function processData(data: UserData) { }
```

**Razón**: `any` elimina todos los beneficios de TypeScript y puede causar errores en runtime.

### ❌ Prohibido Magic Numbers y Strings

```typescript
// ❌ PROHIBIDO: Magic numbers
if (status === 200) { }
setTimeout(() => {}, 3000)

// ❌ PROHIBIDO: Magic strings
if (role === "admin") { }

// ✅ CORRECTO: Constantes con nombres descriptivos
const HTTP_STATUS_OK = 200
const RETRY_DELAY_MS = 3000

if (status === HTTP_STATUS_OK) { }
setTimeout(() => {}, RETRY_DELAY_MS)

// ✅ CORRECTO: Enums para strings
enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

if (role === UserRole.ADMIN) { }
```

**Razón**: Facilita mantenimiento y previene typos.

### ❌ Prohibido console.log en Producción

```typescript
// ❌ PROHIBIDO
console.log('User data:', user)
console.error('Error occurred:', error)

// ✅ CORRECTO: Structured logging
import { Logger } from 'winston' // o tu logger preferido

const logger = new Logger('UserService')

logger.info('User data processed', { userId: user.id })
logger.error('Error occurred', { error: error.message, stack: error.stack })
```

**Razón**: Logs estructurados permiten búsqueda, análisis y alertas.

### ❌ Prohibido Hardcoded Secrets

```typescript
// ❌ PROHIBIDO
const API_KEY = "sk-1234567890abcdef"
const DATABASE_PASSWORD = "mypassword123"

// ✅ CORRECTO: Variables de entorno
const API_KEY = process.env.API_KEY
const DATABASE_PASSWORD = process.env.DATABASE_PASSWORD

// ✅ MEJOR: Validación de env vars
import { z } from 'zod'

const envSchema = z.object({
  API_KEY: z.string().min(1),
  DATABASE_PASSWORD: z.string().min(8),
  DATABASE_URL: z.string().url(),
})

const env = envSchema.parse(process.env)
```

**Razón**: Secrets en código es riesgo de seguridad crítico.

### ❌ Prohibido Queries sin Sanitización

```typescript
// ❌ PROHIBIDO: SQL injection risk
const query = `SELECT * FROM users WHERE id = ${userId}`

// ❌ PROHIBIDO: Interpolación directa
const query = `SELECT * FROM users WHERE email = '${email}'`

// ✅ CORRECTO: Parametrized queries
const query = 'SELECT * FROM users WHERE id = $1'
await db.query(query, [userId])

// ✅ MEJOR: ORM con type-safety
await prisma.user.findUnique({
  where: { id: userId }
})
```

**Razón**: Previene SQL injection.

### ❌ Prohibido Passwords sin Hash

```typescript
// ❌ PROHIBIDO: Password en texto plano
await db.user.create({
  data: {
    email,
    password: password  // ❌ NUNCA
  }
})

// ✅ CORRECTO: Siempre hashear
import * as bcrypt from 'bcrypt'

const hashedPassword = await bcrypt.hash(password, 10)

await db.user.create({
  data: {
    email,
    password: hashedPassword
  }
})
```

**Razón**: Passwords en texto plano es vulnerabilidad crítica.

### ❌ Prohibido Retornar Passwords

```typescript
// ❌ PROHIBIDO: Exponer password
async function getUser(id: string) {
  return await db.user.findUnique({
    where: { id }
    // ❌ Retorna password
  })
}

// ✅ CORRECTO: Excluir password
async function getUser(id: string) {
  return await db.user.findUnique({
    where: { id },
    select: {
      id: true,
      email: true,
      name: true,
      // password: false ← No incluir
    }
  })
}
```

**Razón**: Passwords nunca deben salir de la base de datos.

### ❌ Prohibido Validación Solo en Frontend

```typescript
// ❌ PROHIBIDO: Confiar en frontend
app.post('/users', (req, res) => {
  // ❌ Sin validación backend
  await db.user.create(req.body)
})

// ✅ CORRECTO: Validación backend obligatoria
import { z } from 'zod'

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2)
})

app.post('/users', async (req, res) => {
  const validated = createUserSchema.parse(req.body)
  await db.user.create(validated)
})
```

**Razón**: Frontend puede ser bypasseado.

### ❌ Prohibido Blocking Operations

```typescript
// ❌ PROHIBIDO: Operación síncrona que bloquea
import * as fs from 'fs'

app.get('/data', (req, res) => {
  const data = fs.readFileSync('./large-file.json')  // ❌ BLOQUEA
  res.json(data)
})

// ✅ CORRECTO: Operación asíncrona
import { readFile } from 'fs/promises'

app.get('/data', async (req, res) => {
  const data = await readFile('./large-file.json')
  res.json(JSON.parse(data))
})
```

**Razón**: Blocking operations degradan performance para todos los usuarios.

### ❌ Prohibido Errores sin Manejar

```typescript
// ❌ PROHIBIDO: Promesa sin catch
app.get('/users', (req, res) => {
  db.user.findMany()  // ❌ No maneja error
    .then(users => res.json(users))
})

// ✅ CORRECTO: Try-catch o .catch()
app.get('/users', async (req, res) => {
  try {
    const users = await db.user.findMany()
    res.json(users)
  } catch (error) {
    logger.error('Error fetching users', { error })
    res.status(500).json({ error: 'Internal server error' })
  }
})
```

**Razón**: Errores no manejados crashean la aplicación.

---

## 🏗️ Infraestructura (Docker OBLIGATORIO)

### Principio Fundamental

**TODO el desarrollo DEBE hacerse en Docker**

```yaml
Razones:
  - Consistencia entre dev/staging/prod
  - Aislamiento de dependencias
  - Onboarding más rápido
  - CI/CD listo desde día 1
```

### Docker Compose Mínimo

```yaml
# docker-compose.yml
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: api-dev
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: npm run dev

  postgres:
    image: postgres:15-alpine
    container_name: postgres-dev
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile Multi-Stage

```dockerfile
# Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./

# Development stage
FROM base AS development
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS build
RUN npm ci
COPY . .
RUN npm run build
RUN npm prune --production

# Production stage
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package*.json ./
USER node
CMD ["node", "dist/main.js"]
```

### Comandos Docker (SIEMPRE usar)

```bash
# ✅ Iniciar servicios
docker compose up -d

# ✅ Ver logs
docker compose logs -f api

# ✅ Ejecutar comandos dentro del container
docker compose exec api npm install [package]
docker compose exec api npm run test
docker compose exec api npm run migrate

# ✅ Detener servicios
docker compose down

# ❌ NUNCA ejecutar directamente en host
npm install  # NO
npm run dev  # NO
```

---

## 🏛️ Arquitectura Limpia (OBLIGATORIO)

### Principios SOLID

```typescript
// S - Single Responsibility
// ❌ PROHIBIDO: Clase con múltiples responsabilidades
class UserService {
  createUser() { }
  sendEmail() { }  // ❌ No es responsabilidad de UserService
  generateReport() { }  // ❌ No es responsabilidad de UserService
}

// ✅ CORRECTO: Una responsabilidad por clase
class UserService {
  createUser() { }
}

class EmailService {
  sendEmail() { }
}

class ReportService {
  generateReport() { }
}
```

### Separación de Capas

```
src/
├── presentation/       # Controllers, DTOs, Validation
│   ├── controllers/
│   ├── dto/
│   └── validators/
├── application/        # Use cases, Business Logic
│   ├── services/
│   └── use-cases/
├── domain/            # Entities, Interfaces, Types
│   ├── entities/
│   ├── interfaces/
│   └── types/
├── infrastructure/    # Database, External APIs, Cache
│   ├── database/
│   ├── cache/
│   └── external/
└── shared/            # Utilities, Constants, Helpers
    ├── utils/
    ├── constants/
    └── errors/
```

**Reglas:**
- ❌ Controllers NO acceden directamente a database
- ❌ Services NO conocen detalles de HTTP
- ❌ Domain NO depende de infrastructure
- ✅ Dependencies apuntan hacia adentro (Dependency Inversion)

### Repository Pattern

```typescript
// domain/interfaces/user.repository.interface.ts
export interface IUserRepository {
  findById(id: string): Promise<User | null>
  findByEmail(email: string): Promise<User | null>
  create(data: CreateUserData): Promise<User>
  update(id: string, data: UpdateUserData): Promise<User>
  delete(id: string): Promise<void>
}

// infrastructure/database/user.repository.ts
export class UserRepository implements IUserRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findById(id: string): Promise<User | null> {
    const user = await this.prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        name: true,
        // NO password
      }
    })
    return user ? this.toDomain(user) : null
  }

  private toDomain(raw: any): User {
    // Mapear de DB model a Domain entity
    return new User(raw)
  }
}

// application/services/user.service.ts
export class UserService {
  constructor(
    private readonly userRepo: IUserRepository  // ← Interface
  ) {}

  async getUser(id: string): Promise<User> {
    const user = await this.userRepo.findById(id)
    if (!user) throw new UserNotFoundError()
    return user
  }
}
```

**Beneficios:**
- ✅ Fácil de testear (mock repository)
- ✅ Fácil cambiar de DB (solo reimplementar interface)
- ✅ Domain no acoplado a ORM

---

## 📝 Convenciones de Nomenclatura (OBLIGATORIO)

### Archivos

```typescript
// ✅ CORRECTO: kebab-case
user.controller.ts
create-user.dto.ts
user-not-found.error.ts
jwt-auth.guard.ts

// ❌ PROHIBIDO
UserController.ts       // PascalCase
user_controller.ts      // snake_case
userController.ts       // camelCase
```

### Clases e Interfaces

```typescript
// ✅ CORRECTO: PascalCase
export class UserController { }
export class CreateUserDto { }
export interface IUserRepository { }
export enum UserRole { }

// ❌ PROHIBIDO
export class userController { }
export class create_user_dto { }
```

### Métodos y Variables

```typescript
// ✅ CORRECTO: camelCase
async function findUserById(id: string) { }
const currentUser = await getUser()
let isAuthenticated = false

// ❌ PROHIBIDO
async function FindUserById() { }
const current_user = await getUser()
let IsAuthenticated = false
```

### Constantes

```typescript
// ✅ CORRECTO: UPPER_SNAKE_CASE
const MAX_LOGIN_ATTEMPTS = 5
const JWT_SECRET = process.env.JWT_SECRET
const CACHE_TTL_SECONDS = 3600

// ❌ PROHIBIDO
const maxLoginAttempts = 5
const jwtSecret = process.env.JWT_SECRET
```

### Enums

```typescript
// ✅ CORRECTO: PascalCase + UPPER_CASE values
export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user'
}

export enum HttpStatus {
  OK = 200,
  CREATED = 201,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401
}

// ❌ PROHIBIDO
export enum userRole { }
export enum UserRole {
  admin = 'admin',  // lowercase
  Manager = 'manager'  // PascalCase
}
```

### Regla de Oro de Nomenclatura

```
❌ NUNCA usar snake_case en TypeScript
❌ NUNCA usar PascalCase para archivos
❌ NUNCA usar camelCase para constantes
✅ SIEMPRE consistencia en todo el código
```

---

## 🔐 Seguridad Adicional

### JWT Best Practices

```typescript
// ✅ CORRECTO: Configuración JWT segura
{
  algorithm: 'RS256',  // Asymmetric (más seguro que HS256)
  expiresIn: '15m',    // Short-lived access token
  issuer: 'api.yourdomain.com',
  audience: 'yourdomain.com'
}

// Refresh token
{
  expiresIn: '7d',     // Longer for refresh
  // Store in httpOnly cookie
}
```

### Rate Limiting

```typescript
// ✅ CORRECTO: Rate limiting por endpoint
import rateLimit from 'express-rate-limit'

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 5, // 5 intentos
  message: 'Demasiados intentos de login, intenta más tarde'
})

app.post('/auth/login', loginLimiter, loginController)
```

### CORS

```typescript
// ✅ CORRECTO: CORS restrictivo
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))

// ❌ PROHIBIDO: CORS permisivo
app.use(cors({
  origin: '*',  // ❌ Acepta cualquier origen
  credentials: true
}))
```

### Helmet (Security Headers)

```typescript
// ✅ CORRECTO: Usar Helmet
import helmet from 'helmet'

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"]
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true
  }
}))
```

---

## 📊 Persistencia de Contexto

### Recordatorio de Negocio

> **⚠️ CRÍTICO: Leer SIEMPRE antes de generar código**

```markdown
## 🎯 Contexto del Negocio

### Proyecto
**Nombre**: [Nombre del Proyecto]
**Dominio**: [Industria/Sector]
**Objetivo**: [Propósito principal del sistema]

### Casos de Uso Principales
1. [Caso de uso #1]
2. [Caso de uso #2]
3. [Caso de uso #3]

### Entidades Core del Negocio
- **[Entidad 1]**: [Descripción breve]
- **[Entidad 2]**: [Descripción breve]
- **[Entidad 3]**: [Descripción breve]

### Reglas de Negocio CRÍTICAS

1. **[Regla #1]**
   - Descripción: [Qué hace]
   - Implicación técnica: [Cómo implementar]
   - Ejemplo: [Caso concreto]

2. **[Regla #2]**
   - Descripción: [Qué hace]
   - Implicación técnica: [Cómo implementar]
   - Ejemplo: [Caso concreto]

### Restricciones del Dominio

- ❌ **NUNCA**: [Acción prohibida] porque [razón]
- ✅ **SIEMPRE**: [Acción obligatoria] porque [razón]
- ⚠️ **VALIDAR**: [Condición] antes de [acción]

### Workflows Críticos

#### Workflow: [Nombre]
```
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]
   - Si [condición]: [acción alternativa]
   - Si [otra condición]: [otra acción]
4. [Paso 4]
```

### Actores del Sistema

| Actor | Rol | Permisos Clave |
|-------|-----|----------------|
| [Actor 1] | [Descripción] | [Lista de permisos] |
| [Actor 2] | [Descripción] | [Lista de permisos] |

### Integraciones Externas

- **[Servicio 1]**: [Propósito] | [Criticidad]
- **[Servicio 2]**: [Propósito] | [Criticidad]

### Métricas de Negocio

- **[Métrica 1]**: [Cómo se calcula] | Target: [valor]
- **[Métrica 2]**: [Cómo se calcula] | Target: [valor]

### Glosario del Dominio

| Término | Definición | Aliases |
|---------|------------|---------|
| [Término 1] | [Definición exacta] | [Otros nombres] |
| [Término 2] | [Definición exacta] | [Otros nombres] |
```

---

## ✅ Checklist Pre-Generación

Antes de que la IA genere CUALQUIER código, verificar:

### Contexto
- [ ] He leído el "Recordatorio de Negocio"
- [ ] Entiendo el caso de uso que estoy implementando
- [ ] Conozco las reglas de negocio aplicables
- [ ] Sé qué entidades están involucradas

### Stack
- [ ] Confirmo el framework a usar (NestJS/Fastify/Express)
- [ ] Confirmo la versión de TypeScript (5.3+)
- [ ] Confirmo el ORM (Prisma recomendado)
- [ ] Confirmo la base de datos (PostgreSQL recomendado)

### Guardrails
- [ ] NO voy a usar `any` type
- [ ] NO voy a usar magic numbers/strings
- [ ] NO voy a usar `console.log`
- [ ] NO voy a hardcodear secrets
- [ ] NO voy a retornar passwords
- [ ] SÍ voy a validar todos los inputs
- [ ] SÍ voy a usar logging estructurado
- [ ] SÍ voy a manejar errores apropiadamente

### Nomenclatura
- [ ] Archivos: kebab-case
- [ ] Clases: PascalCase
- [ ] Métodos/variables: camelCase
- [ ] Constantes: UPPER_SNAKE_CASE
- [ ] NO snake_case en TypeScript

### Arquitectura
- [ ] Voy a seguir separación de capas
- [ ] Voy a usar Repository Pattern
- [ ] Controllers solo orquestan, no tienen lógica
- [ ] Business logic en services/use-cases
- [ ] Domain entities independientes

### Docker
- [ ] TODO se ejecuta en Docker
- [ ] docker-compose.yml está configurado
- [ ] Dockerfile multi-stage está listo
- [ ] Healthchecks configurados

---

## 📚 Templates de Código

### Controller Template (NestJS)

```typescript
// src/presentation/controllers/user.controller.ts
import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  HttpCode,
  HttpStatus,
  UseGuards,
  Logger
} from '@nestjs/common'
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger'

import { JwtAuthGuard } from '@/shared/guards/jwt-auth.guard'
import { UserService } from '@/application/services/user.service'
import { CreateUserDto } from '../dto/create-user.dto'
import { UpdateUserDto } from '../dto/update-user.dto'
import { UserResponseDto } from '../dto/user-response.dto'

@Controller('users')
@ApiTags('users')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
export class UserController {
  private readonly logger = new Logger(UserController.name)

  constructor(private readonly userService: UserService) {}

  @Get()
  @ApiOperation({ summary: 'Get all users' })
  @ApiResponse({ status: 200, type: [UserResponseDto] })
  async findAll(
    @Query('page') page: number = 1,
    @Query('limit') limit: number = 10
  ): Promise<UserResponseDto[]> {
    this.logger.log('Finding all users', { page, limit })
    return this.userService.findAll({ page, limit })
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  @ApiResponse({ status: 200, type: UserResponseDto })
  @ApiResponse({ status: 404, description: 'User not found' })
  async findOne(@Param('id') id: string): Promise<UserResponseDto> {
    this.logger.log('Finding user', { id })
    return this.userService.findById(id)
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create user' })
  @ApiResponse({ status: 201, type: UserResponseDto })
  @ApiResponse({ status: 400, description: 'Bad request' })
  async create(@Body() dto: CreateUserDto): Promise<UserResponseDto> {
    this.logger.log('Creating user', { email: dto.email })
    return this.userService.create(dto)
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update user' })
  @ApiResponse({ status: 200, type: UserResponseDto })
  @ApiResponse({ status: 404, description: 'User not found' })
  async update(
    @Param('id') id: string,
    @Body() dto: UpdateUserDto
  ): Promise<UserResponseDto> {
    this.logger.log('Updating user', { id })
    return this.userService.update(id, dto)
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete user' })
  @ApiResponse({ status: 204, description: 'User deleted' })
  @ApiResponse({ status: 404, description: 'User not found' })
  async delete(@Param('id') id: string): Promise<void> {
    this.logger.log('Deleting user', { id })
    await this.userService.delete(id)
  }
}
```

### Service Template

```typescript
// src/application/services/user.service.ts
import { Injectable, Logger } from '@nestjs/common'

import { IUserRepository } from '@/domain/interfaces/user.repository.interface'
import { User } from '@/domain/entities/user.entity'
import { UserNotFoundError } from '@/shared/errors/user-not-found.error'
import { CreateUserDto } from '@/presentation/dto/create-user.dto'
import { UpdateUserDto } from '@/presentation/dto/update-user.dto'
import * as bcrypt from 'bcrypt'

const BCRYPT_ROUNDS = 10

@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name)

  constructor(
    private readonly userRepository: IUserRepository
  ) {}

  async findAll(options: { page: number; limit: number }): Promise<User[]> {
    this.logger.log('Finding all users', options)
    return this.userRepository.findAll(options)
  }

  async findById(id: string): Promise<User> {
    this.logger.log('Finding user by ID', { id })
    
    const user = await this.userRepository.findById(id)
    
    if (!user) {
      this.logger.warn('User not found', { id })
      throw new UserNotFoundError(id)
    }
    
    return user
  }

  async create(dto: CreateUserDto): Promise<User> {
    this.logger.log('Creating user', { email: dto.email })
    
    // Hash password
    const hashedPassword = await bcrypt.hash(dto.password, BCRYPT_ROUNDS)
    
    const user = await this.userRepository.create({
      ...dto,
      password: hashedPassword
    })
    
    this.logger.log('User created successfully', { userId: user.id })
    
    return user
  }

  async update(id: string, dto: UpdateUserDto): Promise<User> {
    this.logger.log('Updating user', { id })
    
    // Verify user exists
    await this.findById(id)
    
    // Hash password if provided
    if (dto.password) {
      dto.password = await bcrypt.hash(dto.password, BCRYPT_ROUNDS)
    }
    
    const user = await this.userRepository.update(id, dto)
    
    this.logger.log('User updated successfully', { userId: user.id })
    
    return user
  }

  async delete(id: string): Promise<void> {
    this.logger.log('Deleting user', { id })
    
    // Verify user exists
    await this.findById(id)
    
    await this.userRepository.delete(id)
    
    this.logger.log('User deleted successfully', { id })
  }
}
```

### DTO Template

```typescript
// src/presentation/dto/create-user.dto.ts
import { IsEmail, IsString, MinLength, IsEnum, IsOptional } from 'class-validator'
import { ApiProperty } from '@nestjs/swagger'
import { UserRole } from '@/domain/enums/user-role.enum'

export class CreateUserDto {
  @ApiProperty({
    example: 'user@example.com',
    description: 'User email address'
  })
  @IsEmail()
  email: string

  @ApiProperty({
    example: 'John Doe',
    description: 'User full name',
    minLength: 2
  })
  @IsString()
  @MinLength(2)
  name: string

  @ApiProperty({
    example: 'SecurePass123!',
    description: 'User password',
    minLength: 8
  })
  @IsString()
  @MinLength(8)
  password: string

  @ApiProperty({
    enum: UserRole,
    example: UserRole.USER,
    description: 'User role',
    required: false
  })
  @IsEnum(UserRole)
  @IsOptional()
  role?: UserRole
}

// src/presentation/dto/user-response.dto.ts
import { ApiProperty } from '@nestjs/swagger'
import { UserRole } from '@/domain/enums/user-role.enum'

export class UserResponseDto {
  @ApiProperty({ example: '123e4567-e89b-12d3-a456-426614174000' })
  id: string

  @ApiProperty({ example: 'user@example.com' })
  email: string

  @ApiProperty({ example: 'John Doe' })
  name: string

  @ApiProperty({ enum: UserRole, example: UserRole.USER })
  role: UserRole

  @ApiProperty({ example: '2024-01-01T00:00:00.000Z' })
  createdAt: Date

  @ApiProperty({ example: '2024-01-01T00:00:00.000Z' })
  updatedAt: Date

  // ❌ NO incluir password
}
```

### Repository Template

```typescript
// src/infrastructure/database/repositories/user.repository.ts
import { Injectable } from '@nestjs/common'
import { PrismaClient } from '@prisma/client'

import { IUserRepository } from '@/domain/interfaces/user.repository.interface'
import { User } from '@/domain/entities/user.entity'

@Injectable()
export class UserRepository implements IUserRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findAll(options: { page: number; limit: number }): Promise<User[]> {
    const skip = (options.page - 1) * options.limit
    
    const users = await this.prisma.user.findMany({
      skip,
      take: options.limit,
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        updatedAt: true,
        // ❌ NO password
      },
      orderBy: {
        createdAt: 'desc'
      }
    })
    
    return users.map(this.toDomain)
  }

  async findById(id: string): Promise<User | null> {
    const user = await this.prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      }
    })
    
    return user ? this.toDomain(user) : null
  }

  async findByEmail(email: string): Promise<User | null> {
    const user = await this.prisma.user.findUnique({
      where: { email },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        password: true,  // Solo para auth
        createdAt: true,
        updatedAt: true,
      }
    })
    
    return user ? this.toDomain(user) : null
  }

  async create(data: any): Promise<User> {
    const user = await this.prisma.user.create({
      data,
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      }
    })
    
    return this.toDomain(user)
  }

  async update(id: string, data: any): Promise<User> {
    const user = await this.prisma.user.update({
      where: { id },
      data,
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        updatedAt: true,
      }
    })
    
    return this.toDomain(user)
  }

  async delete(id: string): Promise<void> {
    await this.prisma.user.delete({
      where: { id }
    })
  }

  private toDomain(raw: any): User {
    return new User({
      id: raw.id,
      email: raw.email,
      name: raw.name,
      role: raw.role,
      password: raw.password,  // Solo si está presente
      createdAt: raw.createdAt,
      updatedAt: raw.updatedAt,
    })
  }
}
```

### Test Template

```typescript
// src/application/services/user.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing'
import { UserService } from './user.service'
import { IUserRepository } from '@/domain/interfaces/user.repository.interface'
import { UserNotFoundError } from '@/shared/errors/user-not-found.error'
import { User } from '@/domain/entities/user.entity'
import { UserRole } from '@/domain/enums/user-role.enum'

describe('UserService', () => {
  let service: UserService
  let repository: jest.Mocked<IUserRepository>

  const mockUser: User = {
    id: '123',
    email: 'test@example.com',
    name: 'Test User',
    role: UserRole.USER,
    createdAt: new Date(),
    updatedAt: new Date(),
  }

  beforeEach(async () => {
    const mockRepository = {
      findById: jest.fn(),
      findByEmail: jest.fn(),
      findAll: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    }

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: 'IUserRepository',
          useValue: mockRepository,
        },
      ],
    }).compile()

    service = module.get<UserService>(UserService)
    repository = module.get('IUserRepository')
  })

  it('should be defined', () => {
    expect(service).toBeDefined()
  })

  describe('findById', () => {
    it('should return user when found', async () => {
      repository.findById.mockResolvedValue(mockUser)

      const result = await service.findById('123')

      expect(result).toEqual(mockUser)
      expect(repository.findById).toHaveBeenCalledWith('123')
    })

    it('should throw UserNotFoundError when user not found', async () => {
      repository.findById.mockResolvedValue(null)

      await expect(service.findById('999')).rejects.toThrow(UserNotFoundError)
    })
  })

  describe('create', () => {
    it('should create user with hashed password', async () => {
      const dto = {
        email: 'new@example.com',
        name: 'New User',
        password: 'password123',
      }

      repository.create.mockResolvedValue(mockUser)

      const result = await service.create(dto)

      expect(result).toEqual(mockUser)
      expect(repository.create).toHaveBeenCalledWith(
        expect.objectContaining({
          email: dto.email,
          name: dto.name,
          password: expect.not.stringContaining('password123'), // Debe estar hasheado
        })
      )
    })
  })

  describe('delete', () => {
    it('should delete existing user', async () => {
      repository.findById.mockResolvedValue(mockUser)
      repository.delete.mockResolvedValue(undefined)

      await service.delete('123')

      expect(repository.findById).toHaveBeenCalledWith('123')
      expect(repository.delete).toHaveBeenCalledWith('123')
    })

    it('should throw error when user not found', async () => {
      repository.findById.mockResolvedValue(null)

      await expect(service.delete('999')).rejects.toThrow(UserNotFoundError)
      expect(repository.delete).not.toHaveBeenCalled()
    })
  })
})
```

---

## 🎓 Ejemplo Completo de Uso

### Contexto de Negocio

```markdown
## Recordatorio de Negocio

**Proyecto**: Sistema de Gestión de Biblioteca
**Dominio**: Gestión de préstamos de libros

### Reglas de Negocio CRÍTICAS

1. **Un usuario puede tener máximo 3 libros prestados simultáneamente**
   - Validar antes de aprobar nuevo préstamo
   - Contar solo préstamos activos (no devueltos)

2. **Préstamos duran 14 días**
   - Calcular fecha de devolución al crear préstamo
   - Enviar recordatorio 2 días antes del vencimiento

3. **Multa por retraso: $2 por día**
   - Calcular automáticamente al devolver libro
   - Usuario no puede pedir prestado si tiene multas pendientes

### Entidades Core
- **User**: Usuarios de la biblioteca
- **Book**: Libros disponibles
- **Loan**: Préstamos (relaciona User y Book)
- **Fine**: Multas por retraso
```

### Implementación

```typescript
// domain/entities/loan.entity.ts
export class Loan {
  id: string
  userId: string
  bookId: string
  loanDate: Date
  dueDate: Date
  returnDate?: Date
  fine?: number

  constructor(data: any) {
    this.id = data.id
    this.userId = data.userId
    this.bookId = data.bookId
    this.loanDate = data.loanDate
    this.dueDate = data.dueDate
    this.returnDate = data.returnDate
    this.fine = data.fine
  }

  isOverdue(): boolean {
    if (this.returnDate) return false
    return new Date() > this.dueDate
  }

  calculateFine(): number {
    if (!this.returnDate || !this.isOverdue()) return 0
    
    const daysLate = Math.ceil(
      (this.returnDate.getTime() - this.dueDate.getTime()) / (1000 * 60 * 60 * 24)
    )
    
    const FINE_PER_DAY = 2
    return daysLate * FINE_PER_DAY
  }
}

// application/services/loan.service.ts
const MAX_ACTIVE_LOANS = 3
const LOAN_DURATION_DAYS = 14

@Injectable()
export class LoanService {
  private readonly logger = new Logger(LoanService.name)

  constructor(
    private readonly loanRepository: ILoanRepository,
    private readonly userRepository: IUserRepository,
    private readonly bookRepository: IBookRepository
  ) {}

  async createLoan(userId: string, bookId: string): Promise<Loan> {
    this.logger.log('Creating loan', { userId, bookId })

    // Validar usuario existe
    const user = await this.userRepository.findById(userId)
    if (!user) throw new UserNotFoundError(userId)

    // Validar libro existe y está disponible
    const book = await this.bookRepository.findById(bookId)
    if (!book) throw new BookNotFoundError(bookId)
    if (!book.isAvailable) throw new BookNotAvailableError(bookId)

    // Validar usuario no tiene multas pendientes
    const hasPendingFines = await this.userRepository.hasPendingFines(userId)
    if (hasPendingFines) {
      throw new UserHasPendingFinesError(userId)
    }

    // Validar límite de préstamos activos
    const activeLoans = await this.loanRepository.countActiveLoans(userId)
    if (activeLoans >= MAX_ACTIVE_LOANS) {
      throw new MaxActiveLoansExceededError(userId, MAX_ACTIVE_LOANS)
    }

    // Calcular fecha de devolución
    const loanDate = new Date()
    const dueDate = new Date()
    dueDate.setDate(dueDate.getDate() + LOAN_DURATION_DAYS)

    // Crear préstamo
    const loan = await this.loanRepository.create({
      userId,
      bookId,
      loanDate,
      dueDate
    })

    // Marcar libro como no disponible
    await this.bookRepository.markAsUnavailable(bookId)

    this.logger.log('Loan created successfully', {
      loanId: loan.id,
      dueDate: loan.dueDate
    })

    return loan
  }

  async returnBook(loanId: string): Promise<Loan> {
    this.logger.log('Returning book', { loanId })

    const loan = await this.loanRepository.findById(loanId)
    if (!loan) throw new LoanNotFoundError(loanId)

    if (loan.returnDate) {
      throw new BookAlreadyReturnedError(loanId)
    }

    const returnDate = new Date()
    
    // Calcular multa si aplica
    loan.returnDate = returnDate
    const fine = loan.calculateFine()

    // Actualizar préstamo
    const updatedLoan = await this.loanRepository.update(loanId, {
      returnDate,
      fine
    })

    // Marcar libro como disponible
    await this.bookRepository.markAsAvailable(loan.bookId)

    // Crear registro de multa si aplica
    if (fine > 0) {
      await this.userRepository.createFine({
        userId: loan.userId,
        loanId: loan.id,
        amount: fine
      })
    }

    this.logger.log('Book returned successfully', {
      loanId,
      fine,
      daysLate: fine / 2
    })

    return updatedLoan
  }
}
```

---

## 📋 Checklist Final

Antes de considerar el código completo:

### Funcionalidad
- [ ] Cumple con las reglas de negocio especificadas
- [ ] Implementa todos los casos de uso requeridos
- [ ] Maneja casos edge correctamente
- [ ] Validación de inputs completa

### Calidad de Código
- [ ] Sin `any` types
- [ ] Sin magic numbers/strings
- [ ] Sin `console.log`
- [ ] Sin secrets hardcodeados
- [ ] Nomenclatura consistente (kebab-case, PascalCase, camelCase)
- [ ] Funciones <50 líneas
- [ ] Clases <300 líneas

### Arquitectura
- [ ] Separación de capas respetada
- [ ] Repository pattern implementado
- [ ] Dependency Injection usado
- [ ] Domain entities independientes
- [ ] Controllers sin lógica de negocio

### Seguridad
- [ ] Inputs validados
- [ ] Passwords hasheados
- [ ] Passwords nunca retornados
- [ ] Queries parametrizados (no concatenación SQL)
- [ ] Rate limiting configurado
- [ ] CORS restrictivo
- [ ] Helmet configurado

### Testing
- [ ] Unit tests escritos
- [ ] Coverage >80%
- [ ] Tests con mocks apropiados
- [ ] Tests E2E para flujos críticos

### Docker
- [ ] docker-compose.yml configurado
- [ ] Dockerfile multi-stage
- [ ] Healthchecks configurados
- [ ] Volumes para persistencia

### Documentación
- [ ] Swagger/OpenAPI documentado
- [ ] README actualizado
- [ ] JSDoc en métodos públicos
- [ ] Comentarios explicativos en lógica compleja

---

<div align="center">

**Plantilla Base Lista para Uso**

Usa esta plantilla al inicio de cada proyecto de API

Mantén consistencia | Previene errores | Acelera desarrollo

</div>

---

## 📖 Uso de Esta Plantilla

### Para IAs

1. **Leer completa** esta plantilla antes de generar código
2. **Verificar** checklist pre-generación
3. **Consultar** "Recordatorio de Negocio" constantemente
4. **Seguir** guardrails sin excepción
5. **Usar** templates como punto de partida

### Para Desarrolladores

1. **Compartir** esta plantilla con la IA al inicio
2. **Customizar** "Recordatorio de Negocio" para tu proyecto
3. **Revisar** código generado contra checklist
4. **Iterar** con la IA si algo no cumple estándares

### Para Equipos

1. **Adoptar** como estándar del equipo
2. **Extender** con reglas específicas de tu dominio
3. **Mantener** actualizada con nuevas mejores prácticas
4. **Educar** nuevos miembros con esta plantilla

---

**Versión**: 1.0  
**Última actualización**: Noviembre 2024  
**Siguiente revisión**: Después de 10 proyectos usando la plantilla
