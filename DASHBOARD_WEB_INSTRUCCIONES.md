# 📊 DASHBOARD WEB - Instrucciones Técnicas Completas

> **Objetivo**: Dashboard web profesional para que clientes gestionen sus API keys y visualicen fraud analytics en tiempo real

---

## 🎯 CONTEXTO Y OBJETIVOS

### Por qué necesitas esto:
- 90% de clientes B2B esperan un dashboard visual
- Facilita onboarding (sin necesidad de código para ver resultados)
- Aumenta engagement y reduce churn
- Permite gestionar API keys sin contactar soporte
- Visualización de ROI (valor que aportas)

### Objetivos del Dashboard:
1. **Gestión de API Keys** - Crear, ver, desactivar keys
2. **Visualización de Transacciones** - Ver transacciones analizadas
3. **Analytics de Fraude** - Gráficos de fraud rate, risk levels
4. **Settings** - Configuración de cuenta

---

## 🏗️ ARQUITECTURA DEL DASHBOARD

### Stack Tecnológico Recomendado:

```
Frontend:
- Framework: Next.js 14 (App Router)
- Styling: TailwindCSS + shadcn/ui
- Charts: Recharts
- Auth: NextAuth.js
- State: React Context / Zustand
- HTTP Client: Fetch API / Axios

Backend:
- API existente de DYGSOM (FastAPI)
- Nuevos endpoints para dashboard
- Auth: JWT tokens

Database:
- PostgreSQL (ya existente)
- Nuevas tablas: users, sessions, organizations
```

### Arquitectura High-Level:

```
┌─────────────────────────────────────────┐
│         Next.js Dashboard               │
│  (dashboard.dygsom.com)                 │
│                                         │
│  - Login / Signup                       │
│  - Transactions View                    │
│  - Analytics Charts                     │
│  - API Key Management                   │
└─────────────────────────────────────────┘
              ↓ HTTPS
┌─────────────────────────────────────────┐
│      FastAPI Backend                    │
│  (api.dygsom.com)                       │
│                                         │
│  - POST /auth/login                     │
│  - GET /dashboard/transactions          │
│  - GET /dashboard/analytics             │
│  - POST /dashboard/api-keys             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         PostgreSQL                      │
│  - users                                │
│  - organizations                        │
│  - transactions                         │
│  - api_keys                             │
└─────────────────────────────────────────┘
```

---

## 📁 ESTRUCTURA DEL PROYECTO

### Estructura Recomendada:

```
dygsom-dashboard/
├── app/                        # Next.js 14 App Router
│   ├── (auth)/                # Auth routes
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── signup/
│   │       └── page.tsx
│   ├── (dashboard)/           # Dashboard routes (protected)
│   │   ├── layout.tsx         # Dashboard layout
│   │   ├── page.tsx           # Overview/home
│   │   ├── transactions/
│   │   │   └── page.tsx
│   │   ├── analytics/
│   │   │   └── page.tsx
│   │   ├── api-keys/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   ├── api/                   # Next.js API routes
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts
│   ├── layout.tsx             # Root layout
│   └── providers.tsx          # Context providers
├── components/                # React components
│   ├── ui/                    # shadcn/ui components
│   ├── charts/                # Chart components
│   ├── layout/                # Layout components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── dashboard/             # Dashboard-specific
│       ├── TransactionTable.tsx
│       ├── StatsCard.tsx
│       ├── FraudRateChart.tsx
│       └── RiskDistributionChart.tsx
├── lib/                       # Utilities
│   ├── api.ts                 # API client
│   ├── auth.ts                # Auth utilities
│   └── utils.ts               # General utilities
├── types/                     # TypeScript types
│   └── index.ts
├── public/                    # Static assets
├── .env.local                 # Environment variables
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## 🔨 PARTE 1: BACKEND - NUEVOS ENDPOINTS

### PASO 1: Crear modelos de User y Organization

**Archivo: src/models/__init__.py**

```python
# Agregar a Prisma schema:
# prisma/schema.prisma

model User {
  id            String   @id @default(uuid())
  email         String   @unique
  password_hash String
  name          String?
  role          String   @default("user") // user, admin
  
  organization_id String?
  organization    Organization? @relation(fields: [organization_id], references: [id])
  
  created_at    DateTime @default(now())
  updated_at    DateTime @updatedAt
  last_login_at DateTime?
  
  @@map("users")
}

