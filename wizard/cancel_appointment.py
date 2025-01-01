import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil import relativedelta



class CancelAppointmentWizard(models.TransientModel):
    _name = "cancel.appointment.wizard"
    _description = "Cancel Appointment Wizard"

    @api.model
    def default_get(self, fields):
        res = super(CancelAppointmentWizard, self).default_get(fields)
        res['date_cancel'] = datetime.date.today()
        # for the active id
        # if self.env.context.get('active_id'):
        #     res['appointment_id'] = self.env.context.get('active_id')
        return res

    appointment_id = fields.Many2one('hospital.appointment', string="Appointment",
                                     domain=[('state', '=', 'draft'), ('priority', 'in', ('0', '1', False))])
    reason = fields.Text(string="Reason")
    date_cancel = fields.Date(string="Cancellation Date")

    def action_cancel(self):
         #for accessing value from settings  to restrict cancel appointment which is close to the appointment day than the value in system parameters

        cancel_day = self.env['ir.config_parameter'].get_param('om_hospital.cancel_days')
        allowed_date = self.appointment_id.booking_date - relativedelta.relativedelta(days=int(cancel_day))
        if cancel_day != 0 and allowed_date < date.today():
            raise ValidationError(_("Sorry Cancellation is not Allowed for this Booking at this time"))

          #for preventing cancellation in same day of booking
        # if self.appointment_id.booking_date == fields.date.today():
        #     raise ValidationError(_("Sorry, cancellation is not  allowed on same date of booking"))
        self.appointment_id.state = 'cancel'
        return{
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cancel.appointment.wizard',
            'target': 'new',
            'res_id': self.id
        }





        # return {
        #         'type': 'ir.actions.client',
        #         'tag': 'reload',
        #     }
