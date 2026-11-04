# Environment Audit — PARAM Rudra (CDAC Delhi)

**Project:** BDW — from-scratch decoder-only LLM
**Stage:** A (environment audit only — no installs, no downloads, no training jobs)
**Executed:** 2026-10-16 10:26:46 India Standard Time
**Account:** `3ioip3lt` / SLURM account `tutor` / QOS `training`
**Connection:** `paramrudra.cdacdelhi.in:4422` (keyboard-interactive)

Every block below is literal captured output from a single SSH session.
No credentials, tokens, keys or secrets are reproduced in this document.

---

## 1. Session identity

`hostname; whoami; id; pwd; date; uptime; umask; ulimit; tool probe`

```text




hostname      : login02
whoami        : 3ioip3lt
id            : uid=56027(3ioip3lt) gid=56027(3ioip3lt) groups=56027(3ioip3lt)
pwd           : /home/tutor/3ioip3lt
HOME          : /home/tutor/3ioip3lt
shell         : /bin/bash
date          : 2026-10-13T11:56:55+05:30
uptime        : up 33 weeks, 5 days, 9 minutes
umask         : 0002
ulimit -n     : 1024
ulimit -u     : 765846
ulimit -v     : unlimited
--- login banner / motd (tail) ---
-rw-r--r-- 1 root root 3612 Feb 10  2025 /etc/motd
#################################################################################################
#        Important:- Request all users to take regular backup of their own data.                #
#################################################################################################
#                    Note : Please donot run jobs on login node                                 #
#################################################################################################
```

---

## 2. Storage, filesystems, writability, quotas

`df -hT`, writability probe, quota tools, `du -sh $HOME`, candidate mounts

```text




=== df -hT (real filesystems) ===
Filesystem                      Type      Size  Used Avail Use% Mounted on
/dev/mapper/almalinux-root      xfs       884G   41G  844G   5% /
/dev/nvme0n1p2                  xfs        10G  312M  9.7G   4% /boot
/dev/nvme0n1p1                  vfat       50M  5.8M   45M  12% /boot/efi
/dev/mapper/almalinux-var       xfs       500G  6.2G  494G   2% /var
172.11.0.9:/beegfs_pool/scratch nfs4      125T  4.2T  120T   4% /scratch
172.11.0.2:/home                nfs4       25T   23T  1.6T  94% /home

=== findmnt (avail) ===
/                                     xfs               884G 843.8G
|-/sys                                sysfs                0      0
| |-/sys/kernel/security              securityfs           0      0
| |-/sys/fs/cgroup                    tmpfs            93.5G  93.5G
| | |-/sys/fs/cgroup/systemd          cgroup               0      0
| | |-/sys/fs/cgroup/perf_event       cgroup               0      0
| | |-/sys/fs/cgroup/devices          cgroup               0      0
| | |-/sys/fs/cgroup/rdma             cgroup               0      0
| | |-/sys/fs/cgroup/net_cls,net_prio cgroup               0      0
| | |-/sys/fs/cgroup/cpu,cpuacct      cgroup               0      0
| | |-/sys/fs/cgroup/memory           cgroup               0      0
| | |-/sys/fs/cgroup/hugetlb          cgroup               0      0
| | |-/sys/fs/cgroup/freezer          cgroup               0      0
| | |-/sys/fs/cgroup/blkio            cgroup               0      0
| | |-/sys/fs/cgroup/cpuset           cgroup               0      0
| | `-/sys/fs/cgroup/pids             cgroup               0      0
| |-/sys/fs/pstore                    pstore               0      0
| |-/sys/firmware/efi/efivars         efivarfs             0      0
| |-/sys/fs/bpf                       bpf                  0      0
| |-/sys/kernel/tracing               tracefs              0      0
| |-/sys/kernel/debug                 debugfs              0      0
| | `-/sys/kernel/debug/tracing       tracefs                      
| |-/sys/fs/fuse/connections          fusectl              0      0
| `-/sys/kernel/config                configfs             0      0
|-/proc                               proc                 0      0
| |-/proc/sys/fs/binfmt_misc          autofs               0      0
| | `-/proc/sys/fs/binfmt_misc        binfmt_misc          0      0
| `-/proc/fs/nfsd                     nfsd                 0      0
|-/dev                                devtmpfs         93.5G  93.5G
| |-/dev/mqueue                       mqueue               0      0

