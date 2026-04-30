from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # This field links an invoice back to the property that generated it.
    # Without this, we'd have no way to find "all invoices for property X".
    estate_property_id = fields.Many2one(
        comodel_name='estate.property',
        string='Estate Property',
        copy=False,
    )