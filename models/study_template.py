from datetime import timedelta
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class StudyTemplate(models.Model):
    """
    Modelo para definir las plantillas de estudio clínico.
    """
    _name = 'study.template'
    _description = 'Clinical Study Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(required=True, tracking=True)
    description = fields.Text()
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('completed', 'Completado')
    ], default='draft', tracking=True)
    
    # Configuración básica
    participant_count = fields.Integer(
        string='Número de participantes',
        required=True,
        tracking=True
    )
    professional_count = fields.Integer(
        string='Número de profesionales',
        required=True,
        tracking=True
    )
    sessions_per_week = fields.Integer(
        string='Sesiones por semana',
        required=True,
        tracking=True
    )
    estimated_duration_days = fields.Integer(
        string='Duración estimada (días)',
        compute='_compute_duration',
        store=True
    )
    
    # Requisitos de personal
    required_specialities_ids = fields.Many2many(
        'study.speciality',
        string='Especialidades esperadas',
        tracking=True
    )
    required_experience_years = fields.Integer(
        string='Años de experiencia esperados',
        tracking=True
    )
    
    # Relaciones
    session_type_ids = fields.One2many(
        'study.template.session.type',
        'template_id',
        string='Tipos de sesiones'
    )
    assignment_ids = fields.One2many(
        'study.professional.assignment',
        'template_id',
        string='Asignaciones de profesionales'
    )
    participant_ids = fields.One2many(
        'study.participant',
        'template_id',
        string='Participantes'
    )
    session_ids = fields.One2many(
        'study.session',
        'template_id',
        string='Sesiones'
    )
    
    # Campos computados
    total_sessions = fields.Integer(
        compute='_compute_total_sessions',
        store=True,
        string='Total de sesiones'
    )
    professional_assigned_count = fields.Integer(
        compute='_compute_counts',
        store=True,
        string='Profesionales asignados'
    )
    participant_assigned_count = fields.Integer(
        compute='_compute_counts',
        store=True,
        string='Participantes asignados'
    )
    session_count_real = fields.Integer(
        compute='_compute_counts',
        store=True,
        string='Sesiones programadas'
    )

    # Métodos compute
    @api.depends('session_type_ids.quantity')
    def _compute_total_sessions(self):
        """Calcula el número total de sesiones basado en la configuración de tipos."""
        for record in self:
            record.total_sessions = sum(record.session_type_ids.mapped('quantity'))

    @api.depends('total_sessions', 'sessions_per_week')
    def _compute_duration(self):
        """Calcula la duración estimada en días basada en las sesiones totales y por semana."""
        for record in self:
            if record.sessions_per_week:
                record.estimated_duration_days = int(
                    record.total_sessions / record.sessions_per_week * 7
                )
            else:
                record.estimated_duration_days = 0

    @api.depends('assignment_ids', 'participant_ids', 'session_ids')
    def _compute_counts(self):
        """Calcula estadísticas sobre asignaciones, participantes y sesiones."""
        for record in self:
            record.professional_assigned_count = len(
                record.assignment_ids.filtered(lambda a: a.state == 'assigned')
            )
            record.participant_assigned_count = len(record.participant_ids)
            record.session_count_real = len(record.session_ids)

    def action_activate(self):
        """Activa la plantilla después de validar todas las condiciones necesarias."""
        self.ensure_one()
        self._validate_professional_assignments()
        self._validate_participant_assignments()
        self._validate_sessions()
        self._activate_and_confirm()
        return True

    def _validate_professional_assignments(self):
        """Valida que haya suficientes profesionales asignados."""
        assigned_count = len(self.assignment_ids.filtered(lambda a: a.state == 'assigned'))
        if assigned_count < self.professional_count:
            raise ValidationError(
                f'Se requieren {self.professional_count} profesionales asignados. '
                f'Actualmente hay {assigned_count}.'
            )

    def _validate_participant_assignments(self):
        """Valida que haya participantes y que todos tengan profesional asignado."""
        if not self.participant_ids:
            raise ValidationError('Se requiere al menos un participante antes de activar.')
            
        unassigned = self.participant_ids.filtered(lambda p: not p.professional_id)
        if unassigned:
            raise ValidationError(
                f'Los siguientes participantes no tienen profesional asignado: '
                f'{", ".join(unassigned.mapped("name"))}'
            )

    def _validate_sessions(self):
        """Valida que existan sesiones generadas."""
        if not self.session_ids:
            raise ValidationError(
                'No hay sesiones generadas. Genere y valide el calendario antes de activar.'
            )

    def _activate_and_confirm(self):
        """Activa la plantilla y confirma las sesiones."""
        self.write({'state': 'active'})
        self.session_ids.write({'state': 'confirmed'})
        for session in self.session_ids:
            session._create_calendar_event()

    def calculate_professional_score(self, professional):
        """Calcula la puntuación de idoneidad (0-100) para un profesional."""
        score = 0.0
        score += self._calculate_experience_score(professional)
        score += self._calculate_speciality_score(professional)
        score += self._calculate_workload_score(professional)
        return round(score, 2)

    def _calculate_experience_score(self, professional):
        """Calcula la puntuación basada en experiencia (máx 40%)."""
        if not self.required_experience_years:
            return 40.0
        experience_ratio = professional.years_experience / self.required_experience_years
        return min(40.0 * experience_ratio, 40.0)

    def _calculate_speciality_score(self, professional):
        """Calcula la puntuación basada en especialidades (máx 40%)."""
        if not self.required_specialities_ids:
            return 40.0
        matching = len(set(self.required_specialities_ids.ids) & set(professional.speciality_ids.ids))
        total = len(self.required_specialities_ids)
        return 40.0 * (matching / total)

    def _calculate_workload_score(self, professional):
        """Calcula la puntuación basada en carga de trabajo (máx 20%)."""
        active_participants = len(professional.active_participant_ids)
        reduction = min(active_participants * 5, 20.0)
        return 20.0 - reduction

    def action_assign_professionals(self):
        """Asigna automáticamente los profesionales más adecuados."""
        self.ensure_one()
        professionals = self._get_available_professionals()
        scored_professionals = self._score_professionals(professionals)
        self._create_professional_assignments(scored_professionals)
        return True

    def _get_available_professionals(self):
        """Obtiene la lista de profesionales disponibles."""
        return self.env['study.professional'].search([('state', '=', 'available')])

    def _score_professionals(self, professionals):
        """Calcula y filtra profesionales por puntuación mínima."""
        scored_professionals = []
        for professional in professionals:
            score = self.calculate_professional_score(professional)
            if score >= 60:
                scored_professionals.append((professional, score))
        return sorted(scored_professionals, key=lambda x: x[1], reverse=True)

    def _create_professional_assignments(self, scored_professionals):
        """Crea las asignaciones para los mejores profesionales."""
        if len(scored_professionals) < self.professional_count:
            raise ValidationError(
                'No hay suficientes profesionales calificados disponibles. '
                f'Se requieren {self.professional_count}, encontrados {len(scored_professionals)}'
            )

        Assignment = self.env['study.professional.assignment']
        for professional, score in scored_professionals[:self.professional_count]:
            Assignment.create({
                'template_id': self.id,
                'professional_id': professional.id,
                'state': 'draft'
            })

    def _find_next_available_slot(self, participant, start_date, session_type):
        """
        Encuentra el siguiente horario disponible compatible entre profesional y participante,
        respetando las restricciones de sesiones por semana y días entre sesiones.
        """
        common_days = self._get_common_available_days(participant)
        _logger.info(f'Días comunes encontrados: {common_days.mapped("name")}')
        
        available_slots = self._get_compatible_time_slots(participant)
        _logger.info(f'Slots horarios disponibles: {available_slots}')
        
        Session = self.env['study.session']
        current_date = start_date
        max_attempts = 120

        _logger.info(f'Buscando slots desde {current_date}')
        
        for _ in range(max_attempts):
            # Verificar si el día es compatible
            if not self._is_compatible_day(current_date, common_days):
                current_date += timedelta(days=1)
                continue
                
            # Verificar restricciones semanales
            week_sessions = Session.search([
                ('participant_id', '=', participant.id),
                ('date', '>=', current_date - timedelta(days=current_date.weekday())),
                ('date', '<', current_date - timedelta(days=current_date.weekday()) + timedelta(days=7)),
                ('state', 'not in', ['cancelled'])
            ])
            
            # Verificar límite de sesiones por semana
            if len(week_sessions) >= self.sessions_per_week:
                # Avanzar al inicio de la siguiente semana
                days_to_next_week = 7 - current_date.weekday()
                current_date += timedelta(days=days_to_next_week)
                continue
                
            # Verificar día de separación entre sesiones si hay más de una por semana
            if self.sessions_per_week > 1 and week_sessions:
                latest_session = max(week_sessions.mapped('date'))
                if (current_date - latest_session).days <= 1:
                    current_date += timedelta(days=1)
                    continue
            
            # Verificar disponibilidad en el día actual
            slot = self._check_day_availability(
                participant, current_date, session_type,
                available_slots, Session
            )
            
            if slot:
                _logger.info(f'Slot encontrado: {slot}')
                return slot
            else:
                _logger.info(f'No hay slots disponibles para {current_date}')
                current_date += timedelta(days=1)
        
        _logger.warning(f'No se encontró slot después de {max_attempts} intentos')
        return None
    
    def _get_common_available_days(self, participant):
        """Obtiene los días disponibles comunes entre profesional y participante."""
        prof_days = participant.professional_id.available_days
        part_days = participant.available_days
        common_days = prof_days & part_days
        
        if not common_days:
            raise ValidationError(
                f'No hay días compatibles entre {participant.name} y '
                f'{participant.professional_id.name}'
            )
        return common_days

    def _get_compatible_time_slots(self, participant):
        """Obtiene los horarios compatibles según preferencias."""
        schedule_map = {
            '1': [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0],     # Mañana
            '2': [15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0], # Tarde
            '3': [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0,      # Ambos
                15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0]
        }
        
        prof_slots = schedule_map.get(participant.professional_id.preferred_schedule, [])
        part_slots = schedule_map.get(participant.preferred_schedule, [])
        available_slots = list(set(prof_slots) & set(part_slots))
        available_slots.sort()  # Ordenamos los slots para empezar por las primeras horas
        
        _logger.info(f'Slots prof: {prof_slots}')
        _logger.info(f'Slots part: {part_slots}')
        _logger.info(f'Slots comunes: {available_slots}')
        
        if not available_slots:
            raise ValidationError(
                f'No hay horarios compatibles entre {participant.name} y '
                f'{participant.professional_id.name}'
            )
        return available_slots

    def _search_available_slot(self, participant, start_date, session_type, 
                            common_days, available_slots):
        """Busca un slot disponible dentro de las restricciones dadas."""
        Session = self.env['study.session']
        current_date = start_date
        max_attempts = 30
        
        for _ in range(max_attempts):
            if self._is_compatible_day(current_date, common_days):
                slot = self._check_day_availability(
                    participant, current_date, session_type,
                    available_slots, Session
                )
                if slot:
                    return slot
            current_date += timedelta(days=1)
        return None

    def _is_compatible_day(self, date, common_days):
        """Verifica si una fecha es compatible según los días disponibles."""
        weekday = str(date.weekday() + 1)  # Convertimos a string para comparar con el code
        is_compatible = any(d.code == weekday for d in common_days)
        _logger.info(f'Verificando día {date}: weekday={weekday}, compatible={is_compatible}')
        return is_compatible

    def _check_day_availability(self, participant, current_date, session_type, available_slots, Session):
        """Verifica la disponibilidad en un día específico y busca slots libres."""
        for slot in available_slots:
            if not self._has_conflicts(participant, current_date, slot, session_type, Session):
                return {
                    'date': current_date,
                    'time': slot
                }
            _logger.info(f'Slot {slot}:00 no disponible: conflicto para {participant.name} el {current_date}')
        return None

    def _get_week_sessions(self, participant, current_date, Session):
        """Obtiene las sesiones de la semana actual."""
        week_start = current_date - timedelta(days=current_date.weekday())
        return Session.search([
            ('participant_id', '=', participant.id),
            ('date', '>=', week_start),
            ('date', '<', week_start + timedelta(days=7)),
            ('state', 'not in', ['cancelled', 'rescheduled'])
        ])

    def _has_session_today(self, week_sessions, current_date):
        """Verifica si ya hay una sesión programada para el día."""
        return bool(week_sessions.filtered(lambda s: s.date == current_date))

    def _can_add_session_type(self, participant, session_type, Session):
        """Verifica si se puede añadir más sesiones de este tipo."""
        all_sessions = Session.search([
            ('participant_id', '=', participant.id),
            ('session_type_id', '=', session_type.id),
            ('state', 'not in', ['cancelled', 'rescheduled'])
        ])
        
        type_config = self.session_type_ids.filtered(
            lambda x: x.session_type_id == session_type
        )
        if not type_config:
            raise ValidationError(
                f'Tipo de sesión {session_type.name} no configurado en la plantilla'
            )
        
        return len(all_sessions) < type_config.quantity

    def _find_free_slot(self, participant, current_date, session_type,
                        available_slots, Session):
        """Busca un slot libre en las horas disponibles."""
        for time_slot in available_slots:
            if not self._has_conflicts(
                participant, current_date, time_slot,
                session_type, Session
            ):
                return {
                    'date': current_date,
                    'time': time_slot
                }
        return None

    def _has_conflicts(self, participant, date, time_slot, session_type, Session):
        """
        Verifica si hay conflictos para un slot específico.
        """
        def format_time(decimal_time):
            """Convierte hora decimal a formato HH:MM"""
            hours = int(decimal_time)
            minutes = int((decimal_time % 1) * 60)
            return f"{hours:02d}:{minutes:02d}"

        # Verificar conflictos del profesional
        professional_sessions = Session.search([
            ('professional_id', '=', participant.professional_id.id),
            ('date', '=', date),
            ('state', 'not in', ['cancelled'])
        ])
        
        for session in professional_sessions:
            # Verificar solapamiento teniendo en cuenta medias horas
            session_end = session.time_start + session.duration
            new_session_end = time_slot + session_type.duration
            
            # Añadir un margen de 15 minutos entre sesiones
            if (time_slot < session_end + 0.25 and new_session_end + 0.25 > session.time_start):
                _logger.debug(
                    f'Conflicto profesional: {participant.professional_id.name} '
                    f'tiene sesión de {format_time(session.time_start)} a {format_time(session_end)} '
                    f'el {date}'
                )
                return True
        
        # Verificar conflictos del participante 
        participant_sessions = Session.search([
            ('participant_id', '=', participant.id),
            ('date', '=', date),
            ('state', 'not in', ['cancelled'])
        ])
        
        for session in participant_sessions:
            # Verificar que haya al menos 30 minutos entre sesiones
            session_end = session.time_start + session.duration
            new_session_end = time_slot + session_type.duration
            
            if (time_slot < session_end + 0.5 and new_session_end + 0.5 > session.time_start):
                _logger.debug(
                    f'Conflicto participante: {participant.name} tiene sesión de '
                    f'{format_time(session.time_start)} a {format_time(session_end)} el {date}'
                )
                return True
        
        return False

    def action_generate_sessions(self):
        """Genera las sesiones para todos los participantes."""
        self.ensure_one()
        self._validate_session_generation()
        self.session_ids.unlink()
        
        # Calcular fecha de inicio (7 días desde la activación)
        start_date = fields.Date.today() + timedelta(days=7)
        self._generate_participant_sessions(start_date)
        return True

    def _validate_session_generation(self):
        """Valida las condiciones para generar sesiones."""
        if self.state != 'draft':
            raise ValidationError('Solo se pueden generar sesiones en estado borrador')
        if not self.participant_ids:
            raise ValidationError('No hay participantes para generar sesiones')

    def _generate_participant_sessions(self, start_date):
        """Genera las sesiones para cada participante."""
        for participant in self.participant_ids.filtered(lambda p: p.professional_id):
            self._generate_sessions_for_participant(participant, start_date)

    def _generate_sessions_for_participant(self, participant, start_date):
        """Genera todas las sesiones para un participante específico."""
        current_date = start_date  # Comenzar desde la fecha de inicio
        for session_type_line in self.session_type_ids:
            self._generate_sessions_by_type(participant, session_type_line, current_date)

    def _generate_sessions_by_type(self, participant, session_type_line, start_date):
        """Genera las sesiones de un tipo específico para un participante."""
        for _ in range(session_type_line.quantity):
            slot = self._find_next_available_slot(
                participant,
                start_date,
                session_type_line.session_type_id
            )
            if not slot:
                raise ValidationError(f'No se encontró horario para {participant.name}')
            
            self._create_session(participant, session_type_line.session_type_id, slot)

    def _create_session(self, participant, session_type, slot):
        """Crea una nueva sesión con los datos proporcionados."""
        return self.env['study.session'].create({
            'template_id': self.id,
            'participant_id': participant.id,
            'professional_id': participant.professional_id.id,
            'session_type_id': session_type.id,
            'date': slot['date'],
            'time_start': slot['time'],
            'state': 'scheduled'
        })