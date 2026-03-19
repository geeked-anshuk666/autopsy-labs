MAX_RETRIES = 3
CHECKOUT_TIMEOUT = 10

def get_connection(pool, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            return pool.checkout(timeout=CHECKOUT_TIMEOUT)
        except PoolTimeoutError:
            if attempt == retries - 1:
                raise