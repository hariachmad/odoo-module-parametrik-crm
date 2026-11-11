from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_my_contact = fields.Boolean(compute='_compute_is_my_contact')

    @api.depends_context('uid')
    def _compute_is_my_contact(self):
        user = self.env.user
        is_exempt = user.has_group('parametrik_crm.group_director')
        for partner in self:
            partner.is_my_contact = (
                is_exempt
                or not partner.id
                or partner.user_id == user
                or user.partner_id == partner
            )