from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.exceptions import UserError

REQUIRED_DMS_FOLDER_NAMES = [
    "Costumer Requirements",
]

STAGE_APPROVAL_FROM = ["Qualified"]
STAGE_APPROVAL_TO = ["Proposition"]

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
    approval_state = fields.Selection(
        [
            ("draft", "Not Requested"),
            ("pending", "Waiting Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Director Approval",
        default="draft",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_by = fields.Many2one("res.users", readonly=True, copy=False)
    approved_date = fields.Datetime(readonly=True, copy=False)
    
    def _stage_matches(self,stage, names):
            return bool(stage) and (stage.name or "").strip().casefold() in [
                n.casefold() for n in names
            ]
    
    def write(self, vals):
        if "stage_id" in vals and not self.env.su:
            new_stage = self.env["crm.stage"].browse(vals["stage_id"])

            if (
                not self.env.context.get("allow_stage_change")
                and not self.env.user.has_group("parametrik_crm.group_business_development")
                and self.filtered(lambda l: l.stage_id != new_stage)
            ):
                raise UserError(
                    "Hanya tim Business Development yang boleh memindahkan stage."
                )

            for lead in self:
                if (
                    lead.stage_id != new_stage
                    and self._stage_matches(lead.stage_id, STAGE_APPROVAL_FROM)
                    and self._stage_matches(new_stage, STAGE_APPROVAL_TO)
                    and lead.approval_state != "approved"
                ):
                    raise UserError(
                        "Lead '%s' butuh approval Director sebelum pindah dari "
                        "Qualified ke Proposition. Klik 'Request Approval' dulu."
                        % lead.display_name
                    )
        if (
            "approval_state" in vals
            and not self.env.su
            and not self.env.context.get("approval_action")
        ):
            raise UserError("Status approval hanya bisa diubah lewat tombol approval.")
        return super().write(vals)
    
    def action_set_won(self):
        return super(CrmLead, self.with_context(allow_stage_change=True)).action_set_won()

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
    
    def _get_missing_dms_folders(self):
        self.ensure_one()
        roots = self.dms_directory_ids
        if not roots:
            return list(REQUIRED_DMS_FOLDER_NAMES)
        Directory = self.env["dms.directory"].sudo()
        File = self.env["dms.file"].sudo()
        lead_dirs = Directory.search([("id", "child_of", roots.ids)])
        missing = []
        for name in REQUIRED_DMS_FOLDER_NAMES:
            folders = lead_dirs.filtered(
                lambda d: (d.name or "").strip().casefold() == name.casefold()
            )
            if not folders or not File.search_count(
                [("directory_id", "child_of", folders.ids)]
            ):
                missing.append(name)
        return missing

    def _check_required_fields_for_convert(self):
        field_names = self._get_required_fields_for_convert()
        errors = []
        for lead in self.filtered(lambda l: l.active and l.type == 'lead'):
            missing = [
                lead._fields[fname].string
                for fname in field_names
                if fname in lead._fields and not lead[fname]
            ]
            for folder_name in lead._get_missing_dms_folders():
                missing.append("File di folder '%s' (tab Documents)" % folder_name)
            if missing:
                errors.append("- %s: %s" % (lead.display_name, ", ".join(missing)))
        if errors:
            raise UserError(
                ("Lengkapi data berikut sebelum convert ke opportunity:\n%s")
                % "\n".join(errors))

    def convert_opportunity(self, partner, user_ids=None, team_id=False):
        self._check_required_fields_for_convert()
        return super(CrmLead, self.with_context(allow_stage_change=True)).convert_opportunity(
            partner, user_ids=user_ids, team_id=team_id
        )

    def action_request_approval(self):
        for lead in self:
            if lead.approval_state not in ("draft", "rejected"):
                raise UserError("Approval sudah diajukan atau sudah disetujui.")
            lead.with_context(approval_action=True).write(
                {"approval_state": "pending"}
            )
            lead.message_post(body="Approval Director diajukan.")
        if not self._stage_matches(lead.stage_id, STAGE_APPROVAL_FROM):
                raise UserError(
                    "Approval hanya bisa diajukan saat lead berada di stage Qualified."
                )
    
    def _check_is_director(self):
        if not self.env.user.has_group("parametrik_crm.group_director"):
            raise UserError("Hanya Director yang boleh menyetujui atau menolak.")
    
    def action_approve(self):
        self._check_is_director()
        self.with_context(approval_action=True).write({
            "approval_state": "approved",
            "approved_by": self.env.user.id,
            "approved_date": fields.Datetime.now(),
        })

    def action_reject(self):
        self._check_is_director()
        self.with_context(approval_action=True).write({
            "approval_state": "rejected",
            "approved_by": self.env.user.id,
            "approved_date": fields.Datetime.now(),
        })
    
    
        
    