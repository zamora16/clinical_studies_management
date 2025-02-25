from odoo import models, fields, api

class AssignTemplateWizard(models.TransientModel):
    _name = 'assign.template.wizard'
    _description = 'Asignar Plantilla a Participantes'

    template_id = fields.Many2one('study.template', 
        string='Plantilla', 
        required=True,
        domain="[('state', '=', 'draft')]"
    )

    def action_assign_template(self):
        participants = self.env['study.participant'].search([
            ('id', 'in', self._context.get('active_ids', []))
        ])
        
        participants.write({
            'template_id': self.template_id.id,
            'state': 'draft'
        })
            
        return {'type': 'ir.actions.act_window_close'}
