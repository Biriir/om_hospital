from odoo import models, fields
from odoo.tools.safe_eval import safe_eval


class OdooPlayGround(models.Model):
    _name = "odoo.playground"
    _description = "Odoo Playground"

    model_id = fields.Many2one('ir.model', string="Model")
    code = fields.Text(string='Code', default=lambda self: 'DEFAULT_ENV_VARIABLES')
    result = fields.Text(string="Result")

    def action_execute(self):
        try:
            if self.model_id:
                model = self.env[self.model_id.model]
            else:
                model = self
            # Safely evaluate the code with the provided context
            self.result = safe_eval(self.code.strip(), {'self': model})
        except Exception as e:
            self.result = str(e)
