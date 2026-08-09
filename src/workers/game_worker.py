import psycopg2
import threading
import time
import logging
from threading import Event
from src.services.game_service import GameService
from src.services.loan_service import LoanService
from src.shared import get_db_connection, _db_pool
import traceback
import os
import fcntl
import sys
import signal
import tempfile

stop_event = Event()
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'game_worker.lock')

def acquire_lock():
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except (IOError, OSError):
        return None

def release_lock(lock_fd):
    try:
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
            try:
                os.remove(LOCK_FILE)
            except:
                pass
    except Exception as e:
        logging.error(f"Error releasing lock: {e}")

def run_game():
    lock_fd = None
    try:
        lock_fd = acquire_lock()
        if not lock_fd:
            logging.warning("Another game worker is already running. Exiting.")
            return

        logging.info("Game loop started with exclusive lock")
        connection_retry_count = 0
        max_connection_retries = 5
        error_count = 0
        max_errors = 10
        withdrawal_processing_count = 0

        while not stop_event.is_set():
            try:
                current_time = time.time()

                with get_db_connection() as conn:
                    connection_retry_count = 0
                    error_count = 0

                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM results WHERE status IN ('upcoming', 'in progress')")
                    game_count = cursor.fetchone()[0]

                    if game_count == 0:
                        scheduled = GameService.schedule_next_game()
                        if scheduled:
                            logging.info("Game scheduled")
                    else:
                        started = GameService.start_pending_game()
                        if started:
                            logging.info(f"Game started: {started}")

                        processed = GameService.process_active_game()
                        if processed:
                            logging.info(f"Game processed: {processed}")

                # Process withdrawal queue periodically (every 30 seconds)
                withdrawal_processing_count += 1
                if withdrawal_processing_count >= 6:  # Every 30 seconds (6 * 5 seconds)
                    try:
                        result = LoanService.process_withdrawal_queue()
                        if result and result.get('success', False):
                            if result.get('processed', 0) > 0:
                                logging.info(f"Processed {result['processed']} withdrawals from queue")
                    except Exception as e:
                        logging.error(f"Error processing withdrawal queue: {e}")
                    withdrawal_processing_count = 0

                time.sleep(5)

            except psycopg2.OperationalError as e:
                connection_retry_count += 1
                error_count += 1
                logging.error(f"Database operational error in game loop: {e}")
                if connection_retry_count >= max_connection_retries:
                    logging.error(f"Max connection retries ({max_connection_retries}) exceeded. Waiting longer...")
                    time.sleep(30)
                    connection_retry_count = 0
                else:
                    logging.info(f"Retrying connection (attempt {connection_retry_count}/{max_connection_retries})...")
                    time.sleep(10)
            except psycopg2.Error as e:
                error_count += 1
                logging.error(f"Database error in game loop: {e}")
                logging.error(traceback.format_exc())
                time.sleep(10)
            except Exception as e:
                error_count += 1
                logging.error(f"Unexpected error in game loop: {e}")
                logging.error(traceback.format_exc())

                if error_count >= max_errors:
                    logging.error(f"Too many errors ({error_count}). Restarting game loop...")
                    error_count = 0
                    time.sleep(30)
                else:
                    time.sleep(10)

    except Exception as e:
        logging.error(f"Fatal error in game loop: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Game loop exiting, releasing lock...")
        release_lock(lock_fd)
        logging.info("Game loop stopped")

def start_game_loop():
    logging.info("Starting game loop thread...")

    try:
        if os.path.exists(LOCK_FILE):
            try:
                lock_fd = open(LOCK_FILE, 'r')
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
                os.remove(LOCK_FILE)
                logging.info("Removed stale lock file")
            except (IOError, OSError):
                logging.warning("Game worker already running. Not starting another instance.")
                return None
    except Exception as e:
        logging.warning(f"Error checking lock file: {e}")

    game_thread = threading.Thread(target=run_game, daemon=True, name="GameWorker")
    game_thread.start()
    logging.info("Game worker thread started")
    return game_thread

def stop_game_loop():
    logging.info("Stopping game loop...")
    stop_event.set()
    logging.info("Game loop stop signal sent")

def signal_handler(sig, frame):
    logging.info(f"Received signal {sig}, stopping game loop...")
    stop_game_loop()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
