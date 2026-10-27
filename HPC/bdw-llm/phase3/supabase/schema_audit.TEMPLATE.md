# schemaaudit — P3.0 owner checklist fill-in

Copy this file to `schema_audit.md` (same directory) and fill **only the
lines marked with `TODO`** — the table names you saw in the Supabase
dashboard and the verified-flag column name for openings (or `null` if the
platform keeps no such flag). The ```json block below is what
`phase3/gateway/ingest.py` executes against; everything else in this file is
free-form notes and is ignored by the parser.

Rules:

- Keys of `"tables"` are the six allowed `parent_type` values; edit them to
  match your live tables one-to-one. Delete a whole entry for types the
  platform does not have — the ingest counts `empty:0` only if you keep the
  entry with a wrong name.
- `verified` is the exact column name carrying the platform's verification
  flag (checked against EVERY row via `row.get(col)`); `null` means
  "treat as unverified for now" (conservative for the S5 citation gate).
- `row_limit` is optional — omit it for a full pull; set it for a pilot.
- Do not paste any data rows or credentials into this file.

```json
{
  "tables": {
    "opportunity": {"table": "TODO_real_table_name", "verified": "TODO_column_or_null"},
    "organization": {"table": "TODO", "verified": null},
    "resource": {"table": "TODO", "verified": null},
    "faq": {"table": "TODO", "verified": null},
    "news": {"table": "TODO", "verified": null},
    "lab_tool": {"table": "TODO", "verified": null}
  }
}
```

## Console quick-notes (paste observation notes below this line, no data)
