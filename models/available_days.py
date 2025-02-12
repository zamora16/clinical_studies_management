from odoo import models, fields

class AvailableDays(models.Model):
    """
    Modelo para gestionar los días disponibles de profesionales y participantes
    """
    _name = 'available.days'
    _description = 'Día Disponible'

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Código', required=True)
    sequence = fields.Integer('Secuencia', default=10)