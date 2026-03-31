# middleware/db_middleware.py
# Updated after INC-2026-001 to add connection timeout handling

MAX_RETRIES = 3
CHECKOUT_TIMEOUT = 10


def get_connection(pool, retries=MAX_RETRIES):
    """
    Attempt to check out a DB connection with retry logic.
    Added after INC-2026-001 to prevent silent hangs on pool exhaustion.
    """
    for attempt in range(retries):
        try:
            return pool.checkout(timeout=CHECKOUT_TIMEOUT)
        except PoolTimeoutError:
            if attempt == retries - 1:
                raise
