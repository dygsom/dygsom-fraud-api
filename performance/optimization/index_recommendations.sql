-- ============================================================================
-- DYGSOM Fraud API - Index Recommendations and Monitoring
-- ============================================================================
-- Purpose: Identify missing indexes, unused indexes, and optimize index usage
-- Impact: Helps maintain optimal query performance over time
-- Usage: Run these queries periodically to audit index health
-- ============================================================================

-- ============================================================================
-- PART 1: INDEX USAGE STATISTICS
-- ============================================================================
-- These queries help you understand which indexes are being used and how often
-- ============================================================================

-- 1.1: Index usage summary for transactions table
-- Shows: Index scan count, rows read, index effectiveness
-- Interpretation: Low idx_scan with high seq_scan indicates missing indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as index_tuples_read,
    idx_tup_fetch as index_tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes
WHERE tablename = 'transactions'
ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC;

COMMENT ON QUERY IS
'Shows index usage statistics for the transactions table.
Action: Indexes with UNUSED status should be investigated for removal.';


-- 1.2: Table scan statistics (sequential vs index scans)
-- Shows: How often table is scanned sequentially vs using indexes
-- Interpretation: High seq_scan ratio indicates missing indexes
SELECT
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    seq_tup_read as sequential_tuples_read,
    idx_scan as index_scans,
    idx_tup_fetch as index_tuples_fetched,
    n_live_tup as live_tuples,
    CASE
        WHEN seq_scan + idx_scan = 0 THEN 0
        ELSE ROUND(100.0 * seq_scan / NULLIF(seq_scan + idx_scan, 0), 2)
    END as seq_scan_pct,
    CASE
        WHEN seq_scan + idx_scan = 0 THEN 0
        ELSE ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2)
    END as idx_scan_pct
FROM pg_stat_user_tables
WHERE tablename = 'transactions'
ORDER BY seq_scan DESC;

COMMENT ON QUERY IS
'Compares sequential scans vs index scans.
Action: If seq_scan_pct > 20%, investigate missing indexes.';


-- 1.3: Index hit ratio (should be >99%)
-- Shows: How often index data is in cache vs read from disk
-- Interpretation: Low ratio indicates need for more memory or better indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_blks_hit as index_blocks_hit,
    idx_blks_read as index_blocks_read,
    CASE
        WHEN (idx_blks_hit + idx_blks_read) = 0 THEN NULL
        ELSE ROUND(100.0 * idx_blks_hit / NULLIF(idx_blks_hit + idx_blks_read, 0), 2)
    END as cache_hit_ratio_pct
FROM pg_statio_user_indexes
WHERE tablename = 'transactions'
    AND (idx_blks_hit + idx_blks_read) > 0
ORDER BY cache_hit_ratio_pct ASC NULLS LAST;

COMMENT ON QUERY IS
'Shows index cache hit ratio.
Target: >99% hit ratio. Lower values indicate memory pressure.';


-- ============================================================================
-- PART 2: UNUSED INDEX DETECTION
-- ============================================================================
-- Identifies indexes that are never used and can be safely dropped
-- WARNING: Only drop indexes after monitoring for at least 7 days
-- ============================================================================

-- 2.1: Completely unused indexes
-- Shows: Indexes with zero scans that consume disk space
-- Action: Consider dropping after verifying with application team
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as times_used,
    pg_get_indexdef(indexrelid) as index_definition
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename = 'transactions'
    AND idx_scan = 0
    AND indexrelid NOT IN (
        -- Don't include primary key and unique constraints
        SELECT conindid
        FROM pg_constraint
        WHERE contype IN ('p', 'u')
    )
ORDER BY pg_relation_size(indexrelid) DESC;

COMMENT ON QUERY IS
'Identifies completely unused indexes (zero scans).
WARNING: Monitor for at least 7 days before dropping.
Command to drop: DROP INDEX CONCURRENTLY index_name;';


-- 2.2: Low-usage large indexes
-- Shows: Indexes that are rarely used but consume significant space
-- Action: Evaluate cost/benefit of keeping these indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_relation_size(indexrelid) as index_size_bytes,
    CASE
        WHEN idx_scan = 0 THEN NULL
        ELSE ROUND(pg_relation_size(indexrelid)::NUMERIC / NULLIF(idx_scan, 0) / 1024, 2)
    END as kb_per_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename = 'transactions'
    AND pg_relation_size(indexrelid) > 10485760  -- Larger than 10MB
    AND idx_scan < 1000  -- Used less than 1000 times
ORDER BY kb_per_scan DESC NULLS LAST;

COMMENT ON QUERY IS
'Shows large indexes with low usage (size > 10MB, scans < 1000).
Action: High kb_per_scan indicates expensive indexes. Consider removal.';