model Organization {
  id         String   @id @default(uuid())
  name       String
  plan       String   @default("startup") // startup, growth, enterprise
  
  users      User[]
  api_keys   ApiKey[]
  
  created_at DateTime @default(now())
  updated_at DateTime @updatedAt
  
  @@map("organizations")
}

// Actualizar modelo ApiKey existente:
model ApiKey {
  id              String   @id @default(uuid())
  key_hash        String   @unique
  name            String
  description     String?
  
  organization_id String
  organization    Organization @relation(fields: [organization_id], references: [id])
  
  rate_limit      Int      @default(1000)
  is_active       Boolean  @default(true)
  expires_at      DateTime?
  
  request_count   Int      @default(0)
  last_used_at    DateTime?
  
  created_at      DateTime @default(now())
  created_by      String?
  
  @@index([organization_id])
  @@map("api_keys")
}
```

**Después de actualizar schema:**

```bash
prisma generate
prisma migrate dev --name add_users_organizations
```

---

### PASO 2: Crear endpoints de autenticación

**Archivo: src/api/v1/endpoints/auth.py**

```python
"""
Authentication endpoints for dashboard users.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import bcrypt
import jwt
from typing import Optional

from src.core.config import settings
from src.dependencies import get_prisma

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT Configuration
SECRET_KEY = settings.JWT_SECRET_KEY  # Add to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    organization_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, prisma = Depends(get_prisma)):
    """
    Sign up new user and organization.
    
    Creates:
    1. New organization
    2. New user (admin)
    3. First API key (auto-generated)
    """
    # Check if user already exists
    existing_user = await prisma.user.find_unique(
        where={"email": request.email}
    )
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create organization
    organization = await prisma.organization.create(
        data={
            "name": request.organization_name,
            "plan": "startup"
        }
    )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    user = await prisma.user.create(
        data={
            "email": request.email,
            "password_hash": password_hash,
            "name": request.name,
            "organization_id": organization.id,
            "role": "admin"
        }
    )
    
    # Create first API key
    from src.core.security import SecurityUtils
    api_key_plain = SecurityUtils.generate_api_key()
    api_key_hash = SecurityUtils.hash_api_key(api_key_plain)
    
    await prisma.apikey.create(
        data={
            "key_hash": api_key_hash,
            "name": "Default API Key",
            "description": "Auto-generated key",
            "organization_id": organization.id,
            "rate_limit": 1000,
            "created_by": user.id
        }
    )
    
    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "organization_id": organization.id
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "plan": organization.plan
            }
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, prisma = Depends(get_prisma)):
    """
    Login user and return JWT token.
    """
    # Find user
    user = await prisma.user.find_unique(
        where={"email": request.email},
        include={"organization": True}
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Update last login
    await prisma.user.update(
        where={"id": user.id},
        data={"last_login_at": datetime.utcnow()}
    )
    
    # Create access token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "organization_id": user.organization_id
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "organization": {
                "id": user.organization.id,
                "name": user.organization.name,
                "plan": user.organization.plan
            } if user.organization else None
        }
    )


@router.get("/me")
async def get_current_user(
    current_user = Depends(get_current_user),  # Add dependency
    prisma = Depends(get_prisma)
):
    """
    Get current authenticated user.
    """
    user = await prisma.user.find_unique(
        where={"id": current_user["user_id"]},
        include={"organization": True}
    )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization": {
            "id": user.organization.id,
            "name": user.organization.name,
            "plan": user.organization.plan
        } if user.organization else None
    }
```

**Dependency para autenticación:**

**Archivo: src/dependencies.py** (agregar)

```python
from fastapi import HTTPException, Header
import jwt

async def get_current_user(authorization: str = Header(None)):
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage:
        current_user = Depends(get_current_user)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        # Decode JWT
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
```

**Agregar a config.py:**

```python
# JWT
JWT_SECRET_KEY: str  # Generate with: openssl rand -hex 32
```

---

### PASO 3: Crear endpoints de dashboard

**Archivo: src/api/v1/endpoints/dashboard.py**

```python
"""
Dashboard endpoints for analytics and management.
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from src.dependencies import get_prisma, get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class TransactionResponse(BaseModel):
    id: str
    transaction_id: str
    amount: float
    currency: str
    fraud_score: float
    risk_level: str
    recommendation: str
    customer_email: str
    customer_ip: str
    timestamp: datetime


