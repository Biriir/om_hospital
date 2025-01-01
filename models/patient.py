
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hospital Patient"

    name = fields.Char(string='Name', tracking= True)
    date_of_birth = fields.Date(string='Date Of Birth')
    ref = fields.Char(string='Refrence')
    age = fields.Integer(string='Age', compute='_compute_age', inverse='_inverse_compute_age',
                         search= '_search_age' ,tracking= True)
    gender = fields.Selection([('male', 'male'), ('female', 'female')], string="Gender", tracking= True)
    active = fields.Boolean(string="Active", default=True)
    image = fields.Image(string="Image")
    tag_ids = fields.Many2many('patient.tag', string="Tags")
    appointment_count = fields.Integer(string="Appointment Count", compute='_compute_appointment_count', store=True)
    appointment_ids = fields.One2many('hospital.appointment', 'patient_id', string="Appointments")
    parent =  fields.Char(string="Parent")
    marital_status =  fields.Selection([('married', 'Married'),('single','Single',)], string="Marital Status")
    partner_name = fields.Char(string="Partner Name")
    is_birthday = fields.Boolean(string="Birthday ?", compute='_compute_is_birthday')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')



    # compute value using read_group method
    # it's suited for use of stat buttons  with computed value
    # @api.depends('appointment_ids')
    # def _compute_appointment_count(self):
    #     appointment_group = self.env['hospital.appointment'].read_group(
    #         domain=[],
    #         fields=['patient_id'],
    #         groupby=['patient_id'])
    #     for appointment in appointment_group:
    #         patient_id = appointment.get('patient_id')[0]
    #         patient_rec = self.browse(patient_id)
    #         patient_rec.appointment_count = appointment['patient_id_count']
    #         self -= patient_rec
    #     self.appointment_count = 0

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        # Group appointments by patient
        appointment_group = self.env['hospital.appointment'].read_group(
            domain=[],
            fields=['patient_id:count'],
            groupby=['patient_id']
        )
        # Prepare a mapping of patient_id to appointment count
        appointment_mapping = {
            appointment['patient_id'][0]: appointment['patient_id_count']
            for appointment in appointment_group if appointment.get('patient_id')
        }

        # Update the appointment_count for each patient
        for record in self:
            record.appointment_count = appointment_mapping.get(record.id, 0)


    #compute value using search_count method
    # @api.depends('appointment_ids')
    # def _compute_appointment_count(self):
    #     for rec in self:
    #         rec.appointment_count = self.env['hospital.appointment'].search_count([('patient_id', '=', rec.id)])


    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for record in self:
            if record.date_of_birth and record.date_of_birth > fields.Date.today():
                raise ValidationError(_("The date of birth cannot be set in the future"))
    # all records passed the test, don't return anything

    # @api.ondelete(at_uninstall=False)
    # def _check_appointments(self):
    #     for rec in self:
    #         if rec.appointment_ids:
    #             raise ValidationError(_("You cannot delete a patient with appointments"))

    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient')
        return super(HospitalPatient, self).create(vals)


    def write(self, vals):
        for rec in self:
            if not self.ref and not vals.get('ref'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient')
        return super(HospitalPatient, self).write(vals)


    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            today = date.today()
            if rec.date_of_birth:
                rec.age = today.year - rec.date_of_birth.year
            else:
                rec.age = 0

    @api.depends('age')
    def _inverse_compute_age(self):
        today = date.today()
        for rec in self:
            rec.date_of_birth = today - relativedelta.relativedelta(years=rec.age)

    def _search_age(self, operator, value):
        date_of_birth = date.today() - relativedelta.relativedelta(years=value)
        start_of_year = date_of_birth.replace(day=1,month=1)
        end_of_year = date_of_birth.replace(day=31, month=12)
        return [('date_of_birth', '>=',start_of_year), ('date_of_birth', '<=',end_of_year)]




# def name_get(self):
#     patient_list = []
#     for record in self:
#         name = record.ref + ' ' + record.name
#         patient_list.append((record.id, name))
#     return patient_list
# we can simplify the code above like shown below
    def name_get(self):
        return [(record.id, "%s:%s" % (record.ref, record.name)) for record in self]

    def action_test(self):
        print("clicked")
        return

    @api.depends('date_of_birth')
    def _compute_is_birthday(self):
        for rec in self:
            is_birthday = False
            if rec.date_of_birth:
                today = date.today()
                if today.day == rec.date_of_birth.day and today.month == rec.date_of_birth.month:
                    is_birthday = True
            rec.is_birthday = is_birthday


    def action_view_appointments(self):
        return {
            'name': _('Appointments'),
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form,calendar,activity',
            'context': {'default_patient_id':self.id},
            'domain': [('patient_id', '=', self.id)],
            'target': 'current',
            'type' : 'ir.actions.act_window',
        }