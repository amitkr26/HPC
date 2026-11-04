# Module 06 - Python Programming

- **Duration:** 40 hrs / 5 Days
- **Faculty:** Usha Rani (PE STG)
- **Schedule:** 02/09/2026 - 09/09/2026
- **Holidays:** 04/09/2026 (Janmashtmi), 05/09 - 06/09/2026 (Weekend)
- **Status:** done

## Folder layout

```
06-PYTHON-PROGRAMMING/
├── README.md
├── COURSE-MATERIAL/
│   ├── ASSIGNMENTS/              <- assignment PDFs and submitted DOCX files
│   └── REFERENCE/                <- Python slides, virtualenv and NumPy handouts
├── 01-PYTHON-BASICS/
│   ├── 03-PRACTICE/              <- Day-1 input, print, variables, arithmetic
│   └── 04-ASSIGNMENTS/           <- Python Assignment 1 notebook
├── 02-FILE-HANDLING/
│   └── 03-PRACTICE/              <- context managers, append log, delete, mkdir/chdir
├── 03-MODULES-AND-IMPORTS/
│   └── 03-PRACTICE/              <- math_tools, greet, main, import demo
├── 05-QUIZZES/
│   └── Python-Indexing-Slicing/  <- indexing/slicing/nditer quiz + solutions
├── assignment/
│   └── templates/                <- earlier weather-dashboard template
└── weather_dashboard_project/    <- completed weather dashboard project
```

## Practice areas

- **Basics:** `01-PYTHON-BASICS/03-PRACTICE/` — input/output, variables, arithmetic.
- **File handling:** `02-FILE-HANDLING/03-PRACTICE/` — `with` blocks, append mode,
  safe read/delete, directory creation and cleanup.
- **Modules and imports:** `03-MODULES-AND-IMPORTS/03-PRACTICE/` — `math_tools.py`
  provides the functions imported by `main.py`; `import_demo.py` shows an
  absolute import from `greet.py`.
- **Assignments:** `01-PYTHON-BASICS/04-ASSIGNMENTS/python_assignment1.ipynb` and
  the PDFs/DOCX files under `COURSE-MATERIAL/ASSIGNMENTS/`.
- **Quiz:** the indexing/slicing/nditer quiz and its solutions are under
  `05-QUIZZES/Python-Indexing-Slicing/`.
- **Project:** `weather_dashboard_project/weather_dashboard/` is the runnable
  Flask/SQLite weather dashboard.

## Run

```bash
python 01-PYTHON-BASICS/03-PRACTICE/hello_world.py
cd 02-FILE-HANDLING/03-PRACTICE && python 01_context_manager_read_write.py
cd 03-MODULES-AND-IMPORTS/03-PRACTICE && python main.py
```

The weather dashboard has its own `requirements.txt`; install it before running
`weather_dashboard_project/weather_dashboard/app.py`.
