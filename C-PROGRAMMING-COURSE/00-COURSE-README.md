# C Programming Course

A structured, progressive, **living** C course built around my real daily
learning. It is not a generic tutorial dump: every module is wired to the
actual programs, assignments, and screenshots that I have already written and
submitted.

## What this course is

- A **master index** that connects theory, syntax, code, practice, MCQs,
  debugging questions, assignments, and projects in one place.
- A **daily journal** that preserves my learning history day by day.
- A **roadmap** that shows exactly where I am and what comes next.
- A **single command** to add every future lesson without breaking anything.

## Where things live

```
C-PROGRAMMING-COURSE/          <- this course (read this first)
├── 00-COURSE-README.md        <- you are here
├── 01-ROADMAP.md              <- the full progression, beginner -> advanced
├── 02-PROGRESS.md             <- what is done / in progress / not started
├── 03-CHEAT-SHEET.md          <- quick revision reference
├── TOPIC-INDEX.md             <- search every topic from one place
├── PRACTICE-INDEX.md          <- every instructor question + the program written for it
├── TEMPLATES/Day-XX/          <- blank template for a new lesson
└── 01-BEGINNER/ ... 17-FINAL-PROJECTS/   <- modules

C/                              <- my learning history (do NOT delete)
├── *.c (flat)                  <- every program, copied into the course code/ folders
└── Assignmenmt/                <- assignment sheets + solved docs
```

The `C/` folder is **learning history** and stays untouched. The course
**references** it. Never delete, rename, or "clean up" files there without
explicitly asking.

## Who this course is for

- Me, learning C day by day.
- It reflects what I have **actually studied**, not a pretend full syllabus.
- Topics I have only seen once are marked **Needs Practice**, not Mastered.

## How to use it

1. Open `01-ROADMAP.md` to see the full path and where I am.
2. Open `02-PROGRESS.md` to see today's status table.
3. For any topic, search `TOPIC-INDEX.md` for its theory/code/practice/assignment.
4. Follow the **Day folders** in order: `01-BEGINNER/Day-01`,
   `01-BEGINNER/Day-02`, `03-ARRAYS/Day-03`, `04-STRINGS/Day-04`, ...

### Where each Day folder lives

A day's folder is placed under the **module that matches its main topic**:

| Day | Topic | Day folder |
| --- | --- | --- |
| Day 1 | C fundamentals | `01-BEGINNER/Day-01/` |
| Day 2 | Conditions, loops, patterns | `01-BEGINNER/Day-02/` |
| Day 3 | Arrays | `03-ARRAYS/Day-03/` |
| Day 4 | Strings | `04-STRINGS/Day-04/` |
| Day 5+ | e.g. Pointers | `05-POINTERS/Day-05/` ... |

## How daily lessons work

Every lesson (past and future) follows the same structure in
`TEMPLATES/Day-XX/`:

```
Day-XX/
├── README.md      <- overview, objective, what was done
├── THEORY.md      <- concepts, progressively
├── SYNTAX.md      <- correct C syntax with comments
├── EXAMPLES.md    <- tiny examples + dry runs
├── PRACTICE.md    <- practice programs (easy -> hard)
├── MCQ.md         <- MCQs, answers on separate lines
├── DEBUGGING.md   <- common mistakes + find-the-error drills
└── code/          <- one .c file per program, snake_case
```

Each lesson covers: objectives, concepts, syntax, simple examples, dry runs,
practice programs, common mistakes, questions (output/error/logic/coding/
conceptual), MCQs, and a revision summary.

## How to practice

- `PRACTICE-INDEX.md` maps every instructor-given question to the program
  written for it (and shows what is still missing).
- Every studied module has a `PRACTICE.md` with six levels:
  Level 1 Basic -> Level 2 Logic -> Level 3 Coding -> Level 4 Debugging ->
  Level 5 Interview/Viva -> Level 6 Challenge.
- Work a level only after honestly passing the previous one.

## How to use the assignments

- Problem sheets and solved documents: `C/Assignmenmt/` (indexed in
  `13-ASSIGNMENTS/`).
- The solved documents follow the format documented in `AGENTS.md`
  (`## C Assignment Deliverable Format`): cloned template, code tables,
  console screenshots, MCQ answers table, Explain section.
- `01-BEGINNER/Day-02/code/`, `03-ARRAYS/Day-03/code/`, `04-STRINGS/Day-04/code/`
  hold the per-question `.c` programs (copied from the flat `C/` history).

## How to revise

- Each studied module has a `REVISION.md`:
  10 quick questions, 10 output questions, 10 find-the-error questions,
  10 coding problems, 10 MCQs, 5 viva questions, 1 mini project.
- `03-CHEAT-SHEET.md` is the one-page memory refresher.
- Never trust "I saw it once" = understanding. Use the honesty rules in
  `01-ROADMAP.md` (Studied vs Practiced vs Understood vs Mastered).

## How to track progress

- `02-PROGRESS.md` is the single source of truth.
- Statuses: `Not Started`, `In Progress`, `Completed`, `Needs Revision`.
- A topic is `Completed` only when the lesson + practice + MCQ + debugging are
  done, not when a file merely exists.

## How to add a new day (exactly)

Tell me:

> Add today's lesson: <topic>

or

> Day 5: <topic>

I will follow this exact checklist (do not skip steps):

1. Identify the topic and its prerequisites.
2. Copy `TEMPLATES/Day-XX/` into the module folder for that topic
   (e.g. a pointers day -> `05-POINTERS/Day-05/`).
3. Fill THEORY.md and SYNTAX.md.
4. Add EXAMPLES.md with dry runs.
5. Write `code/` programs (snake_case, independently compilable).
6. Add PRACTICE.md (Levels 1-6).
7. Add MCQ.md (answers separated).
8. Add DEBUGGING.md (common mistakes).
9. Update `01-ROADMAP.md` if the roadmap changes.
10. Update `02-PROGRESS.md`.
11. Update `TOPIC-INDEX.md`.
12. Update `03-CHEAT-SHEET.md` if a new syntax/function was learned.
13. Do not modify unrelated lessons.
14. Compile-check any new `code/` programs before finishing.

## Recommended learning order (now)

Fundamentals -> Conditions -> Loops -> **Arrays** -> **Strings** ->
(revise both) -> Functions -> Pointers -> Recursion -> Structures -> ...

The next lesson I have not started yet: **Functions**.

## Honesty rule

A program existing in a folder does **not** mean it is understood. The course
always distinguishes:

- **Studied** - I saw it in a lesson/assignment.
- **Practiced** - I ran and modified it myself.
- **Understood** - I can explain it and answer viva questions.
- **Mastered** - I can solve new problems with it without help.

When evidence is missing, the topic is marked **Needs Practice**.