-- ============================================================================
-- PART 3: MISSING INDEX DETECTION
-- ============================================================================
-- Identifies queries that would benefit from additional indexes
-- Requires: pg_stat_statements extension
-- ============================================================================

-- 3.1: Enable pg_stat_statements extension (run once)
-- This extension tracks query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

COMMENT ON EXTENSION pg_stat_statements IS
'Tracks planning and execution statistics for all SQL queries.
Required for missing index detection.';


-- 3.2: Slow queries without index usage
-- Shows: Queries that perform sequential scans and take significant time
-- Interpretation: These queries would benefit from new indexes
/*
SELECT
    query,
    calls,
    ROUND(total_time::NUMERIC / calls, 2) as avg_time_ms,
    ROUND(total_time::NUMERIC, 2) as total_time_ms,
    ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) as cache_hit_ratio,
    rows
FROM pg_stat_statements
WHERE query LIKE '%transactions%'
    AND query NOT LIKE '%pg_%'  -- Exclude system queries
    AND calls > 100  -- Executed at least 100 times
    AND (total_time / calls) > 50  -- Average time > 50ms
ORDER BY (total_time / calls) DESC
LIMIT 20;
*/

COMMENT ON QUERY IS
'Identifies slow queries on transactions table.
Note: Uncomment after ensuring pg_stat_statements is enabled.
Action: Analyze EXPLAIN plans for these queries to identify missing indexes.';


-- 3.3: Sequential scans on large tables
-- Shows: Queries forcing full table scans
-- Action: Add indexes for frequently scanned columns
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    seq_tup_read / NULLIF(seq_scan, 0) as avg_tuples_per_scan,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    n_live_tup as live_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND tablename = 'transactions'
    AND seq_scan > 0
    AND n_live_tup > 10000  -- Tables with >10k rows
ORDER BY seq_scan DESC, seq_tup_read DESC;

COMMENT ON QUERY IS
'Shows tables with frequent sequential scans.
Action: High avg_tuples_per_scan (>1000) suggests missing indexes.';


-- ============================================================================
-- PART 4: INDEX RECOMMENDATIONS
-- ============================================================================
-- Based on query patterns, these are recommended indexes
-- ============================================================================

-- 4.1: Recommended indexes for common query patterns
-- (These are already in query_optimization.sql, but listed here for reference)

/*
RECOMMENDED INDEXES (if not already created):

1. Customer Email + Timestamp (for velocity features)
   CREATE INDEX CONCURRENTLY idx_transactions_customer_recent
   ON transactions (customer_email, timestamp DESC)
   WHERE timestamp > NOW() - INTERVAL '7 days';

2. Customer IP + Timestamp (for IP-based fraud detection)
   CREATE INDEX CONCURRENTLY idx_transactions_ip_recent
   ON transactions (customer_ip, timestamp DESC)
   WHERE timestamp > NOW() - INTERVAL '7 days';

3. Merchant + Risk Level (for merchant fraud rates)
   CREATE INDEX CONCURRENTLY idx_transactions_merchant_recent
   ON transactions (merchant_id, timestamp DESC, risk_level)
   WHERE timestamp > NOW() - INTERVAL '30 days';

4. Risk Level + Timestamp (for dashboard queries)
   CREATE INDEX CONCURRENTLY idx_transactions_risk_timestamp
   ON transactions (risk_level, timestamp DESC)
   WHERE risk_level IN ('HIGH', 'CRITICAL');

5. Amount + Timestamp (for large transaction detection)
   CREATE INDEX CONCURRENTLY idx_transactions_amount_desc
   ON transactions (amount DESC, timestamp DESC)
   WHERE amount > 1000;

6. Fraud Score covering index (for ML evaluation)
   CREATE INDEX CONCURRENTLY idx_transactions_fraud_score_covering
   ON transactions (fraud_score DESC, timestamp DESC)
   INCLUDE (customer_email, amount, risk_level);
*/


-- 4.2: Future index recommendations based on access patterns
-- Run this query to identify potential new indexes based on actual usage

-- This query identifies columns frequently used in WHERE clauses
-- that might benefit from indexes
/*
WITH query_patterns AS (
    SELECT
        query,
        calls,
        mean_time
    FROM pg_stat_statements
    WHERE query LIKE '%WHERE%transactions%'
        AND query NOT LIKE '%pg_%'
        AND calls > 50
    ORDER BY calls DESC
    LIMIT 100
)
SELECT
    'Consider adding index on frequently filtered columns' as recommendation,
    COUNT(*) as query_count
FROM query_patterns;
*/


-- ============================================================================
-- PART 5: INDEX BLOAT DETECTION
-- ============================================================================
-- Identifies indexes that have become bloated and need rebuilding
-- ============================================================================

