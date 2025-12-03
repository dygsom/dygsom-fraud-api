# Script de Pruebas Automatizadas - DYGSOM Fraud API
# Todas las pruebas usan docker compose exec (ambiente dockerizado)
# Uso: .\tests\scripts\run_tests.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DYGSOM FRAUD API - PRUEBAS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$SuccessCount = 0

function Run-Test {
    param([string]$TestName, [scriptblock]$TestCommand)
    
    Write-Host "TEST: $TestName" -ForegroundColor Yellow
    try {
        $result = & $TestCommand
        if ($LASTEXITCODE -eq 0 -or $result) {
            Write-Host "  PASS" -ForegroundColor Green
            $script:SuccessCount++
        } else {
            Write-Host "  FAIL" -ForegroundColor Red
            $script:ErrorCount++
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $script:ErrorCount++
    }
    Write-Host ""
}

# FASE 1: INFRAESTRUCTURA
Write-Host "=== FASE 1: INFRAESTRUCTURA ===" -ForegroundColor Cyan
Write-Host ""

Run-Test "Docker Compose - Servicios corriendo" {
    $output = docker compose ps
    $output -match "Up"
}

Run-Test "PostgreSQL - Conexion disponible" {
    docker compose exec -T postgres pg_isready -U postgres -d dygsom 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "Redis - Servicio disponible" {
    docker compose exec -T redis redis-cli ping 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "API - Container healthy" {
    $output = docker compose ps api
    $output -match "healthy"
}

# FASE 2: HEALTH CHECKS (usando docker compose exec)
Write-Host "=== FASE 2: HEALTH CHECKS ===" -ForegroundColor Cyan
Write-Host ""

Run-Test "Health - Endpoint basico" {
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null http://localhost:3000/health 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "Health - Endpoint ready" {
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null http://localhost:3000/health/ready 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "Metrics - Endpoint publico" {
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null http://localhost:3000/metrics 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

# FASE 3: BASE DE DATOS
Write-Host "=== FASE 3: BASE DE DATOS ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Aplicando migraciones Prisma..." -ForegroundColor Yellow
docker compose exec -T api npx prisma migrate deploy 2>&1 | Out-Null
Write-Host "  Migraciones aplicadas" -ForegroundColor Green
Write-Host ""

Write-Host "Creando API Key de prueba..." -ForegroundColor Yellow
Get-Content tests\scripts\create_test_apikey.sql | docker compose exec -T postgres psql -U postgres -d dygsom 2>&1 | Out-Null
Write-Host "  API Key creada: dygsom_test_api_key_2024" -ForegroundColor Green
Write-Host ""

# FASE 4: AUTENTICACION (usando docker compose exec)
Write-Host "=== FASE 4: AUTENTICACION ===" -ForegroundColor Cyan
Write-Host ""

Run-Test "Autenticacion - 401 sin API Key" {
    $testJson = '{"test":"data"}'
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null -X POST http://localhost:3000/api/v1/fraud/score -H "Content-Type: application/json" -d "$testJson" 2>&1 | Select-String "401"
}

Run-Test "Metrics - Acceso publico sin API Key" {
    $response = curl.exe -s -w "%{http_code}" -o nul http://localhost:3000/metrics
    $response -eq "200"
}

# FASE 5: FRAUD SCORING (usando docker compose exec)
Write-Host "=== FASE 5: FRAUD SCORING ===" -ForegroundColor Cyan
Write-Host ""

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

Run-Test "Fraud Scoring - LOW RISK" {
    $lowJson = '{\"transaction_id\":\"tx-low-001\",\"customer_email\":\"john@gmail.com\",\"customer_ip\":\"192.168.1.1\",\"amount\":100,\"currency\":\"USD\",\"merchant_id\":\"m001\",\"card_bin\":\"424242\",\"device_id\":\"d001\",\"timestamp\":\"' + $timestamp + '\"}'
    $response = docker compose exec -T api curl -s -X POST http://localhost:3000/api/v1/fraud/score -H "Content-Type: application/json" -H "X-API-Key: dygsom_test_api_key_2024" -d "$lowJson"
    $response -match "tx-low-001"
}

Run-Test "Fraud Scoring - HIGH RISK" {
    $highJson = '{\"transaction_id\":\"tx-high-002\",\"customer_email\":\"bad@temp.com\",\"customer_ip\":\"45.67.89.1\",\"amount\":9000,\"currency\":\"USD\",\"merchant_id\":\"m999\",\"card_bin\":\"555555\",\"device_id\":\"d999\",\"timestamp\":\"' + $timestamp + '\"}'
    $response = docker compose exec -T api curl -s -X POST http://localhost:3000/api/v1/fraud/score -H "Content-Type: application/json" -H "X-API-Key: dygsom_test_api_key_2024" -d "$highJson"
    $response -match "tx-high-002"
}

# FASE 6: PERFORMANCE
Write-Host "=== FASE 6: PERFORMANCE ===" -ForegroundColor Cyan
Write-Host ""

Run-Test "Performance - Latencia promedio" {
    $latencies = @()
    for ($i = 1; $i -le 5; $i++) {
        $start = Get-Date
        curl.exe -s -X POST http://localhost:3000/api/v1/fraud/score -H "Content-Type: application/json" -H "X-API-Key: dygsom_test_api_key_2024" -d $lowRiskJson -o nul
        $end = Get-Date
        $latencies += ($end - $start).TotalMilliseconds
    }
    $avg = ($latencies | Measure-Object -Average).Average
    Write-Host "  Latencia: $([math]::Round($avg, 2))ms" -ForegroundColor Cyan
    $avg -lt 300
}

# FASE 7: MONITORING (usando docker compose exec)
Write-Host "=== FASE 7: MONITORING ===" -ForegroundColor Cyan
Write-Host ""

Run-Test "Prometheus - Puerto 9090" {
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null http://prometheus:9090 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "Grafana - Puerto 3002" {
    docker compose exec -T api curl -s -w "%{http_code}" -o /dev/null http://grafana:3000 2>&1 | Out-Null
    $LASTEXITCODE -eq 0
}

Run-Test "Metricas - api_requests_total" {
    $response = docker compose exec -T api curl -s http://localhost:3000/metrics
    $response -match "api_requests_total"
}

Run-Test "Metricas - fraud_score_distribution" {
    $response = docker compose exec -T api curl -s http://localhost:3000/metrics
    $response -match "fraud_score_distribution"
}

# RESUMEN
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TotalTests = $SuccessCount + $ErrorCount
Write-Host "Total: $TotalTests" -ForegroundColor White
Write-Host "  Exitosas: $SuccessCount" -ForegroundColor Green
Write-Host "  Fallidas:  $ErrorCount" -ForegroundColor Red
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "TODAS LAS PRUEBAS PASARON!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Servicios:" -ForegroundColor Cyan
    Write-Host "  API:        http://localhost:3000" -ForegroundColor White
    Write-Host "  Docs:       http://localhost:3000/docs" -ForegroundColor White
    Write-Host "  Metrics:    http://localhost:3000/metrics" -ForegroundColor White
    Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "  - Grafana:    http://localhost:3002" -ForegroundColor White
    Write-Host ""
    Write-Host "API Key: dygsom_test_api_key_2024" -ForegroundColor Yellow
    Write-Host ""
    exit 0
} else {
    Write-Host "ALGUNAS PRUEBAS FALLARON" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ver logs: docker compose logs api" -ForegroundColor White
    Write-Host ""
    exit 1
}
