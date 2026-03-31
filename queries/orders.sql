-- queries/orders.sql
-- Optimized after INC-2026-001 to reduce long-held connections

-- Added index on created_at to reduce full table scans
CREATE INDEX CONCURRENTLY idx_orders_created_at
ON orders(created_at DESC);

-- Optimized query — replaces the previous unindexed version
SELECT * FROM orders
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
