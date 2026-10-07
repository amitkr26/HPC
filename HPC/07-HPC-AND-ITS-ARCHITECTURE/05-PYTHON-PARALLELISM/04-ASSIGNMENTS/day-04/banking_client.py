"""Exercise 2 Part B: Interactive CLI client for the Pyro4 Banking Service.

Connects to the remote BankAccountService through a Pyro4.Proxy and drives it
from a menu loop.  Handles EOF / Ctrl+C / bad numeric input / dead server
gracefully so it never hangs in a non-interactive shell.

Run:  python banking_server.py          (terminal 1)
      python banking_client.py          (terminal 2, paste the printed URI)
"""

import Pyro4

SERVICE_NAME = "BankService"

MENU = """==================================================
        PYRO4 REMOTE BANKING SERVICE (CLI)
==================================================
1. Check Current Balance
2. Deposit Money
3. Withdraw Money
4. View Transaction Statement
5. Exit Application
--------------------------------------------------
"""


def prompt(message):
    """Read one line of input; return None on EOF / Ctrl+C."""
    try:
        return input(message)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def read_uri():
    """Ask for the service URI, falling back to the Name Server entry."""
    raw = prompt("Enter Bank Service URI (or paste from server): ")
    if raw is None:
        return None
    raw = raw.strip()
    return raw or f"PYRONAME:{SERVICE_NAME}"


def read_amount(message):
    """Parse a positive money amount; return None when the input is invalid."""
    raw = prompt(message)
    if raw is None:
        return None
    try:
        return float(raw.strip())
    except ValueError:
        print("Invalid number - please enter a numeric amount.")
        return False


def show_balance(bank):
    balance = bank.get_balance()
    print(f"Current Balance: ${balance:,.2f}")


def do_deposit(bank):
    amount = read_amount("Enter deposit amount: ")
    if amount is None:
        return False
    if amount is False:
        return True
    result = bank.deposit(amount)
    if isinstance(result, str):
        print(result)
    else:
        print(f"Deposited ${amount:,.2f}. New Balance: ${result:,.2f}")
    return True


def do_withdraw(bank):
    amount = read_amount("Enter withdrawal amount: ")
    if amount is None:
        return False
    if amount is False:
        return True
    result = bank.withdraw(amount)
    if isinstance(result, str):
        print(result)
    else:
        print(f"Withdrew ${amount:,.2f}. New Balance: ${result:,.2f}")
    return True


def show_statement(bank):
    statement = bank.get_statement()
    if not statement:
        print("No transactions yet.")
        return
    print("Transaction Statement:")
    for index, entry in enumerate(statement, start=1):
        print(f"  {index:3}. {entry}")


def run_menu(bank):
    """Menu loop; returns when the user exits or input is exhausted."""
    while True:
        print(MENU, end="")
        choice = prompt("Enter your choice [1-5]: ")
        if choice is None:
            print("Goodbye (input closed).")
            return
        choice = choice.strip()
        if choice == "1":
            show_balance(bank)
        elif choice == "2":
            if not do_deposit(bank):
                return
        elif choice == "3":
            if not do_withdraw(bank):
                return
        elif choice == "4":
            show_statement(bank)
        elif choice == "5":
            print("Thank you for banking with us. Goodbye!")
            return
        else:
            print("Invalid choice - enter a number from 1 to 5.")
        print("-" * 50)


def main():
    uri = read_uri()
    if not uri:
        print("No URI provided. Exiting.")
        return

    try:
        bank = Pyro4.Proxy(uri)
    except Pyro4.errors.PyroError as exc:
        print(f"Could not create a proxy for '{uri}': {exc}")
        return

    print("Connected to the Remote Banking Service.\n")
    try:
        run_menu(bank)
    except (Pyro4.errors.CommunicationError, Pyro4.errors.NamingError) as exc:
        print(f"\nLost contact with the banking server: {exc}")
    finally:
        bank._pyroRelease()


if __name__ == "__main__":
    main()
