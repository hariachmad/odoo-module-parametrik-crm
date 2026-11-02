from odoo import fields, models


class LeadRequiredField(models.Model):
    _name = 'crm.lead.required.field'
    _description = 'Required Fields for Lead Conversion'

    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        required=True,
        ondelete='cascade',
        domain="[('model', '=', 'crm.lead'), ('store', '=', True)]",
    )
    is_required = fields.Boolean(string='Required', default=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('field_company_uniq', 'unique(field_id, company_id)',
         'This field already exists in the configuration.'),
    ]