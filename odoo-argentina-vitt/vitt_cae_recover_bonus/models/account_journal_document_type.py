# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import UserError
import logging
import xmltodict
import datetime

_logger = logging.getLogger(__name__)


class AccountJournalDocumentType(models.Model):
    _inherit = "account.journal.document.type"

    @api.multi
    def get_pyafipws_consult_invoice2(self, document_number):
        self.ensure_one()
        document_type = self.document_type_id.code
        company = self.journal_id.company_id
        afip_ws = self.journal_id.afip_ws
        if not afip_ws:
            raise UserError(_('No AFIP WS selected on point of sale %s') % (self.journal_id.name))
        if afip_ws == 'wsbfe':
            ws = company.get_connection(afip_ws).connect()
            ws.GetCMP(
                document_type,
                self.journal_id.point_of_sale_number,
                document_number)
            attributes = [
                'PuntoVenta', 'CbteNro', 'FechaCbte', 'ImpTotal', 'CAE',
                'Vencimiento', 'FchVencCAE', 'Resultado', 'XmlResponse']
            msg = ''
            title = _('Invoice number %s\n' % document_number)

            # TODO ver como hacer para que tome los enter en los mensajes
            #print ws.__dict__
            for pu_attrin in attributes:
                msg += "%s: %s\n" % (
                    pu_attrin, str(getattr(ws, pu_attrin)).decode("utf8"))

            msg += " - ".join([
                ws.Excepcion,
                ws.ErrMsg,
                ws.Obs])
            # TODO parsear este response. buscar este metodo que puede ayudar
            # b = ws.ObtenerTagXml("CAE")
            # import xml.etree.ElementTree as ET
            # T = ET.fromstring(ws.XmlResponse)

            #_logger.info('%s\n%s' % (title, msg))
            #raise UserError(title + msg)
            return ws.__dict__
        return super(AccountJournalDocumentType, self).get_pyafipws_consult_invoice2(document_number)

class AfipWsConsultWizard(models.TransientModel):
    _inherit = 'afip.ws.consult.wizard'

    @api.multi
    def confirm(self):
        self.ensure_one()
        id = self._context.get('active_id', False)
        inv = self.env['account.invoice'].browse(id)

        if inv.journal_id.afip_ws == 'wsbfe':
            if inv.afip_auth_code:
                raise UserError(_('solo sin CAE'))

            journal_document_type_id = inv.journal_document_type_id.id
            if not journal_document_type_id:
                raise UserError(_('No Journal Document Class as active_id on context'))
            journal_document_type = self.env[
                'account.journal.document.type'].browse(journal_document_type_id)

            ws = journal_document_type.get_pyafipws_consult_invoice2(self.number)

            doc = xmltodict.parse(ws['XmlResponse'])
            if 'BFEResultGet' not in doc['soap:Envelope']['soap:Body']['BFEGetCMPResponse']['BFEGetCMPResult'].keys():
                raise UserError(_('No existen datos de esa factura en la Afip'))

            res = doc['soap:Envelope']['soap:Body']['BFEGetCMPResponse']['BFEGetCMPResult']['BFEResultGet']
            if not 'Cae' in res.keys() or not 'Fecha_cbte_orig' in res.keys():
                raise UserError(_('No se pudo retraer CAE'))

            inv2 = self.env['account.invoice'].search([('afip_auth_code', '=', res['Cae'])])
            if inv2:
                raise UserError(_('you have an invoice with this CAE: %s') % (inv2.display_name2))


            if not inv.date_invoice:
                raise UserError(_('por favor complete la fecha primero en la factura'))
            date = inv.date_invoice
            #print date.replace("-", "")==res['Fecha_cbte_orig'].replace("-", "")
            #print int(float(res['Imp_total']) * 100) == int(float(inv.amount_total) * 100)
            #print int(res['Punto_vta'])==int(inv.journal_id.point_of_sale_number)
            #print int(res['Tipo_cbte'])==int(inv.journal_document_type_id.document_type_id.code)
            #print res['Imp_moneda_Id']==inv.currency_id.afip_code
            if date.replace("-", "")==res['Fecha_cbte_orig'].replace("-", "") and \
                int(float(res['Imp_total']) * 100) == int(float(inv.amount_total) * 100) and \
                int(res['Punto_vta'])==int(inv.journal_id.point_of_sale_number) and \
                int(res['Tipo_cbte'])==int(inv.journal_document_type_id.document_type_id.code) and \
                res['Imp_moneda_Id']==inv.currency_id.afip_code:

                date2 = datetime.datetime.strptime(res['Fch_venc_Cae'],'%Y%m%d').date()
                afip_auth_code = res['Cae']
                afip_result = 'A'
                afip_xml_request = ws['XmlRequest']
                afip_xml_response = ws['XmlResponse']

                inv.write({'afip_auth_code':afip_auth_code,
                        'afip_auth_code_due':date2,
                        'afip_result':afip_result,
                        'afip_xml_request':afip_xml_request,
                        'afip_xml_response':afip_xml_response})
                inv.action_invoice_open()
            else:
                raise UserError(_('la factura no corresponde con los datos obtenidos'))
        else:
            return super(AfipWsConsultWizard, self).confirm()

