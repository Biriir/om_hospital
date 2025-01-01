
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError




class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hospital Appointment"
    _rec_name = 'reference'
    _order = 'id desc'

    patient_id = fields.Many2one('hospital.patient', string="Patient", tracking=1 , ondelete='restrict')
    gender = fields.Selection(string="Gender", related='patient_id.gender', readonly=False)
    appointment_time = fields.Datetime(string='Appointment Time', default=fields.Datetime.now, tracking=True)
    reference = fields.Char(string='Reference')
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, tracking=3)
    ref = fields.Char(string='Refrence', help="Refrence from patient record ")
    prescription = fields.Html(string='Prescription')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancel', 'Canceled')], default='draft', string="status", required=True, tracking=20)
    doctor_id = fields.Many2one('res.users', string='doctor', tracking=True)
    pharmacy_lines_ids = fields.One2many('appointment.pharmacy.lines', 'appointment_id', string='Pharmacy Lines')
    hide_sales_price = fields.Boolean(string="Hide Sales Price")
    operation_id = fields.Many2one('hospital.operation', string="Operation")
    progress = fields.Integer(string="Progress", compute='_compute_progress')
    duration = fields.Float(string='Duration')
    note = fields.Html(string='Note')

    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    price_totals = fields.Monetary(string='Totals', compute='_compute_price_totals', currency_field='currency_id', store=True)

    @api.depends('pharmacy_lines_ids.price_subtotal')
    def _compute_price_totals(self):
        for rec in self:
            rec.price_totals = sum(rec.pharmacy_lines_ids.mapped('price_subtotal'))

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == 'draft':
                progress = 25
            elif rec.state == 'in_consultation':
                progress = 50
            elif rec.state == 'done':
                progress = 100
            else:
                progress = 0
            rec.progress = progress

# function for creating line number to pharmacy lines
    def set_line_number(self):
        sl_no = 0
        for line in self.pharmacy_lines_ids:
            sl_no += 1
            line.sl_no = sl_no
        return



    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].next_by_code('hospital.appointment')
        res = super(HospitalAppointment, self).create(vals)
# for creating line number serial  for pharmacy lines
        res.set_line_number()
        return res


#for creating line number for pharmacy lines ones updated
    def write(self,values):
        res = super(HospitalAppointment, self).write(values)
        self.set_line_number()
        return res



    # def unlink(self):
    #     for rec in self:
    #         if self.state == 'done':
    #             raise ValidationError(_("You cannot delete appointment with 'Done' status"))
    #     return super(HospitalAppointment, self).unlink()

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        self.ref = self.patient_id.ref

    def action_test(self):
        #url action
        return{
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'https://www.meritadvisory.so'
            # #dynamic url
            # 'url': self.field,
        }

    def action_notification(self):
        action = self.env.ref('om_hospital.action_hospital_patient')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Click to open patient records'),
                'message': '%s',
                'links': [{
                    'label': self.patient_id.name,
                    'url': f'#action={action.id}&id={self.patient_id.id}&model=hospital.patient'

                }],
                'sticky': True,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'hospital.patient',
                    'res_id': self.patient_id.id,
                    'views': [(False,'form')]
                }
            }
        }



    def action_share_whatsapp(self):
        if not self.patient_id.phone:
            raise ValidationError(_("Missing Phone Number in the patient record"))
        message = 'Hi *%s*, your appointment number is : *%s*, Thank you' % (self.patient_id.name,self.ref)
        whatsapp_api_url = 'https://web.whatsapp.com/send?phone=%s&text=%s' % (self.patient_id.phone,message)
        self.message_post(body=message, subject='WhatsApp Message')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }


    def action_in_consultation(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'in_consultation'

    def action_done(self):
        for rec in self:
            rec.state = 'done'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Successfully Done',
                'type': 'rainbow_man',
            }

        }

    def action_cancel(self):
        action = self.env.ref('om_hospital.action_cancel_appointment').read()[0]
        return action

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'


    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == 'draft':
                progress = 25
            elif rec.state == 'in_consultation':
                progress = 50
            elif rec.state == 'done':
                progress = 100
            else:
                progress = 0
            rec.progress = progress




class AppointmentPharmacyLines(models.Model):
    _name = "appointment.pharmacy.lines"
    _description = "Appointment Pharmacy lines"

    sl_no = fields.Integer(string="SNO.")
    product_id = fields.Many2one('product.product', required=True)
    price_unit = fields.Float(related='product_id.list_price', digits='Product Price')
    qty = fields.Integer(string='Quantity', default=1)
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
    price_subtotal = fields.Monetary(string='Subtotal',compute='_compute_price_subtotal')
    currency_id = fields.Many2one(related='appointment_id.currency_id')


    @api.depends('price_unit','qty')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.price_unit * rec.qty









