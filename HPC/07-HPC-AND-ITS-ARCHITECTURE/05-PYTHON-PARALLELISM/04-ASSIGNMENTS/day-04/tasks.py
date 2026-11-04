"""Exercise 4 Step 2: Task definitions for the Order & Invoice pipeline.

Three tasks meant to be chained:
    validate_order -> calculate_tax_and_discount -> generate_invoice_pdf

Worker: celery -A tasks worker --loglevel=info
"""

import time

from celery_config import app


@app.task
def validate_order(order_id, items, total_amount):
    """Validate that items is non-empty and total_amount > 0.

    Returns {"order_id": ..., "status": "VALIDATED", "total": ...} on success
    and a dict with status "REJECTED" plus an "error" key on failure.
    """
    time.sleep(1)
    if not items:
        return {
            "order_id": order_id,
            "status": "REJECTED",
            "total": total_amount,
            "error": "order must contain at least one item",
        }
    try:
        total = float(total_amount)
    except (TypeError, ValueError):
        return {
            "order_id": order_id,
            "status": "REJECTED",
            "total": total_amount,
            "error": "total_amount must be numeric",
        }
    if total <= 0:
        return {
            "order_id": order_id,
            "status": "REJECTED",
            "total": total_amount,
            "error": "total_amount must be greater than zero",
        }
    return {"order_id": order_id, "status": "VALIDATED", "total": total_amount}


@app.task
def calculate_tax_and_discount(order_data, tax_rate=0.18):
    """Take the validate_order output and add tax and the net payable total."""
    total = float(order_data["total"])
    tax = total * tax_rate
    net_payable = total + tax
    updated = dict(order_data)
    updated.update(
        {
            "tax_rate": tax_rate,
            "tax": tax,
            "final_total": net_payable,
        }
    )
    return updated


@app.task
def generate_invoice_pdf(order_data, customer_email):
    """Simulate rendering an invoice PDF and emailing it to the customer."""
    time.sleep(2)
    return (
        f"Invoice #INV-{order_data['order_id']} generated and sent to "
        f"{customer_email}"
    )
