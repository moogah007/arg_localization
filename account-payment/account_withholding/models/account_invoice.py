# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, Warning


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    state_id = fields.Many2one(
        'res.country.state',
        string="State",
        states={'paid': [('readonly', True)]},
    )

    @api.onchange('partner_id')
    def onchange_partner_id_new(self):
        self.state_id = self.partner_id.state_id

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()

        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        found_wh = False
        for inv_line in credit_aml.invoice_id.invoice_line_ids:
            if inv_line.account_id.wtax_ids:
                found_wh = True
        if found_wh:
            if credit_aml.invoice_id.amount_total - credit_aml.invoice_id.residual != 0:
                raise ValidationError(_('la factura no debe tener ningun pago asociado'))
        return super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id)

    @api.multi
    def write(self,vals):
        for rec in self:
            if rec.origin:
                if len(rec.origin.split()) == 1:
                    po = rec.env['purchase.order'].search([('name', '=', rec.origin)])
                    if po:
                        vals['state_id'] = po.state_id.id
                    if not 'state_id' in vals.keys():
                        vals['state_id'] = rec.partner_id.state_id.id
                else:
                    vals['state_id'] = rec.partner_id.state_id.id

            if rec.nc_ref_id and (rec.nc_ref_id != rec.id):
                found_wh = False
                acc_lst = {}
                acc_lstnc = {}
                warn = ''

                #number = rec.origin.split(' ')
                #if len(number) > 1:
                #    number = number[3]
                #inv_orig = rec.env['account.invoice'].search([('number', '=', number), ('state', '!=', 'draft')])

                inv_orig_ = rec.env['account.invoice'].search(
                    [('nc_ref_id', '=', rec.nc_ref_id), ('state', '!=', 'draft'),('type','in', ['in_refund','in_invoice'])]
                )


                if inv_orig_:
                    for inv_orig in inv_orig_:
                        for inv_line in inv_orig.invoice_line_ids:
                            if inv_line.account_id.wtax_ids:
                                found_wh = True
                            if inv_line.account_id.id in acc_lst.keys():
                                acc_lst[inv_line.account_id.name] = acc_lst[inv_line.account_id.name] + inv_line.price_unit
                            else:
                                acc_lst[inv_line.account_id.name] = inv_line.price_unit

                        if found_wh:
                            for line in rec.invoice_line_ids:
                                if line.account_id.id in acc_lstnc.keys():
                                    acc_lstnc[line.account_id.name] = acc_lstnc[line.account_id.name] + line.price_unit
                                else:
                                    acc_lstnc[line.account_id.name] = line.price_unit

                            for item in acc_lstnc.keys():
                                if not item in acc_lst.keys():
                                    raise ValidationError(_('La factura de NC tiene una cuenta que no esta presente en la factura original'))
                                #else:
                                    #if acc_lstnc[item] > acc_lst[item]:
                                        #raise Warning(_('La factura de NC tiene un monto mayor que la factura original: ' + str(acc_lstnc[item]) + '>' + str(acc_lst[item])))
        return super(AccountInvoice, self).write(vals)
