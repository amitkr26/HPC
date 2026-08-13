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
`C:\Users\STUDENT\Desktop\Amit\C\Assignmenmt\Amit_Kumar_Lab4_Day4_Assignment.docx`.
Best approach: clone that docx and swap in the new assignment's code and
screenshots so all styles and layout are preserved.

Document structure (in body order):
1. Title paragraph (Title style, Times New Roman 28pt):
   `Amit_Lab<labnum> - Day <day> Assignment` (e.g. "Amit_Lab4 - Day 4 Assignment")
2. Subtitle paragraph (normal style): topic line, e.g. "C Programming - Strings"
3. For each question N (Heading 2, Times New Roman 13pt): `Question N: <desc>`
   - A 1-cell table (style Table1, light gray borders, width 9360 dxa, left
     justified) containing the FULL source code as Consolas 9pt runs, one
     run per line with a line break between lines.
   - A paragraph `Output:`
   - A 1-cell table (style Table2, dark borders) containing the real console
     screenshot of the program output (inline picture, ~5.6 in wide).
   - A blank paragraph.
4. `MCQ Questions: Answers` (Heading 2) followed by a 2-column table
   (`Q` | `Answer`) with one row per question, answers like `B) 8`.
5. `Explain` (Heading 2) followed by the numbered explain questions and their
   answers as normal paragraphs. Where the explanation needs short C
   examples, put them in 1-cell code tables (Consolas).

Companion artifacts per assignment (in the `C\Day<N>` folder, like Day3/Day4):
- One `.c` source file per question (`q01_<name>.c` ... `qNN_<name>.c`),
  compiled with gcc to `.exe`.
- One `in_qNN.txt` input file for interactive programs.
- One `qNN_output.png` real console screenshot per question (OCR-verified).
- The solved document as both `.docx` and `.pdf` named
  `Amit_Kumar_Lab<labnum>_Day<day>_Assignment.docx/.pdf`.

