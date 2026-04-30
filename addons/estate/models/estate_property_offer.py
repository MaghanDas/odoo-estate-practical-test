from odoo import api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Real Estate Property Offer'
    _order = 'price desc'  # Highest offer shown first

    price = fields.Float()
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        copy=False,
    )
    partner_id = fields.Many2one('res.partner', string='Buyer', required=True)
    property_id = fields.Many2one('estate.property', required=True)

    # Deadline = creation date + validity days
    validity = fields.Integer(string='Validity (days)', default=7)
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',  # Allows user to edit the deadline directly
        store=True,
    )

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for offer in self:
            base = offer.create_date.date() if offer.create_date else fields.Date.today()
            offer.date_deadline = fields.Date.add(base, days=offer.validity)

    def _inverse_date_deadline(self):
        # When user edits deadline directly, recalculate validity days
        for offer in self:
            base = offer.create_date.date() if offer.create_date else fields.Date.today()
            offer.validity = (offer.date_deadline - base).days

    def action_accept(self):
        for offer in self:
            # Only one offer can be accepted per property
            if offer.property_id.state == 'offer_accepted':
                raise UserError("An offer has already been accepted for this property.")
            offer.status = 'accepted'
            # Set the property's buyer and selling price from this offer
            offer.property_id.buyer_id = offer.partner_id
            offer.property_id.selling_price = offer.price
            offer.property_id.state = 'offer_accepted'
        return True

    def action_refuse(self):
        for offer in self:
            offer.status = 'refused'
        return True

    @api.model
    def create(self, vals):
        # When a new offer is created, update property state
        property_rec = self.env['estate.property'].browse(vals.get('property_id'))
        if vals.get('price', 0) < property_rec.best_price:
            raise UserError(
                f"The offer price ({vals.get('price')}) cannot be lower than "
                f"the existing best offer ({property_rec.best_price})."
            )
        property_rec.state = 'offer_received'
        return super().create(vals)