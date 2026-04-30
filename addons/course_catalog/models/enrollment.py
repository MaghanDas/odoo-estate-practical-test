from odoo import fields, models


class Enrollment(models.Model):
    _name = "course.enrollment"
    _description = "Course Enrollment"

    course_id = fields.Many2one(
        "course.catalog",
        required=True,
        ondelete="cascade",
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        string="Student",
    )
    amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        related="course_id.currency_id",
        store=True,
        readonly=True,
    )
    enrolled_on = fields.Date(default=fields.Date.context_today)
