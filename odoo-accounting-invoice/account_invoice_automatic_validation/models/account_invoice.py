# -*- coding: utf-8 -*-

from odoo import fields, models, api, registry


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    automatic_validation = fields.Boolean(
        copy=False, readonly=True, states={'draft': [('readonly', False)]})

    def run_automatic_invoice_validation(self):
        invoices = self.env['account.invoice'].search(
            [('state', '=', 'draft'), ('automatic_validation', '=', True)])
        for invoice in invoices:
            with api.Environment.manage():
                new_cr = registry(self._cr.dbname).cursor()
                new_env = api.Environment(
                    new_cr, self.env.uid, self.env.context)

                try:
                    invoice.with_env(new_env).action_invoice_open()
                    new_env.cr.commit()
                except Exception:
                    new_cr.rollback()
                    pass
                # close the new cursor
                new_cr.close()
        return {}