=== home quota tools ===
bash: lfs: command not found
bash: reportquota: command not found

=== du -sh $HOME (this may take a moment) ===
1.3G	/home/tutor/3ioip3lt

=== /scratch ===
drwx--x--x 3 root root 3 Mar  4  2026 /scratch
SCRATCH: NOT WRITABLE

=== other candidate mounts ===
ls: cannot access '/data': No such file or directory
ls: cannot access '/datasets': No such file or directory
ls: cannot access '/projects': No such file or directory
ls: cannot access '/project': No such file or directory
ls: cannot access '/work': No such file or directory
ls: cannot access '/app': No such file or directory
ls: cannot access '/opt/data': No such file or directory
drwxr-xr-x. 2 root root 6 Oct  9  2021 /mnt
drwx--x--x  3 root root 3 Mar  4  2026 /scratch
[exit code 2]
```

---

## 3. Python and software environment

`which`, versions, `venv`/`ensurepip`, import probe, `pip index`, module system
(`module spider`, `module show` — metadata only, nothing loaded)

```text




=== which ===
/usr/bin/which: no conda in (/home/tutor/3ioip3lt/hpc/venv/bin:/home/apps/openmpi-4.1.5/bin:/home/apps/gcc-12.3/bin:/home/tutor/3ioip3lt/.local/bin:/home/tutor/3ioip3lt/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin)
/usr/bin/which: no mamba in (/home/tutor/3ioip3lt/hpc/venv/bin:/home/apps/openmpi-4.1.5/bin:/home/apps/gcc-12.3/bin:/home/tutor/3ioip3lt/.local/bin:/home/tutor/3ioip3lt/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin)
/home/tutor/3ioip3lt/hpc/venv/bin/python
/home/tutor/3ioip3lt/hpc/venv/bin/python3
/home/tutor/3ioip3lt/hpc/venv/bin/pip
/home/tutor/3ioip3lt/hpc/venv/bin/pip3

=== versions ===
Python 3.11.4
Python 3.11.4
pip 26.2.1 from /home/tutor/3ioip3lt/hpc/venv/lib/python3.11/site-packages/pip (python 3.11)

=== sys ===
executable: /home/tutor/3ioip3lt/hpc/venv/bin/python
version: 3.11.4 (main, Jul  5 2023, 13:45:01) [GCC 11.2.0]
prefix: /home/tutor/3ioip3lt/hpc/venv
platform: linux-x86_64

=== venv capability ===
venv: OK
ensurepip: OK

=== pip config / index ===
WARNING: This command is only meant for debugging. Do not use this with automation for parsing and getting these details, since the output and options of this command may change without notice.
pip version: pip 26.2.1 from /home/tutor/3ioip3lt/hpc/venv/lib/python3.11/site-packages/pip (python 3.11)
sys.version: 3.11.4 (main, Jul  5 2023, 13:45:01) [GCC 11.2.0]
sys.executable: /home/tutor/3ioip3lt/hpc/venv/bin/python
sys.getdefaultencoding: utf-8
sys.getfilesystemencoding: utf-8
locale.getencoding: UTF-8
sys.platform: linux

=== preinstalled scientific libs ===
  numpy            OK   2.4.6
  scipy            OK   1.17.1
  pandas           OK   3.0.6
  matplotlib       OK   3.11.2
  torch            MISSING (ModuleNotFoundError)
  torchvision      MISSING (ModuleNotFoundError)
  transformers     MISSING (ModuleNotFoundError)
  datasets         MISSING (ModuleNotFoundError)
  tokenizers       MISSING (ModuleNotFoundError)
  sentencepiece    MISSING (ModuleNotFoundError)
  sklearn          MISSING (ModuleNotFoundError)
  tqdm             MISSING (ModuleNotFoundError)
  yaml             MISSING (ModuleNotFoundError)
  requests         MISSING (ModuleNotFoundError)