-- 5.1: Index bloat estimation
-- Shows: Estimated bloat in indexes
-- Action: Indexes with >30% bloat should be rebuilt
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    ROUND(100 * (pg_relation_size(indexrelid) -
        (SELECT SUM(avg_width * n_distinct)
         FROM pg_stats
         WHERE schemaname = pui.schemaname
           AND tablename = pui.tablename)::NUMERIC
    ) / NULLIF(pg_relation_size(indexrelid), 0), 2) as estimated_bloat_pct
FROM pg_stat_user_indexes pui
WHERE schemaname = 'public'
    AND tablename = 'transactions'
    AND pg_relation_size(indexrelid) > 10485760  -- Larger than 10MB
ORDER BY estimated_bloat_pct DESC;

COMMENT ON QUERY IS
'Estimates index bloat percentage.
Action: Rebuild indexes with >30% bloat using REINDEX CONCURRENTLY.';


-- 5.2: Rebuild bloated indexes
-- Command template (run during low traffic)
/*
REINDEX INDEX CONCURRENTLY index_name;

OR for all indexes on a table:
REINDEX TABLE CONCURRENTLY transactions;
*/


-- ============================================================================
-- PART 6: INDEX MAINTENANCE RECOMMENDATIONS
-- ============================================================================
-- Best practices for maintaining healthy indexes
-- ============================================================================

-- 6.1: Check for indexes needing statistics update
-- Shows: Tables where auto-analyze hasn't run recently
SELECT
    schemaname,
    tablename,
    last_analyze,
    last_autoanalyze,
    CASE
        WHEN last_autoanalyze IS NULL THEN 'NEVER_ANALYZED'
        WHEN last_autoanalyze < NOW() - INTERVAL '7 days' THEN 'STALE'
        WHEN last_autoanalyze < NOW() - INTERVAL '1 day' THEN 'OLD'
        ELSE 'FRESH'
    END as analyze_status,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND tablename = 'transactions'
ORDER BY last_autoanalyze ASC NULLS FIRST;

COMMENT ON QUERY IS
'Shows when table statistics were last analyzed.
Action: If STALE or high dead_tuple_pct, run ANALYZE transactions;';


-- 6.2: Manual maintenance commands (run as needed)

-- Update table statistics (run after bulk operations)
-- ANALYZE transactions;

-- Reclaim space from dead tuples (run weekly)
-- VACUUM ANALYZE transactions;

-- Rebuild all indexes (run monthly or when bloated)
-- REINDEX TABLE CONCURRENTLY transactions;


-- ============================================================================
-- PART 7: INDEX VALIDATION
-- ============================================================================
-- Verify that indexes are healthy and valid
-- ============================================================================

-- 7.1: Check for invalid indexes
-- Shows: Indexes that failed to build or became corrupted
-- Action: Drop and recreate invalid indexes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_get_indexdef(indexrelid) as index_definition
FROM pg_stat_user_indexes pui
JOIN pg_index pi ON pui.indexrelid = pi.indexrelid
WHERE schemaname = 'public'
    AND tablename = 'transactions'
    AND NOT pi.indisvalid;

COMMENT ON QUERY IS
'Shows invalid indexes that need to be rebuilt.
Action: DROP INDEX CONCURRENTLY index_name; then recreate.';


-- 7.2: Check for duplicate indexes
-- Shows: Indexes that cover the same columns (redundant)
-- Action: Keep the most efficient one, drop duplicates
SELECT
    a.schemaname,
    a.tablename,
    a.indexname as index1,
    b.indexname as index2,
    pg_get_indexdef(a.indexrelid) as index1_def,
    pg_get_indexdef(b.indexrelid) as index2_def,
    pg_size_pretty(pg_relation_size(a.indexrelid)) as index1_size,
    pg_size_pretty(pg_relation_size(b.indexrelid)) as index2_size
FROM pg_stat_user_indexes a
JOIN pg_stat_user_indexes b
    ON a.schemaname = b.schemaname
    AND a.tablename = b.tablename
    AND a.indexrelid > b.indexrelid  -- Avoid duplicates
WHERE a.schemaname = 'public'
    AND a.tablename = 'transactions'
    AND pg_get_indexdef(a.indexrelid) = pg_get_indexdef(b.indexrelid);

COMMENT ON QUERY IS
'Detects duplicate indexes (same definition).
Action: Keep one, drop the other to save space.';


-- 7.3: Check index size vs table size
-- Shows: Proportion of space used by indexes
-- Interpretation: Indexes larger than table might indicate over-indexing
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    ROUND(100.0 * pg_indexes_size(schemaname||'.'||tablename) /
        NULLIF(pg_total_relation_size(schemaname||'.'||tablename), 0), 2) as index_ratio_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND tablename = 'transactions';

