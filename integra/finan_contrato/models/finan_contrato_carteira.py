# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes
from finan_contrato import NATUREZA


class finan_contrato_ajuste_carteira(osv.Model):
    _description = u'Contrato - Ajustar carteira'
    _name = 'finan.contrato.ajuste.carteira'
    _order = 'data_carteira desc'

    _columns = {
        'natureza': fields.selection(NATUREZA, u'Natureza'),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira anterior', ondelete='restrict'),
        'carteira_nova_id': fields.many2one('finan.carteira', u'Carteira nova', ondelete='restrict'),
        'company_id': fields.many2one('res.company', u'Empresa/Grupo', ondelete='restrict'),
        'data_ajuste': fields.date(u'Data do ajuste'),
        'partner_id': fields.many2one('res.partner', u'Cliente', ondelete='restrict'),
        'contrato_excecoes_ids': fields.many2many('finan.contrato', 'finan_contrato_ajuste_carteira_excecao', 'ajuste_id', 'contrato_id', u'Exceções ao ajuste'),
        'contrato_reajustar_ids': fields.one2many('finan.contrato.ajuste.carteira.contrato', 'ajuste_id', u'Contratos a reajustar'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
    }

    _defaults = {
        'natureza': 'R',
        'data_carteira': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def buscar_contratos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('finan.contrato.ajuste.carteira.contrato')
        contrato_pool = self.pool.get('finan.contrato')

        for ajuste_obj in self.browse(cr, uid, ids):
            if ajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse ajuste já foi confirmado e não pode ser refeito!')

            #
            # Exclui os contratos incluídos anteriormente
            #
            for cont_obj in ajuste_obj.contrato_reajustar_ids:
                cont_obj.unlink()

            #
            # Faz uma lista dos contratos a serem excluídos do ajuste
            #
            excecao = []
            for cont_obj in ajuste_obj.contrato_excecoes_ids:
                excecao += [cont_obj.id]

            sql = '''
            select
                c.id
            from
                finan_contrato c
                join res_company cc on cc.id = c.company_id
            where
                c.ativo = True and
                (cc.id = {company_id}
                or cc.parent_id = {company_id}
                )
                and c.carteira_id = {carteira_id}
                and c.natureza = '{natureza}'
                and (
                    c.data_carteira between '{data_inicial}' and '{data_final}'
                    or c.data_carteira is null
                )
            '''

            filtro = {
                'company_id': ajuste_obj.company_id.id,
                'carteira_id': ajuste_obj.carteira_id.id,
                'natureza': ajuste_obj.natureza,
                'excecoes': str(excecao).replace('[', '').replace(']', ''),
                'data_inicial': ajuste_obj.data_inicial,
                'data_final': ajuste_obj.data_final,
            }

            if len(excecao) > 0:
                sql += '''
                and c.id not in ({excecoes})
                '''

            if ajuste_obj.partner_id:
                filtro['partner_id'] = ajuste_obj.partner_id.id
                sql += '''
                and c.partner_id = {partner_id}
                '''

            sql = sql.format(**filtro)
            print(sql)

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            for id, in dados:
                contrato_obj = contrato_pool.browse(cr, uid, id)
                dados_item = {
                    'ajuste_id': ajuste_obj.id,
                    'contrato_id': id,
                }
                item_pool.create(cr, uid, dados_item)


    def efetiva_carteira(self, cr, uid, ids, context={}):
        for ajuste_obj in self.browse(cr, uid, ids):
            if ajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse ajuste já foi confirmado e não pode ser refeito!')

            if not ajuste_obj.data_confirmacao:
                raise osv.except_osv(u'Erro!', u'Para efetivar o ajuste, é preciso preencher a data e hora de confirmação!')

            #
            # Vamos agora varrer todos os contratos a serem reajustados
            #
            for item_obj in ajuste_obj.contrato_reajustar_ids:
                item_obj.contrato_id.write({'carteira_id': ajuste_obj.carteira_id.id})
                item_obj.contrato_id.gera_todas_parcelas()

            #
            # Agora, trava o ajuste, para não ser mais alterado
            #
            ajuste_obj.write({'confirmado': True})

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Não deixa alterar ajustes confirmados
        #
        for ajuste_obj in self.browse(cr, uid, ids):
            if ajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse ajuste já foi confirmado e não pode ser alterado!')

        return super(finan_contrato_ajuste_carteira, self).write(cr, uid, ids, dados, context=context)

    def unlink(self, cr, uid, ids, context={}):
        #
        # Não deixa excluir ajustes confirmados
        #
        for ajuste_obj in self.browse(cr, uid, ids):
            if ajuste_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Esse ajuste já foi confirmado e não pode ser excluído!')

        return super(finan_contrato_ajuste_carteira, self).unlink(cr, uid, ids, context=context)


finan_contrato_ajuste_carteira()


class finan_contrato_ajuste_carteira_contrato(osv.Model):
    _description = u'Itens do ajuste'
    _name = 'finan.contrato.ajuste.carteira.contrato'
    _order = 'ajuste_id, contrato_id'

    _columns = {
        'ajuste_id': fields.many2one('finan.contrato.ajuste.carteira', u'Ajuste', required=True, ondelete="cascade"),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="restrict"),

        'company_id': fields.related('contrato_id', 'company_id', relation='res.company', string=u'Empresa', type='many2one'),
        'numero': fields.related('contrato_id', 'numero', type='char', string=u'Número'),
        'partner_id': fields.related('contrato_id', 'partner_id', relation='res.partner', string=u'Parceiro', type='many2one'),
    }


finan_contrato_ajuste_carteira_contrato()
