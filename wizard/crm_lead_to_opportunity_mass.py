from odoo import models, _
from odoo.exceptions import UserError


class CrmLead2opportunityPartnerMass(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    def _get_required_lead_fields(self):
        return ['prospect_source', 'est_timeline_start_date', 'est_timeline_end_date', 'pain_point', 'business_impact', 'is_decision_maker', 'decision_process','decision_criteria','competitors']

    def _check_required_lead_fields(self):
        self.ensure_one()
        Lead = self.env['crm.lead']
        field_names = self._get_required_lead_fields()

        leads = self.lead_tomerge_ids
        if self.name == 'convert_and_merge':
            leads |= self.duplicated_lead_ids
        leads = leads.filtered(lambda l: l.active and l.type == 'lead')

        errors = []
        for lead in leads:
            missing = [
                Lead._fields[fname].string
                for fname in field_names
                if not lead[fname]
            ]
            if missing:
                errors.append("- %s: %s" % (lead.display_name, ", ".join(missing)))

        if errors:
            raise UserError(_(
                "Lengkapi data berikut sebelum convert ke opportunity:\n%s",
                "\n".join(errors),
            ))

    def action_apply(self):
        self._check_required_lead_fields()
        return super().action_apply()