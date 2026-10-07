"""Exercise 2 Part A: Pyro4 remote server - Remote Banking & Wallet Service.

Exports a single @Pyro4.expose'd BankAccountService object through a Pyro4
Daemon, prints the generated PYRO:... URI (and registers it with the Pyro
Name Server when one is running), then serves requests forever.

Run:  python banking_server.py          (start `pyro-ns` first for the name
                                          server part; it is optional)
Then: python banking_client.py          (paste the printed URI)
"""

import Pyro4

SERVICE_NAME = "BankService"


@Pyro4.expose
class BankAccountService:
    """Remote bank account: balance, deposits, withdrawals and statement."""

    def __init__(self):
        self.balance = 1000.0
        self.transactions = []  # List of strings describing transactions

    def get_balance(self):
        """Return the current account balance."""
        return self.balance

    def deposit(self, amount):
        """Add a positive amount to the balance.

        Returns the new balance as a float, or an error string when the
        amount is invalid.
        """
        # Validate amount > 0, update balance, record in transaction log
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return "ERROR: Deposit amount must be a number."
        if amount <= 0:
            return f"ERROR: Deposit amount must be positive (got {amount})."
        self.balance += amount
        self.transactions.append(
            f"DEPOSIT  : +${amount:,.2f} -> balance ${self.balance:,.2f}"
        )
        return self.balance

    def withdraw(self, amount):
        """Deduct a positive amount from the balance.

        Returns the new balance as a float, or an error string when the
        amount is invalid or the funds are insufficient.
        """
        # Validate amount > 0 and balance >= amount, deduct, record log
        # Return error string if insufficient funds
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return "ERROR: Withdrawal amount must be a number."
        if amount <= 0:
            return f"ERROR: Withdrawal amount must be positive (got {amount})."
        if amount > self.balance:
            return (
                f"ERROR: Insufficient funds - requested ${amount:,.2f}, "
                f"available ${self.balance:,.2f}"
            )
        self.balance -= amount
        self.transactions.append(
            f"WITHDRAW : -${amount:,.2f} -> balance ${self.balance:,.2f}"
        )
        return self.balance

    def get_statement(self):
        """Return a copy of the transactions list."""
        # Return copy of transactions list
        return list(self.transactions)


def main():
    """Register the service with a Pyro4 Daemon and start the request loop."""
    service = BankAccountService()

    daemon = Pyro4.Daemon(host="localhost")
    uri = daemon.register(service)
    print("BankAccountService registered.")
    print(f"Pyro URI: {uri}")
    print(f"(client may also use: PYRONAME:{SERVICE_NAME})")

    try:
        ns = Pyro4.locateNS()
        ns.register(SERVICE_NAME, uri)
        print(f"Also registered in the Pyro Name Server as '{SERVICE_NAME}'.")
    except (Pyro4.errors.NamingError, Pyro4.errors.CommunicationError):
        print("Pyro Name Server not reachable - use the Pyro URI printed above.")

    print("Starting request loop (Ctrl+C to stop)...")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("\nShutting down the banking server.")
    finally:
        daemon.close()


if __name__ == "__main__":
    main()
