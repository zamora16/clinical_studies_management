
from odoo import models, fields


class StudySessionType(models.Model):
    """
    Modelo para definir los tipos de sesión de los estudios clínicos.
    """
    _name = 'study.session.type'
    _description = 'Clinical Study Session Type'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    duration = fields.Float(string='Duración', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El nombre del tipo de sesión debe ser único')
    ]