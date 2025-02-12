from odoo import models, fields, api

class StudyProfessional(models.Model):
    """
    Modelo para gestionar los profesionales.
    """
    _name = 'study.professional'
    _description = 'Profesional de Estudio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _valid_field_parameter(self, field, name):
        return name == 'multiple' or super()._valid_field_parameter(field, name)

    # Información personal
    name = fields.Char('Nombre', required=True, tracking=True)
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Teléfono', tracking=True)

    # Información profesional
    speciality_ids = fields.Many2many(
        'study.speciality',
        string='Especialidades',
        tracking=True,
        help="Especialidades del profesional. Se utilizan para determinar "
            "la compatibilidad con los estudios."
    )
    years_experience = fields.Integer(
        string='Años de experiencia',
        tracking=True,
        help="Años de experiencia profesional. Este valor se utiliza "
            "para calcular la puntuación de compatibilidad con los estudios."
    )

    # Disponibilidad y preferencias horarias
    available_days = fields.Many2many(
        'available.days', 
        string='Días Disponibles',
        required=True,
        tracking=True,
        help="Días de la semana en los que el profesional puede atender sesiones. "
            "Se utiliza para la asignación automática de participantes y "
            "la generación de calendarios."
    )
    preferred_schedule = fields.Selection([
        ('1', 'Mañana'),
        ('2', 'Tarde'),
        ('3', 'Ambos')
    ], 
        string="Horario preferido", 
        required=True, 
        tracking=True,
        help="Preferencia horaria para realizar sesiones:\n"
            "- Mañana: 8:00 - 13:00\n"
            "- Tarde: 15:00 - 19:00\n"
            "- Ambos: Disponible en ambas franjas horarias"
    )

    # Estado
    state = fields.Selection([
        ('available', 'Disponible'),
        ('busy', 'Ocupado'),
        ('on_leave', 'De baja')
    ], 
        default='available', 
        tracking=True,
        string='Estado',
        help="Estado actual del profesional:\n"
            "- Disponible: Puede ser asignado a nuevos estudios y participantes\n"
            "- Ocupado: Ha alcanzado su capacidad máxima de participantes (no implementado)\n"
            "- De baja: Temporalmente no disponible para sesiones"
    )

    # Usuario asociado
    user_id = fields.Many2one(
        'res.users', 
        string='Usuario asociado',
        tracking=True
    )

    # Relaciones
    assignment_ids = fields.One2many(
        'study.professional.assignment',
        'professional_id',
        string='Asignaciones',
        help="Lista de asignaciones del profesional a diferentes estudios clínicos. "
            "Cada asignación incluye información sobre compatibilidad y participantes."
    )
    active_participant_ids = fields.One2many(
        'study.participant',
        'professional_id',
        string='Participantes Activos',
        domain=[('template_id.state', '=', 'active')],
        help="Participantes actualmente asignados al profesional en estudios activos. "
            "No incluye participantes de estudios completados o en borrador."
    )

    # Campos computados
    participant_count = fields.Integer(
        compute='_compute_participant_count',
        store=True,
        string='Número de participantes',
        help="Número total de participantes activos asignados actualmente al profesional. "
            "Se utiliza para controlar la carga de trabajo."
    )
    study_count = fields.Integer(
        compute='_compute_study_count',
        store=True,
        string='Número de estudios',
        help="Número total de estudios clínicos en los que el profesional está "
            "actualmente participando."
    )
    sessions_completed = fields.Integer(
        compute='_compute_sessions_stats',
        store=True,
        string='Sesiones completadas',
        help="Número total de sesiones que el profesional ha completado "
            "con todos sus participantes asignados."
    )
    sessions_pending = fields.Integer(
        compute='_compute_sessions_stats',
        store=True,
        string='Sesiones pendientes',
        help="Número total de sesiones pendientes programadas "
            "con todos sus participantes asignados."
    )

    @api.depends('active_participant_ids')
    def _compute_participant_count(self):
        """Calcula el número de participantes activos asignados al profesional."""
        for record in self:
            record.participant_count = len(record.active_participant_ids)

    @api.depends('assignment_ids')
    def _compute_study_count(self):
        """Calcula el número de estudios asignados activamente al profesional."""
        for record in self:
            assigned_studies = record.assignment_ids.filtered(
                lambda a: a.state == 'assigned'
            )
            record.study_count = len(assigned_studies)

    def calculate_participant_affinity(self, participant):
        """Calcula la afinidad (0-100) entre profesional y participante."""
        score = 0.0
        score += self._calculate_schedule_days_score(participant)
        score += self._calculate_schedule_time_score(participant)
        score += self._calculate_workload_affinity_score()
        return round(score, 2)

    def _calculate_schedule_days_score(self, participant):
        """Calcula la puntuación basada en días coincidentes (máx 40%)."""
        prof_days = set(self.available_days.mapped('code'))
        part_days = set(participant.available_days.mapped('code'))
        matching_days = len(prof_days & part_days)
        
        if matching_days >= 3:
            return 40.0
        elif matching_days == 2:
            return 25.0
        elif matching_days == 1:
            return 10.0
        return 0.0

    def _calculate_schedule_time_score(self, participant):
        """Calcula la puntuación basada en franjas horarias (máx 30%)."""
        if self.preferred_schedule == participant.preferred_schedule:
            return 30.0
        elif '3' in (self.preferred_schedule, participant.preferred_schedule):
            return 20.0
        return 0.0

    def _calculate_workload_affinity_score(self):
        """Calcula la puntuación basada en carga actual (máx 30%)."""
        active_cases = len(self.active_participant_ids)
        if active_cases <= 2:
            return 30.0
        elif active_cases <= 4:
            return 20.0
        elif active_cases <= 6:
            return 10.0
        elif active_cases <= 8:
            return 5.0
        return 0.0