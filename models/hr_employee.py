from odoo import models, api, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hours_per_day = fields.Float(related='resource_calendar_id.hours_per_day', store=True)