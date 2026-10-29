from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    prospect_source = fields.Selection(
        [
            ("website", "Website"),
            ("referral", "Referral"),
            ("event", "Event"),
            ("other", "Other"),
        ],
        string="Prospect Source",
    )
    CONVERT_REQUIRED_CANDIDATES = [
    'prospect_source', 'est_timeline_start_date', 'est_timeline_end_date',
    'pain_point', 'business_impact', 'is_decision_maker',
    'decision_process', 'decision_criteria', 'competitors','budget'
]
    est_timeline_start_date = fields.Datetime()
    est_timeline_end_date = fields.Datetime()
    pain_point = fields.Text()
    business_impact = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Business Impact",
    )
    is_decision_maker = fields.Boolean(
    string="Is Decision Maker",
    help="Tandai jika contact ini adalah pengambil keputusan"
    )
    decision_process = fields.Text()
    decision_criteria = fields.Text()
    competitors = fields.Text()
    budget = fields.Monetary(
    string="Budget",
    currency_field="company_currency",
)

    @api.constrains('est_timeline_start_date', 'est_timeline_end_date')
    def _check_timeline_dates(self):
        for record in self:
            now = datetime.now()
            if record.est_timeline_start_date and record.est_timeline_start_date < now:
                raise ValidationError("Start date tidak boleh kurang dari waktu sekarang.")
            if record.est_timeline_end_date and record.est_timeline_end_date < now:
                raise ValidationError("End date tidak boleh kurang dari waktu sekarang.")
            if (record.est_timeline_start_date and record.est_timeline_end_date and
                record.est_timeline_end_date < record.est_timeline_start_date):
                raise ValidationError("End date harus lebih besar atau sama dengan Start date.")
    
    def _get_required_fields_for_convert(self):
        params = self.env['ir.config_parameter'].sudo().search(
            [('key', '=like', 'crm_custom.req_%')]
        )
        enabled = {p.key for p in params if p.value}

        if 'crm_custom.req_convert_enabled' not in enabled:
            return []

        return [
            field_name
            for field_name in self.CONVERT_REQUIRED_CANDIDATES
            if 'crm_custom.req_%s' % field_name in enabled
        ]

    def _check_required_fields_for_convert(self):
        field_names = self._get_required_fields_for_convert()
        errors = []
        for lead in self.filtered(lambda l: l.active and l.type == 'lead'):
            missing = [
                lead._fields[fname].string
                for fname in field_names
                if fname in lead._fields and not lead[fname]
            ]
            if missing:
                errors.append("- %s: %s" % (lead.display_name, ", ".join(missing)))
        if errors:
            raise UserError(
                ("Lengkapi data berikut sebelum convert ke opportunity:\n%s")
                % "\n".join(errors)
            )

    def convert_opportunity(self, partner, user_ids=None, team_id=False):
        self._check_required_fields_for_convert()
        return super().convert_opportunity(partner, user_ids=user_ids, team_id=team_id)

        
    