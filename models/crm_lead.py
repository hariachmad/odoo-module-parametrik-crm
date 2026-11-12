from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.exceptions import UserError
from markupsafe import Markup

REQUIRED_DMS_FOLDER_NAMES = [
    "Customer Requirements",
]

REQUIRED_DMS_FOLDER_NAMES_APPROVAL = [
    "Cost Estimation",
    "Presentation File",           
    "Customer Requirements",  
    "Solution Concept",
    "Technical Solution"
]

STAGE_APPROVAL_FROM = ["Qualified","New"]
STAGE_APPROVAL_TO = ["Proposition", "Won"]


class CrmLead(models.Model):
    _inherit = "crm.lead"
    
    CONVERT_REQUIRED_CANDIDATES = [
        'prospect_source', 'est_timeline_start_date', 'est_timeline_end_date',
        'pain_point', 'business_impact', 'is_decision_maker',
        'decision_process', 'decision_criteria', 'competitors', 'budget','champion'
    ]
    
    champion = fields.Many2one(
        comodel_name='res.partner',
        string='Champion',
        domain="[('is_company', '=', False)]",
        help='Champion / internal advocate dari customer',
        tracking=True,
    )
    prospect_source = fields.Selection(
        [
            ("website", "Website"),
            ("referral", "Referral"),
            ("event", "Event"),
            ("other", "Other"),
        ],
        string="Prospect Source",
    )
    est_timeline_start_date = fields.Datetime(
        string="Estimated Timeline Start Date",
        help="Estimated timeline start date",
    )
    est_timeline_end_date = fields.Datetime(
        string="Estimated Timeline End Date",
        help="Estimated timeline End date",
    )
    pain_point = fields.Text(
        string="Pain Point",
        help="What problem is the customer currently experiencing that makes them need our solution?",
    )
    business_impact = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Business Impact",
        help="How important is this project to customer's business",
    )
    is_decision_maker = fields.Boolean(
        string="Is Decision Maker",
        help="Check if this contact is the decision maker"
    )
    decision_process = fields.Text(
        string="Decision Process",
        help="How does the customer make purchasing decisions, and what steps must be completed before they agree to buy our product or service"
    )
    decision_criteria = fields.Text(
        string="Decision Criteria",
        help="What criteria must be met for the customer to buy our product or service"
    )
    competitors = fields.Text(
        string="Competitors",
        help="List of competitors"
    )
    budget = fields.Monetary(
        string="Estimated Budget",
        currency_field="company_currency",
        help="Estimated budget for this project from customer",
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
    
    reject_reason = fields.Text(
    string="Rejection Reason",
    readonly=True,
    copy=False,
    tracking=True,
    help="Alasan penolakan approval",
    )

    rejected_by = fields.Many2one(
        'res.users',
        string="Rejected By",
        readonly=True,
        copy=False,
        tracking=True,
    )

    rejected_date = fields.Datetime(
        string="Rejected On",
        readonly=True,
        copy=False,
        tracking=True,
    )
    
    approved_by = fields.Many2one("res.users", readonly=True, copy=False)
    approved_date = fields.Datetime(readonly=True, copy=False)  
    
    is_my_lead = fields.Boolean(compute='_compute_is_my_lead')

    @api.depends_context('uid')
    def _compute_is_my_lead(self):
        user = self.env.user
        is_exempt = user.has_group('parametrik_crm.group_director')
        for lead in self:
            lead.is_my_lead = (
                is_exempt
                or not lead.id
                or lead.user_id == user
            )  

    def _stage_matches(self, stage, names):
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
                    "Only the Business Development team is allowed to move stages."
                )

            for lead in self:
                if (
                    lead.stage_id != new_stage
                    and self._stage_matches(lead.stage_id, STAGE_APPROVAL_FROM)
                    and self._stage_matches(new_stage, STAGE_APPROVAL_TO)
                    and lead.approval_state != "approved"
                ):
                    raise UserError(
                        "Lead '%s' requires Director approval before moving from "
                        "Qualified to Proposition. Please click 'Request Approval' first."
                        % lead.display_name
                    )
        if (
            "approval_state" in vals
            and not self.env.su
            and not self.env.context.get("approval_action")
        ):
            raise UserError("The approval status can only be changed via the approval buttons.")
        return super().write(vals)

    def action_set_won(self):
        return super(CrmLead, self.with_context(allow_stage_change=True)).action_set_won()

    @api.constrains('est_timeline_start_date', 'est_timeline_end_date')
    def _check_timeline_dates(self):
        for record in self:
            now = datetime.now()
            if record.est_timeline_start_date and record.est_timeline_start_date < now:
                raise ValidationError("Start date cannot be earlier than the current time.")
            if record.est_timeline_end_date and record.est_timeline_end_date < now:
                raise ValidationError("End date cannot be earlier than the current time.")
            if (record.est_timeline_start_date and record.est_timeline_end_date and
                    record.est_timeline_end_date < record.est_timeline_start_date):
                raise ValidationError("End date must be greater than or equal to Start date.")

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

    def _get_missing_dms_folders(self, folder_names=None):
        self.ensure_one()
        folder_names = folder_names or REQUIRED_DMS_FOLDER_NAMES
        roots = self.dms_directory_ids
        if not roots:
            return list(folder_names)
        Directory = self.env["dms.directory"].sudo()
        File = self.env["dms.file"].sudo()
        lead_dirs = Directory.search([("id", "child_of", roots.ids)])
        missing = []
        for name in folder_names:
            folders = lead_dirs.filtered(
                lambda d: (d.name or "").strip().casefold() == name.casefold()
            )
            if not folders or not File.search_count(
                [("directory_id", "child_of", folders.ids)]
            ):
                missing.append(name)
        return missing
    
    def _check_required_dms_for_approval(self):
        errors = []
        for lead in self:
            missing = lead._get_missing_dms_folders(REQUIRED_DMS_FOLDER_NAMES_APPROVAL)
            if missing:
                errors.append(
                    "- %s: %s" % (
                        lead.display_name,
                        ", ".join("File in folder '%s'" % m for m in missing),
                    )
                )
        if errors:
            raise UserError(
                "Please upload files in the following DMS folders (Documents tab) "
                "before requesting approval:\n%s" % "\n".join(errors)
            )

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
                missing.append("File in folder '%s' (Documents tab)" % folder_name)
            if missing:
                errors.append("- %s: %s" % (lead.display_name, ", ".join(missing)))
        if errors:
            raise UserError(
                ("Please complete the following data before converting to an opportunity:\n%s")
                % "\n".join(errors))

    def convert_opportunity(self, partner, user_ids=None, team_id=False):
        self._check_required_fields_for_convert()
        return super(CrmLead, self.with_context(allow_stage_change=True)).convert_opportunity(
            partner, user_ids=user_ids, team_id=team_id
        )

    def action_request_approval(self):
        self._check_required_dms_for_approval()
        director_group = self.env.ref("parametrik_crm.group_director")
        directors = director_group.users.filtered(lambda u: u.active)
        if not directors:
            raise UserError("There is no user in the Director group yet.")

        director_partners = directors.partner_id.filtered(lambda p: p.email)
        if not director_partners:
            raise UserError("No director has a valid email address.")
        
        template = self.env.ref("parametrik_crm.email_template_approval_request")

        for lead in self:
            if lead.approval_state not in ("draft", "rejected"):
                raise UserError("Approval has already been requested or approved.")
            if not self._stage_matches(lead.stage_id, STAGE_APPROVAL_FROM):
                raise UserError(
                    "Approval can only be requested when the lead is in the "
                    "Qualified or New stage."
                )

            lead.with_context(approval_action=True).write({
                "approval_state": "pending",
                "reject_reason": False,
                "rejected_by": False,
                "rejected_date": False,
            })

            lead.message_post(
                body=Markup("<b>{user}</b> requested Director approval for {link}. Please review.").format(
                    user=self.env.user.name,
                    link=lead._get_html_link(),
                ),
                partner_ids=directors.partner_id.ids,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
            
            template.send_mail(
            lead.id,
            force_send=True,
            email_values={
                "recipient_ids": [(6, 0, director_partners.ids)],
                "email_to": ",".join(director_partners.mapped("email")),
            },
        )

            for director in directors:
                lead.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=director.id,
                    summary="Approval Opportunity",
                    note="Please approve or reject this opportunity.",
                    date_deadline=fields.Date.today(),
                )
        return True

    def _check_is_director(self):
        if not self.env.user.has_group("parametrik_crm.group_director"):
            raise UserError("Only a Director can approve or reject.")

    def action_approve(self):
        self._check_is_director()
        self.with_context(approval_action=True).write({
            "approval_state": "approved",
            "approved_by": self.env.user.id,
            "approved_date": fields.Datetime.now(),
            "reject_reason": False,
            "rejected_by": False,
            "rejected_date": False,
        })
        for lead in self:
            lead.activity_feedback(["mail.mail_activity_data_todo"])
            lead.message_post(
                body=Markup("Approved by <b>{user}</b>.").format(user=self.env.user.name),
                subtype_xmlid="mail.mt_note",
            )

    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Approval',
            'res_model': 'crm.lead.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lead_id': self.id, 'active_id': self.id},
        }