=== module system ===
module is a function
module () 
{ 

--------------------------- /home/apps/modulefiles ----------------------------
   MLDL/modulefiles/caffe_gpu
   MLDL/modulefiles/caffe
   MLDL/modulefiles/horovod_pytorch
   MLDL/modulefiles/horovod_tensorflow
   MLDL/modulefiles/horovod
   MLDL/modulefiles/pytorch_gpu
   MLDL/modulefiles/pytorch
   MLDL/modulefiles/rapids
   MLDL/modulefiles/tensorflow_gpu
   MLDL/modulefiles/tensorflow
   MLDL/modulefiles/theano_gpu
   MLDL/modulefiles/theano                             (D)
   compiler/gcc/12.3                                   (L)
   compiler/oneapi-2024/advisor/2024.1
   compiler/oneapi-2024/ccl/2021.12.0
   compiler/oneapi-2024/compiler-intel-llvm/2024.1.0
   compiler/oneapi-2024/compiler-intel-llvm32/2024.1.0
   compiler/oneapi-2024/compiler-rt/2024.1.0
   compiler/oneapi-2024/compiler-rt32/2024.1.0
   compiler/oneapi-2024/compiler/2024.1.0
   compiler/oneapi-2024/compiler32/2024.1.0
   compiler/oneapi-2024/dal/2024.0.0
   compiler/oneapi-2024/debugger/2024.1.0
   compiler/oneapi-2024/dev-utilities/2024.0.0
   compiler/oneapi-2024/dnnl/3.4.0
   compiler/oneapi-2024/dpct/2024.1.0
   compiler/oneapi-2024/dpl/2022.5
   compiler/oneapi-2024/ifort/2024.1.0
   compiler/oneapi-2024/ifort32/2024.1.0
   compiler/oneapi-2024/intel_ipp_ia32/2021.11
   compiler/oneapi-2024/intel_ipp_intel64/2021.11
   compiler/oneapi-2024/intel_ippcp_ia32/2021.11
   compiler/oneapi-2024/intel_ippcp_intel64/2021.11
   compiler/oneapi-2024/mkl/2024.1
   compiler/oneapi-2024/mkl32/2024.1
   compiler/oneapi-2024/mpi/2021.12
   compiler/oneapi-2024/oclfpga/2024.1.0
   compiler/oneapi-2024/tbb/2021.12
   compiler/oneapi-2024/tbb32/2021.12
   compiler/oneapi-2024/vtune/2024.1
   compiler/openmpi/4.1.5                              (L)
   container/apptainer/1.3.2
   cuda/12.3
   gromacs/2024.2
   opencilk/2.1
   python/3
   python/3.9                                          (D)
   spack/spack

  Where:
   D:  Default Module
   L:  Module is loaded

If the avail list is too long consider trying:

"module --default avail" or "ml -d av" to just list the default modules.
"module overview" or "ml ov" to display the number of modules for each name.

--- module spider python ---

----------------------------------------------------------------------------
  python:
----------------------------------------------------------------------------
     Versions:
        python/3
        python/3.9

----------------------------------------------------------------------------
  For detailed information about a specific "python" package (including how to load the modules) use the module's full name.
  Note that names that have a trailing (E) are extensions provided by other modules.
  For example:

     $ module spider python/3.9
----------------------------------------------------------------------------
```

---

## 4. SLURM scheduler

`sinfo`, `scontrol show partition`, `sacctmgr show qos`, `sacctmgr show assoc`,
`squeue`, `sacct`

```text




=== versions ===
slurm 23.11.5
slurm 23.11.5

=== sinfo -a ===
PARTITION  AVAIL NOD STATE  CPU_LOAD   NODES(A/I/O/T)       NODELIST
standard*  up    6   drain* 0.00       0/0/6/6              rdcn[31-36]
standard*  up    7   down*  0.00       0/0/7/7              rdcn[19,22-24,26,29-30]
standard*  up    8   drain  0.00       0/0/8/8              rdcn[08,11-13,15,18,25,28]
standard*  up    15  idle   0.00-25.00 0/15/0/15            rdcn[01-07,09-10,14,16-17,20-21,27]
cpu        up    6   drain* 0.00       0/0/6/6              rdcn[31-36]
cpu        up    7   down*  0.00       0/0/7/7              rdcn[19,22-24,26,29-30]
cpu        up    8   drain  0.00       0/0/8/8              rdcn[08,11-13,15,18,25,28]
cpu        up    15  idle   0.00-25.00 0/15/0/15            rdcn[01-07,09-10,14,16-17,20-21,27]
gpu        up    2   idle   0.00       0/2/0/2              rdgpu[01-02]

=== partitions ===
PartitionName=standard
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=YES QoS=N/A
   DefaultTime=02:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=4-00:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
   Nodes=rdcn[01-36]
   State=UP TotalCPUs=1728 TotalNodes=36 SelectTypeParameters=NONE
   JobDefaults=(null)
---
PartitionName=cpu
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=NO QoS=N/A
   DefaultTime=02:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=4-00:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
   Nodes=rdcn[01-36]
   State=UP TotalCPUs=1728 TotalNodes=36 SelectTypeParameters=NONE
   JobDefaults=(null)
---
PartitionName=gpu
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=NO QoS=N/A
   DefaultTime=02:00:00 DisableRootJobs=NO ExclusiveUser=NO GraceTime=0 Hidden=NO
   MaxNodes=UNLIMITED MaxTime=4-00:00:00 MinNodes=0 LLN=NO MaxCPUsPerNode=UNLIMITED MaxCPUsPerSocket=UNLIMITED
   Nodes=rdgpu[01-02]
   State=UP TotalCPUs=96 TotalNodes=2 SelectTypeParameters=NONE
   JobDefaults=(null)
   TRESBillingWeights=CPU=1.6,GRES/gpu=70.0

=== QOS ===
Name|MaxWall|MaxTRESPU|MaxTRESPU|MinTRES|GrpTRES|MaxJobsPU|MaxSubmit|Priority
normal||||||||0
aicte|00:05:00|cpu=10,node=2|cpu=10,node=2||||2|0
mit|00:10:00|cpu=5,node=1|cpu=5,node=1||node=10|2||0
tutor|00:05:00|cpu=4,gres/gpu=1,mem=1G,node=1|cpu=4,gres/gpu=1,mem=1G,node=1||||2|0
iitk|00:15:00|node=2|node=2||||2|0
iitdh|00:05:00|cpu=96,node=2|cpu=96,node=2||||2|0
spit|00:10:00|cpu=10,node=2|cpu=10,node=2||||2|0
aicte_qip|00:05:00|cpu=4,node=1|cpu=4,node=1|||2||0
coep_qip|00:15:00|cpu=4,node=1|cpu=4,node=1|||2||0
cdacd||||||10||0
dtu_training|00:15:00|cpu=20,node=1|cpu=20,node=1|||5||0
iiitn_fdp|15:00:00|cpu=5,gres/gpu=1|cpu=5,gres/gpu=1|||2||0
chuk_delhi|12:00:00|||||||50
guest_delhi|12:00:00|||||||50
iitrpr_qos|10:00:00||||||20|100
coep_qip19|6-00:00:00|cpu=96,node=2|cpu=96,node=2|||2||0
om_sir_users|02:00:00|cpu=96|cpu=96|||20||0
 |02:00:00|cpu=96|cpu=96|||20||0
nitap|00:30:00|cpu=8,gres/gpu=1,node=2|cpu=8,gres/gpu=1,node=2|||2||0
klu|00:30:00|cpu=8,gres/gpu=1,node=2|cpu=8,gres/gpu=1,node=2|||2||0
training|00:15:00|cpu=4,gres/gpu=1,node=2|cpu=4,gres/gpu=1,node=2|||||0
cumminscollege|00:15:00|cpu=4,gres/gpu=1,node=2|cpu=4,gres/gpu=1,node=2|||2||0

=== my association ===
Account|Partition|QOS|MaxTRESPU|GrpTRES|GrpJobs|MaxJobsPU|MaxSubmit|Share
tutor||training||||||1

=== my jobs ===
JOBID PARTITION NAME ST TIME NODES CPUS
31569                      cuda_lab        gpu  COMPLETED   00:00:01      0:0 
31570                      cudadiag        gpu  COMPLETED   00:00:01      0:0 
31571                        gpuhdr        gpu  COMPLETED   00:00:01      0:0 
31573                    cuda_build        gpu  COMPLETED   00:00:02      0:0 
31574                      cuda_run        gpu  COMPLETED   00:00:04      0:0
```

---

## 5. Login-node hardware

`lscpu`, `free -h`, `nvidia-smi` (expected absent), `nvcc`

```text




=== lscpu ===
Architecture:        x86_64
CPU(s):              48
On-line CPU(s) list: 0-47
Thread(s) per core:  1
Core(s) per socket:  24
Socket(s):           2
NUMA node(s):        2
Model name:          Intel(R) Xeon(R) Gold 6240R CPU @ 2.40GHz
CPU MHz:             3671.695
CPU max MHz:         4000.0000
CPU min MHz:         1000.0000
Virtualization:      VT-x
NUMA node0 CPU(s):   0-23
NUMA node1 CPU(s):   24-47

=== free -h ===
              total        used        free      shared  buff/cache   available
Mem:          187Gi        41Gi        23Gi       445Mi       122Gi       143Gi
Swap:          95Gi        95Gi        55Mi

=== nvidia-smi on LOGIN node (expected to fail) ===
/usr/bin/which: no nvidia-smi in (/home/tutor/3ioip3lt/hpc/venv/bin:/home/apps/openmpi-4.1.5/bin:/home/apps/gcc-12.3/bin:/home/tutor/3ioip3lt/.local/bin:/home/tutor/3ioip3lt/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin)
nvidia-smi: not on PATH
bash: nvidia-smi: command not found

=== /dev/nvidia* on login ===
ls: cannot access '/dev/nvidia*': No such file or directory
```

---

## 6. Outbound network from the login node

`curl` reachability, proxy variables, Python DNS + TLS probe

```text
=== curl-based reachability (getent is broken site-wide) ===
--- getent sanity check ---
-rwxr-x--- 1 root root 33920 Jan 28  2025 /usr/bin/getent
bash: line 3: /usr/bin/getent: Permission denied
getent exit=0
--- DNS via curl (proves resolution works) ---
https://pypi.org/simple/                             HTTP 200  4.568418s
https://huggingface.co/api/datasets                  HTTP 200  1.349999s
https://dumps.wikimedia.org/                         HTTP 200  1.313041s
https://github.com                                   HTTP 200  0.249288s
https://raw.githubusercontent.com                    HTTP 301  0.024851s

=== proxy env ===
http_proxy=unset
https_proxy=unset
no_proxy=unset
NO_PROXY=unset

=== python-side DNS + TLS ===
  resolve pypi.org                 -> 151.101.128.223
  resolve huggingface.co           -> 99.86.30.118
  resolve dumps.wikimedia.org      -> 208.80.154.242
  hf api status: 200 bytes: 200
```

---

## 7. Existing workspace

`ls -la $HOME`, probe for `$HOME/bdw-llm`, existing projects, git, `.bashrc`

```text




=== $HOME listing ===
total 64
drwx------  11 3ioip3lt 3ioip3lt  4096 Oct 13 11:56 .
drwx--x--x 558 root     root     16384 Oct 13 10:45 ..
-rw-------   1 3ioip3lt 3ioip3lt   106 Oct 13 10:27 .Xauthority
-rw-------   1 3ioip3lt 3ioip3lt   251 Oct  8 13:00 .bash_history
-rw-------   1 3ioip3lt 3ioip3lt    18 Sep  3 17:23 .bash_logout
-rw-------   1 3ioip3lt 3ioip3lt   141 Sep  3 17:23 .bash_profile
-rw-------   1 3ioip3lt 3ioip3lt  1009 Oct  7 14:07 .bashrc
drwxrwxr-x   4 3ioip3lt 3ioip3lt    47 Oct  7 14:06 .cache
drwx------   4 3ioip3lt 3ioip3lt    49 Oct  7 14:04 .config
drwx------   3 3ioip3lt 3ioip3lt    33 Sep  3 17:23 .dbus
-rw-------   1 3ioip3lt 3ioip3lt    16 Sep  3 17:23 .esd_auth
-r--------   1 3ioip3lt 3ioip3lt   205 Oct 13 11:56 .google_authenticator
drwx------   5 3ioip3lt 3ioip3lt    57 Oct  7 14:02 .local
drwx------   4 3ioip3lt 3ioip3lt    51 Sep  3 17:23 .mozilla
drwx------   3 3ioip3lt 3ioip3lt    34 Oct 13 09:54 .nv
drwx------   2 3ioip3lt 3ioip3lt    97 Sep  3 17:23 .ssh
drwxrwxr-x   2 3ioip3lt 3ioip3lt    40 Oct 13 09:49 gccbin
drwxrwxr-x   8 3ioip3lt 3ioip3lt   129 Oct  7 14:08 hpc

=== bdw-llm present? ===
bdw-llm: ABSENT (safe to create)

=== any existing python projects in $HOME (depth<=2) ===

=== existing venvs / conda ===
none found

=== git ===
/usr/bin/git
git version 2.43.7

=== existing hpc workspace (from earlier session) ===
/home/tutor/3ioip3lt/hpc
HPC
README.md
build
jobs
results
src
venv
```

---

## 8. GPU node — inside a scheduled allocation

3-minute `sbatch` on `--partition=gpu --gpus=1` (inspection probe, **not** a
training job):

```text
--- sbatch state: state=COMPLETED (job 31730) ---
### /home/tutor/3ioip3lt/hpc/jobs/bdw_a_gpu-31730.out
==========================================
SLURM_CLUSTER_NAME = paramrudra
SLURM_ARRAY_JOB_ID = 
SLURM_ARRAY_TASK_ID = 
SLURM_ARRAY_TASK_COUNT = 
SLURM_ARRAY_TASK_MAX = 
SLURM_ARRAY_TASK_MIN = 
SLURM_JOB_ACCOUNT = tutor
SLURM_JOB_ID = 31730
SLURM_JOB_NAME = bdw_a_gpu
SLURM_JOB_NODELIST = rdgpu01
SLURM_JOB_USER = 3ioip3lt
SLURM_JOB_UID = 56027
SLURM_JOB_PARTITION = gpu
SLURM_TASK_PID = 3205970
SLURM_SUBMIT_DIR = /home/tutor/3ioip3lt/hpc/jobs
SLURM_CPUS_ON_NODE = 2
SLURM_NTASKS = 1
SLURM_TASK_PID = 3205970
==========================================
node      : rdgpu01
user      : 3ioip3lt
date      : 2026-10-16T10:22:28+05:30
nproc     : 48
--- nvidia-smi -L ---
GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-16845317-cfa6-e9c5-4858-eb7ffd7d6be2)
--- gpu detail ---
name, memory.total [MiB], driver_version, compute_cap
NVIDIA A100 80GB PCIe, 81920 MiB, 545.23.06, 8.0
--- full nvidia-smi (head) ---
Fri Oct 16 10:22:29 2026       
+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 545.23.06              Driver Version: 545.23.06    CUDA Version: 12.3     |
|-----------------------------------------+----------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
|                                         |                      |               MIG M. |
|=========================================+======================+======================|
|   0  NVIDIA A100 80GB PCIe          Off | 00000000:3B:00.0 Off |                    0 |
| N/A   30C    P0              39W / 300W |      4MiB / 81920MiB |      0%      Default |
|                                         |                      |             Disabled |
+-----------------------------------------+----------------------+----------------------+
                                                                                         
