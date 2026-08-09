from src.repositories.deposit_repository import DepositRepository
from src.services.wallet_service import WalletService
from src.repositories.transaction_repository import TransactionRepository
from datetime import datetime
import logging
from decimal import Decimal

class DepositService:
    MIN_DEPOSIT = 50
    MAX_DEPOSIT = 50000
    
    @staticmethod
    def create_deposit_request(user_id, username, amount):
        if amount < DepositService.MIN_DEPOSIT:
            return {'success': False, 'error': f'Minimum deposit amount is KES {DepositService.MIN_DEPOSIT}'}
        
        if amount > DepositService.MAX_DEPOSIT:
            return {'success': False, 'error': f'Maximum deposit amount is KES {DepositService.MAX_DEPOSIT}'}
        
        voucher_code = f"DPT{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"
        
        success = DepositRepository.create_request(user_id, username, float(amount), voucher_code)
        
        if success:
            return {'success': True, 'voucher_code': voucher_code}
        
        return {'success': False, 'error': 'Failed to create deposit request'}
    
    @staticmethod
    def approve_deposit(request_id, admin_id, admin_notes=None):
        request = DepositRepository.get_request_by_id(request_id)
        if not request or request.status != 'pending':
            return {'success': False, 'error': 'Deposit not found or already processed'}
        
        # Deposit adds to wallet but NOT to win_earnings
        wallet_result = WalletService.deposit(request.user_id, float(request.amount), admin_id)
        if not wallet_result['success']:
            return {'success': False, 'error': wallet_result['error']}
        
        success = DepositRepository.update_request_status(request_id, 'completed', admin_id, admin_notes)
        
        if success:
            return {'success': True}
        
        return {'success': False, 'error': 'Failed to approve deposit'}
    
    @staticmethod
    def reject_deposit(request_id, admin_id, admin_notes=None):
        request = DepositRepository.get_request_by_id(request_id)
        if not request or request.status != 'pending':
            return {'success': False, 'error': 'Deposit not found or already processed'}
        
        success = DepositRepository.update_request_status(request_id, 'rejected', admin_id, admin_notes)
        return {'success': success}
    
    @staticmethod
    def get_pending_count():
        return len(DepositRepository.get_pending_requests())
    
    @staticmethod
    def get_request_by_voucher(voucher_code):
        return DepositRepository.get_request_by_voucher_code(voucher_code)