COMMENT ON QUERY IS
'Shows index-to-table size ratio.
Typical: 10-30%. >50% might indicate over-indexing.';


-- ============================================================================
-- PART 8: MONITORING QUERIES FOR REGULAR EXECUTION
-- ============================================================================
-- Run these queries weekly to monitor index health
-- ============================================================================

-- 8.1: Weekly index health report
DO $$
DECLARE
    unused_count INTEGER;
    invalid_count INTEGER;
    bloated_count INTEGER;
BEGIN
    -- Count unused indexes
    SELECT COUNT(*) INTO unused_count
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public'
        AND tablename = 'transactions'
        AND idx_scan = 0;

    -- Count invalid indexes
    SELECT COUNT(*) INTO invalid_count
    FROM pg_stat_user_indexes pui
    JOIN pg_index pi ON pui.indexrelid = pi.indexrelid
    WHERE pui.schemaname = 'public'
        AND pui.tablename = 'transactions'
        AND NOT pi.indisvalid;

    -- Report
    RAISE NOTICE '=== INDEX HEALTH REPORT ===';
    RAISE NOTICE 'Unused indexes: %', unused_count;
    RAISE NOTICE 'Invalid indexes: %', invalid_count;

    IF unused_count > 0 THEN
        RAISE WARNING 'Found % unused indexes - investigate for removal', unused_count;
    END IF;

    IF invalid_count > 0 THEN
        RAISE WARNING 'Found % invalid indexes - rebuild immediately', invalid_count;
    END IF;

    IF unused_count = 0 AND invalid_count = 0 THEN
        RAISE NOTICE 'All indexes healthy ✓';
    END IF;
END $$;


-- ============================================================================
-- PART 9: AUTOMATED INDEX RECOMMENDATIONS
-- ============================================================================
-- Suggestions for new indexes based on query patterns
-- ============================================================================

-- 9.1: Recommend indexes for columns used in WHERE clauses
-- This is a heuristic approach based on common patterns
CREATE OR REPLACE FUNCTION recommend_missing_indexes()
RETURNS TABLE (
    recommendation TEXT,
    reason TEXT,
    priority TEXT,
    estimated_benefit TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'CREATE INDEX CONCURRENTLY idx_transactions_device_id ON transactions(device_id, timestamp DESC);' as recommendation,
        'device_id frequently appears in fraud pattern detection queries' as reason,
        'MEDIUM' as priority,
        'Expected 5-10x speedup for device-based queries' as estimated_benefit
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexdef LIKE '%device_id%'
    )

    UNION ALL

    SELECT
        'CREATE INDEX CONCURRENTLY idx_transactions_card_bin ON transactions(card_bin, timestamp DESC);',
        'card_bin used in BIN-based fraud analysis',
        'LOW',
        'Expected 3-5x speedup for BIN-based queries'
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexdef LIKE '%card_bin%'
    )

    UNION ALL

    SELECT
        'CREATE INDEX CONCURRENTLY idx_transactions_currency ON transactions(currency, amount DESC);',
        'currency filtering with amount sorting in reports',
        'LOW',
        'Expected 2-3x speedup for currency-based reports'
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexdef LIKE '%currency%'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recommend_missing_indexes IS
'Generates index recommendations based on common query patterns.
Run: SELECT * FROM recommend_missing_indexes();';


-- Execute recommendations
-- SELECT * FROM recommend_missing_indexes();


-- ============================================================================
-- DEPLOYMENT CHECKLIST
-- ============================================================================
/*
BEFORE RUNNING IN PRODUCTION:

1. ✓ Enable pg_stat_statements extension
   - Required for query performance monitoring
   - Run: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

2. ✓ Reset statistics to get fresh data
   - Run: SELECT pg_stat_reset();
   - Run: SELECT pg_stat_statements_reset();

3. ✓ Monitor for at least 7 days before making changes
   - Collect index usage data
   - Identify query patterns

4. ✓ Run during low-traffic periods
   - Create indexes with CONCURRENTLY
   - Drop indexes with CONCURRENTLY
   - Rebuild indexes with CONCURRENTLY

5. ✓ Verify query plans after changes
   - Use EXPLAIN ANALYZE before/after
   - Ensure indexes are being used

6. ✓ Set up automated monitoring
   - Weekly: Run index health report
   - Daily: Check for invalid indexes
   - Monthly: Rebuild bloated indexes

7. ✓ Document changes
   - Keep track of added/removed indexes
   - Note performance improvements
   - Update this file with learnings
*/

-- ============================================================================
-- END OF INDEX RECOMMENDATIONS
-- ============================================================================
