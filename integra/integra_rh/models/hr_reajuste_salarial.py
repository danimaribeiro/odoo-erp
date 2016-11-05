# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from pybrasil.inscricao import limpa_formatacao
from pybrasil.data import parse_datetime, mes_passado, primeiro_dia_mes, ultimo_dia_mes, data_hora_horario_brasilia, formata_data
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import decimal
from pybrasil.valor import formata_valor
import base64
from dateutil.relativedelta import relativedelta
from sped.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil



METODO_ARREDONDAMENTO = [
    [decimal.ROUND_HALF_EVEN, 'ABNT; para zero (< 0,5[02468]): 0,125 => 0,12 => 0,1; -0,125 => -0,12 => -0,1'],
    [decimal.ROUND_HALF_UP, 'Para zero (> 0,5): 0,125 => 0,13 => 0,1; -0,125 => -0,13 => -0,1'],
    [decimal.ROUND_HALF_DOWN, 'Para zero (< 0,5): 0,125 => 0,12 => 0,1; -0,125 => -0,12 => -0,1'],
    [decimal.ROUND_DOWN, 'Para zero: 0,125 => 0,12 => 0,1; -0,125 => -0,12 => -0,1'],
    [decimal.ROUND_CEILING, 'Para +Infinito: 0,125 => 0,13 => 0,2; -0,125 => -0,12 => -0,1'],
    [decimal.ROUND_FLOOR, 'Para -Infinito: 0,125 => 0,12 => 0,1; -0,125 => -0,13 => -0,2'],
    [decimal.ROUND_05UP, 'Para zero (0,[12346789]): 0,125 => 0,12 => 0,1; -0,125 => -0,12 => -0,1'],
    [decimal.ROUND_UP, 'Para cima: 0,125 => 0,13 => 0,2; -0,125 => -0,13 => -0,2'],
]
METODO_ARREDONDAMENTO_DICT = dict(METODO_ARREDONDAMENTO)



