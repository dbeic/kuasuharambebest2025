import os
import logging
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from datetime import datetime
from dotenv import load_dotenv
import time
import threading

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CASH_DATABASE = os.getenv('CASH_DATABASE')
if not CASH_DATABASE:
    CASH_DATABASE = os.getenv('DATABASE_URL')
    if CASH_DATABASE:
        logging.info("Using DATABASE_URL environment variable")
    else:
        raise ValueError("Neither CASH_DATABASE nor DATABASE_URL environment variable is set")

def ensure_ssl(dsn):
    if 'postgresql' in dsn and 'sslmode' not in dsn:
        if '?' in dsn:
            return dsn + '&sslmode=require'
        else:
            return dsn + '?sslmode=require'
    return dsn

CASH_DATABASE = ensure_ssl(CASH_DATABASE)

_db_pool = None
_pool_lock = threading.Lock()
_pool_initialized = False
max_retries = 3

def create_pool():
    """Create a new connection pool. Thread-safe."""
    global _db_pool, _pool_initialized
    
    with _pool_lock:
        # Close existing pool if it exists
        if _db_pool is not None:
            try:
                _db_pool.closeall()
            except Exception as e:
                logging.warning(f"Error closing existing pool: {e}")
            _db_pool = None
        
        try:
            new_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=CASH_DATABASE,
                keepalives=1,
                keepalives_idle=5,
                keepalives_interval=2,
                keepalives_count=2,
                connect_timeout=10
            )
            # Validate the pool by getting a test connection
            test_conn = new_pool.getconn()
            cursor = test_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            new_pool.putconn(test_conn)
            
            _db_pool = new_pool
            _pool_initialized = True
            logging.info("Database connection pool created successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to create connection pool: {e}")
            _db_pool = None
            _pool_initialized = False
            return False

def ensure_pool_initialized():
    """Ensure the pool is initialized. Thread-safe."""
    global _pool_initialized
    
    if _pool_initialized and _db_pool is not None:
        return True
    
    with _pool_lock:
        # Double-check after acquiring lock
        if _pool_initialized and _db_pool is not None:
            return True
        
        for attempt in range(max_retries):
            if create_pool():
                return True
            logging.warning(f"Pool initialization attempt {attempt + 1} failed, retrying...")
            time.sleep(2)
        
        return False

# Initial pool creation (synchronous, at module import time)
for attempt in range(max_retries):
    if create_pool():
        break
    logging.warning(f"Initial pool creation attempt {attempt + 1} failed, retrying...")
    time.sleep(2)

if _db_pool is None:
    raise RuntimeError("Failed to create database connection pool after multiple attempts")

@contextmanager
def get_db_connection():
    """Get a database connection from the pool. Thread-safe with automatic recovery."""
    global _db_pool
    
    conn = None
    fallback_used = False
    
    try:
        # Ensure pool is initialized
        if not ensure_pool_initialized():
            logging.warning("Pool not available, using direct connection")
            conn = psycopg2.connect(CASH_DATABASE)
            fallback_used = True
            yield conn
            return
        
        # Get connection from pool with retry for connection errors
        max_connection_retries = 3
        pool_conn = None
        
        for attempt in range(max_connection_retries):
            try:
                pool_conn = _db_pool.getconn()
                # Validate connection
                cursor = pool_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn = pool_conn
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if pool_conn:
                    try:
                        _db_pool.putconn(pool_conn)
                    except:
                        pass
                    pool_conn = None
                if attempt < max_connection_retries - 1:
                    time.sleep(1)
                else:
                    # All retries failed, try to recreate the pool
                    logging.info("All connection retries failed, attempting pool recreation...")
                    with _pool_lock:
                        if create_pool():
                            # Try one more time with the new pool
                            try:
                                pool_conn = _db_pool.getconn()
                                cursor = pool_conn.cursor()
                                cursor.execute("SELECT 1")
                                cursor.close()
                                conn = pool_conn
                                break
                            except Exception as e2:
                                logging.error(f"Pool recreation succeeded but connection failed: {e2}")
                                # Fall through to fallback connection
        
        if conn is None:
            # Fallback: direct connection
            logging.warning("Using fallback direct connection")
            conn = psycopg2.connect(CASH_DATABASE)
            fallback_used = True
            yield conn
            return
        
        yield conn
        
    except Exception as e:
        logging.error(f"Error getting database connection: {e}")
        # Try fallback direct connection one more time
        try:
            if conn is not None:
                # Try to close the failed connection
                try:
                    conn.close()
                except:
                    pass
            conn = psycopg2.connect(CASH_DATABASE)
            fallback_used = True
            yield conn
            return
        except Exception as e2:
            logging.error(f"Fallback connection also failed: {e2}")
            raise
    finally:
        if conn is not None:
            try:
                if not fallback_used and _db_pool is not None:
                    try:
                        _db_pool.putconn(conn)
                    except Exception as e:
                        logging.warning(f"Error returning connection to pool: {e}")
                        try:
                            conn.close()
                        except:
                            pass
                else:
                    # Close direct connections
                    try:
                        conn.close()
                    except:
                        pass
            except Exception as e:
                logging.warning(f"Error in connection cleanup: {e}")

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def notify_clients(event_type, data):
    logging.info(f"Game Event: {event_type} - {data}")