class AnalyticsSummary(BaseModel):
    total_transactions: int
    fraud_detected: int
    fraud_rate: float
    total_amount_analyzed: float
    avg_fraud_score: float


@router.get("/transactions")
async def get_transactions(
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    risk_level: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
):
    """
    Get transactions for current organization.
    
    Filters:
    - risk_level: LOW, MEDIUM, HIGH, CRITICAL
    - date_from: Start date
    - date_to: End date
    - limit: Max results
    - offset: Pagination offset
    """
    organization_id = current_user["organization_id"]
    
    # Build filters
    where = {
        "organization_id": organization_id
    }
    
    if risk_level:
        where["risk_level"] = risk_level
    
    if date_from or date_to:
        where["timestamp"] = {}
        if date_from:
            where["timestamp"]["gte"] = date_from
        if date_to:
            where["timestamp"]["lte"] = date_to
    
    # Query transactions
    transactions = await prisma.transaction.find_many(
        where=where,
        order_by={"timestamp": "desc"},
        take=limit,
        skip=offset
    )
    
    # Count total
    total = await prisma.transaction.count(where=where)
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90)
):
    """
    Get analytics summary for last N days.
    
    Returns:
    - Total transactions
    - Fraud detected
    - Fraud rate
    - Total amount analyzed
    - Average fraud score
    """
    organization_id = current_user["organization_id"]
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Aggregate queries
    stats = await prisma.transaction.aggregate(
        where={
            "organization_id": organization_id,
            "timestamp": {"gte": date_from}
        },
        _count=True,
        _sum={"amount": True},
        _avg={"fraud_score": True}
    )
    
    # Count high-risk transactions
    fraud_count = await prisma.transaction.count(
        where={
            "organization_id": organization_id,
            "timestamp": {"gte": date_from},
            "risk_level": {"in": ["HIGH", "CRITICAL"]}
        }
    )
    
    total = stats._count or 0
    fraud_rate = (fraud_count / total * 100) if total > 0 else 0
    
    return AnalyticsSummary(
        total_transactions=total,
        fraud_detected=fraud_count,
        fraud_rate=round(fraud_rate, 2),
        total_amount_analyzed=stats._sum.amount or 0,
        avg_fraud_score=round(stats._avg.fraud_score or 0, 3)
    )


@router.get("/analytics/fraud-rate-over-time")
async def get_fraud_rate_over_time(
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90)
):
    """
    Get fraud rate over time (daily aggregation).
    
    Returns:
    Array of {date, fraud_rate, total_transactions}
    """
    organization_id = current_user["organization_id"]
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Raw SQL for daily aggregation
    results = await prisma.execute_raw(f"""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE risk_level IN ('HIGH', 'CRITICAL')) as fraud_count,
            ROUND(
                COUNT(*) FILTER (WHERE risk_level IN ('HIGH', 'CRITICAL'))::numeric / 
                COUNT(*)::numeric * 100,
                2
            ) as fraud_rate
        FROM transactions
        WHERE organization_id = '{organization_id}'
          AND timestamp >= '{date_from.isoformat()}'
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
    """)
    
    return results


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma),
    days: int = Query(7, ge=1, le=90)
):
    """
    Get risk level distribution.
    
    Returns:
    {LOW: 850, MEDIUM: 120, HIGH: 25, CRITICAL: 5}
    """
    organization_id = current_user["organization_id"]
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Group by risk level
    results = await prisma.transaction.group_by(
        by=["risk_level"],
        where={
            "organization_id": organization_id,
            "timestamp": {"gte": date_from}
        },
        _count=True
    )
    
    # Format as dict
    distribution = {item.risk_level: item._count for item in results}
    
    return distribution


@router.get("/api-keys")
async def get_api_keys(
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma)
):
    """
    Get all API keys for current organization.
    
    Note: Does not return actual keys, only metadata.
    """
    organization_id = current_user["organization_id"]
    
    api_keys = await prisma.apikey.find_many(
        where={"organization_id": organization_id},
        order_by={"created_at": "desc"}
    )
    
    return {
        "api_keys": [
            {
                "id": key.id,
                "name": key.name,
                "description": key.description,
                "rate_limit": key.rate_limit,
                "is_active": key.is_active,
                "request_count": key.request_count,
                "last_used_at": key.last_used_at,
                "created_at": key.created_at,
                # Never return actual key
            }
            for key in api_keys
        ]
    }