+---------------------------------------------------------------------------------------+
| Processes:                                                                            |
--- CUDA toolkit ---
nvcc not on PATH
/usr/local/cuda
/usr/local/cuda-12
/usr/local/cuda-12.3
--- python on GPU node ---
Python 3.11.4
torch present: False
--- outbound network from GPU node ---
https://pypi.org/simple/                           curl: (6) Could not resolve host: pypi.org
 -> http=000
https://huggingface.co/api/datasets                curl: (6) Could not resolve host: huggingface.co
 -> http=000
https://dumps.wikimedia.org/                       curl: (6) Could not resolve host: dumps.wikimedia.org
 -> http=000
--- exit ---
PROBE_OK
--- stderr ---
### /home/tutor/3ioip3lt/hpc/jobs/bdw_a_gpu-31730.err
[stderr]
/usr/bin/cluster-env: line 31: /usr/bin/getent: Permission denied
```

---

## 9. CPU node — inside a scheduled allocation

3-minute `sbatch` on `--partition=standard --cpus-per-task=4`:

```text
--- sbatch state: state=COMPLETED (job 31731) ---
### /home/tutor/3ioip3lt/hpc/jobs/bdw_a_cpu-31731.out
==========================================
SLURM_CLUSTER_NAME = paramrudra
SLURM_ARRAY_JOB_ID = 
SLURM_ARRAY_TASK_ID = 
SLURM_ARRAY_TASK_COUNT = 
SLURM_ARRAY_TASK_MAX = 
SLURM_ARRAY_TASK_MIN = 
SLURM_JOB_ACCOUNT = tutor
SLURM_JOB_ID = 31731
SLURM_JOB_NAME = bdw_a_cpu
SLURM_JOB_NODELIST = rdcn14
SLURM_JOB_USER = 3ioip3lt
SLURM_JOB_UID = 56027
SLURM_JOB_PARTITION = standard
SLURM_TASK_PID = 4188239
SLURM_SUBMIT_DIR = /home/tutor/3ioip3lt/hpc/jobs
SLURM_CPUS_ON_NODE = 4
SLURM_NTASKS = 1
SLURM_TASK_PID = 4188239
==========================================
node      : rdcn14
nproc     : 48
model     :  Intel(R) Xeon(R) Gold 6240R CPU @ 2.40GHz
--- memory ---
              total        used        free      shared  buff/cache   available
