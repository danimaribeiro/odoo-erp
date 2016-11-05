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


class hr_reajuste_cargo(osv.Model):
    _name = 'hr.reajuste_cargo'
    _description = u'Alteração de Cargos'
    _rec_name = 'descricao'
    _order = 'data desc'

    _columns = {
        'descricao': fields.char(u'Descrição', size=30),
        'data': fields.date(u'Data da alteração'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'cargos_reajustar_ids': fields.one2many('hr.reajuste.cargo.lancamento', 'reajuste_cargo_id', u'Cargos a reajustar'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        'company_id': fields.many2one('res.company', u'Empresa', select=True, ondelete='restrict'),

        'sindicato_id': fields.many2one('res.partner', u'Filiação sindical', ondelete='restrict'),
        'excluir_sindicato': fields.boolean(u'Excluir?'),
        'contrato_excluido_ids': fields.many2many('hr.contract', 'hr_reajuste_cargo_excluido', 'reajuste_cargo_id', 'contract_id'),
        'create_uid': fields.many2one('res.users', u'Confirmado por:', ondelete='restrict'),

        'funcao_id': fields.many2one('hr.job', u'Cargo', select=True, ondelete='restrict'),
        'excluir_funcao': fields.boolean(u'Excluir?'),

        'new_funcao_id': fields.many2one('hr.job', u'Novo Cargo/Atividade', select=True, ondelete='restrict'),
        'cbo_id': fields.many2one('hr.cbo', u'CBO', select=True, ondelete='restrict'),
        'excluir_cbo': fields.boolean(u'Excluir?'),

        'motivo_id': fields.many2one('hr.motivo.alteracao.contratual', u'Motivo', ondelete='restrict'),

        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'excluir_centrocusto': fields.boolean(u'Excluir?'),

        'nome_arquivo': fields.char(u'Nome arquivo', size=120),
        'arquivo': fields.binary(u'Relatório de alteração'),
    }

    _defaults = {
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def buscar_contratos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('hr.reajuste.cargo.lancamento')
        contrato_pool = self.pool.get('hr.contract')

        for reajuste_obj in self.browse(cr, uid, ids):
            if reajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Essa alteração já foi confirmada e não pode ser refeita!')

            #
            # Exclui os contratos incluídos anteriormente
            #
            for cont_obj in reajuste_obj.cargos_reajustar_ids:
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
                c.date_end is Null
                and cc.id = {company_id}
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

                dados_item = {
                    'reajuste_cargo_id': reajuste_obj.id,
                    'contrato_id': id,
                    'company_id': contrato_obj.company_id.id,
                    'cbo_id': reajuste_obj.new_funcao_id.cbo_id.id  if reajuste_obj.new_funcao_id.cbo_id else False,
                    'centrocusto_id': contrato_obj.centrocusto_id.id if contrato_obj.centrocusto_id else False,
                    'old_job_id': contrato_obj.job_id.id,
                    'new_job_id': reajuste_obj.new_funcao_id.id,
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
                raise osv.except_osv(u'Erro!', u'Essa alteração já foi confirmada e não pode ser refeita!')

            if not reajuste_obj.data_confirmacao:
                raise osv.except_osv(u'Erro!', u'Para efetivar a alteração, é preciso preencher a data e hora de confirmação!')

            #
            # Vamos agora varrer todos os contratos a serem reajustados
            #
            for item_obj in reajuste_obj.cargos_reajustar_ids:
                dados = {
                    'contract_id': item_obj.contrato_id.id,
                    'tipo_alteracao': 'C',
                    'data_alteracao': reajuste_obj.data,
                    'regime_trabalhista': item_obj.contrato_id.regime_trabalhista,
                    'regime_previdenciario': item_obj.contrato_id.regime_previdenciario,
                    'natureza_atividade': item_obj.contrato_id.natureza_atividade,
                    'categoria_trabalhador': item_obj.contrato_id.categoria_trabalhador,
                    'job_id': item_obj.new_job_id.id,
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
            for item_obj in reajuste_obj.cargos_reajustar_ids:
                linha = DicionarioBrasil()
                linha['contrato'] = item_obj.contrato_id.descricao or ''
                linha['cbo'] = item_obj.cbo_id.codigo if item_obj.cbo_id else ''
                linha['centrocusto'] = item_obj.centrocusto_id.nome if item_obj.centrocusto_id else ''
                linha['old_job_id'] = item_obj.old_job_id.name or ''
                linha['new_job_id'] = item_obj.new_job_id.name or ''

                linhas.append(linha)

            if not len(linhas):
                return {}

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Alteração de Cargos ' + formata_data(reajuste_obj.data)

            if reajuste_obj.data_confirmacao:
                rel.title += ' - conf. ' + formata_data(reajuste_obj.data_confirmacao, formato='%d/%m/%Y %H:%M:%S')

            rel.monta_contagem = True
            rel.colunas = [
                ['contrato'   , 'C', 90, u'Contrato', False],
                ['cbo'   , 'C', 6, u'CBO', False],
                ['centrocusto'   , 'C', 30, u'Centro de custo', False],
                ['old_job_id' , 'C', 20, u'Cargo Antigo', True],
                ['new_job_id', 'C', 20, u'Novo Cargo', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['local', u'Local', False],
            #]
            #rel.monta_grupos(rel.grupos)
            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome_arquivo': 'alteracao_cargo.pdf',
                'arquivo': base64.encodestring(pdf),
            }

            return dados

        def write(self, cr, uid, ids, dados, context={}):
            for r_obj in self.browse(cr, uid, ids):
                if r_obj.confirmado:
                    raise osv.except_osv(u'Erro!', u'É proibido alterar o registro de alteração confirmado!')

            return super(hr_reajuste_cargo, self).write(cr, uid, ids, dados, context=context)

        def unlink(self, cr, uid, ids, context={}):
            for r_obj in self.browse(cr, uid, ids):
                if r_obj.confirmado:
                    raise osv.except_osv(u'Erro!', u'É proibido alterar o registro de alteração confirmado!')

            return super(hr_reajuste_cargo, self).unlink(cr, uid, ids, context=context)


hr_reajuste_cargo()


class hr_reajuste_cargo_lancamento(osv.Model):
    _description = u'Itens do reajuste de cargo'
    _name = 'hr.reajuste.cargo.lancamento'

    _columns = {
        'reajuste_cargo_id': fields.many2one(u'hr.reajuste_cargo', u'Reajuste Cargo', required=True, ondelete="cascade"),
        'contrato_id': fields.many2one('hr.contract', u'Contrato', required=True, ondelete="restrict"),

        'company_id': fields.many2one('res.company', string=u'Empresa', select=True, ondelete='restrict'),
        'cbo_id': fields.many2one('hr.cbo', string=u'CBO', select=True, ondelete='restrict'),
        'centrocusto_id': fields.many2one('finan.centrocusto', string=u'Centro de custo', select=True, ondelete='restrict'),

        'old_job_id': fields.many2one('hr.job', string=u'Antigo Cargo', select=True, ondelete='restrict'),
        'new_job_id': fields.many2one('hr.job', string=u'Novo Cargo', select=True, ondelete='restrict'),
    }


hr_reajuste_cargo_lancamento()