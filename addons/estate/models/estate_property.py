from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'id desc'  # Newest first

    # -------------------------------------------------------------------------
    # Basic Fields
    # -------------------------------------------------------------------------
    name = fields.Char(string='Property Name', required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(
        string='Available From',
        default=lambda self: fields.Date.add(fields.Date.today(), months=3),
        copy=False,  # Not copied when duplicating a record
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(copy=False, readonly=True)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(string='Living Area (sqm)')
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West'),
        ]
    )
    active = fields.Boolean(default=True)  # False = archived/hidden
    company_id = fields.Many2one(
    'res.company',
    string='Company',
    default=lambda self: self.env.company,
)
    # State drives the status bar at the top of the form
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled'),
        ],
        required=True,
        default='new',
        copy=False,
    )

    # -------------------------------------------------------------------------
    # Relational Fields
    # -------------------------------------------------------------------------
    property_type_id = fields.Many2one(
        'estate.property.type', string='Property Type'
    )
    buyer_id = fields.Many2one(
        'res.partner',      # res.partner = Odoo's built-in contacts model
        string='Buyer',
        copy=False,
    )
    salesperson_id = fields.Many2one(
        'res.users',        # res.users = Odoo's built-in users model
        string='Salesperson',
        default=lambda self: self.env.user,  # Default = current logged-in user
    )
    tag_ids = fields.Many2many(
        'estate.property.tag', string='Tags'
        # Many2many: a property can have many tags, a tag can belong to many properties
    )
    offer_ids = fields.One2many(
        'estate.property.offer', 'property_id', string='Offers'
    )

    # -------------------------------------------------------------------------
    # Computed Fields (calculated automatically, not stored by user)
    # -------------------------------------------------------------------------
    total_area = fields.Integer(
        string='Total Area (sqm)',
        compute='_compute_total_area',
        # No 'store=True' means it's calculated on the fly, not saved to DB
    )
    best_price = fields.Float(
        string='Best Offer',
        compute='_compute_best_price',
    )

    # -------------------------------------------------------------------------
    # Constraints (database-level — fastest, checked by PostgreSQL)
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'check_expected_price',
            'CHECK(expected_price > 0)',
            'The expected price must be strictly positive.',
        ),
        (
            'check_selling_price',
            'CHECK(selling_price >= 0)',
            'The selling price must be positive.',
        ),
    ]

    # -------------------------------------------------------------------------
    # Compute Methods
    # -------------------------------------------------------------------------
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        # 'self' can be multiple records at once (a "recordset")
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            # mapped() extracts a list of values; max() gets the highest
            record.best_price = max(record.offer_ids.mapped('price'), default=0.0)

    # -------------------------------------------------------------------------
    # Onchange (reacts when user changes a field in the form, before saving)
    # -------------------------------------------------------------------------
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # -------------------------------------------------------------------------
    # Python-level Constraint (more complex logic than SQL can handle)
    # -------------------------------------------------------------------------
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            # Only check if a selling price has been set
            if record.selling_price > 0:
                # Selling price must be >= 90% of expected price
                min_price = record.expected_price * 0.90
                if record.selling_price < min_price:
                    raise ValidationError(
                        'The selling price cannot be lower than 90% of the expected price. '
                        f'Minimum: {min_price:.2f}'
                    )

    # -------------------------------------------------------------------------
    # Action Buttons (called when user clicks buttons in the form)
    # -------------------------------------------------------------------------
    def action_sold(self):
        for record in self:
            if record.state == 'cancelled':
                raise UserError("Cancelled properties cannot be sold.")
            record.state = 'sold'
        return True

    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError("Sold properties cannot be cancelled.")
            record.state = 'cancelled'
        return True