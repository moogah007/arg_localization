# -*- coding: utf-8 -*-
from odoo import http, models, fields, api, _
from datetime import datetime
import calendar


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    partner_id = fields.Many2one('res.partner',string="Invoicing Address",translate=True)

    @api.model
    def default_get(self, default_fields):
        res = super(AccountJournal, self).default_get(default_fields)
        res.update({
            'partner_id': self.env.user.company_id.partner_id.id,
        })
        return res
