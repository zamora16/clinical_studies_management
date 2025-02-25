from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudyProfessionalAssignment(models.Model):
    """
    Modelo que gestiona las asignaciones de profesionales a plantillas de estudio.
    """
    _name = 'study.professional.assignment'
    _description = 'Clinical Study Professional Assignment'

    # Campos relacionales
    template_id = fields.Many2one(
        'study.template', 
        required=True, 
        string='Plantilla de estudio',
        ondelete='cascade',
        tracking=True,
        help="Plantilla de estudio a la que se asigna el profesional"
    )
    professional_id = fields.Many2one(
        'study.professional', 
        required=True, 
        string='Profesional',
        ondelete='cascade',
        tracking=True,
        help="Profesional asignado a la plantilla"
    )
    participant_ids = fields.One2many(
        'study.participant', 
        'professional_id',
        domain="[('template_id', '=', template_id)]",
        string='Participantes asignados',
        help="Participantes asignados a este profesional en esta plantilla"
    )
    
    # Campos computados
    score = fields.Float(
        compute='_compute_score', 
        store=True, 
        string='Puntuación',
        help="Puntuación de compatibilidad del profesional con la plantilla (0-100)"
    )
    participant_count = fields.Integer(
        compute='_compute_participant_count', 
        store=True,
        string='Número de participantes',
        help="Número total de participantes asignados"
    )
    
    # Estado
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('assigned', 'Asignado'),
        ('declined', 'Declinado')
    ], default='draft', tracking=True, string='Estado')

    # Restricciones SQL
    _sql_constraints = [
        ('unique_assignment', 
         'UNIQUE(template_id, professional_id)',
         'Ya existe una asignación para este profesional en este estudio')
    ]

    @api.depends('professional_id', 'template_id', 'professional_id.available_days')
    def _compute_score(self):
        """
        Combina las puntuaciones de compatibilidad profesional-plantilla.
        """
        for record in self:
            if record.professional_id and record.template_id:
                record.score = record.template_id.calculate_professional_score(
                    record.professional_id
                )
            else:
                record.score = 0

    @api.depends('participant_ids')
    def _compute_participant_count(self):
        """Calcula el número total de participantes asignados."""
        for record in self:
            record.participant_count = len(record.participant_ids)

    def action_assign(self):
        """
        Activa la asignación del profesional a la plantilla.
        
        Raises:
            ValidationError: Si la asignación no está en estado borrador o
                           si el profesional ya está asignado a la plantilla.
        """
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError('Solo se pueden activar asignaciones en estado borrador')
            
        # Verificar asignación existente
        if self._check_existing_assignment():
            raise ValidationError(
                f'El profesional {self.professional_id.name} ya está asignado a este estudio'
            )

        self.state = 'assigned'
        return True
    
    def action_decline(self):
        """Declina la asignación del profesional a la plantilla."""
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError('Solo se pueden declinar asignaciones en estado borrador')
            
        self.state = 'declined'
        return True
        
    def _check_existing_assignment(self):
        """
        Verifica si ya existe una asignación activa para este profesional y plantilla.
        
        Returns:
            bool: True si existe una asignación, False en caso contrario
        """
        return self.search_count([
            ('template_id', '=', self.template_id.id),
            ('professional_id', '=', self.professional_id.id),
            ('state', '=', 'assigned'),
            ('id', '!=', self.id)
        ]) > 0