@router.post("/api-keys")
async def create_api_key(
    name: str,
    description: str = "",
    rate_limit: int = 1000,
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma)
):
    """
    Create new API key.
    
    Returns the plain key ONCE. User must save it.
    """
    organization_id = current_user["organization_id"]
    user_id = current_user["user_id"]
    
    # Generate key
    from src.core.security import SecurityUtils
    api_key_plain = SecurityUtils.generate_api_key()
    api_key_hash = SecurityUtils.hash_api_key(api_key_plain)
    
    # Create in DB
    api_key = await prisma.apikey.create(
        data={
            "key_hash": api_key_hash,
            "name": name,
            "description": description,
            "organization_id": organization_id,
            "rate_limit": rate_limit,
            "created_by": user_id
        }
    )
    
    return {
        "api_key": api_key_plain,  # ONLY time we return plain key
        "id": api_key.id,
        "name": api_key.name,
        "rate_limit": api_key.rate_limit,
        "created_at": api_key.created_at,
        "warning": "Save this key now. You won't be able to see it again."
    }


@router.delete("/api-keys/{key_id}")
async def deactivate_api_key(
    key_id: str,
    current_user = Depends(get_current_user),
    prisma = Depends(get_prisma)
):
    """
    Deactivate API key (soft delete).
    """
    organization_id = current_user["organization_id"]
    
    # Verify key belongs to organization
    api_key = await prisma.apikey.find_first(
        where={
            "id": key_id,
            "organization_id": organization_id
        }
    )
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Deactivate
    await prisma.apikey.update(
        where={"id": key_id},
        data={"is_active": False}
    )
    
    return {"message": "API key deactivated successfully"}
```

**Actualizar router principal:**

**Archivo: src/api/v1/router.py**

```python
from src.api.v1.endpoints import fraud, admin, auth, dashboard

# Include routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
# ... existing routers
```

---

## 🔨 PARTE 2: FRONTEND - NEXT.JS DASHBOARD

### PASO 1: Setup del proyecto Next.js

```bash
# Create Next.js project
npx create-next-app@latest dygsom-dashboard --typescript --tailwind --app

cd dygsom-dashboard

# Install dependencies
npm install @radix-ui/react-dropdown-menu @radix-ui/react-dialog
npm install recharts
npm install axios
npm install next-auth
npm install date-fns
npm install lucide-react
npm install class-variance-authority clsx tailwind-merge

# Install shadcn/ui
npx shadcn-ui@latest init

# Add shadcn components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add toast
```

---

### PASO 2: Configurar variables de entorno

**Archivo: .env.local**

```bash
# API Backend
NEXT_PUBLIC_API_URL=http://localhost:3000
# En producción: https://api.dygsom.com

