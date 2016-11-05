# -*- coding: utf-8 -*-

from osv import fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64
from decimal import Decimal as D


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')
TIPO_INTERNO = (
    ('R', u'Retorno'),
)


class stock_move(osv.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    def _get_custo_unitario(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #for id in ids:
            #res[id] = False

        #return res

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.location_id.location_custo_id:
                location_id =  item_obj.location_id.location_custo_id.id
            else:
                location_id =  item_obj.location_id.id

            sql_saldo = """
            select
                coalesce(s.quantidade, 0) as quantidade,
                coalesce(s.vr_unitario_medio, 0) as vr_unitario_custo

            from
                stock_saldo s
            where
                s.company_id = {company_id}
                and s.data = '{data}'
                and s.product_id = {product_id}
                and s.location_id = {location_id};
            """

            sql_custo = """
               select
                   coalesce(cm.vr_unitario_custo, 0) as vr_unitario_custo

               from
                   custo_medio({company_id}, {location_id}, {product_id}) cm

               where
                   cm.data <= '{data}'

               order by
                   cm.data desc, cm.entrada_saida desc, cm.move_id desc

               limit 1;
            """
            sql_saldo = sql_saldo.format(company_id=item_obj.company_id.id,location_id=location_id, product_id=item_obj.product_id.id,data=item_obj.date[:10])
            sql_custo = sql_custo.format(company_id=item_obj.company_id.id,location_id=location_id, product_id=item_obj.product_id.id,data=item_obj.date[:10])

            print(sql_saldo)
            cr.execute(sql_saldo)
            dados = cr.fetchall()

            if len(dados) == 0:
                print(sql_custo)
                cr.execute(sql_custo)
                dados = cr.fetchall()

            if len(dados) == 0:
                res[item_obj.id] = 0
            else:
                res[item_obj.id] = D(dados[0][0] or 0)

        return res

    _columns = {
        'vr_custo_unitario': fields.function(_get_custo_unitario, type='float', string=u'Valor Custo Unitário', digits=(18, 4), store=True),
        'name': fields.char(u'Nome', size=250, required=False, select=True),
        'romaneio': fields.integer(u'Romaneio', select=True),
        'operacao_id': fields.many2one('stock.operacao', u'Operação', select=True),

        #
        # Campos somente leitura
        #
        'company_readonly_id': fields.many2one('res.company', u'Empresa', readonly=True),
        'location_readonly_id': fields.many2one('stock.location', u'Local de origem', readonly=True),
        'location_dest_readonly_id': fields.many2one('stock.location', u'Local de destino', readonly=True),
        'operacao_readonly_id': fields.many2one('stock.operacao', u'Operação', readonly=True),
    }

    def ajusta_romaneio(self, cr, uid, ids):
        for move_obj in self.pool.get('stock.move').browse(cr, uid, ids):
            if move_obj.state == 'done':
                if move_obj.picking_id:
                    #
                    # Inventário em cliente não troca os lançamentos pra operação de agora
                    #
                    if move_obj.picking_id.type == 'invcli':
                        continue

                    if not move_obj.picking_id.operacao_id:
                        raise osv.except_osv(u'Inválido !', u'É preciso escolher a operação de estoque para o romaneio!')

                    if not move_obj.picking_id.romaneio:
                        move_obj.picking_id.romaneio = 1

                    location_id = move_obj.picking_id.location_id.id
                    location_dest_id = move_obj.picking_id.location_dest_id.id
                    romaneio = move_obj.picking_id.romaneio
                    operacao_id = move_obj.picking_id.operacao_id.id

                    cr.execute('''
                        update stock_move set
                        romaneio = %d, location_id = %d, location_dest_id = %d,
                        operacao_id = %d
                        where id = %d and state='done' and (romaneio is null or romaneio = 0);
                        ''' % (romaneio, location_id, location_dest_id, operacao_id, move_obj.id))

    def create(self, cr, uid, dados, context={}):
        res = super(stock_move, self).create(cr, uid, dados, context=context)

        self.pool.get('stock.move').ajusta_romaneio(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(stock_move, self).write(cr, uid, ids, dados, context=context)

        self.pool.get('stock.move').ajusta_romaneio(cr, uid, ids)

        return res

    def unlink(self, cr, uid, ids, context={}):
        if context is None:
            context = {}

        ctx = context.copy()

        for move in self.browse(cr, uid, ids, context=context):
            if move.state not in ['draft', 'waiting', 'confirmed', 'assigned'] and not ctx.get('call_unlink',False):
                raise osv.except_osv(u'Aviso!', u'Você está tentando excluir uma movimentação de estoque que está confirmada ou cancelada!')

        return super(osv.Model, self).unlink(cr, uid, ids, context=ctx)

    def onchange_product_id(self, cr, uid, ids,  prod_id=False, loc_id=False, loc_dest_id=False, address_id=False):
        res = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, address_id=address_id)

        if 'value' in res and prod_id:
            produto_obj = self.pool.get('product.product').browse(cr, uid, prod_id)

            if getattr(produto_obj, 'orcamento_categoria_id', False):
                res['value']['orcamento_categoria_id'] = produto_obj.orcamento_categoria_id.id

        return res

    def onchange_operacao_id(self, cr, uid, ids, operacao_id, company_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not operacao_id:
            return res

        operacao_obj = self.pool.get('stock.operacao').browse(cr, uid, operacao_id)
        picking_pool = self.pool.get('stock.picking')
        picking_pool._valida_operacao_empresa(cr, uid, operacao_id, company_id)

        #valores['company_id'] = operacao_obj.company_id.id
        if operacao_obj.location_id:
            valores['location_id'] = operacao_obj.location_id.id
        if operacao_obj.location_dest_id:
            valores['location_dest_id'] = operacao_obj.location_dest_id.id
        #valores['note'] = operacao_obj.obs

        #if getattr(operacao_obj, 'familiatributaria_ids', False):
            #familiatributaria_ids = []
            #for ft_obj in operacao_obj.familiatributaria_ids:
                #familiatributaria_ids.append(ft_obj.id)

            #valores['familiatributaria_ids'] = familiatributaria_ids

        return res


stock_move()
