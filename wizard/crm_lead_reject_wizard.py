from odoo import models, fields, api
from odoo.exceptions import UserError
from markupsafe import Markup


class CrmLeadRejectWizard(models.TransientModel):
    _name = 'crm.lead.reject.wizard'
    _description = 'Reject Lead Approval Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise UserError("Rejection reason is required.")
        self.lead_id.with_context(approval_action=True).write({
            'approval_state': 'rejected',
            'reject_reason': self.reason,
            'rejected_by': self.env.user.id,
            'rejected_date': fields.Datetime.now(),
            'approved_by': False,
            'approved_date': False,
        })
        self.lead_id.activity_feedback(["mail.mail_activity_data_todo"])
        self.lead_id.message_post(
            body=Markup("Rejected by <b>{user}</b>.<br/>Reason: {reason}").format(
                user=self.env.user.name, reason=self.reason,
            ),
            subtype_xmlid="mail.mt_note",
        )
        return {'type': 'ir.actions.act_window_close'}