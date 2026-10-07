"""Exercise 7 - Race Condition Detector.

Part A observes a lost-update race on a shared bank account, Part B
fixes it with a threading.Lock, and Part C runs both versions ten times
and counts how often each produces the correct result.
"""

import threading
import time

STARTING_BALANCE = 1000
NUM_THREADS = 5
WITHDRAWALS_PER_THREAD = 100
WITHDRAW_AMOUNT = 1
EXPECTED_BALANCE = STARTING_BALANCE - NUM_THREADS * WITHDRAWALS_PER_THREAD * WITHDRAW_AMOUNT


def withdraw(account, amount, num_times, lock=None):
    """Perform ``num_times`` withdrawals, optionally protected by ``lock``."""
    for _ in range(num_times):
        if lock is None:
            if account["balance"] >= amount:
                current = account["balance"]
                time.sleep(0.0001)
                account["balance"] = current - amount
        else:
            with lock:
                if account["balance"] >= amount:
                    current = account["balance"]
                    time.sleep(0.0001)
                    account["balance"] = current - amount


def run_once(use_lock):
    """Run one 5-thread x 100-withdrawal experiment and return the balance."""
    account = {"balance": STARTING_BALANCE}
    lock = threading.Lock() if use_lock else None
    threads = [threading.Thread(target=withdraw,
                                args=(account, WITHDRAW_AMOUNT,
                                      WITHDRAWALS_PER_THREAD, lock))
               for _ in range(NUM_THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return account["balance"]


def run_experiment(use_lock, runs=10):
    """Repeat the experiment ``runs`` times and count correct balances."""
    balances = [run_once(use_lock) for _ in range(runs)]
    correct = sum(1 for balance in balances if balance == EXPECTED_BALANCE)
    return correct, balances


def main():
    """Demonstrate the race, the lock-based fix, and the 10-run tally."""
    print("=== Part A: unsafe withdrawal (race condition) ===")
    unsafe_final = run_once(use_lock=False)
    print(f"  Expected balance : ${EXPECTED_BALANCE}")
    print(f"  Actual balance   : ${unsafe_final}")
    print(f"  Correct          : {unsafe_final == EXPECTED_BALANCE}")
    if unsafe_final != EXPECTED_BALANCE:
        print(f"  Lost updates!    : ${unsafe_final - EXPECTED_BALANCE} "
              f"never deducted")

    print("\n=== Part B: withdrawal protected by threading.Lock ===")
    safe_final = run_once(use_lock=True)
    print(f"  Expected balance : ${EXPECTED_BALANCE}")
    print(f"  Actual balance   : ${safe_final}")
    print(f"  Correct          : {safe_final == EXPECTED_BALANCE}")

    print("\n=== Part C: 10 runs of each version ===")
    unsafe_correct, unsafe_balances = run_experiment(use_lock=False, runs=10)
    safe_correct, safe_balances = run_experiment(use_lock=True, runs=10)

    print(f"  Unsafe version: correct in {unsafe_correct}/10 runs "
          f"(balances: {unsafe_balances})")
    print(f"  Safe version  : correct in {safe_correct}/10 runs "
          f"(balances: {safe_balances})")
    print("\n  The unsafe version fails frequently; the locked version "
          "always succeeds.")


if __name__ == "__main__":
    main()
