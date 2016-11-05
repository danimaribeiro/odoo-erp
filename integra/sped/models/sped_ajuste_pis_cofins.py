# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *
from sped_calcula_impostos import calcula_pis_cofins


class sped_ajuste_pis_cofins(orm.Model):
    _name = 'sped.ajuste.pis.cofins'
    _description = u'Ajuste de PIS-COFINS por NCM e CFOP'
    _order = 'data_inicial desc, data_final desc'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'ncm_ids': fields.many2many('sped.ncm', 'sped_ajuste_pis_cofins_ncm', 'ajuste_id', 'ncm_id', u'NCMs'),
        'cfop_ids': fields.many2many('sped.cfop', 'sped_ajuste_pis_cofins_cfop', 'ajuste_id', 'cfop_id', u'CFOPs'),
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Nova alíquota e CST do PIS-COFINS', select=True, ondelete='restrict'),
        'cst_pis_cofins': fields.selection(ST_PIS, u'Nova situação tributária', select=True),
        'item_ids': fields.one2many('sped.ajuste.pis.cofins.item', 'ajuste_id', u'Itens das notas'),

        'confirmado': fields.boolean(u'Confirmado?'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        'confirmador_id': fields.many2one('res.users', u'Confirmado por'),
    }

    def buscar_itens(self, cr, uid, ids, context={}):
        documentoitem_pool = self.pool.get('sped.documentoitem')
        ajusteitem_pool = self.pool.get('sped.ajuste.pis.cofins.item')

        sql = """
        select
            di.id

        from
            sped_documento d
            join sped_documentoitem di on di.documento_id = d.id
            join product_product p on p.id = di.produto_id

        where
            d.company_id = {company_id}
            and d.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
            and di.cfop_id in {cfop_ids}
            and p.ncm_id in {ncm_ids}
            and di.al_pis_cofins_id != {al_pis_cofins_id}
            and di.cst_pis != '{cst_pis_cofins}';
        """

        for ajuste_obj in self.browse(cr, uid, ids, context=context):
            if ajuste_obj.confirmado:
                continue

            if len(ajuste_obj.ncm_ids) == 0:
                continue

            if len(ajuste_obj.cfop_ids) == 0:
                continue

            filtro = {
                'company_id': ajuste_obj.company_id.id,
                'data_inicial': ajuste_obj.data_inicial,
                'data_final': ajuste_obj.data_final,
                'cst_pis_cofins': ajuste_obj.cst_pis_cofins,
                'al_pis_cofins_id': ajuste_obj.al_pis_cofins_id.id,
            }

            ncm_ids = []
            for ncm_obj in ajuste_obj.ncm_ids:
                ncm_ids.append(ncm_obj.id)

            filtro['ncm_ids'] = str(tuple(ncm_ids)).replace(',)', ')')

            cfop_ids = []
            for cfop_obj in ajuste_obj.cfop_ids:
                cfop_ids.append(cfop_obj.id)

            filtro['cfop_ids'] = str(tuple(cfop_ids)).replace(',)', ')')

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            print(dados)

            for item_obj in ajuste_obj.item_ids:
                item_obj.unlink()

            for di_id, in dados:
                item_obj = documentoitem_pool.browse(cr, 1, di_id)

                dados_item = {
                    'ajuste_id': ajuste_obj.id,
                    'documentoitem_id': di_id,
                    'al_pis_cofins_id': item_obj.al_pis_cofins_id.id if item_obj.al_pis_cofins_id else False,
                    'cst_pis_cofins': item_obj.cst_pis,
                }
                ajusteitem_pool.create(cr, uid, dados_item)

        return {}

    def confirmar_itens(self, cr, uid, ids, context={}):
        for ajuste_obj in self.browse(cr, uid, ids, context=context):
            if ajuste_obj.confirmado:
                continue

            if len(ajuste_obj.ncm_ids) == 0:
                continue

            if len(ajuste_obj.cfop_ids) == 0:
                continue

            al_pis_cofins_obj = ajuste_obj.al_pis_cofins_id
            for item_obj in ajuste_obj.item_ids:
                item_nota_obj = item_obj.documentoitem_id

                item_nota_obj.md_pis_proprio = al_pis_cofins_obj.md_pis_cofins
                item_nota_obj.al_pis_proprio = al_pis_cofins_obj.al_pis or 0
                item_nota_obj.md_cofins_proprio = al_pis_cofins_obj.md_pis_cofins
                item_nota_obj.al_cofins_proprio = al_pis_cofins_obj.al_cofins or 0

                if item_nota_obj.documento_id.entrada_saida == '0':
                    item_nota_obj.cst_pis = al_pis_cofins_obj.cst_pis_cofins_entrada
                    item_nota_obj.cst_cofins = al_pis_cofins_obj.cst_pis_cofins_entrada

                else:
                    item_nota_obj.cst_pis = al_pis_cofins_obj.cst_pis_cofins_saida
                    item_nota_obj.cst_cofins = al_pis_cofins_obj.cst_pis_cofins_saida

                atual = calcula_pis_cofins(self, cr, uid, item_nota_obj)
                atual['id'] = item_nota_obj.id
                atual['al_pis_cofins_id'] = al_pis_cofins_obj.id
                atual['al_pis_proprio'] = item_nota_obj.al_pis_proprio or 0
                atual['al_cofins_proprio'] = item_nota_obj.al_pis_proprio or 0

                sql = """
                update sped_documentoitem set
                    al_pis_cofins_id = {al_pis_cofins_id},
                    cst_pis = '{cst_pis}',
                    md_pis_proprio = '{md_pis_proprio}',
                    bc_pis_proprio = {bc_pis_proprio},
                    al_pis_proprio = {al_pis_proprio},
                    vr_pis_proprio = {vr_pis_proprio},
                    cst_cofins = '{cst_pis}',
                    md_cofins_proprio = '{md_cofins_proprio}',
                    bc_cofins_proprio = {bc_cofins_proprio},
                    al_cofins_proprio = {al_cofins_proprio},
                    vr_cofins_proprio = {vr_cofins_proprio}
                where
                    id = {id};
                """
                sql = sql.format(**atual)
                #print(sql)
                cr.execute(sql)

            ajuste_obj.write({'confirmado': True, 'confirmador_id': uid, 'data_confirmacao': fields.datetime.now()})

        return {}


sped_ajuste_pis_cofins()



class sped_ajuste_pis_cofins_item(orm.Model):
    _name = 'sped.ajuste.pis.cofins.item'
    _description = u'Item de ajuste de PIS-COFINS por NCM e CFOP'

    _columns = {
        'ajuste_id': fields.many2one('sped.ajuste.pis.cofins', u'Ajuste', ondelete='cascade'),
        'documentoitem_id': fields.many2one('sped.documentoitem', u'Item da NF', ondelete='restrict'),
        'documento_id': fields.related('documentoitem_id', 'documento_id', type='many2one', relation='sped.documento', string=u'NF'),
        'product_id': fields.related('documentoitem_id', 'produto_id', type='many2one', relation='product.product', string=u'Produto'),
        'cfop_id': fields.related('documentoitem_id', 'cfop_id', type='many2one', relation='sped.cfop', string=u'CFOP'),
        'ncm_id': fields.related('product_id', 'ncm_id', type='many2one', relation='sped.ncm', string=u'NCM'),
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota e CST do PIS-COFINS', select=True, ondelete='restrict'),
        'cst_pis_cofins': fields.selection(ST_PIS, u'Situação tributária anterior', select=True),
    }


sped_ajuste_pis_cofins_item()