Mem:          187Gi        22Gi       160Gi       4.4Gi       4.6Gi       160Gi
--- python ---
Python 3.11.4
--- outbound network from CPU node ---
https://pypi.org/simple/                           curl: (6) Could not resolve host: pypi.org
 -> http=000
https://huggingface.co/api/datasets                curl: (6) Could not resolve host: huggingface.co
 -> http=000
https://dumps.wikimedia.org/                       curl: (6) Could not resolve host: dumps.wikimedia.org
 -> http=000
PROBE_OK
--- stderr ---
### /home/tutor/3ioip3lt/hpc/jobs/bdw_a_cpu-31731.err
[stderr]
/usr/bin/cluster-env: line 31: /usr/bin/getent: Permission denied
```

---

## 10. Summary of verified constraints

| Item | Verified value | Evidence |
|---|---|---|
| Scheduler | Slurm 23.11.5 | §4 |
| Account / QOS | `tutor` / `training` | §4 |
| Partitions | `standard` (default, `rdcn01-36`), `cpu` (same nodes), `gpu` (`rdgpu01-02`) | §4 |
| QOS `training` limit | `MaxWall=00:15:00`, `MaxTRESPU=cpu=4,gres/gpu=1,node=2` | §4 |
| GPU per node | `gpu:2` (2 × A100 80 GB) — see §8 for the measured device | §4/§8 |
| CPU per node | 48 cores (2 × 24, no SMT), Xeon Gold 6240R | §5 |
| RAM per node | ~187 GiB (+ 95 GiB swap) | §5 |
| GPU on login | **absent** — no `nvidia-smi`, no `/dev/nvidia*` | §5 |
| `/scratch` | exists (125 T) but **NOT writable** by users | §2 |
| `/home` | 25 T total, **94 % full, 1.6 T free** | §2 |
| Outbound HTTPS | PyPI, Hugging Face, Wikimedia, GitHub all **HTTP 200** from login | §6 |
| Outbound HTTPS from compute | **NONE** — no DNS on compute nodes: `/etc/resolv.conf` is fully commented (`#nameserver 14.139.5.5`), `Could not resolve host`, `http=000` for PyPI/HF/Wikimedia from both GPU and CPU nodes | §8/§9 |
| Download staging point | all downloads **must** run on the login node and be written to `/home` (NFS); compute jobs read them from shared storage | §6/§8/§9 |
| Python | 3.11.4 via `~/hpc/venv` (auto-activated by `.bashrc`) | §3 |
| `venv` + `ensurepip` | available | §3 |
| ML libraries in venv | numpy/scipy/pandas/matplotlib present; **torch, transformers, datasets, tokenizers absent** | §3 |
| Cluster ML modules | `MLDL/modulefiles/pytorch_gpu`, `tensorflow_gpu`, etc. exist (metadata only — not loaded) | §3 |
| `getent` | broken site-wide (see §6) — use `curl` for connectivity checks | §6 |
| `$HOME/bdw-llm` | was **absent** before this audit | §7 |

---

## 11. Known limitations of this audit

* Nothing was installed and nothing was downloaded; the ML stack is **not yet**
  verified to work — that belongs to Stage B.
* GPU/CUDA/PyTorch runtime is only confirmed for the probe hardware in §8.
  PyTorch itself is not installed, so `torch.cuda.is_available()` is **untested**.
* Language-dataset access (Hugging Face dataset configs, licenses, streaming)
  was **not** exercised — that is Stage C.
* `du -sh $HOME` and `df` were taken on the login node; per-user quota tooling
  (`quota`/`lfs quota`) is absent, so only the global filesystem figures are known.

_Generated by the Stage A audit script. Raw transcript retained with the script._
