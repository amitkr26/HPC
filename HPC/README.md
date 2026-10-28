# HPC Study Materials

Personal learning repository for the **Advanced Certificate Course – HPC (AI), July 2026 Batch**. Modules follow the official course schedule.

## Repository Structure

```
HPC/
├── COURSE.md                         # official course schedule, parsed (modules, dates, status)
├── 01-COMPUTER-NETWORKS/             # Computer Networks & Interconnects (48hrs)
│   ├── COURSE-MATERIAL/              #   session slide PDFs (Session 1–11)
│   ├── PRACTICE/                     #   Cisco Packet Tracer files (.pkt)
│   └── ComputerNetworksSample*.pdf   #   sample-question packs (Q + keyed A)
├── 02-LINUX-AND-OS/                  # Linux and Operating Systems (48hrs)
│   ├── COURSE-MATERIAL/              #   assignment sheets, question papers, PPTs, handouts
│   ├── SOLUTIONS/                    #   shell-script solutions q01–q58 + launcher
│   └── LinuxSampleQuestions*.pdf     #   sample-question packs (Q + solution)
├── 03-CLOUD-COMPUTING/               # Cloud Computing & Operation/Deployment Strategies (48hrs)
│   ├── COURSE-MATERIAL/              #   session slide PDFs (Sessions 1, 2, 3, 4, 6)
│   └── CLoudComputingSample*.pdf     #   sample-question packs (Q + keyed A)
├── 04-C-AND-DS/                    # C and Data Structure (64hrs)
│   ├── COURSE-MATERIAL/            #   reference PDFs + assignment docx
│   └── (topic folders 01–21, assignments, mini-projects)
├── 05-CPP-PROGRAMMING/             # C++ Programming (40hrs)
│   ├── COURSE-MATERIAL/            #   day slide PDFs + assignment docx
│   └── (topic folders, assignments)
├── 06-PYTHON-PROGRAMMING/          # Python Programming (40hrs) — day-1 basics practice
├── 07-HPC-AND-ITS-ARCHITECTURE/    # Intro to HPC & Its Architecture (48hrs) — OpenMP, lectures, assignments
│   └── COURSE-MATERIAL/REFERENCE/  #   + HPC Architecture Q&A packs, CUDA & GPU-architecture PDFs
├── 08-CPP-PARALLEL-PROGRAMMING/    # C++ with Parallel Programming (40hrs) — module done 24/09
├── 09-ADVANCED-PROGRAMMING-HPC/    # Advanced Programming – HPC (72hrs) — profiling + GDB debugging
├── 10-STATISTICS-AND-DATA-HANDLING/# Statistical Analysis & Data Handling using Python (48hrs) — module done 16/10
├── 11-ML-DL-OPENVINO/              # Intro to ML, DL & OpenVINO (48hrs) — ends 28/10
├── 12-APTITUDE-AND-COMMUNICATION/  # Aptitude & Effective Communication (50hrs) — starts 29/10
├── 13-PROJECT-MODULE/              # Project Module (100hrs) — hpc-vlsi-placement project; runs 06/11–23/11
├── bdw-llm/                        # Standalone project — from-scratch LLM on PARAM Rudra
│   ├── docs/                       #   stage reports A–J, each md5-verified
│   ├── scripts/                    #   one SLURM script per stage + the job output it cites
│   ├── src/                        #   tokenizer, model, training loop, evaluation
│   └── tokenizer/                  #   trained byte-level BPE vocab (16,384)
├── 99-EXTRA/                       # Resumes, interview prep (VLSI/Digital), misc
│   ├── INTERVIEW-PREP/
│   ├── RESUME/
│   │   └── COMPANY-SPECIFIC/
│   └── IMAGES/
└── 99-REFERENCES/                  # Course details, review/archive items
    └── REVIEW/
```

## Guides

- **Course schedule (from the official PDF)** – `COURSE.md` (all 13 modules, dates, faculties, holidays, status)
- **C++** – `05-CPP-PROGRAMMING/README.md` (course overview + roadmap)
- **C** – `04-C-AND-DS/README.md` (course overview + roadmap)
- **Assignments vs. code mapping** – `ASSIGNMENT-MAPPING.md`
- **HPC module 07** – `07-HPC-AND-ITS-ARCHITECTURE/README.md`
- **Python module 06** – `06-PYTHON-PROGRAMMING/README.md`
- **BDW from-scratch LLM project** – `bdw-llm/README.md` (overview), `bdw-llm/docs/FINAL_REPORT.md` (results)

## Course Details

Parsed schedule with dates, faculties, holidays and per-module status: [`COURSE.md`](COURSE.md).
Source document: `99-REFERENCES/Course_Details_2026.pdf` (dates tentative per the source).
Modules in teaching order: Networks → Linux/OS → Cloud → C → C++ → Python → HPC Arch → C++ Parallel → Advanced HPC → Statistics → ML/DL/OpenVINO → Aptitude → Project.