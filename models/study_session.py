from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class StudySession(models.Model):
    """
    Modelo para la gestión de sesiones clínicas.
    """
    _name = 'study.session'
    _description = 'Clinical Study Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date, time_start'

    # Campos básicos
    name = fields.Char(compute='_compute_name', store=True)
    date = fields.Date(required=True, tracking=True, string="Fecha")
    time_start = fields.Float(required=True, string="Hora de inicio")
    time_end = fields.Float(compute='_compute_time_end', store=True, string="Hora de finalización",
    help="Hora de finalización calculada automáticamente basada en la hora de inicio "
         "y la duración del tipo de sesión."                        )
    notes = fields.Text()
    state = fields.Selection([
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada')
    ], default='scheduled', tracking=True,
    help="Estado actual de la sesión:\n"
         "- Programada: Sesión planificada pendiente de confirmación\n"
         "- Confirmada: Sesión validada y notificada a los participantes\n"
         "- Completada: Sesión realizada satisfactoriamente\n"
         "- Cancelada: Sesión cancelada y eliminada del calendario")

    # Relaciones
    template_id = fields.Many2one(
        'study.template', 
        required=True, 
        ondelete='cascade',
        string="Plantilla de estudio",
        help="Plantilla de estudio a la que pertenece la sesión."
    )
    session_type_id = fields.Many2one(
        'study.session.type', 
        required=True, 
        ondelete='restrict',
        help="Tipo de sesión que define su duración y características específicas."
    )
    participant_id = fields.Many2one(
        'study.participant', 
        required=True, 
        ondelete='cascade',
        string="Participante",
        help="Participante para quien está programada la sesión."
    )
    professional_id = fields.Many2one(
        'study.professional', 
        required=True, 
        ondelete='cascade',
        string="Profesional",
        help="Profesional asignado para realizar la sesión."
    )
    calendar_event_id = fields.Many2one(
        'calendar.event',
        help="Evento de calendario asociado a esta sesión. Se crea automáticamente "
            "cuando la sesión es confirmada."
    )

    # Campos relacionados
    duration = fields.Float(
        related='session_type_id.duration', 
        readonly=True,
        help="Duración planificada de la sesión en horas, heredada del tipo de sesión. "
            "Se utiliza para calcular la hora de finalización."
    )

    # Métodos compute
    @api.depends('participant_id.name', 'session_type_id.name', 'date')
    def _compute_name(self):
        """Genera un nombre descriptivo para la sesión combinando tipo, participante y fecha."""
        for record in self:
            record.name = (f'{record.session_type_id.name} - {record.participant_id.name} '
                        f'({record.date})') if (record.participant_id and record.session_type_id
                                                and record.date) else 'Nueva Sesión'

    @api.depends('time_start', 'duration')
    def _compute_time_end(self):
        """Calcula la hora de finalización basada en la hora de inicio y duración."""
        for record in self:
            record.time_end = record.time_start + record.duration

    @api.constrains('participant_id', 'date', 'time_start', 'session_type_id')
    def _check_availability(self):
        """Verifica que no existan conflictos de horario para la sesión."""
        for session in self:
            # Verificar ambas disponibilidades de una vez
            for entity in ['professional', 'participant']:
                if session._has_schedule_conflict(entity):
                    raise ValidationError(
                        f'El {entity} ya tiene una sesión programada en ese horario'
                    )

    def _has_schedule_conflict(self, entity_type):
        """
        Verifica si existe conflicto de horario para una entidad.
        
        Args:
            entity_type (str): Tipo de entidad ('professional' o 'participant')
            
        Returns:
            bool: True si existe conflicto, False en caso contrario
        """
        field_name = f'{entity_type}_id'
        entity_id = getattr(self, field_name).id
        
        domain = [
            ('id', '!=', self.id),
            (field_name, '=', entity_id),
            ('date', '=', self.date),
            ('state', 'not in', ['cancelled']),
            '|',
                '&', ('time_start', '>=', self.time_start),
                    ('time_start', '<', self.time_start + self.duration),
                '&', ('time_start', '<=', self.time_start),
                    ('time_end', '>', self.time_start)
        ]
        
        return bool(self.search_count(domain))

    def action_confirm(self):
        """Confirma la sesión y crea su evento de calendario."""
        self.write({'state': 'confirmed'})
        for session in self:
            session._create_calendar_event()

    def action_complete(self):
        """Marca la sesión como completada."""
        self.write({'state': 'completed'})

    def action_cancel(self):
        """Cancela la sesión y elimina su evento de calendario."""
        # Identificar eventos a eliminar antes de cambiar el estado
        events_to_delete = self.mapped('calendar_event_id')
        self.write({'state': 'cancelled', 'calendar_event_id': False})
        events_to_delete.unlink()

    def _create_calendar_event(self):
        """
        Crea un evento de calendario para la sesión.
        
        Returns:
            calendar.event: El evento de calendario creado
        """
        self.ensure_one()
        
        start_dt = datetime.combine(self.date, datetime.min.time()) + timedelta(hours=self.time_start)
        stop_dt = start_dt + timedelta(hours=self.duration)
        
        event = self.env['calendar.event'].create({
            'name': self.name,
            'start': start_dt,
            'stop': stop_dt,
            'duration': self.duration,
            'user_id': self.env.user.id,
            'privacy': 'private'
        })
        
        self.calendar_event_id = event
        return event