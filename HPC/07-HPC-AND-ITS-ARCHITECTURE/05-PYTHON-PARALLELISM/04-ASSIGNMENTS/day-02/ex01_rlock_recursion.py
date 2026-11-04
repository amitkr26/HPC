"""Exercise 1: Reentrant Locks (RLock) & Nested Resource Access.

Demonstrates that a plain threading.Lock deadlocks when a method recursively
calls itself while holding the lock, whereas threading.RLock allows the same
thread to re-acquire the lock at every recursion level.
"""

import threading

HIERARCHY = {
    "src": {
        "main.py": 120,
        "utils.py": 80,
        "tests": {
            "test_main.py": 60,
            "test_utils.py": 45,
        },
    },
    "docs": {
        "readme.md": 30,
        "guide": {
            "intro.md": 25,
            "advanced.md": 55,
        },
    },
}


def count_files(node):
    """Return the number of files contained in a (nested dict) folder."""
    total = 0
    for value in node.values():
        if isinstance(value, dict):
            total += count_files(value)
        else:
            total += 1
    return total


class FolderScanner:
    """Walks a simulated directory tree while guarding a shared counter."""

    def __init__(self, lock):
        self.lock = lock
        self.files_scanned = 0

    def scan_directory(self, folder):
        """Recursively scan *folder*, incrementing the protected counter.

        The lock is taken for the whole method body, so the recursive call
        for sub-folders tries to acquire the very same lock again.
        """
        with self.lock:
            for name, value in folder.items():
                if isinstance(value, dict):
                    print(f"  entering sub-folder: {name}")
                    self.scan_directory(value)
                else:
                    self.files_scanned += 1
                    print(f"  scanned file: {name} ({value} bytes) -> "
                          f"files_scanned={self.files_scanned}")


def demonstrate_lock_deadlock(hierarchy, timeout=2.0):
    """Show that a standard Lock deadlocks on the nested acquisition."""
    print("=" * 70)
    print("PART A: threading.Lock (non-reentrant)")
    print("=" * 70)
    scanner = FolderScanner(threading.Lock())
    worker = threading.Thread(
        target=scanner.scan_directory,
        args=(hierarchy,),
        name="scanner-with-Lock",
        daemon=True,
    )
    worker.start()
    worker.join(timeout)

    if worker.is_alive():
        print(f"[DEADLOCK] Thread still blocked after {timeout}s: the nested "
              f"call tried to acquire the already-held Lock.")
        print("[DEADLOCK] Daemon thread is abandoned so the script can exit.")
    else:
        print("Thread finished without deadlocking (unexpected).")
    return worker.is_alive()


def demonstrate_rlock(hierarchy, expected):
    """Show that an RLock lets the same thread re-acquire while recursing."""
    print()
    print("=" * 70)
    print("PART B: threading.RLock (re-entrant)")
    print("=" * 70)
    scanner = FolderScanner(threading.RLock())
    worker = threading.Thread(
        target=scanner.scan_directory,
        args=(hierarchy,),
        name="scanner-with-RLock",
        daemon=True,
    )
    worker.start()
    worker.join(10.0)

    assert not worker.is_alive(), "RLock scan hung - re-entrancy failed!"
    print(f"[RLock] Scan completed, files_scanned={scanner.files_scanned}")
    assert scanner.files_scanned == expected, (
        f"Expected {expected} files but counted {scanner.files_scanned}"
    )
    print(f"[RLock] ASSERT OK: scanned {scanner.files_scanned} files, "
          f"matches expected total {expected}.")
    return scanner.files_scanned


def main():
    expected = count_files(HIERARCHY)
    print(f"Directory hierarchy contains {expected} files.\n")

    deadlocked = demonstrate_lock_deadlock(HIERARCHY)
    scanned = demonstrate_rlock(HIERARCHY, expected)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"threading.Lock  -> deadlock observed : {deadlocked}")
    print(f"threading.RLock -> scan finished     : True "
          f"({scanned} files, no deadlock)")
    print("Rule: use Lock by default; use RLock only when methods of the "
          "same class re-acquire a lock they already hold.")


if __name__ == "__main__":
    main()
