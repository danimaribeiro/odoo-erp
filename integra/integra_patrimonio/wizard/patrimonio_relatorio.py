# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class patrimonio_relatorio(osv.osv_memory):
    _name = 'patrimonio.relatorio'
    _description = u'Relatórios de Patrimônio'

    _columns = {
        'situacao': fields.selection([['A', u'Ativo'], ['B', u'Baixado'], ['T', u'Todos']], u'Situação'),
        #'data_inicial': fields.date(u'Data inicial'),
        #'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'category_id': fields.many2one('account.asset.category', u'Categoria'),

        'nome': fields.char(u'Nome do arquivo', 254, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 254, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),

        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro Custo'),
        #'conta_id': fields.many2one('finan.conta', u'Conta financeira'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'patrimonio.relatorio', context=c),
        'situacao': 'T'
    }


    def gera_relatorio_patrimonio(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            sql = """
                select
                    case
                       when patri.state != 'done' then 'Ativo  '
                       else 'Baixado'
                    end as situacao,
                    coalesce(cc.nome_completo, '') as centro_custo,
                    coalesce(categ.name, '') as categoria,
                    coalesce(patri.code, '') as plaqueta,
                    patri.purchase_date as data_compra,
                    coalesce(patri.name, '') as produto,
                    coalesce(patri.purchase_value, 0) as valor_compra,
                    coalesce(patri.salvage_value, 0) as valor_depreciado,
                    coalesce(patri.purchase_value, 0) - coalesce(patri.salvage_value, 0) as valor_residual,
                    (select
                      d.data_emissao_brasilia

                    from
                        sped_documentoitem_patrimonio dip
                        join sped_documentoitem di on di.id = dip.sped_documentoitem_id
                        join sped_documento d on d.id = di.documento_id
                        join sped_operacao op on op.id = d.operacao_id

                    where
                      op.baixa_patrimonio = True
                      and dip.asset_id = patri.id

                    order by
                     d.data_emissao_brasilia

                    limit 1) as data_baixa,
                    (select
                      coalesce(di.vr_nf, 0)

                    from
                        sped_documentoitem_patrimonio dip
                        join sped_documentoitem di on di.id = dip.sped_documentoitem_id
                        join sped_documento d on d.id = di.documento_id
                        join sped_operacao op on op.id = d.operacao_id

                    where
                      op.baixa_patrimonio = True
                      and dip.asset_id = patri.id

                    order by
                     d.data_emissao_brasilia

                    limit 1) as valor_baixa,
                    (select
                      d.numero

                    from
                        sped_documentoitem_patrimonio dip
                        join sped_documentoitem di on di.id = dip.sped_documentoitem_id
                        join sped_documento d on d.id = di.documento_id
                        join sped_operacao op on op.id = d.operacao_id

                    where
                      op.baixa_patrimonio = True
                      and dip.asset_id = patri.id

                    order by
                     d.data_emissao_brasilia

                    limit 1) as nf_baixa

                from
                    account_asset_asset patri
                    join res_company c on c.id = patri.company_id
                    left join account_asset_category categ on categ.id = patri.category_id
                    left join finan_centrocusto cc on cc.id = patri.centrocusto_id

                where
                    (patri.company_id = {company_id} or c.parent_id = {company_id})
            """

            filtro = {
                'company_id': rel_obj.company_id.id
            }
            filtro_texto = u'Empresa/unidade: ' + rel_obj.company_id.name

            if rel_obj.category_id:
                sql += """
                    and patri.category_id = {category_id}
                    """
                filtro['category_id'] = rel_obj.category_id.id
                filtro_texto += u'; Categoria: ' + rel_obj.category_id.name

            if rel_obj.centrocusto_id:
                sql += """
                    and patri.centrocusto_id = {centrocusto_id}
                    """
                filtro['centrocusto_id'] = rel_obj.centrocusto_id.id
                filtro_texto += u'; Centro de custo: ' + rel_obj.centrocusto_id.nome_completo

            if rel_obj.situacao == 'A':
                sql += """
                        and patri.state != 'close'
                    """
                filtro_texto += u'; Somente ativos'

            elif rel_obj.situacao == 'B':
                sql += """
                        and patri.state = 'close'
                    """
                filtro_texto += u'; Somente baixados'

            sql += """
                order by
                    categoria,
                    plaqueta,
                    data_compra,
                    produto;
                """

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for situacao, centro_custo, categoria, plaqueta, data_compra, produto, valor_compra, valor_depreciado, valor_residual, data_baixa, valor_baixa, nf_baixa in dados:
                linha = DicionarioBrasil()
                linha['situacao'] = situacao
                linha['categoria'] = categoria
                linha['plaqueta'] = plaqueta
                linha['data_compra'] = formata_data(data_compra)
                linha['produto'] = produto
                linha['valor_compra'] = D(valor_compra)
                linha['valor_depreciado'] = D(valor_depreciado)
                linha['valor_residual'] = D(valor_residual)
                linha['data_baixa'] = ''
                linha['valor_baixa'] = ''
                linha['nf_baixa'] = ''
                linha['centro_custo'] = centro_custo

                if data_baixa:
                    linha['data_baixa'] = formata_data(data_baixa)
                    linha['valor_baixa'] = formata_valor(valor_baixa).rjust(10)
                    linha['nf_baixa'] = formata_valor(nf_baixa, casas_decimais=0).rjust(7)

                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Patrimônio'
            rel.band_page_header.elements[-1].text = filtro_texto

            rel.colunas = [
                ['plaqueta', 'C', 10, u'Plaqueta', False, 'E'],
                ['data_compra', 'C', 10, u'Aquisição', False, 'E'],
                ['produto', 'C', 80, u'Produto', False, 'E'],
                ['valor_compra', 'F', 10, u'Vr. Aquisição', True, 'D'],
                ['valor_depreciado', 'F', 10, u'Vr.Deprec.', True, 'D'],
                ['valor_residual', 'F', 10, u'Vr. Residual', True, 'D'],
                ['centro_custo', 'C', 40, u'Centro de custo', False, 'E'],
                ['data_baixa', 'C', 10, u'Baixa', False, 'E'],
                ['valor_baixa', 'C', 10, u'Vr. Baixa', False, 'D'],
                ['nf_baixa', 'C', 7, u'NF Baixa', False, 'D'],
            ]

            rel.monta_detalhe_automatico(rel.colunas)
            rel.monta_contagem = True

            rel.grupos = [
                ['categoria', u'Categoria', False],
            ]
            rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'patrimonio_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


patrimonio_relatorio()
