# Odoo 16 Backend Developer Practical Test

## Modules

### `estate/` — Foundation
Real estate property management module built following the official Odoo 16
tutorial. Manages properties, offers, types, and tags with a full state
machine (New → Offer Received → Offer Accepted → Sold / Cancelled).

### `estate_account/` — Task A
Separate accounting integration addon. Automatically creates a draft customer
invoice when a property is marked as Sold:
- 6% commission on the selling price
- Fixed €100 administrative fee

Includes a smart button on the property form showing linked invoices.

### `course_catalog/` — Task B
Fixed version of a provided buggy module. Five bugs corrected — see NOTES.md
for the full list.

## Running the Tests

```powershell
docker exec odoo16 odoo -d estate_dev --test-enable --stop-after-init -u estate_account --log-level=test
```

Expected result: `0 failed, 0 error(s) of 4 tests`

## Notes

See [NOTES.md](./NOTES.md) for full workflow description, AI usage, and
decisions made during implementation.