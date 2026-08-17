# AWS Guidance

- Prefer the AWS MCP Server for AWS interactions — it provides sandboxed
  execution, observability, and audit logging. If unavailable, use the
  AWS CLI directly.
- Before starting a task, check whether a relevant AWS skill is available.
  Load the skill with `retrieve_skill` and prefer its guidance over
  general knowledge.
- When uncertain about specific AWS details (API parameters, permissions,
  limits, error codes), verify against documentation rather than guessing.
  State uncertainty explicitly if you cannot confirm.
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or
  CloudFormation) over direct CLI commands.
- When working with infrastructure, follow AWS Well-Architected Framework
  principles.
- Do not use em dashes in AWS resource names or descriptions. Use
  hyphens instead.

## Secret Safety

- MUST load the `aws-secrets-manager` skill first for any secret,
  credential, API key, token, or password task. MUST NOT call
  `secretsmanager get-secret-value` or `batch-get-secret-value`, and MUST
  NOT hit the Secrets Manager Agent daemon directly. MUST use
  `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with
  `asm-exec` so the secret resolves at runtime without entering context.

## C Assignment Deliverable Format

When solving C assignments, ALWAYS create the solved document in the exact
format used by the reference file
`C:\Users\STUDENT\Desktop\Amit\C-PROGRAMMING-COURSE\C\Assignmenmt\Amit_Kumar_Lab5_6_Day5_6_Assignment.docx`.
Best approach: clone that docx and swap in the new assignment's code and
screenshots so all styles and layout are preserved.

Document structure (in body order):
1. Title paragraph (normal style, bold, Calibri 16pt / 203200 EMU):
   `C Program - Day <N> Assignment`
2. Question list paragraphs (normal style, Calibri 12pt, plain text):
   one paragraph per question describing what to implement (may span
   multiple paragraphs for longer questions).
3. Empty paragraphs as spacing.
4. Lab title paragraph (normal style, bold, Calibri 16pt):
   `Amit_Lab<labnum> - Day <day> Assignment`
5. Subtitle paragraph (normal style, Calibri 12pt): topic line,
   e.g. "C Programming - Functions, Structures & Pointers"
6. For each question N (normal style, bold heading):
   `Question N: <title>`
   - A 1-cell code table (style `Table<N*2-1>`, e.g. Table1 for Q1,
     Table3 for Q2) containing the FULL source code.
   - A paragraph `Output:` (normal style, bold)
   - A 1-cell screenshot table (style `Table<N*2>`, e.g. Table2 for Q1,
     Table4 for Q2) containing the real console screenshot (inline picture).
   - A blank paragraph.
   IMPORTANT: Each question gets its own unique numbered Table style.
   Do NOT reuse Table1/Table2 for all questions. Q1=Table1+Table2,
   Q2=Table3+Table4, Q3=Table5+Table6, etc.
7. `MCQ Questions: Answers` paragraph (normal style, bold) followed by a
   2-column table (`Q` | `Answer`) with one row per question.
8. `Explain` paragraph (normal style, bold) followed by the numbered explain
   questions (bold heading) and their answers (normal paragraphs).
   Where the explanation needs short C examples, put them in 1-cell code
   tables (unique numbered style, e.g. Table42 for Q5).

Companion artifacts per assignment (in the `C\Day<N>` folder, like Day5/Day6):
- One `.c` source file per question (`q01_<name>.c` ... `qNN_<name>.c`),
  compiled with gcc to `.exe`.
- One `in_qNN.txt` input file for interactive programs.
- One `qNN_output.png` real console screenshot per question (pixel-verified,
  real console content at 1129x635 resolution).
- The solved document as both `.docx` and `.pdf` named
  `Amit_Kumar_Lab<labnum>_Day<day>_Assignment.docx/.pdf`.

## C Programming Course Updates

There is a living C course at `C-PROGRAMMING-COURSE\`. Before working on C
learning material, read `00-COURSE-README.md`. Do NOT restructure the `C\`
folder (it is learning history). Never mark a topic Completed/Mastered without
evidence (studied/practiced/understood/mastered rule in the course README).

When the user says "Add today's lesson: <topic>" (or "Day N: <topic>"), follow
the exact checklist in `00-COURSE-README.md` (How to add a new day): copy
`TEMPLATES\Day-XX`, fill theory/syntax/examples/code/practice/MCQ/debugging,
then update `01-ROADMAP.md`, `02-PROGRESS.md`, `TOPIC-INDEX.md`, and
`03-CHEAT-SHEET.md` as needed. Compile-check every new `.c` file with
`C:\MinGW\bin\gcc.exe`.

