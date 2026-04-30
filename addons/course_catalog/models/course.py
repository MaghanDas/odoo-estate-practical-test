from odoo import api, fields, models


class Course(models.Model):
    _name = "course.catalog"
    _description = "Course"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    instructor_id = fields.Many2one("res.users", string="Instructor")
    description = fields.Text()
    price = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    enrollment_ids = fields.One2many(
        "course.enrollment",
        "course_id",
        string="Enrollments",
    )
    enrollment_count = fields.Integer(
        compute="_compute_enrollment_count",
        store=True,
    )
    total_revenue = fields.Monetary(
        compute="_compute_total_revenue",
        store=True,
    )

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for course in self:
            course.enrollment_count = len(course.enrollment_ids)

    @api.depends("enrollment_ids.amount")
    def _compute_total_revenue(self):
        for course in self:
            course.total_revenue = sum(course.enrollment_ids.mapped("amount"))
