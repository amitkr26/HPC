"""Exercise 1: MPI Token Ring Communication.

Circular token-passing ring across all MPI ranks using point-to-point
communication (comm.sendrecv). Rank 0 originates the token, every other rank
increments the hop count, appends its rank to the history and forwards the
token; when the token returns to rank 0 the total hop count and the full path
are printed.

Launch with:  mpirun -n 4 python ex01_mpi_ring.py
"""

from mpi4py import MPI

TOKEN = {"hops": 0, "history": [0]}


def main():
    """Run one full token circulation around the MPI ring."""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 3:
        if rank == 0:
            print(f"ERROR: need at least 3 processes, got {size}.")
            print("Launch with: mpirun -n 4 python ex01_mpi_ring.py")
        MPI.Finalize()
        return

    next_rank = (rank + 1) % size
    prev_rank = (rank - 1 + size) % size

    if rank == 0:
        token = dict(TOKEN)
        token["history"] = list(TOKEN["history"])
        print(f"[Rank 0] originating token: {token}")

        # send the token onward, then receive it back from the last rank
        received = comm.sendrecv(token, dest=next_rank, source=prev_rank)

        received["hops"] += 1
        received["history"].append(0)
        print(f"[Rank 0] token returned: total hops = {received['hops']}")
        print(f"[Rank 0] path traversal history = {received['history']}")
        print(f"[Rank 0] expected hops = {size}, ring is {'OK' if received['hops'] == size else 'BROKEN'}")
    else:
        # blocking wait for the token from the previous rank, then forward it
        token = comm.recv(source=prev_rank)
        token["hops"] += 1
        token["history"].append(rank)
        comm.send(token, dest=next_rank)
        print(f"[Rank {rank}] forwarded token, hops = {token['hops']}")

    comm.Barrier()


if __name__ == "__main__":
    main()