class AccountInvoiceCAERecover(models.TransientModel):
    _inherit = 'account.invoice.caerecover'

    def confirm(self):
        if self.journal_id.afip_ws == 'wsbfe':
            ws = self.doctype_id.get_pyafipws_consult_invoice2(self.number)

            doc = xmltodict.parse(ws['XmlResponse'])
            if 'BFEResultGet' not in doc['soap:Envelope']['soap:Body']['BFEGetCMPResponse']['BFEGetCMPResult'].keys():
                raise UserError(_('No existen datos de esa factura en la Afip'))

            res = doc['soap:Envelope']['soap:Body']['BFEGetCMPResponse']['BFEGetCMPResult']['BFEResultGet']
            if not 'Cae' in res.keys() or not 'Fecha_cbte_orig' in res.keys():
                raise UserError(_('No se pudo retraer CAE'))

            inv = self.env['account.invoice'].search([('afip_auth_code', '=', res['Cae'])])
            if inv:
                raise UserError(_('you have an invoice with this CAE: %s') % (inv.display_name2))

            active_ids = self._context.get('active_ids', [])
            invoices = self.env['account.invoice'].browse(active_ids)
            foundf = False
            for inv in invoices:
                if inv.type in ['out_invoice','out_refund'] and inv.state == 'draft' and \
                        self.doctype_id.id == inv.journal_document_type_id.id and self.journal_id.id == inv.journal_id.id:

                    date = inv.date_invoice
                    if date.replace("-", "") == res['Fecha_cbte_orig'].replace("-", "") and \
                            int(float(res['Imp_total']) * 100) == int(float(inv.amount_total) * 100) and \
                            int(res['Punto_vta']) == int(inv.journal_id.point_of_sale_number) and \
                            int(res['Tipo_cbte']) == int(inv.journal_document_type_id.document_type_id.code) and \
                            res['Imp_moneda_Id'] == inv.currency_id.afip_code:
                        date2 = datetime.datetime.strptime(res['Fch_venc_Cae'], '%Y%m%d').date()
                        afip_auth_code = res['Cae']
                        afip_result = 'A'
                        afip_xml_request = ws['XmlRequest']
                        afip_xml_response = ws['XmlResponse']

                        inv.write({'afip_auth_code': afip_auth_code,
                                   'afip_auth_code_due': date2,
                                   'afip_result': afip_result,
                                   'afip_xml_request': afip_xml_request,
                                   'afip_xml_response': afip_xml_response})
                        inv.action_invoice_open()
                        foundf = True
                        break

            if not foundf:
                raise UserError(_('Los datos no corresponden con ninguna dentro del sistema'))
        else:
            return super(AccountInvoiceCAERecover, self).confirm()