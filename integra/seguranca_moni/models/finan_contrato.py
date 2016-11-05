# -*- encoding: utf-8 -*-


from decimal import Decimal as D
from osv import osv, fields
#from plano_contas_antigo import PLANO_CONTAS
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from moni import le_arquivo_moni
from pybrasil.inscricao import *
from pybrasil.data import hoje
from dateutil.relativedelta import relativedelta
from exporta_moni import Moni


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    def exporta_moni(self, cr, uid, ids, context={}):
        for contrato_obj in self.browse(cr, uid, ids):
            moni = Moni()

            moni.cnpj_cpf = contrato_obj.partner_id.cnpj_cpf or ''
            moni.ie_rg = contrato_obj.partner_id.ie or ''
            moni.fantasia = contrato_obj.partner_id.fantasia or ''
            moni.razao_social = contrato_obj.partner_id.razao_social or ''
            moni.contrato_id = contrato_obj.id
            moni.fone = []

            if contrato_obj.partner_id.fone:
                moni.fone.append(contrato_obj.partner_id.fone)

            if contrato_obj.partner_id.celular:
                moni.fone.append(contrato_obj.partner_id.celular)

            moni.endereco = contrato_obj.partner_id.endereco or ''
            moni.numero = contrato_obj.partner_id.numero or ''
            moni.bairro = contrato_obj.partner_id.bairro or ''
            moni.cidade = contrato_obj.partner_id.cidade or ''
            moni.estado = contrato_obj.partner_id.estado or ''
            moni.cep = contrato_obj.partner_id.cep or ''
            moni.numero_contrato = contrato_obj.numero or ''
            moni.valor = D(contrato_obj.valor_mensal or 0)

            if contrato_obj.partner_id.address:
                moni.contato = contrato_obj.partner_id.address[0].name or ''

                if contrato_obj.partner_id.address[0].phone and contrato_obj.partner_id.address[0].phone not in moni.fone:
                    moni.fone.append(contrato_obj.partner_id.address[0].phone)

                if contrato_obj.partner_id.address[0].mobile and contrato_obj.partner_id.address[0].mobile not in moni.fone:
                    moni.fone.append(contrato_obj.partner_id.address[0].mobile)

                if contrato_obj.partner_id.address[0].fax and contrato_obj.partner_id.address[0].fax not in moni.fone:
                    moni.fone.append(contrato_obj.partner_id.address[0].fax)

            else:
                moni.contato = contrato_obj.partner_id.name or ''

            moni.host = '191.8.127.83'

            print('moni.cadastra_cliente()', moni.cadastra_cliente())




finan_contrato()
