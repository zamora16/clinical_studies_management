from odoo import models, fields

class StudySpeciality(models.Model):
    """
    Modelo para gestionar las especialidades de los profesionales.
    """
    _name = 'study.speciality'
    _description = 'Clinical Study Speciality'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')