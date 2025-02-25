from odoo import models, fields

class ProfessionalReportWizard(models.TransientModel):
    _name = 'professional.report.wizard'
    _description = 'Asistente para generar reporte de profesional'

    include_personal_info = fields.Boolean('Información Personal', default=True)
    include_specialities = fields.Boolean('Especialidades', default=True)
    include_experience = fields.Boolean('Experiencia', default=True)
    include_availability = fields.Boolean('Disponibilidad', default=True)
    include_statistics = fields.Boolean('Estadísticas', default=True)
    include_participants = fields.Boolean('Participantes Activos', default=True)

    def action_print_report(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        data = {
            'ids': active_ids,
            'model': 'study.professional',
            'form': {
                'include_personal_info': self.include_personal_info,
                'include_specialities': self.include_specialities,
                'include_experience': self.include_experience,
                'include_availability': self.include_availability,
                'include_statistics': self.include_statistics,
                'include_participants': self.include_participants,
            }
        }
        return self.env.ref('clinical_studies_management.action_report_professional_print').report_action(self.env['study.professional'].browse(active_ids), data=data)