# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from relatorio import *
from finan.wizard.relatorio import FinanRelatorioAutomaticoRetrato

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'
    _name = 'finan.relatorio'

    _columns = {
                 
    }

    _defaults = {
               
    }



finan_relatorio()
