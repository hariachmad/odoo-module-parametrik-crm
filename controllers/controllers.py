# from odoo import http


# class ParametrikCrm(http.Controller):
#     @http.route('/parametrik_crm/parametrik_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/parametrik_crm/parametrik_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('parametrik_crm.listing', {
#             'root': '/parametrik_crm/parametrik_crm',
#             'objects': http.request.env['parametrik_crm.parametrik_crm'].search([]),
#         })

#     @http.route('/parametrik_crm/parametrik_crm/objects/<model("parametrik_crm.parametrik_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('parametrik_crm.object', {
#             'object': obj
#         })

