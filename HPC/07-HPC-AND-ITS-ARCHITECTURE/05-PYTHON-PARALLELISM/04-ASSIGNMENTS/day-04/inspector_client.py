"""Exercise 3 Part B: Interactive CLI client for the RPyC System Inspector.

Connects to the inspector server with rpyc.connect() and drives it from a
menu loop.  Handles EOF / Ctrl+C / bad input / unreachable server gracefully
so it never hangs in a non-interactive shell.

Run:  python inspector_server.py          (terminal 1)
      python inspector_client.py [host] [port]     (terminal 2)
"""

import sys

import rpyc

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 18861

MENU = """==================================================
     RPYC REMOTE SYSTEM INSPECTOR (CLIENT CLI)
==================================================
1. Inspect Remote Host System Info
2. List Files on Remote Directory
3. Compute Exponential Table on Remote Host
4. Evaluate Math Expression on Remote Host
5. Disconnect & Exit
--------------------------------------------------
"""


def prompt(message):
    """Read one line of input; return None on EOF / Ctrl+C."""
    try:
        return input(message)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def show_system_info(service):
    info = service.get_system_info()
    print("-" * 50)
    print(f"  Remote OS        : {info.get('system')} {info.get('release')}")
    print(f"  Remote Hostname  : {info.get('hostname')}")
    print(f"  Remote CPU Count : {info.get('cpu_count')}")
    print(f"  Remote Time      : {info.get('server_time')}")
    print("-" * 50)


def do_list_files(service):
    raw = prompt("Directory on server [default .]: ")
    if raw is None:
        return False
    path = raw.strip() or "."
    try:
        entries = service.list_files(path)
    except OSError as exc:
        print(f"Server could not list '{path}': {exc}")
        return True
    if not entries:
        print(f"'{path}' is empty.")
        return True
    print(f"{len(entries)} entries in '{path}':")
    for index, name in enumerate(entries, start=1):
        print(f"  {index:3}. {name}")
    return True


def do_compute_powers(service):
    raw_base = prompt("Base (e.g. 2): ")
    if raw_base is None:
        return False
    raw_exp = prompt("Maximum exponent (e.g. 10): ")
    if raw_exp is None:
        return False
    try:
        base = int(raw_base.strip())
        max_exponent = int(raw_exp.strip())
    except ValueError:
        print("Both values must be whole numbers.")
        return True
    try:
        table = service.compute_powers(base, max_exponent)
    except (ValueError, TypeError) as exc:
        print(f"Server rejected the request: {exc}")
        return True
    for exponent in sorted(table):
        print(f"  {base}^{exponent:3} = {table[exponent]}")
    return True


def do_execute_expression(service):
    raw = prompt('Expression (e.g. "2**32 - 1" or "math.sqrt(144)"): ')
    if raw is None:
        return False
    if not raw.strip():
        print("Empty expression - nothing to evaluate.")
        return True
    try:
        result = service.execute_expression(raw)
    except ValueError as exc:
        print(f"Server rejected the expression: {exc}")
        return True
    print(f"  {raw.strip()} = {result}")
    return True


def run_menu(service, conn):
    """Menu loop; returns when the user exits or input is exhausted."""
    while True:
        print(MENU, end="")
        choice = prompt("Enter your choice [1-5]: ")
        if choice is None:
            print("Disconnecting (input closed).")
            return
        choice = choice.strip()
        if choice == "1":
            show_system_info(service)
        elif choice == "2":
            if not do_list_files(service):
                return
        elif choice == "3":
            if not do_compute_powers(service):
                return
        elif choice == "4":
            if not do_execute_expression(service):
                return
        elif choice == "5":
            print("Closing connection. Goodbye!")
            conn.close()
            return
        else:
            print("Invalid choice - enter a number from 1 to 5.")
        print("-" * 50)


def main():
    host = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_HOST
    try:
        port = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_PORT
    except ValueError:
        print(f"Usage: {sys.argv[0]} [host] [port:int]")
        return

    try:
        conn = rpyc.connect(host, port)
    except OSError as exc:
        print(f"Cannot reach the inspector server at {host}:{port} - {exc}")
        print("Start it first with: python inspector_server.py")
        return

    service = conn.root
    print(f"Connected to {host}:{port}.\n")
    try:
        run_menu(service, conn)
    except (EOFError, OSError) as exc:
        print(f"\nConnection to the server was lost: {exc}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
