# -*- coding: utf-8 -*-


from osv import osv, fields


class orcamento_comissao(osv.Model):
    _name = 'orcamento.comissao'

    _columns = {
        'name': fields.char(u'Tabela de comissão', size=64),
        'tipo': fields.selection((('V', 'Venda'), ('L', 'Locação')), u'Tipo'),
        'comissao_item_ids': fields.one2many('orcamento.comissao_item', 'comissao_id', u'Itens de comissão'),
    }


orcamento_comissao()


class orcamento_comissao_item(osv.Model):
    _name = 'orcamento.comissao_item'
    _description = u'Itens de tabela de comissão'
    _order = 'comissao_id, margem, meses_retorno_investimento'

    _columns = {
        'comissao_id': fields.many2one('orcamento.comissao', u'Tabela de comissão', ondelete='cascade'),
        'margem': fields.float(u'Máximo de margem'),
        'comissao_preco_minimo': fields.float(u'Comissão (%) para preço mínimo'),
        'comissao': fields.float(u'Comissão (%) para preço venda/sugerido'),
        'meses_retorno_investimento': fields.float(u'Máximo meses para recuperação do investimento'),
        'grupo_aprovacao_id': fields.many2one('orcamento.grupo.aprovacao', u'Grupo com permissão mínima de aprovação'),
    }
    _rec_name = 'comissao'
    _order = 'comissao'


orcamento_comissao_item()
