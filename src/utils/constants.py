GAME_STAKE_AMOUNT = 10.0
PLATFORM_FEE_PERCENTAGE = 0.10
GAME_CYCLE_SECONDS = 30

MIN_WITHDRAWAL = 100
MAX_WITHDRAWAL = 50000
MIN_DEPOSIT = 50
MAX_DEPOSIT = 50000

OTP_EXPIRY_MINUTES = 30
OTP_MAX_ATTEMPTS = 5

DAILY_WITHDRAWAL_LIMIT = 3
DAILY_ATTEMPT_LIMIT = 5

SESSION_TIMEOUT_MINUTES = 30

RATE_LIMITS = {
    'default': '200 per day',
    'login': '5 per minute, 200 per hour',
    'play': '10 per minute',
    'withdraw': '3 per hour',
    'deposit': '5 per hour',
    'admin': '50 per hour'
}
