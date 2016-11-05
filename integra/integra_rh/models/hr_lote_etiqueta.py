# -*- coding: utf-8 -*-

from osv import fields, osv
#from pybrasil.data import parse_datetime
from hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from finan.wizard.finan_relatorio import Report
import os
import base64


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class hr_lote_etiqueta(osv.osv_memory):
    _name = 'hr.lote_etiqueta'
    _rec_name = 'company_id'
    _description = u'Lotes de etiquetas'
    _order = 'ano desc, mes desc, company_id'

    def get_employee_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        etiqueta_pool = self.pool.get('hr.employee')

        for lote_etiqueta_obj in self.browse(cr, uid, ids):
            dados = {
                'company_id': lote_etiqueta_obj.company_id.id,
            }

            sql = """
                select
                    c.id

                from hr_contract c
                join res_company co on co.id = c.company_id
                join hr_employee e on e.id = c.employee_id

                where
                    (c.date_end is null)
                    and (c.jornada_segunda_a_sexta_id is not null or c.jornada_escala_id is not null)
                    and (c.company_id = {company_id} or co.parent_id = {company_id})
                order by
                    e.nome;""".format(**dados)

            cr.execute(sql)
            etiquetas_ids_lista = cr.fetchall()
            etiqueta_ids = []
            for dados in etiquetas_ids_lista:
                etiqueta_ids.append(dados[0])
            res[lote_etiqueta_obj.id] = etiqueta_ids

        return res


    _columns = {
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'company_id': fields.many2one('res.company', u'Unidade/Empresa', select=True),
        #'contract_ids': fields.function(get_employee_ids, type='one2many', relation='hr.contract', method=True, string=u'Contratos a gerar'),
        'contract_ids': fields.many2many('hr.contract', 'hr_lote_etiqueta_contract', 'lote_id', 'contract_id', u'Contratos a gerar'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
    }

    def atualizar_dados(self, cr, uid, ids, context={}):
        lote_holerite_id = ids[0]

        lote_holerite_obj = self.browse(cr, uid, lote_holerite_id)

        res = {}
        valores = {}
        res['value'] = valores

        contract_ids = []
        for contract_obj in lote_holerite_obj.contract_ids:
            contract_ids.append(contract_obj.id)

        valores['contract_ids'] = contract_ids

        return res

    def gerar_etiquetas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        lote_etiqueta_id = ids[0]

        rel = Report('Lote Etiquetas', cr, uid)
        lote_etiqueta_obj = self.browse(cr, uid, lote_etiqueta_id)

        res = {}
        valores = {}
        res['value'] = valores

        contracts = []
        for contrato_obj in lote_etiqueta_obj.contract_ids:
            contracts.append(contrato_obj.id)

        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'etiqueta_empregado.jrxml')
        etiqueta = 'etiqueta_empregado.pdf'

        di, data_competencia = primeiro_ultimo_dia_mes(lote_etiqueta_obj.ano, int(lote_etiqueta_obj.mes))

        rel.parametros['DATA_ANO'] = str(lote_etiqueta_obj.mes) +"/"+ str(lote_etiqueta_obj.ano)
        rel.parametros['REGISTRO_IDS'] =  str(tuple(contracts)).replace("u'", "'").replace(',)', ')')
        rel.parametros['DATA_COMPETENCIA'] = str(data_competencia)

        pdf, formato = rel.execute()

        dados = {
            'nome': u'lote_etiquetas.pdf',
            'arquivo': base64.encodestring(pdf)
        }
        lote_etiqueta_obj.write(dados)
        return True


hr_lote_etiqueta()
