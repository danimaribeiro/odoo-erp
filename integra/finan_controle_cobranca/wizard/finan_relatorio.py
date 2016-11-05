# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import Report

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class finan_relatorio(osv.osv_memory):
    _inherit = 'finan.relatorio'

    _columns = {

    }

    _defaults = {

    }

    def gera_relatorio_controle_cobranca(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        filtro = {
            'data_inicial': rel_obj.data_inicial,
            'data_final': rel_obj.data_final,
        }

        sql = """
        select
            rp.name as empresa,
            cli.name as cliente,
            coalesce(cli.endereco,'') || ', ' || coalesce(cli.numero,'') as endereco,
            cli.bairro as bairro,
            coalesce(cli.fone, cli.celular) as telefone,
            cc.data as data_ligacao,
            cc.data_agendamento as data_agendamento,
            ru.name as usuario,
            co.name as cobrador,
            cc.vr_total,
            (select count(l.id)
            from finan_cobranca_itens cci
            join finan_lancamento l on l.id = cci.lancamento_id
            where
            cci.cobranca_id = cc.id) as lancamentos,
            cc.obs as observacao

        from finan_controle_cobranca cc
            join res_partner cli on cli.id = cc.partner_id
            join res_users ru on ru.id = cc.create_uid
            join res_users co on co.id = cc.cobrador_id
            left join res_company c on c.id = cc.company_id
            left join res_company ccc on cc.id = c.parent_id
            left join res_company cccc on cccc.id = ccc.parent_id
            left join res_company rp on rp.id = c.partner_id
        where
        """

        if rel_obj.provisionado:
            sql += """
            cc.data_agendamento between '{data_inicial}' and '{data_final}'
            """

        else:
            sql += """
            cc.data between '{data_inicial}' and '{data_final}'
            """

        if rel_obj.company_id:
            sql += """
                and (
                    c.id = {company_id}
                    or ccc.id = {company_id}
                    or cccc.id = {company_id}
                )
            """
            filtro['company_id'] = str(rel_obj.company_id.id)

        sql_relatorio = sql.format(**filtro)


        rel = Report('Relatório Controle de Cobrança', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_controle_cobranca.jrxml')
        rel.parametros['DATA_INICIAL'] = formata_data(rel_obj.data_inicial)
        rel.parametros['DATA_FINAL'] = formata_data(rel_obj.data_final)
        rel.parametros['SQL'] = sql_relatorio
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': 'Controle_Conbracao_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

finan_relatorio()
