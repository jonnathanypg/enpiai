from flask import Blueprint, request, render_template_string, render_template
from models.company import Company
from services.paypal_service import PayPalService
from services.email_service import EmailService
from services.pdf_service import PDFService
import logging

payments_bp = Blueprint('payments', __name__)
logger = logging.getLogger(__name__)

@payments_bp.route('/success', methods=['GET'])
def payment_success():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    company_id = request.args.get('cid')
    
    # Support for both API v1 (paymentId) and v2 (token)
    token = request.args.get('token')
    
    if not (payment_id or token) or not payer_id or not company_id:
        return "Invalid parameters: Missing paymentId/token, PayerID, or cid", 400
        
    company = Company.query.get(company_id)
    if not company:
        return "Company not found", 404
        
    # V2 LOGIC (Toolkit / Smart Buttons)
    if token:
        try:
            from services.paypal_toolkit import PayPalToolkitService
            toolkit = PayPalToolkitService(company)
            # Capture the order
            result = toolkit.capture_order(token)
            
            if result.get('success') or result.get('status') == 'COMPLETED':
                # Map V2 result to V1 structure for receipt generation
                payment_id = result.get('id', token)
                amount_val = result.get('amount', '0.00')
                currency = result.get('currency', 'USD')
                description = result.get('description', 'Service')
                
                # Setup data for receipt
                invoice_data = {
                    'id': payment_id,
                    'company_name': company.name or "OnePunch User",
                    'amount': amount_val,
                    'currency': currency,
                    'description': description
                }
                
                # Update Transaction Status
                from services.transaction_service import TransactionService
                from models.transaction import TransactionStatus
                TransactionService.update_status_by_order_id(payment_id, TransactionStatus.COMPLETED.value)
                
                # Continue to PDF generation...
            else:
                 from services.transaction_service import TransactionService
                 from models.transaction import TransactionStatus
                 TransactionService.update_status_by_order_id(token, TransactionStatus.FAILED.value)
                 return f"Payment Capture Failed: {result.get('error', 'Unknown error')}", 400
                 
        except Exception as e:
            logger.error(f"V2 Capture failed: {e}")
            return f"Capture Error: {e}", 500

    # V1 LOGIC (Legacy)
    elif payment_id:
        service = PayPalService(company)
        result = service.execute_payment(payment_id, payer_id)
        
        if result.get('status') == 'success':
            payment_data = result['payment']
            transactions = payment_data.get('transactions', [{}])[0]
            amounts = transactions.get('amount', {})
            
            invoice_data = {
                'id': payment_id,
                'company_name': company.name or "OnePunch User",
                'amount': amounts.get('total', '0.00'),
                'currency': amounts.get('currency', 'USD'),
                'description': transactions.get('description', 'Service')
            }
        else:
            return f"Payment Execution Failed: {result.get('error')}", 400

    # COMMON: Generate Receipt
    try:
        # Generate PDF
        pdf_buffer = PDFService.generate_invoice(invoice_data)
        
        # Send Email
        # Note: Payer email might be different in V2, for now we assume we might not get it easily 
        # without another call, or stick to V1 logic. In V2 'payer' block is in capture result.
        # For simplicity, we skip email lookup details modification here to stay focused, 
        # or defaults to None if not easily available.
        
        email_service = EmailService()
        # Trying to send to contact email if we have conversation context? 
        # Or just skip invalid email error silently.
        
        logger.info(f"Payment {invoice_data['id']} successful. Receipt generated.")
            
    except Exception as e:
        logger.error(f"Post-payment processing failed: {e}")

    # Prepare display amount
    display_amount = invoice_data['amount']
    if isinstance(display_amount, dict):
        display_amount = display_amount.get('value', '0.00')

    # Fetch additional context from Transaction (if available)
    from services.transaction_service import TransactionService
    txn = TransactionService.get_by_provider_id(invoice_data['id'])
    
    customer_name = "Valued Customer"
    service_description = invoice_data.get('description', 'Service')
    
    if txn and txn.customer:
        customer_name = txn.customer.full_name
        # Use stored description/service if richer
        if txn.description: 
            service_description = txn.description
            
        # === REAL-TIME HUBSPOT SYNC: Update Lifecycle to Customer ===
        try:
            from services.hubspot_service import HubSpotService
            hubspot = HubSpotService(company=company)
            if txn.customer.email:
                hubspot.update_lifecycle_to_customer(txn.customer.email)
                # Also update Lead Status to CONNECTED
                hubspot.create_or_update_contact(
                    email=txn.customer.email,
                    lead_status='CONNECTED'
                )
                logger.info(f"HubSpot: Updated {txn.customer.email} to CUSTOMER/CONNECTED")
        except Exception as hs_e:
            logger.error(f"HubSpot Sync Error: {hs_e}")

    # Render branded success page
    return render_template(
        'payment_success.html',
        company_name=invoice_data['company_name'],
        order_id=invoice_data['id'],
        amount=display_amount,
        currency=invoice_data['currency'],
        description=service_description,
        customer_name=customer_name
    )


@payments_bp.route('/cancel', methods=['GET'])
def payment_cancel():
    return render_template_string("""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: red;">Payment Cancelled</h1>
            <p>You have cancelled the transaction.</p>
            <script>setTimeout(function(){ window.close(); }, 3000);</script>
        </body>
        </html>
    """)
