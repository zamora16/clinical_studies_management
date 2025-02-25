from odoo import models, api

class ProfessionalReport(models.AbstractModel):
    _name = 'report.clinical_studies_management.professional_report_document'
    _description = 'Parser para el reporte de profesionales'

    @api.model
    def _get_report_values(self, docids, data=None):
        
        # Si tenemos docids directamente, los usamos
        if docids:
            professionals = self.env['study.professional'].browse(docids)
            data = data or {}
        # Si no, los obtenemos del diccionario
        elif data and data.get('ids'):
            professionals = self.env['study.professional'].browse(data['ids'])
        else:
            professionals = self.env['study.professional']
        
        # Obtener opciones del reporte
        report_options = data.get('form', {}) if data else {}
        
        return {
            'doc_ids': docids or [],
            'doc_model': data and data.get('model') or 'study.professional',
            'professionals': professionals,
            'options': report_options,
            'get_schedule_name': self._get_schedule_name,
        }
        
    def _get_schedule_name(self, code):
        """Convertir código de horario a nombre"""
        schedule_names = {
            '1': 'Mañana',
            '2': 'Tarde',
            '3': 'Ambos',
        }
        return schedule_names.get(code, '')