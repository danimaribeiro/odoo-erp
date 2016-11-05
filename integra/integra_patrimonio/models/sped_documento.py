# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class sped_documento(osv.Model):
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    def ajusta_patrimonio(self, cr, uid, ids, context={}):
        if not ids:
            return

        for doc_obj in self.browse(cr, uid, ids):
            #
            # Somente cria o patrimônio para entrada
            # com notas de terceiros
            #
            if doc_obj.emissao == '0':
                continue

            for item_obj in doc_obj.documentoitem_ids:
                #
                # Somente valida a quantidade de patrimônios caso
                # haja pelo menos 1 associação de patrimônio com o
                # item da nota
                #
                if not len(item_obj.asset_ids):
                    continue

                #
                # Não valida se a quantidade de patrimônios bater
                # com a quantidade entrada no estoque
                #
                if len(item_obj.asset_ids) == int(item_obj.quantidade_estoque or 0):
                    continue

                #
                # Somente cria automaticamente os itens de patrimônio
                # para produtos com unidade de medida por "unidade"
                # (nunca metros, quilos etc. etc.)
                #
                if item_obj.produto_id.uom_id.category_id.name.upper() not in ['UNIT', 'UNIDADE']:
                    continue

                #
                # Pegamos o 1º item do Patrimônio, e duplicamos até a quantidade
                # necessária
                #
                patrimonio_obj = item_obj.asset_ids[0]

                qtd = int(item_obj.quantidade_estoque) - len(item_obj.asset_ids)
                for i in range(qtd):
                    novo_patrimonio_id = self.pool.get('account.asset.asset').copy(cr, uid, patrimonio_obj.id)
                    #
                    # Já ativa após a criação
                    #
                    self.pool.get('account.asset.asset').write(cr, uid, [novo_patrimonio_id], {'state': 'open'})
                    
                if patrimonio_obj.state == 'draft':
                    patrimonio_obj.write({'state': 'open'})

    def baixa_patrimonio(self, cr, uid, ids, context={}):
        if not ids:
            return

        for doc_obj in self.browse(cr, uid, ids):
            #
            # Somente baixa o patrimônio para
            # com notas próprias
            #
            if doc_obj.emissao != '0':
                continue

            if not doc_obj.operacao_id.baixa_patrimonio:
                continue

            for item_obj in doc_obj.documentoitem_ids:
                #
                # Somente valida a quantidade de patrimônios caso
                # haja pelo menos 1 associação de patrimônio com o
                # item da nota
                #
                if not len(item_obj.asset_ids):
                    continue

                for patrimonio_obj in item_obj.asset_ids:
                    patrimonio_obj.write({'state': 'close', 'data_baixa': doc_obj.data_emissao, 'nf_venda_id': doc_obj.id })

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documento, self).write(cr, uid, ids, dados, context={})
        self.pool.get('sped.documento').ajusta_patrimonio(cr, uid, ids, context)
        self.pool.get('sped.documento').baixa_patrimonio(cr, uid, ids, context)
        return res


sped_documento()
