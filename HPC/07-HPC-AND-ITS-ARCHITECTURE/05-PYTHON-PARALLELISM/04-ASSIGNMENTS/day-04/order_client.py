"""Exercise 4 Step 3: Client driver for the Order & Invoice pipeline.

Part 1 submits three independent validate_order tasks with .delay(), prints
their task UUIDs, polls their status with progress dots and fetches results.
Part 2 builds a three-stage Celery chain and waits for the final invoice.

Prerequisites: a running broker + result backend (e.g. Redis) and a worker:
    docker run -d -p 6379:6379 redis:alpine
    celery -A tasks worker --loglevel=info

Run:  python order_client.py
"""

import time

from celery import chain
from celery.exceptions import TimeoutError as CeleryTimeoutError
from kombu.exceptions import OperationalError

from tasks import calculate_tax_and_discount, generate_invoice_pdf, validate_order

POLL_INTERVAL = 0.5
WAIT_TIMEOUT = 60

INDEPENDENT_ORDERS = [
    ("ORD-101", ["Item A", "Item B"], 250.0),
    ("ORD-102", ["Item C"], 480.5),
    ("ORD-103", ["Item D", "Item E", "Item F"], 99.0),
]


def monitor(async_res, timeout=WAIT_TIMEOUT):
    """Poll async_res.status printing progress dots, then return the result."""
    deadline = time.monotonic() + timeout
    while (
        async_res.status in ("PENDING", "RECEIVED", "STARTED", "RETRY")
        and time.monotonic() < deadline
    ):
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)
    print(f" [{async_res.status}]")
    if async_res.status != "SUCCESS":
        print(f"  task {async_res.id} did not reach SUCCESS.")
        return None
    return async_res.get(timeout=10)


def submit_independent_orders():
    """Submit three order validations asynchronously and collect their results."""
    async_results = []
    for order_id, items, total_amount in INDEPENDENT_ORDERS:
        async_res = validate_order.delay(order_id, items, total_amount)
        print(f"Task Dispatched: {async_res.id}")
        async_results.append((order_id, async_res))

    for order_id, async_res in async_results:
        print(f"Waiting for {order_id} ", end="", flush=True)
        result = monitor(async_res)
        if result is None:
            print(f"{order_id} -> no result")
        else:
            print(f"{order_id} -> {result}")


def run_pipeline():
    """Build and await the validate -> tax -> invoice chain."""
    order_pipeline = chain(
        validate_order.s("ORD-202", ["Laptop", "Mouse"], 1200.0)
        | calculate_tax_and_discount.s(tax_rate=0.18)
        | generate_invoice_pdf.s(customer_email="customer@example.com")
    )
    chain_result = order_pipeline.apply_async()
    print(f"Pipeline submitted (id: {chain_result.id})!")
    print("Waiting for final invoice...")
    final_msg = chain_result.get(timeout=WAIT_TIMEOUT)
    print("Pipeline Output:", final_msg)


def main():
    print("=== Independent task submissions ===")
    submit_independent_orders()
    print()
    print("=== Sequential chained pipeline ===")
    run_pipeline()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted - exiting.")
    except CeleryTimeoutError as exc:
        print(f"\nTimed out waiting for a task result: {exc}")
        print("Is a worker running?  celery -A tasks worker --loglevel=info")
    except (OperationalError, ConnectionError, OSError) as exc:
        print(f"\nCannot reach the broker/result backend: {exc}")
        print("Start Redis (docker run -d -p 6379:6379 redis:alpine) and a worker.")
