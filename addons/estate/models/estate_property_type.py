from odoo import fields, models

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'name'  # Always sorted by name alphabetically

    name = fields.Char(required=True)

    # One type can have many properties (e.g. many "House" properties)
    property_ids = fields.One2many(
        'estate.property', 'property_type_id', string='Properties'
    )


# Concept: One2many vs Many2one
# Many2one: "This property belongs to ONE type." (foreign key)
# One2many: "This type has MANY properties." (reverse of Many2one)
# They always come in pairs.
