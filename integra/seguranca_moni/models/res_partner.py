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


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'moni_ids': fields.one2many('importa.moni', 'partner_id', u'Contratos no MONI'),
    }


res_partner()
