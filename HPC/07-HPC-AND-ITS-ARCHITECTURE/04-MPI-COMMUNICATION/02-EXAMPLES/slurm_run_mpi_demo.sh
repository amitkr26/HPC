#!/bin/bash
#SBATCH --job-name=02_mpi_demo-run
#SBATCH --output=p2p_async.out
#SBATCH --error=p2p_async.err
#SBATCH --partition=cpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1       #Adjust if you have fewer cores per node
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00
#SBATCH --exclusive                  # Get full node
#SBATCH --hint=nomultithread         # Use only physical cores

# Set environment variables to avoid threading conflicts
#export OMP_NUM_THREADS=1
#export OPENBLAS_NUM_THREADS=1
#export SLURM_GPU_BIND=closest

export OMPI_MCA_btl="^openib"


echo "Node: $(hostname)"

module load openmpi-4.1.6

mpic++ 2_p2p_async.cpp -o 2_p2p_async

mpirun ./2_p2p_async


