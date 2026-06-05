# Migration Registry

Lane A stewards this file. All lanes must claim a migration number here before creating a migration file.
This prevents sequence collisions across lanes.

## Claiming a number

1. Read this file to find the next available number.
2. Add a row to the "Claimed" table below (lane, number, description, date).
3. Name your migration file: `NNNN_<lane_prefix>_<description>.sql` (e.g., `0003_b_area_geometry.sql`).
4. Commit both this file and the migration in the same change.

## Lane prefixes

| Lane | Prefix |
|---|---|
| Lane A | `a` |
| Lane B | `b` |
| Lane C | `c` |
| Lane D | `d` |

## Applied migrations

| Number | File | Description | Applied |
|---|---|---|---|
| 0001 | `0001_initial_spine.sql` | Core schema: all tables, enums, intents | 2026-06-03 (generated) |
| 0002 | `0002_d_report_review_lifecycle.sql` | Report review status and action audit fields | 2026-06-05 |

## Claimed (not yet applied)

| Number | Lane | Description | Claimed on |
|---|---|---|---|
| _(next: 0003)_ | - | - | - |

## Notes

- Do not renumber applied migrations.
- If a migration conflicts with another lane's pending change, stop and coordinate via the human.
- Lane A may add shared indexes or maintenance migrations with prefix `a` or `shared`.
