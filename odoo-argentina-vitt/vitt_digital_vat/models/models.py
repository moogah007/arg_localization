# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta
from odoo import http, models, fields, api, _
from cStringIO import StringIO
import base64
from decimal import *
import time
import string
from odoo.exceptions import ValidationError, Warning, UserError
import unicodedata

TWOPLACES = Decimal(10) ** -2

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    printable = set(string.printable)
    res =  u"".join([c for c in nfkd_form if not unicodedata.combining(c)])[:30]
    return filter(lambda x: x in printable, res)

def parse(str):
    printable = set(string.printable)
    tstr =  filter(lambda x: x in printable, str)
    return tstr[:30]

def MultiplybyRate(rate, amountincur, curcomp, invcur):
    if curcomp != invcur:
        total =  float(rate) * float(amountincur)
    else:
        total = amountincur

    total = Decimal(total).quantize(TWOPLACES)
    total *= 100
    longtotal = long(total)
    return longtotal

def converttolong(amount):
    if amount < 0:
        amount = -amount
    return long(amount*100)

class ExcelDigitalVAT(models.TransientModel):
    _name= "excel.digital.vat"
    file_p_cbte = fields.Binary('Download')
    file_name_p_cbte = fields.Char('LIBRO_IVA_DIGITAL_COMPRAS_CBTE', size=64)
    file_v_cbte = fields.Binary('Download')
    file_name_v_cbte = fields.Char('LIBRO_IVA_DIGITAL_VENTAS_CBTE', size=64)

    file_p_alic = fields.Binary('Download')
    file_name_p_alic = fields.Char('LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS', size=64)
    file_v_alic = fields.Binary('Download')
    file_name_v_alic = fields.Char('LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS', size=64)

    file_p_imp = fields.Binary('Download')
    file_name_p_imp = fields.Char('LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA', size=64)
    file_s_imp = fields.Binary('Download')
    file_name_s_imp = fields.Char('LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL', size=64)

    file_tv_cbte = fields.Binary('Download')
    file_name_tv_cbte = fields.Char('LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE', size=64)
    file_tc_cbte = fields.Binary('Download')
    file_name_tc_cbte = fields.Char('LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE', size=64)

    file_null_cbte = fields.Binary('Download')
    file_name_null_cbte = fields.Char('LIBRO_IVA_DIGITAL_VENTAS_ANULADAS', size=64)

    errors = fields.Binary('Errores')
    file_errors = fields.Char('Errores', size=64)

