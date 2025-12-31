# Legacy wrapper - redirects to new service layer
from core.services.sales_service import process_retail_sale as _process_retail_sale

def process_retail_sale(customer, items, payment_amount):
    """
    Legacy wrapper for process_retail_sale.
    Maintains backward compatibility with old signature.
    """
    return _process_retail_sale(
        customer_identifier=customer,
        items=items,
        payment_amount=payment_amount,
        payment_method="manual",
        payment_reference=None
    )