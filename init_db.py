import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shared import get_db_connection
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)

def init_database():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # ============================================================
            # EXISTING TABLES (Keep all original creation code)
            # ============================================================
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    wallet NUMERIC DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Users table created/verified")

            # Create admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Admins table created/verified")

            # Create results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id SERIAL PRIMARY KEY,
                    game_code TEXT UNIQUE,
                    timestamp TIMESTAMP,
                    num_users INTEGER,
                    total_amount NUMERIC,
                    deduction NUMERIC,
                    winner TEXT,
                    winner_amount NUMERIC,
                    outcome_message TEXT,
                    status TEXT DEFAULT 'upcoming'
                )
            """)
            print("✅ Results table created/verified")

            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount NUMERIC NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    game_code TEXT
                )
            """)
            print("✅ Transactions table created/verified")

            # Create game_queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_queue (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Game queue table created/verified")

            # Create allowed_users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS allowed_users (
                    username TEXT PRIMARY KEY
                )
            """)
            print("✅ Allowed users table created/verified")

            # Create withdrawal_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    requested_amount NUMERIC NOT NULL,
                    withdrawal_fee NUMERIC NOT NULL,
                    net_amount NUMERIC NOT NULL,
                    status TEXT DEFAULT 'pending',
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_time TIMESTAMP NULL,
                    processed_by INTEGER NULL,
                    admin_notes TEXT,
                    receipt_code TEXT UNIQUE
                )
            """)
            print("✅ Withdrawal requests table created/verified")

            # Create deposit_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deposit_requests (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    amount NUMERIC NOT NULL,
                    voucher_code TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_time TIMESTAMP NULL,
                    processed_by INTEGER NULL,
                    admin_notes TEXT
                )
            """)
            print("✅ Deposit requests table created/verified")

            # Create user_suspensions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_suspensions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    suspension_end TIMESTAMP NOT NULL,
                    suspended_by INTEGER,
                    suspended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ User suspensions table created/verified")

            # Create withdrawal_limits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_limits (
                    user_id INTEGER PRIMARY KEY,
                    last_withdrawal_time TIMESTAMP NULL,
                    daily_attempts INTEGER DEFAULT 0,
                    last_attempt_time TIMESTAMP NULL
                )
            """)
            print("✅ Withdrawal limits table created/verified")

            # Create withdrawal_fees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_fees (
                    id SERIAL PRIMARY KEY,
                    min_amount NUMERIC NOT NULL,
                    max_amount NUMERIC NOT NULL,
                    fee_amount NUMERIC DEFAULT 0,
                    fee_percentage NUMERIC DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            print("✅ Withdrawal fees table created/verified")

            # Create win_earnings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS win_earnings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    game_code TEXT NOT NULL,
                    amount NUMERIC NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_withdrawn BOOLEAN DEFAULT FALSE,
                    withdrawn_at TIMESTAMP NULL
                )
            """)
            print("✅ Win earnings table created/verified")

            # Create user_activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    username TEXT,
                    ip_address TEXT,
                    path TEXT,
                    method TEXT,
                    user_agent TEXT,
                    referrer TEXT
                )
            """)
            print("✅ User activity table created/verified")

            # Create visit_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visit_logs (
                    id SERIAL PRIMARY KEY,
                    ip_address TEXT,
                    user_agent TEXT,
                    referrer TEXT,
                    path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Visit logs table created/verified")

            # Create platform_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS platform_stats (
                    id SERIAL PRIMARY KEY,
                    stat_key TEXT UNIQUE NOT NULL,
                    stat_value NUMERIC DEFAULT 0.0,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Platform stats table created/verified")

            # ============================================================
            # NEW LOAN SYSTEM TABLES (Added)
            # ============================================================
            
            print("\n📊 Creating loan system tables...")

            # 1. User Loans Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_loans (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    loan_amount NUMERIC(10,2) NOT NULL DEFAULT 200.00,
                    repaid_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    remaining_balance NUMERIC(10,2) NOT NULL DEFAULT 200.00,
                    is_fully_repaid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ User loans table created")

            # 2. Withdrawal Queue Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdrawal_queue (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount NUMERIC(10,2) NOT NULL,
                    queue_position INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    estimated_payment_date TIMESTAMP
                )
            """)
            print("✅ Withdrawal queue table created")

            # 3. Loan Repayment History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS loan_repayments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    game_code VARCHAR(20),
                    amount NUMERIC(10,2) NOT NULL,
                    repayment_type VARCHAR(20) DEFAULT 'automatic',
                    win_earnings_before NUMERIC(10,2),
                    win_earnings_after NUMERIC(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Loan repayments table created")

            # 4. House Account Tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS house_account (
                    id SERIAL PRIMARY KEY,
                    total_balance NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    available_balance NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    pending_withdrawals NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    total_deposits NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    total_fees NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    total_loan_repayments NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ House account table created")

            # 5. Real Money Deposits Tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS real_money_deposits (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount NUMERIC(10,2) NOT NULL,
                    is_used_for_withdrawal BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Real money deposits table created")

            # ============================================================
            # INDEXES (Existing + New)
            # ============================================================
            
            print("\n📊 Creating indexes...")

            # Existing indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_queue_user_id ON game_queue(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_game_code ON transactions(game_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_status ON results(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_timestamp ON results(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_game_code ON results(game_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_user_id ON withdrawal_requests(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_status ON withdrawal_requests(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_timestamp ON withdrawal_requests(request_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deposit_requests_user_id ON deposit_requests(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deposit_requests_status ON deposit_requests(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deposit_requests_timestamp ON deposit_requests(request_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deposit_requests_voucher_code ON deposit_requests(voucher_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_suspensions_user_id ON user_suspensions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_suspensions_end ON user_suspensions(suspension_end)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_win_earnings_user_id ON win_earnings(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_win_earnings_game_code ON win_earnings(game_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_win_earnings_withdrawn ON win_earnings(is_withdrawn)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_username ON user_activity(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visit_logs_timestamp ON visit_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visit_logs_ip ON visit_logs(ip_address)")

            # New loan system indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_loans_user_id ON user_loans(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_loans_fully_repaid ON user_loans(is_fully_repaid)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_user_id ON withdrawal_queue(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_status ON withdrawal_queue(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_position ON withdrawal_queue(queue_position)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_loan_repayments_user_id ON loan_repayments(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_real_money_deposits_user_id ON real_money_deposits(user_id)")

            print("✅ All indexes created successfully")

            # ============================================================
            # INITIAL DATA (Existing + New)
            # ============================================================

            # Insert default withdrawal fees
            cursor.execute("SELECT COUNT(*) FROM withdrawal_fees")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO withdrawal_fees (min_amount, max_amount, fee_amount, fee_percentage, is_active)
                    VALUES
                    (100, 1000, 10, 0, TRUE),
                    (1001, 5000, 25, 0, TRUE),
                    (5001, 20000, 50, 0, TRUE),
                    (20001, 50000, 100, 0, TRUE)
                """)
                print("✅ Default withdrawal fees inserted")

            # Insert initial house account
            cursor.execute("SELECT COUNT(*) FROM house_account")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO house_account (total_balance, available_balance, pending_withdrawals)
                    VALUES (0.00, 0.00, 0.00)
                """)
                print("✅ Initial house account created")

            # Create admin user from .env
            admin_username = os.getenv('CASH_USERNAME')
            admin_password = os.getenv('CASH_PASSWORD')

            if not admin_username or not admin_password:
                print("\n❌ ERROR: Admin credentials not found in .env file!")
                print("   CASH_USERNAME and CASH_PASSWORD must be set in .env")
                print("\n   Please set these variables in your .env file:")
                print("   CASH_USERNAME=your_admin_username")
                print("   CASH_PASSWORD=your_secure_password")
                print("\n   Then run: python init_db.py")
                raise ValueError("CASH_USERNAME and CASH_PASSWORD must be set in .env")

            cursor.execute("SELECT id, username, hashed_password, role FROM admins WHERE username = %s", (admin_username,))
            existing_admin = cursor.fetchone()

            if existing_admin:
                print(f"✅ Admin user '{admin_username}' already exists (ID: {existing_admin[0]})")
            else:
                hashed = generate_password_hash(admin_password)
                cursor.execute(
                    "INSERT INTO admins (username, hashed_password, role) VALUES (%s, %s, 'admin')",
                    (admin_username, hashed)
                )
                print(f"✅ Admin user '{admin_username}' created from .env configuration")

            conn.commit()
            print("\n🎉 Database initialization completed successfully!")
            print("   ✅ All existing tables verified")
            print("   ✅ New loan tables created")
            print("   ✅ All indexes created")
            print("   ✅ Default data inserted")
            print("   ✅ Admin user configured")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    init_database()
