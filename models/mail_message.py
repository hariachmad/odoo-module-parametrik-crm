from odoo import api, fields, models


class MailMessage(models.Model):
    _inherit = 'mail.message'

    crm_lead_user_id = fields.Many2one(
        'res.users', string='Lead Salesperson',
        compute='_compute_crm_lead_user_id', store=True, index=True,
    )

    @api.depends('model', 'res_id')
    def _compute_crm_lead_user_id(self):
        for msg in self:
            user = False
            if msg.model == 'crm.lead' and msg.res_id:
                lead = self.env['crm.lead'].sudo().browse(msg.res_id).exists()
                user = lead.user_id.id
            msg.crm_lead_user_id = user 