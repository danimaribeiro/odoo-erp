# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class purchase_solicitacao_cotacao(osv.Model):
    _name = 'purchase.solicitacao.cotacao'
    _description = u'Solicitação de materiais'
    _order = 'data desc, codigo'
    _rec_name = 'codigo'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for purchase_cotacao in self.browse(cr, uid, ids):
            res[purchase_cotacao.id] = purchase_cotacao.id

        return res
    
    def _cotacao_aprovada(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for id in ids:
            res[id] = False
            
            sql = """
            select
                pc.id
            
            from
                purchase_solicitacao_cotacao_item_orcado pscio
                join purchase_cotacao_item_solicitacao pcis on pcis.solicitacao_item_id = pscio.id
                join purchase_cotacao pc on pc.id = pcis.cotacao_id
                
            where
                pscio.solicitacao_id = {id}
                and pc.situacao = 'F'
                
            order by
                pc.data desc
                
            limit 1;
            """     
            sql = sql.format(id=id)
            cr.execute(sql)
            dados = cr.fetchall()
            
            if len(dados) and dados[0][0]:
                res[id] = dados[0][0]
            
        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=True, select=True),
        'company_id': fields.many2one('res.company',string=u'Empresa'),
        'data': fields.date(u'Data'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
        'solicitante_id': fields.many2one('res.users', u'Solicitante'),
        'aprovador_id': fields.many2one('res.users', u'Aprovador'),
        'data_hora_aprovacao': fields.datetime(u'Data de aprovação'),
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De data'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A data'),
        'obs': fields.text(u'Observações'),
        
        'item_pre_orcado_ids': fields.one2many('purchase.solicitacao.cotacao.item.orcado', 'solicitacao_id', u'Itens pré-orçados'),
        
        'planejamento_ids': fields.many2many('project.orcamento.item.planejamento', 'purchase_solicitacao_planejamento', 'solicitacao_id', 'planejamento_id', u'Planejamentos'),
        'item_ids': fields.many2many('project.orcamento.item', 'purchase_solicitacao_item', 'solicitacao_id', 'item_id', u'Itens do orçamento'),
        
        'cotacao_aprovada_id': fields.function(_cotacao_aprovada, type='many2one', relation='purchase.cotacao', string=u'Cotação aprovada'),
    }

    _defaults = {
        'data': fields.date.today,
        #'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'purchase.cotacao', context=c),
    }

    def create(self, cr, uid, dados, context={}):
        dados['solicitante_id'] = uid

        return super(purchase_solicitacao_cotacao, self).create(cr, uid, dados, context)

    def aprovar(self, cr, uid, ids, context={}):
        solicitacao_pool = self.pool.get('purchase.solicitacao.cotacao')
        item_pool = self.pool.get('project.orcamento.item')
        

        solicitacao_pool.write(cr, uid, ids, {'aprovador_id': uid, 'data_hora_aprovacao': fields.datetime.now()})
        
        for id in ids:
            cr.execute('update purchase_solicitacao_cotacao_item_orcado set aprovado = true where solicitacao_id = {id}'.format(id=id))
        
        return True
        #item_ids = item_pool.search(cr, uid, [('solicitacao_id', 'in', ids)])
        #item_pool.write(cr, uid, item_ids, {'situacao': 'A'})
        
    def alimenta_solicitacao(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('purchase.solicitacao.cotacao.item.orcado')
        
        for solicitacao_obj in self.browse(cr, uid, ids):
            for item_obj in solicitacao_obj.item_pre_orcado_ids:
                item_obj.unlink()
                
            item_ja_lancado = []
            for planejamento_obj in solicitacao_obj.planejamento_ids:
                dados = {
                    'solicitacao_id': solicitacao_obj.id,
                    'item_id': planejamento_obj.item_id.id,
                    'planejamento_id': planejamento_obj.id,
                    'product_id': planejamento_obj.item_id.product_id.id,
                    'quantidade': planejamento_obj.quantidade or 0,
                    'centrocusto_id': planejamento_obj.item_id.centrocusto_id.id if planejamento_obj.item_id.centrocusto_id else False
                }
                item_pool.create(cr, uid, dados)
                item_ja_lancado.append(planejamento_obj.item_id.id)
                
            for item_obj in solicitacao_obj.item_ids:
                if item_obj.id in item_ja_lancado:
                    continue
                
                dados = {
                    'solicitacao_id': solicitacao_obj.id,
                    'item_id': item_obj.id,
                    'planejamento_id': False,
                    'product_id': item_obj.product_id.id,
                    'quantidade': item_obj.quantidade or 0,
                    'centrocusto_id': item_obj.centrocusto_id.id if item_obj.centrocusto_id else False
                }
                item_pool.create(cr, uid, dados)
                
        return True


purchase_solicitacao_cotacao()