# NextAuth
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3001
```

---

### PASO 3: Crear API client

**Archivo: lib/api.ts**

```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  signup: async (data: {
    email: string;
    password: string;
    name: string;
    organization_name: string;
  }) => {
    const response = await apiClient.post('/api/v1/auth/signup', data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await apiClient.post('/api/v1/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  getMe: async () => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },
};

// Dashboard API
export const dashboardAPI = {
  getTransactions: async (params?: {
    limit?: number;
    offset?: number;
    risk_level?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    const response = await apiClient.get('/api/v1/dashboard/transactions', {
      params,
    });
    return response.data;
  },

  getAnalyticsSummary: async (days: number = 7) => {
    const response = await apiClient.get(
      `/api/v1/dashboard/analytics/summary?days=${days}`
    );
    return response.data;
  },

  getFraudRateOverTime: async (days: number = 7) => {
    const response = await apiClient.get(
      `/api/v1/dashboard/analytics/fraud-rate-over-time?days=${days}`
    );
    return response.data;
  },

  getRiskDistribution: async (days: number = 7) => {
    const response = await apiClient.get(
      `/api/v1/dashboard/analytics/risk-distribution?days=${days}`
    );
    return response.data;
  },

  getApiKeys: async () => {
    const response = await apiClient.get('/api/v1/dashboard/api-keys');
    return response.data;
  },

  createApiKey: async (data: {
    name: string;
    description?: string;
    rate_limit?: number;
  }) => {
    const response = await apiClient.post('/api/v1/dashboard/api-keys', data);
    return response.data;
  },

  deactivateApiKey: async (keyId: string) => {
    const response = await apiClient.delete(
      `/api/v1/dashboard/api-keys/${keyId}`
    );
    return response.data;
  },
};
```

---

### PASO 4: Crear página de login

**Archivo: app/(auth)/login/page.tsx**

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authAPI.login(email, password);
      
      // Save token
      localStorage.setItem('access_token', response.access_token);
      
      // Redirect to dashboard
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>
            Sign in to your DYGSOM dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}
            
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
            
            <div className="text-center text-sm">
              Don't have an account?{' '}
              <a href="/signup" className="text-blue-600 hover:underline">
                Sign up
              </a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### PASO 5: Crear dashboard overview page

**Archivo: app/(dashboard)/page.tsx**

```typescript
'use client';

import { useEffect, useState } from 'react';
import { dashboardAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FraudRateChart } from '@/components/dashboard/FraudRateChart';
import { RiskDistributionChart } from '@/components/dashboard/RiskDistributionChart';
import { Activity, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      const data = await dashboardAPI.getAnalyticsSummary(7);
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Last 7 days overview</p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Transactions
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.total_transactions.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Fraud Detected
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {summary?.fraud_detected}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary?.fraud_rate}% of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Amount Analyzed
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${summary?.total_amount_analyzed.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Fraud Score
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.avg_fraud_score.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              Out of 1.00
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Fraud Rate Over Time</CardTitle>
            <CardDescription>Daily fraud rate trend</CardDescription>
          </CardHeader>
          <CardContent>
            <FraudRateChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>Transactions by risk level</CardDescription>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

### PASO 6: Crear componente de chart

**Archivo: components/dashboard/FraudRateChart.tsx**

```typescript
'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { dashboardAPI } from '@/lib/api';
import { format } from 'date-fns';

export function FraudRateChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const result = await dashboardAPI.getFraudRateOverTime(7);
      
      // Format data for chart
      const formatted = result.map((item: any) => ({
        date: format(new Date(item.date), 'MMM dd'),
        fraudRate: parseFloat(item.fraud_rate),
        total: item.total,
      }));
      
      setData(formatted);
    } catch (error) {
      console.error('Error loading fraud rate:', error);
    }
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="fraudRate"
          stroke="#ef4444"
          strokeWidth={2}
          name="Fraud Rate %"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Backend:
- [ ] Prisma schema actualizado (User, Organization)
- [ ] Migrations corridas
- [ ] Endpoints de auth (/signup, /login, /me)
- [ ] JWT secret configurado
- [ ] Endpoints de dashboard (/transactions, /analytics, /api-keys)
- [ ] get_current_user dependency
- [ ] Routers incluidos en main

### Frontend:
- [ ] Next.js project creado
- [ ] Dependencies instaladas
- [ ] API client configurado
- [ ] Login page
- [ ] Signup page
- [ ] Dashboard layout
- [ ] Overview page con stats
- [ ] Charts (fraud rate, risk distribution)
- [ ] Transactions table page
- [ ] API keys management page

---

## 🧪 TESTING

### 1. Test Backend

```bash
# Test signup
curl -X POST http://localhost:3000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "organization_name": "Test Org"
  }'

# Expected: Returns access_token

# Test login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Test dashboard (with token)
curl http://localhost:3000/api/v1/dashboard/analytics/summary \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 2. Test Frontend

```bash
# Run development server
npm run dev

# Open browser
open http://localhost:3001

# Test flow:
1. Go to /signup
2. Create account
3. Login
4. See dashboard
5. View transactions
6. Create API key
```

---

## 📊 RESULTADO FINAL

Al completar esto tendrás:

✅ **Dashboard profesional** con:
- Authentication completa (signup/login)
- Overview con métricas clave
- Charts de fraud rate y risk distribution
- Tabla de transacciones con filtros
- Gestión de API keys
- Settings de cuenta

✅ **Backend robusto** con:
- User management
- Organization management
- JWT authentication
- Protected endpoints
- Analytics APIs

✅ **Listo para clientes** que puedan:
- Ver resultados en tiempo real
- Gestionar sus API keys
- Visualizar ROI
- Exportar reportes

---

**Tiempo estimado: 1-2 semanas full-time**

¿Quieres que continúe con más páginas específicas (Transactions table, API Keys management, Settings)?