class citi_reports(models.TransientModel):
    _name = 'wizard.digital.vat'

    date_from = fields.Date(string='Date From', required=True,default=datetime.now().strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    LIBRO_IVA_DIGITAL_COMPRAS_CBTE = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_COMPRAS_CBTE",translate=True,default=True)
    LIBRO_IVA_DIGITAL_VENTAS_CBTE = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_VENTAS_CBTE",translate=True,default=True)
    LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS",translate=True,default=True)
    LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS",translate=True,default=True)
    LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA",translate=True)
    LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL",translate=True)
    LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE",translate=True)
    LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE",translate=True)
    LIBRO_IVA_DIGITAL_VENTAS_ANULADAS = fields.Boolean(string="Exportar LIBRO_IVA_DIGITAL_VENTAS_ANULADAS",translate=True)

    def print_digital_vat(self):
        tstr = ""
        filename = ""

        if not self.LIBRO_IVA_DIGITAL_COMPRAS_CBTE and not\
            self.LIBRO_IVA_DIGITAL_VENTAS_CBTE and not\
            self.LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS and not\
            self.LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS and not\
            self.LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA and not\
            self.LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL and not\
            self.LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE and not\
            self.LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE and not \
            self.LIBRO_IVA_DIGITAL_VENTAS_ANULADAS:

            raise Warning(_("Por favor seleccione al menos un archivo a exportar"))


        context = self._context
        oldciti = self.env['vitt_sales_reports.reportciti']
        gARRAYVAT = oldciti.getvatarray()
        export_id = self.env['excel.digital.vat'].create({})

        #SALES
        domain = [
            '&',('date', '>=', self.date_from),('date', '<=', self.date_to),
            ('type', '!=', 'in_invoice'),('type', '!=', 'in_refund'),'|',('state', '=', 'open'),
            ('state', '=', 'paid')
        ]
        invoiceModel = self.env['account.invoice']
        invoices = invoiceModel.search(domain,order="date_invoice")

        if self.LIBRO_IVA_DIGITAL_VENTAS_CBTE:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    tstr += inv.date_invoice[0:4] + inv.date_invoice[5:7] + inv.date_invoice[8:10]
                    tstr += "{:0>3}".format(inv.journal_document_type_id.document_type_id.code)
                    doc_nr = inv.document_number.split('-')
                    tstr += "{:0>5}".format(doc_nr[0]) + "{:0>20}".format(doc_nr[1])
                    tstr += "{:0>20}".format(doc_nr[1])
                    tstr += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                    tstr += "{:0>20}".format(inv.partner_id.main_id_number)

                    tmpstr = remove_accents(inv.partner_id.name)

                    tstr += "{:<30}".format(tmpstr)

                    total = MultiplybyRate(inv.currency_rate, inv.amount_total, inv.company_currency_id,
                                           inv.currency_id)
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotnovat(inv))
                    tstr += "{:0>15}".format(total)

                    #total = converttolong(inv.gettotexempt(inv))
                    total = 0
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotexempt(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotpercepincome(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotgrossincome2(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotlocPercep(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotinttaxes(inv))
                    if total < 0:
                        total *= -1
                    tstr += "{:0>15}".format(total)

                    tstr += "{:>3}".format(inv.currency_id.afip_code)
                    if inv.currency_id != inv.company_currency_id:
                        tstr += "{:0>10}".format(long(Decimal(inv.currency_rate).quantize(TWOPLACES) * 1000000))
                    else:
                        tstr += '0001000000'

                    vatcodesqty = oldciti.getvatcodeslistg3(inv)
                    vatcodeex = oldciti.getallcodes2(inv)

                    if vatcodesqty > 0 and len(vatcodeex) >= 0:
                        tstr += str(vatcodesqty)
                    elif vatcodesqty == 0 and len(vatcodeex) > 0:
                        tstr += '1'

                    if inv.journal_document_type_id.document_type_id.code in ('195', '196', '197'):
                        tstr += 'T'
                    else:
                        if inv.fiscal_position_id.afip_code == False:
                            tstr += '0'
                        else:
                            tstr += "{:>1}".format(inv.fiscal_position_id.afip_code)

                    total = converttolong(inv.gettotothers(inv))
                    tstr += "{:0>15}".format(total)

                    if inv.journal_document_type_id.document_type_id.document_letter_id.name != 'E' and \
                        inv.journal_document_type_id.document_type_id.code \
                        not in ["60", "63", "64", "82","81"] and not \
                        inv.journal_document_type_id.document_type_id.dont_show_duedate:

                        tstr += inv.date_due[0:4] + inv.date_due[5:7] + inv.date_due[8:10]
                    else:
                        tstr += '00000000'
                    tstr += '\r\n'

            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_v_cbte': base64.encodestring(fp_str.getvalue()),
                    'file_name_v_cbte': "LIBRO_IVA_DIGITAL_VENTAS_CBTE.txt",
                    })
                fp_str.close()


        if self.LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) != '066' and \
                            "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) != '067':

                        # print "-----------"
                        if inv.fiscal_position_id.afip_code == False or \
                                "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) in ('195','196','197'):
                            vatcodes = oldciti.getallcodes(inv)
                            # print "sin posicion"
                        else:
                            # print "con posicion"
                            vatcodes = oldciti.getallcodessl(inv)

                        # print inv.journal_document_type_id.document_type_id.code
                        # print inv.document_number
                        # print "vatcodes", vatcodes

                        for code in vatcodes:
                            tstr += "{:0>3}".format(inv.document_type_id.code)
                            docnr = inv.document_number.split('-')
                            tstr += "{:0>5}".format(docnr[0]) + "{:0>20}".format(docnr[1])
                            # tstr_v_alic += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                            # tstr_v_alic += "{:0>20}".format(inv.partner_id.main_id_number)
                            if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) in ('195','196','197'):
                                if code in gARRAYVAT:
                                    total = oldciti.getbaseforcodet(inv, gARRAYVAT[code])
                                else:
                                    total = 0
                            else:
                                if inv.fiscal_position_id.afip_code == False:
                                    if code in gARRAYVAT:
                                        total = oldciti.getbaseforcode(inv, gARRAYVAT[code])
                                    else:
                                        total = 0
                                else:
                                    if inv.journal_document_type_id.document_type_id.document_letter_id.name != 'E':
                                        total = 0
                                    else:
                                        total = oldciti.getbaseforcode(inv, gARRAYVAT[code])

                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            tstr += "{:0>15}".format(total)

                            if inv.fiscal_position_id.afip_code == False or \
                                    "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) in ('195','196','197'):
                                codetype = oldciti.getcodetype(inv, code)
                                tstr += "{:0>4}".format(codetype)
                            else:
                                tstr += "{:0>4}".format('3')

                            if code in gARRAYVAT:
                                total = oldciti.gettotforcode(inv, gARRAYVAT[code])
                            else:
                                total = 0
                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            tstr += "{:0>15}".format(total)

                            tstr += '\r\n'

            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_v_alic': base64.encodestring(fp_str.getvalue()),
                    'file_name_v_alic': "LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS.txt",
                    })
                fp_str.close()

        if self.LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) in ('195','196','197'):
                        tstr += inv.date_invoice[0:4] + inv.date_invoice[5:7] + inv.date_invoice[8:10]
                        tstr += "{:0>3}".format(inv.journal_document_type_id.document_type_id.code)
                        doc_nr = inv.document_number.split('-')
                        tstr += "{:0>5}".format(doc_nr[0]) + "{:0>20}".format(doc_nr[1])
                        tstr += "{:0>20}".format(doc_nr[1])
                        tstr += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                        tstr += "{:0>20}".format(inv.partner_id.main_id_number)
                        tmpstr = remove_accents(inv.partner_id.name)
                        tstr += "{:<30}".format(tmpstr)

                        total = MultiplybyRate(inv.currency_rate, inv.amount_total, inv.company_currency_id, inv.currency_id)
                        tstr += "{:0>15}".format(total)

                        total = converttolong(inv.gettotnovat(inv))
                        tstr += "{:0>15}".format(total)

                        tstr += '000000000000000'

                        total = converttolong(inv.gettotexempt(inv))
                        tstr += "{:0>15}".format(total)

                        total = converttolong(inv.gettotpercepincome(inv))
                        tstr += "{:0>15}".format(total)

                        total = converttolong(inv.gettotgrossincome2(inv))
                        tstr += "{:0>15}".format(total)

                        total = converttolong(inv.gettotlocPercep(inv))
                        tstr += "{:0>15}".format(total)

                        total = converttolong(inv.gettotinttaxes(inv))
                        tstr += "{:0>15}".format(total)

                        tstr += "{:>3}".format(inv.currency_id.afip_code)

                        if inv.currency_id != inv.company_currency_id:
                            tstr += "{:0>10}".format(long(Decimal(inv.currency_rate).quantize(TWOPLACES) * 1000000))
                        else:
                            tstr += '0001000000'

                        vatcodesqty = oldciti.getvatcodeslistg3(inv)
                        tstr += str(vatcodesqty)

                        if inv.fiscal_position_id.afip_code == None or inv.fiscal_position_id.afip_code == '0':
                            tstr += '1'
                        else:
                            tstr += "{:>1}".format(inv.fiscal_position_id.afip_code)

                        total = converttolong(inv.gettotothers(inv))
                        tstr += "{:0>15}".format(total)

                        if inv.journal_document_type_id.document_type_id.dont_show_duedate == False:
                            tstr += inv.date_due[0:4] + inv.date_due[5:7] + inv.date_due[8:10]

                        total = converttolong(inv.gettotottaxrefund(inv))
                        tstr += "{:0>15}".format(total)

                        tstr += '\r\n'

            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_tv_cbte': base64.encodestring(fp_str.getvalue()),
                    'file_name_tv_cbte': "LIBRO_IVA_DIGITAL_VENTAS_TurIVA_CBTE.txt",
                    })
                fp_str.close()


        if self.LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '066' or \
                            "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '067':

                        vatcodes = oldciti.getallcodesimp(inv)  # this is id of vatcode
                        for code in vatcodes:
                            tstr += "{:0>15}".format(inv.document_number)

                            total = oldciti.getbaseforcodeimp(inv, code)
                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            if total < 0:
                                total = total * -1
                                tstr += '-' + "{:0>14}".format(total)
                            else:
                                tstr += "{:0>15}".format(total)

                            tstr += "{:0>4}".format(oldciti.getvatafipcode(inv, code))

                            total = oldciti.gettotforcodeimp(inv, code)
                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            tstr += "{:0>15}".format(total)

                            tstr += '\r\n'

                        if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '066' and \
                                len(oldciti.getallcodes2(inv)) >= 1 and len(vatcodes) == 0:
                            tstr += "{:0>15}".format(inv.document_number)

                            total = 0
                            tstr += "{:0>15}".format(total)

                            tstr += "{:0>4}".format(0)

                            total = 0
                            tstr += "{:0>15}".format(total)

                            tstr += '\r\n'
            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_s_imp': base64.encodestring(fp_str.getvalue()),
                    'file_name_s_imp': "LIBRO_IVA_DIGITAL_IMPORTACION_SERVICIOS_CREDITO_FISCAL.txt",
                    })
                fp_str.close()

        #SALES
        domain = [
            ('date', '>=', self.date_from),('date', '<=', self.date_to),
            ('type', '!=', 'in_invoice'),('type', '!=', 'in_refund'),('state', '=', 'cancel')
        ]
        invoiceModel = self.env['account.invoice']
        invoices = invoiceModel.search(domain,order="date_invoice")

        if self.LIBRO_IVA_DIGITAL_VENTAS_ANULADAS:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    tstr += inv.date_invoice[0:4] + inv.date_invoice[5:7] + inv.date_invoice[8:10]
                    tstr += "{:0>3}".format(inv.journal_document_type_id.document_type_id.code)
                    doc_nr = inv.document_number.split('-')
                    tstr += "{:0>5}".format(doc_nr[0])
                    tstr += "{:0>20}".format(doc_nr[1])
                    if inv.cancel_date:
                        tstr += inv.cancel_date[0:4] + inv.cancel_date[5:7] + inv.cancel_date[8:10]
                    else:
                        tstr += "NO__DATE"
                    tstr += '\r\n'
            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_null_cbte': base64.encodestring(fp_str.getvalue()),
                    'file_name_null_cbte': "LIBRO_IVA_DIGITAL_VENTAS_ANULADAS.txt",
                    })
                fp_str.close()



        #COMPRAS
        domain = [
            '&',('date', '>=', self.date_from),('date', '<=', self.date_to),
            ('type', '!=', 'out_invoice'),('type', '!=', 'out_refund'),'|',('state', '=', 'open'),
            ('state', '=', 'paid')
        ]
        invoiceModel = self.env['account.invoice']
        invoices = invoiceModel.search(domain,order="date_invoice")

        if self.LIBRO_IVA_DIGITAL_COMPRAS_CBTE:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    tstr += inv.date_invoice[0:4] + inv.date_invoice[5:7] + inv.date_invoice[8:10]
                    tstr += "{:0>3}".format(inv.journal_document_type_id.document_type_id.code)
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) != '066' \
                            and "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) != '067':

                        nr = inv.document_number.split('-')
                        tstr += "{:0>5}".format(nr[0]) + "{:0>20}".format(nr[1])
                        tstr += "{:>16}".format(' ')
                    else:
                        tstr += "{:0>25}".format('0')
                        tstr += "{:0>16}".format(inv.document_number)
                    tstr += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                    tstr += "{:0>20}".format(inv.partner_id.main_id_number)

                    tmpstr = remove_accents(inv.partner_id.name)

                    tstr += "{:<30}".format(tmpstr)

                    total = MultiplybyRate(inv.currency_rate, inv.amount_total, inv.company_currency_id,
                                           inv.currency_id)
                    tstr += "{:0>15}".format(total)

                    if inv.journal_document_type_id.document_type_id.document_letter_id.name == 'B' or \
                            inv.journal_document_type_id.document_type_id.document_letter_id.name == 'C':
                        total = 0
                    else:
                        total = converttolong(inv.gettotnovat(inv))
                    tstr += "{:0>15}".format(total)

                    if inv.journal_document_type_id.document_type_id.document_letter_id.name == 'B' or \
                            inv.journal_document_type_id.document_type_id.document_letter_id.name == 'C':
                        total = 0
                    else:
                        total = converttolong(inv.gettotexempt(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotpercep(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotprofit(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotgrossincome2(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotlocPercep(inv))
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotinttaxes(inv))
                    tstr += "{:0>15}".format(total)

                    tstr += "{:>3}".format(inv.currency_id.afip_code)

                    if inv.currency_id != inv.company_currency_id:
                        tstr += "{:0>10}".format(long(Decimal(inv.currency_rate).quantize(TWOPLACES) * 1000000))
                    else:
                        tstr += '0001000000'

                    vatcodesqty = oldciti.getvatcodeslistg3(inv)
                    vatimp = oldciti.getallcodes2(inv)
                    if inv.journal_document_type_id.document_type_id.document_letter_id.name == 'B' or \
                            inv.journal_document_type_id.document_type_id.document_letter_id.name == 'C':
                        tstr += '0'
                    elif len(vatimp) > 0 and vatcodesqty == 0:
                        tstr += '1'
                    else:
                        tstr += str(vatcodesqty)

                    if inv.fiscal_position_id.afip_code_purch == None:
                        tstr += '0'
                    else:
                        tstr += "{:>1}".format(inv.fiscal_position_id.afip_code_purch)

                    if inv.journal_document_type_id.document_type_id.document_letter_id.name != 'B' and \
                            inv.journal_document_type_id.document_type_id.document_letter_id.name != 'C':
                        total = oldciti.getgrandtotalvat(inv)
                    else:
                        total = 0
                    total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                    tstr += "{:0>15}".format(total)

                    total = converttolong(inv.gettotothers(inv))
                    tstr += "{:0>15}".format(total)

                    tstr += "{:0>11}".format(0)
                    tstr += "{:>30}".format(' ')
                    tstr += "{:0>15}".format(0)
                    tstr += '\r\n'

            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_p_cbte': base64.encodestring(fp_str.getvalue()),
                    'file_name_p_cbte': "LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt",
                    })
                fp_str.close()

        if self.LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS:
            tstr = ""
            for inv in invoices:
                if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) not in [
                    '066', '067', '006', '007', '008', '006', '009', '010', '011',
                    '012', '013', '015', '016', '061', '064', '082', '083', '111',
                    '113', '114', '116', '117'] and inv.journal_id.use_documents:

                    if inv.fiscal_position_id.afip_code == False:
                        vatcodes = oldciti.getallcodes(inv)
                    else:
                        vatcodes = oldciti.getallcodes2(inv)

                    for code in vatcodes:
                        tstr += "{:0>3}".format(inv.document_type_id.code)
                        tmp = inv.document_number.split('-')
                        if len(tmp) == 2:
                            tstr += "{:0>5}".format(tmp[0]) + "{:0>20}".format(tmp[1])
                        else:
                            tstr += "{:0>25}".format(tmp)
                        tstr += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                        tstr += "{:0>20}".format(inv.partner_id.main_id_number)
                        if inv.fiscal_position_id.afip_code == False:
                            if code in gARRAYVAT:
                                total = oldciti.getbaseforcode(inv, gARRAYVAT[code])
                            else:
                                total = 0
                        else:
                            total = 0

                        total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                        tstr += "{:0>15}".format(total)

                        if inv.fiscal_position_id.afip_code == False:
                            codetype = oldciti.getcodetype(inv, code)
                            tstr += "{:0>4}".format(codetype)
                        else:
                            tstr += "{:0>4}".format('3')

                        if code in gARRAYVAT:
                            total = oldciti.gettotforcode(inv, gARRAYVAT[code])
                        else:
                            total = 0
                        total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                        tstr += "{:0>15}".format(total)

                        # tstr_alic += "{:0>4}".format(long(self.gettaxperc(code)*100))
                        tstr += '\r\n'
            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_p_alic': base64.encodestring(fp_str.getvalue()),
                    'file_name_p_alic': "LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt",
                    })
                fp_str.close()

        if self.LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '066' or \
                            "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '067':

                        vatcodes = oldciti.getallcodesimp(inv)  # this is id of vatcode
                        for code in vatcodes:
                            tstr += "{:0>15}".format(inv.document_number)

                            total = oldciti.getbaseforcodeimp(inv, code)
                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            if total < 0:
                                total = total * -1
                                tstr += '-' + "{:0>14}".format(total)
                            else:
                                tstr += "{:0>15}".format(total)

                            tstr += "{:0>4}".format(oldciti.getvatafipcode(inv, code))

                            total = oldciti.gettotforcodeimp(inv, code)
                            total = MultiplybyRate(inv.currency_rate, total, inv.company_currency_id, inv.currency_id)
                            tstr += "{:0>15}".format(total)

                            tstr += '\r\n'

                        if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) == '066' and \
                                len(oldciti.getallcodes2(inv)) >= 1 and len(vatcodes) == 0:
                            tstr += "{:0>15}".format(inv.document_number)

                            total = 0
                            tstr += "{:0>15}".format(total)

                            tstr += "{:0>4}".format(0)

                            total = 0
                            tstr += "{:0>15}".format(total)

                            tstr += '\r\n'
            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_p_imp': base64.encodestring(fp_str.getvalue()),
                    'file_name_p_imp': "LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA.txt",
                    })
                fp_str.close()

        if self.LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE:
            tstr = ""
            for inv in invoices:
                if inv.journal_id.use_documents:
                    if "{:0>3}".format(inv.journal_document_type_id.document_type_id.code) in ('195', '196', '197'):
                        tstr += inv.date_invoice[0:4] + inv.date_invoice[5:7] + inv.date_invoice[8:10]
                        #print len(tstr)
                        tstr += "{:0>3}".format(inv.journal_document_type_id.document_type_id.code)
                        #print len(tstr)
                        doc_nr = inv.document_number.split('-')
                        tstr += "{:0>5}".format(doc_nr[0]) + "{:0>20}".format(doc_nr[1])
                        #print len(tstr)
                        tstr += "{:0>16}".format('0')
                        #print len(tstr)
                        tstr += "{:0>2}".format(inv.partner_id.main_id_category_id.afip_code)
                        #print len(tstr)
                        tstr += "{:0>20}".format(inv.partner_id.main_id_number)
                        #print len(tstr)
                        tmpstr = remove_accents(inv.partner_id.name)
                        tstr += "{:<30}".format(tmpstr[0:30])
                        #print len(tstr)

                        total = MultiplybyRate(inv.currency_rate, inv.amount_total, inv.company_currency_id,
                                               inv.currency_id)
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.gettotnovat(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        #tstr += '000000000000000'

                        total = converttolong(inv.gettotexempt(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.gettotpercep(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.getotherNP(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.gettotgrossincome2(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.gettotlocPercep(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        total = converttolong(inv.gettotinttaxes(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        tstr += "{:>3}".format(inv.currency_id.afip_code)
                        #print len(tstr)

                        if inv.currency_id != inv.company_currency_id:
                            tstr += "{:0>10}".format(long(Decimal(inv.currency_rate).quantize(TWOPLACES) * 1000000))
                        else:
                            tstr += '0001000000'
                        #print len(tstr)

                        vatcodesqty = oldciti.getvatcodeslistg3(inv)
                        tstr += str(vatcodesqty)
                        #print len(tstr)

                        if inv.fiscal_position_id.afip_code == None or inv.fiscal_position_id.afip_code == '0':
                            tstr += '1'
                        else:
                            tstr += "{:>1}".format(inv.fiscal_position_id.afip_code)
                        #print len(tstr)

                        tstr += '000000000000000'

                        total = converttolong(inv.gettotothers(inv))
                        tstr += "{:0>15}".format(total)
                        #print len(tstr)

                        tstr += '00000000000'
                        tstr += "{:>30}".format(' ')

                        tstr += '000000000000000'

                        #tstr += inv.date_due[0:4] + inv.date_due[5:7] + inv.date_due[8:10]
                        #print len(tstr)

                        total = converttolong(inv.gettotottaxrefund(inv))
                        tstr += "{:0>15}".format(total)

                        tstr += '\r\n'

            if tstr:
                fp_str = StringIO()
                fp_str.write(tstr)
                export_id.write({
                    'file_tc_cbte': base64.encodestring(fp_str.getvalue()),
                    'file_name_tc_cbte': "LIBRO_IVA_DIGITAL_COMPRAS_TurIVA_CBTE.txt",
                    })
                fp_str.close()

        return{
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.digital.vat',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }
