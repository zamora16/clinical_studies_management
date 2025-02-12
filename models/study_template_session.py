from odoo import models, fields, api

class StudyTemplateSessionType(models.Model):
    """
    Modelo para configurar las sesiones en una determinada plantilla de estudio.
    """
    _name = 'study.template.session.type'
    _description = 'Template Session Type Configuration'
    _order = 'sequence'

    template_id = fields.Many2one('study.template', required=True, ondelete='cascade')
    session_type_id = fields.Many2one('study.session.type', required=True, ondelete='restrict')
    quantity = fields.Integer(string='Cantidad', required=True, default=1)
    sequence = fields.Integer(string='Secuencia', default=10)

    _sql_constraints = [
        ('template_type_uniq', 
         'unique(template_id, session_type_id)',
         'Cada tipo de sesión solo puede configurarse una vez por plantilla')
    ]