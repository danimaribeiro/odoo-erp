# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora, hoje, mes_passado, primeiro_dia_mes, ultimo_dia_mes
import base64
from relatorio import *
from finan.wizard.finan_relatorio import Report
from pybrasil.valor.decimal import Decimal as D


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

class crm_claim_relatorio(osv.osv_memory):
    _name = 'crm.claim.relatorio'
    _description = u'CRM Relatório de atendimento'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'company_id': fields.many2one('res.company', u'Empresa'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.claim.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'formato': 'pdf',
    }

    def gera_relatorio_atendimento(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            rp.name as empresa,
            cl.date,
            cli.name as cliente,
            ru.name as responsavel,
            rua.name as responsavel_atendimento,
            ct.name as estado_emocional,
            d.name as setor_envolvido,
            cl.description as descricao,
            cl.cause as diagnostico,
            e.nome as funcionario_envolvido,
            cl.resolution as medidas

            from crm_claim cl
            join res_company c on c.id = cl.company_id
            join res_partner rp on rp.id = c.partner_id
            join res_partner cli on cli.id = cl.partner_id
            join res_users ru on ru.id = cl.user_id
            left join hr_department d on d.id = cl.departamento_id
            left join hr_employee e on e.id = cl.employee_id
            left join res_users rua on rua.id = cl.user_atendimento
            left join crm_case_categ ct on ct.id = cl.categ_id

        where
            cl.date between '{data_inicial}' and '{data_final}'
            and (
                c.id = {company_id}
                or c.parent_id = {company_id}
            )"""

        sql += """
        order by
            rp.name,
            cl.date,
            cli.name;"""

        filtro = {
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
            'company_id': rel_obj.company_id.id,
        }

        sql = sql.format(**filtro)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Relatório de Atendimento', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'crm_relatorio_atendimento.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql

        pdf, formato = rel.execute()

        dados = {
            'nome': u'RELATORIO_ATENDIMENTOS_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True



crm_claim_relatorio()


