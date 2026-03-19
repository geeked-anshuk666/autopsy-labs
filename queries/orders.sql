-- Optimized after INC-2026-001
CREATE INDEX CONCURRENTLY idx_orders_created_at
ON orders(created_at DESC);

SELECT * FROM orders
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;