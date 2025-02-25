from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class StudyParticipant(models.Model):
    """
    Modelo para gestionar los participantes.
    """
    _name = 'study.participant'
    _description = 'Participante de Estudio'

    @api.model
    def _valid_field_parameter(self, field, name):
        # Añadir 'multiple' como parámetro válido
        return name == 'multiple' or super()._valid_field_parameter(field, name)

    # Campos básicos
    name = fields.Char('Nombre', required=True, tracking=True)
    surname = fields.Char('Apellidos', required=True, tracking=True)
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Teléfono', tracking=True)

    # Campos relacionados con el estudio
    template_id = fields.Many2one(
        'study.template', 
        string='Plantilla',
        ondelete='cascade',
        help="Plantilla de estudio a la que está asignado el participante. Define el protocolo y estructura del estudio."
    )
    professional_id = fields.Many2one(
        'study.professional',
        string='Profesional asignado',
        ondelete='cascade',
        help="Profesional responsable del seguimiento del participante durante el estudio."
    )

    available_days = fields.Many2many(
        'available.days', 
        string='Días Disponibles',
        tracking=True,
        required=True,
        help="Días de la semana en los que el participante está disponible para sesiones. "
            "Es importante para la programación automática del calendario."
    )

    preferred_schedule = fields.Selection([
        ('1', 'Mañana'),
        ('2', 'Tarde'),
        ('3', 'Ambos')
    ], 
        string="Horario preferido", 
        required=True, 
        tracking=True,
        help="Preferencia horaria del participante para las sesiones:\n"
            "- Mañana: 8:00 - 13:00\n"
            "- Tarde: 15:00 - 19:00\n"
            "- Ambos: Disponible en ambas franjas"
    )

    # Campos relacionados con sesiones
    session_ids = fields.One2many(
        'study.session', 
        'participant_id', 
        string='Sesiones',
        help="Lista de todas las sesiones programadas para este participante."
    )

    sessions_completed = fields.Integer(
        compute='_compute_sessions_stats', 
        store=True,
        string='Sesiones completadas',
        help="Número total de sesiones que ya han sido realizadas y marcadas como completadas."
    )

    sessions_pending = fields.Integer(
        compute='_compute_sessions_stats', 
        store=True,
        string='Sesiones pendientes',
        help="Número de sesiones que aún están pendientes de realizar."
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente de asignación'),
        ('active', 'Activo'),
        ('completed', 'Completado')
    ], 
        default='draft', 
        tracking=True, 
        string='Estado',
        help="Estado actual del participante en el estudio:\n"
            "- Borrador: Recién creado, pendiente de configuración\n"
            "- Pendiente de asignación: Esperando asignación de profesional\n"
            "- Activo: Participando activamente en el estudio\n"
            "- Completado: Ha finalizado todas las sesiones del estudio"
    )


    partner_id = fields.Many2one(
        'res.partner',
        string='Partner asociado',
        required=True,
        ondelete='cascade',
        auto_join=True,
    )


    @api.model_create_multi
    def create(self, vals_list):
        """Crear partner automáticamente si no existe"""
        Partner = self.env['res.partner']
        for vals in vals_list:
            if not vals.get('partner_id'):
                partner = Partner.create({
                    'name': f"{vals.get('name', '')} {vals.get('surname', '')}",
                    'email': vals.get('email'),
                    'phone': vals.get('phone'),
                    'type': 'other',
                })
                vals['partner_id'] = partner.id
        return super().create(vals_list)

    @api.depends('session_ids.state')
    def _compute_sessions_stats(self):
        for record in self:
            completed = len(record.session_ids.filtered(lambda s: s.state == 'completed'))
            total = len(record.session_ids)
            record.sessions_completed = completed
            record.sessions_pending = total - completed

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Clear professional when template changes"""
        self.professional_id = False

    @api.constrains('professional_id', 'template_id')
    def _check_professional_template(self):
        """Ensure professional is assigned to participant's template"""
        for participant in self.filtered(lambda p: p.professional_id and p.template_id):
            if not participant.professional_id.assignment_ids.filtered(
                lambda a: a.template_id == participant.template_id and a.state == 'assigned'
            ):
                raise ValidationError(
                    'El profesional debe estar asignado a la plantilla del participante'
                )


    def action_assign_professional(self):
        """Asigna el profesional más compatible basado en horario y carga de trabajo"""
        self.ensure_one()
        
        # Buscar profesionales asignados al estudio
        professionals = self.env['study.professional'].search([
            ('assignment_ids.template_id', '=', self.template_id.id),
            ('assignment_ids.state', '=', 'assigned')
        ])
        if not professionals:
            raise ValidationError('No hay profesionales asignados al estudio')

        # Obtener el profesional con mayor afinidad
        best_professional = max(professionals, 
                            key=lambda p: p.calculate_participant_affinity(self))
        
        if best_professional.calculate_participant_affinity(self) < 50:
            raise ValidationError(
                'No se encontró un profesional compatible. '
                f'La mejor puntuación fue {best_professional.calculate_participant_affinity(self):.0f}/100'
            )

        self.write({
            'professional_id': best_professional.id,
            'state': 'active'
        })
        return True

    def _generate_sessions(self):
        """Genera calendario optimizado de sesiones"""
        if not self.professional_id:
            raise ValidationError('Se requiere un profesional asignado')

        # Obtener días compatibles
        common_days = self.professional_id.available_days & self.available_days
        if not common_days:
            raise ValidationError('No hay días compatibles')
        
        # Obtener horarios compatibles
        schedule_map = {
            '1': range(8, 13),     # Mañana
            '2': range(15, 19),    # Tarde
            '3': list(range(8, 13)) + list(range(15, 19))  # Ambos
        }
        
        available_slots = set(schedule_map[self.professional_id.preferred_schedule]) & \
                        set(schedule_map[self.preferred_schedule])
        
        if not available_slots:
            raise ValidationError('No hay horarios compatibles')
            
    def action_bulk_assign_professionals(self):
        """Asignar profesionales a múltiples participantes"""
        if not self:
            raise ValidationError('No hay participantes seleccionados')
            
        for participant in self:
            try:
                participant.action_assign_professional()
            except ValidationError as e:
                _logger.error(f'Error asignando profesional a {participant.name}: {str(e)}')
                continue
                
        return True
    

    def action_bulk_assign_template(self):
        """Aignar plantilla a múltiples participantes"""
        if not self:
            raise ValidationError('No hay participantes seleccionados')
            
        return {
            'name': 'Asignar Plantilla',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.template.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_ids': self.ids,
            }
        }