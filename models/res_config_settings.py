from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lead_req_convert_enabled = fields.Boolean(
        string='Aktifkan Validasi Field Wajib saat Convert',
        config_parameter='crm_custom.req_convert_enabled',
    )
    lead_req_prospect_source = fields.Boolean(
        string='Prospect Source',
        config_parameter='crm_custom.req_prospect_source',
    )
    lead_req_est_timeline_start_date = fields.Boolean(
        string='Est. Timeline Start Date',
        config_parameter='crm_custom.req_est_timeline_start_date',
    )
    lead_req_est_timeline_end_date = fields.Boolean(
        string='Est. Timeline End Date',
        config_parameter='crm_custom.req_est_timeline_end_date',
    )
    lead_req_pain_point = fields.Boolean(
        string='Pain Point',
        config_parameter='crm_custom.req_pain_point',
    )
    lead_req_business_impact = fields.Boolean(
        string='Business Impact',
        config_parameter='crm_custom.req_business_impact',
    )
    lead_req_is_decision_maker = fields.Boolean(
        string='Is Decision Maker',
        config_parameter='crm_custom.req_is_decision_maker',
    )
    lead_req_decision_process = fields.Boolean(
        string='Decision Process',
        config_parameter='crm_custom.req_decision_process',
    )
    lead_req_decision_criteria = fields.Boolean(
        string='Decision Criteria',
        config_parameter='crm_custom.req_decision_criteria',
    )
    lead_req_competitors = fields.Boolean(
        string='Competitors',
        config_parameter='crm_custom.req_competitors',
    )
    lead_req_budget = fields.Boolean(
        string='Budget',
        config_parameter='crm_custom.req_budget',
    )