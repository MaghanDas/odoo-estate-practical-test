from odoo import fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = 'estate.property'   # Extend — NOT create new

    # ------------------------------------------------------------------
    # New fields added to estate.property by this module
    # ------------------------------------------------------------------

    # One property can generate multiple invoices (though in practice: one)
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='estate_property_id',
        string='Invoices',
    )

    # Computed count — used by the smart button to show the number
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count',
    )

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    # ------------------------------------------------------------------
    # Override action_sold to inject invoice creation
    # ------------------------------------------------------------------

    def action_sold(self):
        # Guard 1: must have a buyer (offer must be accepted first)
        for record in self:
            if not record.buyer_id:
                raise UserError(
                    "This property has no buyer. "
                    "Please accept an offer before marking it as Sold."
                )

        # Guard 2: idempotency — don't create a second invoice if already sold
        for record in self:
            if record.state == 'sold':
                raise UserError(
                    f"'{record.name}' is already Sold. "
                    "No duplicate invoice will be created."
                )

        # Call the ORIGINAL action_sold from the estate module
        # This is what actually changes state to 'sold'
        result = super().action_sold()

        # Now create an invoice for each property being sold
        for record in self:
            record._create_invoice()

        return result

    # ------------------------------------------------------------------
    # Invoice creation logic
    # ------------------------------------------------------------------

    def _create_invoice(self):
        """Create a draft customer invoice with commission + admin fee."""
        self.ensure_one()

        # Use the current user's active company
        company = self.env.company

        # Find the sales journal for this company
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', company.id),
        ], limit=1)

        if not journal:
            raise UserError(
                f"No sales journal found for '{company.name}'. "
                "Please configure one in Accounting › Configuration › Journals."
            )

        # Get income account from the journal
        income_account = journal.default_account_id

        if not income_account:
            raise UserError(
                "The sales journal has no default income account set. "
                "Please configure it in Accounting › Configuration › Journals."
            )

        # Calculate amounts
        commission = self.selling_price * 0.06
        admin_fee = 100.00

        # Create the invoice
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.buyer_id.id,
            'journal_id': journal.id,
            'company_id': company.id,
            'estate_property_id': self.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': f'Commission (6%) — {self.name}',
                    'quantity': 1.0,
                    'price_unit': commission,
                    'account_id': income_account.id,
                }),
                (0, 0, {
                    'name': 'Administrative Fee',
                    'quantity': 1.0,
                    'price_unit': admin_fee,
                    'account_id': income_account.id,
                }),
            ],
        })
    # ------------------------------------------------------------------
    # Smart button action — opens related invoices
    # ------------------------------------------------------------------

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('estate_property_id', '=', self.id)],
        }