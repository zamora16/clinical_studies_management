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
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        participants = self.env['study.participant'].browse(active_ids)
        
        for participant in participants:
            participant.write({
                'template_id': self.template_id.id,
                'state': 'draft'
            })
            
        return {'type': 'ir.actions.act_window_close'}