class hr_reajuste_salarial(osv.Model):
    _name = 'hr.reajuste_salarial'
    _description = u'Reajuste Salarial'
    _order = 'data_confirmacao desc, data desc'

    _columns = {
        'data': fields.date(u'Data do reajuste'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'contrato_reajustar_ids': fields.one2many('hr.reajuste.salarial.contrato', 'reajuste_salarial_id', u'Contratos a reajustar'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        #'contract_alteracao_ids': fields.one2many('hr.contract_alteracao', 'reajuste_salarial_id', u'Contratos alterados'),
        'company_id': fields.many2one('res.company', u'Empresa', select=True, ondelete='restrict'),
        'valor': fields.float(u'Valor', digits=(18,6)),
        'sindicato_id': fields.many2one('res.partner', u'Filiação sindical', ondelete='restrict'),
        'excluir_sindicato': fields.boolean(u'Excluir?'),
        'contrato_excluido_ids': fields.many2many('hr.contract', 'hr_reajuste_salario_excluido', 'reajuste_salarial_id', 'contract_id'),
        'user_id': fields.many2one('res.users', u'Confirmado por:', ondelete='restrict'),
        'arredondamento': fields.selection(METODO_ARREDONDAMENTO, u'Arredondamento'),
        'funcao_id': fields.many2one('hr.job', u'Função', select=True, ondelete='restrict'),
        'excluir_funcao': fields.boolean(u'Excluir?'),
        'cbo_id': fields.many2one('hr.cbo', u'CBO', select=True, ondelete='restrict'),
        'excluir_cbo': fields.boolean(u'Excluir?'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'excluir_centrocusto': fields.boolean(u'Excluir?'),
        'gerar_folha_complementar': fields.boolean(u'Gerar folha complementar?'),
        'motivo_id': fields.many2one('hr.motivo.alteracao.contratual', u'Motivo', ondelete='restrict'),

        'nome_arquivo': fields.char(u'Nome arquivo', size=120),
        'arquivo': fields.binary(u'Relatório de reajuste'),
    }

    _defaults = {
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'arredondamento': decimal.ROUND_HALF_EVEN,
    }

    def buscar_contratos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('hr.reajuste.salarial.contrato')
        contrato_pool = self.pool.get('hr.contract')

        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser refeito!')

            #
            # Exclui os contratos incluídos anteriormente
            #
            for cont_obj in reajuste_obj.contrato_reajustar_ids:
                cont_obj.unlink()

            #
            # Faz uma lista dos contratos a serem excluídos do reajuste
            #
            excecao = []
            for cont_obj in reajuste_obj.contrato_excluido_ids:
                excecao += [cont_obj.id]


            sql = '''
            select
                c.id
            from
                hr_contract c
                join res_company cc on cc.id = c.company_id
                join hr_employee e on e.id = c.employee_id
                join hr_job f on f.id = c.job_id
                left join hr_cbo cbo on cbo.id = f.cbo_id

            where
                c.date_end is Null and
                (cc.id = {company_id}
                or cc.parent_id = {company_id}
                )
                and c.date_start <= '{data_reajuste}'
            '''

            filtro = {
                'company_id': reajuste_obj.company_id.id,
                'excecoes': str(excecao).replace('[', '').replace(']', ''),
                'data_reajuste': reajuste_obj.data,
            }
            if len(excecao) > 0:
                sql += '''
                and c.id not in ({excecoes})
                '''

            if reajuste_obj.sindicato_id:
                filtro['sindicato_id'] = reajuste_obj.sindicato_id.id

                if reajuste_obj.excluir_sindicato:
                    sql += '''
                        and c.sindicato_id != {sindicato_id}
                    '''
                else:
                    sql += '''
                        and c.sindicato_id = {sindicato_id}
                    '''

            if reajuste_obj.funcao_id:
                filtro['funcao_id'] = reajuste_obj.funcao_id.id

                if reajuste_obj.excluir_funcao:
                    sql += '''
                        and c.job_id != {funcao_id}
                    '''
                else:
                    sql += '''
                        and c.job_id = {funcao_id}
                    '''

            if reajuste_obj.cbo_id:
                filtro['cbo_codigo'] = reajuste_obj.cbo_id.codigo

                if reajuste_obj.excluir_cbo:
                    sql += '''
                        and cbo.codigo != '{cbo_codigo}'
                    '''
                else:
                    sql += '''
                        and cbo.codigo = '{cbo_codigo}'
                    '''

            if reajuste_obj.centrocusto_id:
                filtro['centrocusto_id'] = reajuste_obj.centrocusto_id.id

                if reajuste_obj.excluir_centrocusto:
                    sql += '''
                        and c.centrocusto_id != {centrocusto_id}
                    '''
                else:
                    sql += '''
                        and c.centrocusto_id = {centrocusto_id}
                    '''

            sql += '''
                    order by
                        e.nome
                    '''

            sql = sql.format(**filtro)
            print(sql)

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            for id, in dados:
                contrato_obj = contrato_pool.browse(cr, uid, id)
                valor_novo = D(contrato_obj.wage) * (D(1) + (D(reajuste_obj.valor) /  D(100)))
                valor_novo = valor_novo.quantize(D('0.01'), reajuste_obj.arredondamento or decimal.ROUND_HALF_EVEN)

                dados_item = {
                    'reajuste_salarial_id': reajuste_obj.id,
                    'contrato_id': id,
                    'company_id': contrato_obj.company_id.id,
                    'job_id': contrato_obj.job_id.id,
                    'cbo_id': contrato_obj.job_id.cbo_id.id if contrato_obj.job_id.cbo_id else False,
                    'centrocusto_id': contrato_obj.centrocusto_id.id if contrato_obj.centrocusto_id else False,
                    'valor_antigo': contrato_obj.wage,
                    'valor_novo': valor_novo,
                }
                item_pool.create(cr, uid, dados_item)

            #
            # Agora, cria a listagem
            #
            dados = self._relatorio_reajuste(cr, uid, [reajuste_obj.id])
            reajuste_obj.write(dados)

    def confirmar_reajuste(self, cr, uid, ids, context={}):
        alteracao_pool = self.pool.get('hr.contract_alteracao')

        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse reajuste já foi confirmado e não pode ser refeito!')

            if not reajuste_obj.data_confirmacao:
                raise osv.except_osv(u'Erro!', u'Para efetivar o reajuste, é preciso preencher a data e hora de confirmação!')

            #
            # Vamos agora varrer todos os contratos a serem reajustados
            #
            for item_obj in reajuste_obj.contrato_reajustar_ids:
                dados = {
                    'contract_id': item_obj.contrato_id.id,
                    'tipo_alteracao': 'R',
                    'data_alteracao': reajuste_obj.data,
                    'wage': item_obj.valor_novo,
                    'unidade_salario': item_obj.contrato_id.unidade_salario,
                    'horas_mensalista': item_obj.contrato_id.horas_mensalista,
                    'struct_id': item_obj.contrato_id.struct_id.id,
                    'motivo_id': reajuste_obj.motivo_id.id,
                }

                alteracao_pool.create(cr, uid, dados)

            #
            # Agora, cria a listagem
            #
            dados = self._relatorio_reajuste(cr, uid, [reajuste_obj.id])
            reajuste_obj.write(dados)

            #
            # Agora, trava o reajuste, para não ser mais alterado
            #
            reajuste_obj.write({'confirmado': True})

    def _relatorio_reajuste(self, cr, uid, ids, context={}):
        for reajuste_obj in self.browse(cr, uid, ids):
            linhas = []
            for item_obj in reajuste_obj.contrato_reajustar_ids:
                linha = DicionarioBrasil()
                linha['contrato'] = item_obj.contrato_id.descricao or ''
                #linha['empresa'] = item_obj.company_id.name if item_obj.company_id else ''
                linha['funcao'] = item_obj.job_id.name if item_obj.job_id else ''
                linha['cbo'] = item_obj.cbo_id.codigo if item_obj.cbo_id else ''
                linha['centrocusto'] = item_obj.centrocusto_id.nome if item_obj.centrocusto_id else ''
                linha['valor_antigo'] = D(item_obj.valor_antigo or 0)
                linha['valor_novo'] = D(item_obj.valor_novo or 0)

                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Reajuste Salarial ' + formata_data(reajuste_obj.data)

            if reajuste_obj.data_confirmacao:
                rel.title += ' - conf. ' + formata_data(reajuste_obj.data_confirmacao, formato='%d/%m/%Y %H:%M:%S')

            rel.monta_contagem = True
            rel.colunas = [
                ['contrato'   , 'C', 100, u'Contrato', False],
                #['empresa'   , 'C', 60, u'Empresa', False],
                ['funcao'   , 'C', 30, u'Função', False],
                ['cbo'   , 'C', 6, u'CBO', False],
                ['centrocusto'   , 'C', 30, u'Centro de custo', False],
                ['valor_antigo' , 'F', 10, u'Valor antigo', True],
                ['valor_novo', 'F', 10, u'Valor novo', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['local', u'Local', False],
            #]
            #rel.monta_grupos(rel.grupos)

            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Percentual '
            filtro.text += formata_valor(reajuste_obj.valor, casas_decimais=6)
            filtro.text += '% - Arredondamento '
            filtro.text += METODO_ARREDONDAMENTO_DICT[reajuste_obj.arredondamento]

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome_arquivo': 'reajuste_salarial.pdf',
                'arquivo': base64.encodestring(pdf),
            }

            return dados

        def write(self, cr, uid, ids, dados, context={}):
            for r_obj in self.browse(cr, uid, ids):
                if r_obj.confirmado:
                    raise osv.except_osv(u'Erro!', u'É proibido alterar o registro de reajuste confirmado!')

            return super(hr_reajuste_salarial, self).write(cr, uid, ids, dados, context=context)

        def unlink(self, cr, uid, ids, context={}):
            for r_obj in self.browse(cr, uid, ids):
                if r_obj.confirmado:
                    raise osv.except_osv(u'Erro!', u'É proibido alterar o registro de reajuste confirmado!')

            return super(hr_reajuste_salarial, self).unlink(cr, uid, ids, context=context)


hr_reajuste_salarial()


class hr_reajuste_salarial_contrato(osv.Model):
    _description = u'Itens do reajuste salarial'
    _name = 'hr.reajuste.salarial.contrato'

    _columns = {
        'reajuste_salarial_id': fields.many2one(u'hr.reajuste_salarial', u'Reajuste Salarial', required=True, ondelete="cascade"),
        'contrato_id': fields.many2one('hr.contract', u'Contrato', required=True, ondelete="restrict"),

        'company_id': fields.many2one('res.company', string=u'Empresa', select=True, ondelete='restrict'),
        'job_id': fields.many2one('hr.job', string=u'Função', select=True, ondelete='restrict'),
        'cbo_id': fields.many2one('hr.cbo', string=u'CBO', select=True, ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', string=u'Centro de custo', select=True, ondelete='restrict'),

        'valor_antigo': fields.float(u'Valor antigo'),
        'valor_novo': fields.float(u'Valor novo'),
    }


hr_reajuste_salarial_contrato()
