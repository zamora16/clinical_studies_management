# -*- coding: utf-8 -*-
# from odoo import http


# class ClinicalStudiesManagement(http.Controller):
#     @http.route('/clinical_studies_management/clinical_studies_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/clinical_studies_management/clinical_studies_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('clinical_studies_management.listing', {
#             'root': '/clinical_studies_management/clinical_studies_management',
#             'objects': http.request.env['clinical_studies_management.clinical_studies_management'].search([]),
#         })

#     @http.route('/clinical_studies_management/clinical_studies_management/objects/<model("clinical_studies_management.clinical_studies_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('clinical_studies_management.object', {
#             'object': obj
#         })
