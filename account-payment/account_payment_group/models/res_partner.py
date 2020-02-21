from odoo import fields, models, api
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP

class ResPartner(models.Model):
    _inherit = 'res.partner'

    apg_warn = fields.Selection(WARNING_MESSAGE, 'Sales Order', default='no-message', help=WARNING_HELP, required=True)
    apg_warn_msg = fields.Text('Message for Payment Group')


class AccountPaymentgroup(models.Model):
    _inherit = 'account.payment.group'

    @api.onchange('partner_id')
    def onchange_pid_on_apg(self):
        if self.partner_id:
            if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
                partner = self.partner_id.parent_id
            elif self.partner_id.picking_warn not in ('no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
                partner = self.partner_id.parent_id
            else:
                partner = self.partner_id
            if partner.apg_warn != 'no-message':
                if partner.apg_warn == 'block':
                    self.partner_id = False
                return {'warning': {
                    'title': ("Warning for %s") % partner.name,
                    'message': partner.apg_warn_msg
                }}
