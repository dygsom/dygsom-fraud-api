-- Script para crear API Key de prueba
-- Este script es idempotente y puede ejecutarse múltiples veces

INSERT INTO "ApiKey" (id, name, key_hash, is_active, rate_limit, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'test-key',
    encode(sha256('dygsom_test_api_key_2024'::bytea), 'hex'),
    true,
    100,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "ApiKey" WHERE name = 'test-key'
);
