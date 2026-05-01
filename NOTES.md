# NOTES.md — Submission Workflow Description  | By: Maghan Das


## Environment

- Odoo 16 Community Edition via Docker (company-provided starter kit)
- Base image: `odoo:16.0` + `pip install debugpy` for IDE attach
- VS Code with Python and XML (Red Hat) extensions
- OS: Windows, Docker Desktop

---

## How I Used AI

I used Claude as a pair programmer throughout. My discipline was:

- Feed it **only the relevant model/file** when asking for code, never the full source tree
- Always read the generated output before applying it
- Cross-check field names and method signatures against Odoo 16 behaviour in the running instance
- When something failed, paste **only the traceback** — not the entire codebase

---

## Foundation — `estate` module

### Approach

Followed the official Odoo 16 tutorial structure. Used AI to generate
boilerplate (field definitions, view skeletons) and wrote the business logic
with explanation of each decision.

### AI accepted as-is

- Model field definitions (`Char`, `Float`, `Selection`, `Many2one`, `One2many`, `Many2many`)
- `_sql_constraints` syntax
- `@api.depends` / `@api.onchange` skeleton
- Security CSV column structure

### AI suggestions I caught and corrected

**1. `column_invisible` in tree view**
AI generated `<field name="state" column_invisible="True"/>` in the list view.
This attribute does not exist in Odoo 16 — it was introduced in Odoo 17.
Odoo threw a `ParseError: Invalid view` on install.
Fixed to: `<field name="state" invisible="1"/>` which is the correct v16 syntax.

**2. XML corrupted during manual edit**
While applying the `invisible` fix manually, a stray `<data>` wrapper and a
misplaced `</tree>` tag crept in. Odoo error:
`ValueError: Wrong value for ir.ui.view.type: 'data'`
Resolution: replaced the entire views file from scratch rather than patching
the broken XML. Lesson: always overwrite, never patch corrupted XML by hand.

### Key decisions

- Used `base.group_user` for access rights (all internal users) rather than
  creating a dedicated `Estate / User` group — sufficient for this exercise,
  noted here per submission instructions.
- `best_price` uses `max(..., default=0.0)` to handle zero-offer edge case.
- `_order = 'id desc'` on `estate.property` so newest listings appear first.

---

## Task A — `estate_account` module

### Approach

Created a separate addon depending on `estate` and `account`.
Overrode `action_sold` using `super()` to preserve original state transition,
then appended invoice creation. Kept `_create_invoice` as a separate private
method for clarity and testability.

### AI accepted as-is

- Module manifest structure with correct `depends`
- `_inherit = 'account.move'` to add `estate_property_id` field
- `(0, 0, {...})` ORM syntax for inline `invoice_line_ids` creation
- View inheritance pattern (`inherit_id` + `<sheet position="before">`)

### AI suggestions I caught and corrected

**3. `self.company_id` on `estate.property`**
AI generated journal search using `self.company_id.id`. At runtime this threw:
`AttributeError: 'estate.property' object has no attribute 'company_id'`
`company_id` is not automatically present on every Odoo model — it must be
explicitly declared or inherited via a mixin. Since adding a full multi-company
field was out of scope, I replaced it with `self.env.company` which resolves
the active company from the user session. This is the correct Odoo 16 idiom
for single-company setups and is still multi-company safe when the user
switches companies in the UI.

**4. Income account resolution**
AI initially suggested resolving the income account via
`account.move._get_default_journal().default_account_id` — a method chain
that does not exist as a public API in v16. Verified by checking the
`account.move` source in the running container:
```
docker exec odoo16 grep -n "default_account" \
  /usr/lib/python3/dist-packages/odoo/addons/account/models/account_move.py
```
Replaced with the simpler and correct approach:
`journal.default_account_id` — the sales journal's own default account,
which is exactly what Odoo uses internally for manual invoices.

### Idempotency decision

Re-running `action_sold` on an already-sold property raises a `UserError`
rather than silently no-op-ing. Rationale: silent no-op could mask bugs;
an explicit error makes the duplicate call visible and traceable.

### Constraint: no buyer

Attempting to sell without `buyer_id` raises a `UserError` before
`super().action_sold()` is called, so state never changes to `sold`.

- **Multi-company**: `company_id` field added to `estate.property` 
  (defaults to current user's company). Invoice creation uses 
  `self.company_id` to find the correct journal and account, 
  making it fully multi-company safe.
  
### Acceptance criteria result

```
property.action_sold()
→ invoice_count == 1                          ✅
→ inv.move_type == 'out_invoice'              ✅
→ inv.partner_id == buyer                     ✅
→ inv.amount_untaxed == 12000.0 + 100 = 12100 ✅  (200000 * 0.06 + 100)
→ inv.state == 'draft'                        ✅
```

Verified live in the running Odoo 16 instance. Invoice shows 12,100.00 Ft
tax-excluded; total is higher due to Hungarian 27% VAT configured in the
demo database — this does not affect the untaxed assertion.

---

## Task B — `course_catalog` bugs

Five bugs fixed. One per line, file + line + explanation:

1. `models/course.py` line 11 — `"res.user"` → `"res.users"`: Odoo's user
   model is always plural; wrong name caused immediate crash at module load.

2. `models/course.py` line 39 — `@api.depends("enrollment_ids")` →
   `@api.depends("enrollment_ids.amount")`: without dot-notation, the computed
   `total_revenue` only recomputed when enrollments were added/removed, not
   when an existing enrollment's amount was edited — silent wrong data.

3. `security/ir.model.access.csv` line 2 — `model_course_catlog` →
   `model_course_catalog`: one-character typo in the model XML ID; Odoo could
   not resolve the ACL reference and refused to install.

4. `views/course_views.xml` line 16 — `instuctor_id` → `instructor_id`:
   typo in the form view field reference; form view crashed on render because
   the field does not exist on the model.

5. `views/course_views.xml` line 79 — added missing `name="Course Catalog"`
   attribute to the child menuitem; without it the menu entry has no label.

---

## What I did more

- Write a Python test file (`tests/test_estate_account.py`) that runs the
  acceptance-criteria pseudocode as an actual `TransactionCase`.
- Cleaner commit history — currently one commit per phase; would split into
  one commit per logical change in a real project.

---

## Time log

| Phase | Time |
|-------|------|
| Environment setup (Docker, VS Code) | ~45 min |
| Foundation (`estate` module) | ~2 h |
| Task A (`estate_account`) | ~1.5 h |
| Task B (`course_catalog` bugs) | ~45 min |
| NOTES.md + cleanup | ~30 min |
| **Total** | **~5.5 h** |

Went slightly over the 4-hour target due to the XML corruption incident
and the `company_id` debugging session — both documented above.
