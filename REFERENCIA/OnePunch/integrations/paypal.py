"""
PayPal Integration
Conversational payment processing
"""
import os
from typing import Dict, Optional, Any
import paypalrestsdk


class PayPalIntegration:
    """PayPal integration for conversational payments"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        mode: str = 'sandbox'
    ):
        """
        Initialize PayPal integration
        
        Args:
            client_id: PayPal client ID
            client_secret: PayPal client secret
            mode: 'sandbox' or 'live'
        """
        self.client_id = client_id or os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('PAYPAL_CLIENT_SECRET')
        self.mode = mode or os.getenv('PAYPAL_MODE', 'sandbox')
        
        self._configured = False
    
    def _configure(self):
        """Configure PayPal SDK"""
        if self._configured:
            return
        
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials not configured")
        
        paypalrestsdk.configure({
            'mode': self.mode,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        })
        
        self._configured = True
    
    def create_payment(
        self,
        amount: float,
        currency: str = 'USD',
        description: str = 'Payment',
        return_url: str = 'http://localhost:5000/payment/success',
        cancel_url: str = 'http://localhost:5000/payment/cancel'
    ) -> Dict[str, Any]:
        """
        Create a PayPal payment
        
        Args:
            amount: Payment amount
            currency: Currency code
            description: Payment description
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
        
        Returns:
            Payment details including approval URL
        """
        self._configure()
        
        payment = paypalrestsdk.Payment({
            'intent': 'sale',
            'payer': {
                'payment_method': 'paypal'
            },
            'redirect_urls': {
                'return_url': return_url,
                'cancel_url': cancel_url
            },
            'transactions': [{
                'amount': {
                    'total': str(amount),
                    'currency': currency
                },
                'description': description
            }]
        })
        
        if payment.create():
            # Find approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == 'approval_url':
                    approval_url = link.href
                    break
            
            return {
                'success': True,
                'payment_id': payment.id,
                'approval_url': approval_url,
                'amount': amount,
                'currency': currency,
                'description': description
            }
        else:
            return {
                'success': False,
                'error': payment.error
            }
    
    def execute_payment(
        self,
        payment_id: str,
        payer_id: str
    ) -> Dict[str, Any]:
        """
        Execute an approved payment
        
        Args:
            payment_id: PayPal payment ID
            payer_id: PayPal payer ID from redirect
        
        Returns:
            Execution result
        """
        self._configure()
        
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({'payer_id': payer_id}):
            return {
                'success': True,
                'payment_id': payment.id,
                'state': payment.state,
                'transaction': payment.transactions[0].to_dict() if payment.transactions else None
            }
        else:
            return {
                'success': False,
                'error': payment.error
            }
    
    def create_invoice(
        self,
        merchant_email: str,
        customer_email: str,
        items: list,
        currency: str = 'USD'
    ) -> Dict[str, Any]:
        """
        Create a PayPal invoice
        
        Args:
            merchant_email: Merchant's PayPal email
            customer_email: Customer's email
            items: List of items with name, quantity, price
            currency: Currency code
        
        Returns:
            Invoice details
        """
        self._configure()
        
        # Calculate total
        total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
        
        invoice_items = []
        for item in items:
            invoice_items.append({
                'name': item.get('name', 'Item'),
                'quantity': item.get('quantity', 1),
                'unit_price': {
                    'currency': currency,
                    'value': str(item.get('price', 0))
                }
            })
        
        invoice = paypalrestsdk.Invoice({
            'merchant_info': {
                'email': merchant_email
            },
            'billing_info': [{
                'email': customer_email
            }],
            'items': invoice_items,
            'note': 'Thank you for your business!',
            'payment_term': {
                'term_type': 'DUE_ON_RECEIPT'
            }
        })
        
        if invoice.create():
            return {
                'success': True,
                'invoice_id': invoice.id,
                'total': total,
                'currency': currency,
                'status': invoice.status
            }
        else:
            return {
                'success': False,
                'error': invoice.error
            }
    
    def send_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Send an invoice to the customer
        
        Args:
            invoice_id: PayPal invoice ID
        
        Returns:
            Send result
        """
        self._configure()
        
        invoice = paypalrestsdk.Invoice.find(invoice_id)
        
        if invoice.send():
            return {
                'success': True,
                'invoice_id': invoice_id,
                'message': 'Invoice sent successfully'
            }
        else:
            return {
                'success': False,
                'error': invoice.error
            }
    
    def get_payment_link(
        self,
        amount: float,
        currency: str = 'USD',
        description: str = 'Payment',
        return_url: str = 'http://localhost:5000/payment/success',
        cancel_url: str = 'http://localhost:5000/payment/cancel'
    ) -> str:
        """
        Get a simple payment link for conversational sharing
        
        Args:
            amount: Payment amount
            currency: Currency code
            description: Payment description
            return_url: Success redirect URL
            cancel_url: Cancel redirect URL
        
        Returns:
            Payment approval URL
        """
        result = self.create_payment(
            amount=amount,
            currency=currency,
            description=description,
            return_url=return_url,
            cancel_url=cancel_url
        )
        
        if result['success']:
            return result['approval_url']
        else:
            raise Exception(f"Failed to create payment: {result.get('error')}")
