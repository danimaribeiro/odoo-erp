# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_contrato(osv.Model):
    _inherit = 'finan.contrato'

    _columns = {
        'contrato_vendedor_ids': fields.one2many('finan.contrato.vendedor', 'contrato_id', u'Vendedores - histórico'),
    }

    #def onchange_sale_order_id(self, cr, uid, ids, company_id, sale_order_id, context={}):
        #res = {}
        #valores = {}
        #res['value'] = valores

        #if sale_order_id:
            #order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

            #valores['partner_id'] = order_obj.partner_id.id

            #if getattr(order_obj, 'hr_department_id', False):
                #valores['hr_department_id'] = order_obj.hr_department_id.id

            #if getattr(order_obj, 'grupo_economico_id', False):
                #valores['grupo_economico_id'] = order_obj.grupo_economico_id.id

            #if getattr(order_obj, 'res_partner_category_id', False):
                #valores['res_partner_category_id'] = order_obj.res_partner_category_id.id

            #valores['vendedor_id'] = order_obj.user_id.id

        #return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_contrato, self).write(cr, uid, ids, dados, context=context)

        sql = '''
        update finan_contrato c set
            vendedor_id = (
                select
                    cv.vendedor_id
                from
                    finan_contrato_vendedor cv
                where
                    cv.contrato_id = {contrato_id}
                    and cv.data_final is null
                order by
                    cv.data_inicial desc
                limit 1
            )
        where
            c.id = {contrato_id}
            and exists(select cv.id from finan_contrato_vendedor cv where cv.contrato_id = {contrato_id});
        '''
        for id in ids:
            cr.execute(sql.format(contrato_id=id))

        return res


finan_contrato()


class finan_contrato_vendedor(osv.Model):
    _name = 'finan.contrato.vendedor'
    _description = u'Vendedores do contrato'
    _order = 'contrato_id, data_inicial desc'

    def _get_data_final(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for cv_obj in self.browse(cr, uid, ids):
            sql = """
            select
                fcv.data_inicial - interval '1 day'
            from
                finan_contrato_vendedor fcv
            where
                fcv.contrato_id = {contrato_id}
                and fcv.data_inicial > '{data}'
            order by
                fcv.data_inicial
            limit 1;
            """
            sql = sql.format(contrato_id=cv_obj.contrato_id.id, data=cv_obj.data_inicial)
            cr.execute(sql)
            dados = cr.fetchall()

            res[cv_obj.id] = False
            if len(dados):
                res[cv_obj.id] = dados[0][0]

        return res

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'vendedor_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
        'data_inicial': fields.date(u'Data inicial', index=True),
        'data_final': fields.function(_get_data_final, type='date', string=u'Data final', store=True, index=True),
        'forca_ajuste': fields.datetime(u'Força ajuste'),
    }

    def _ajusta_datas(self, cr, uid, contrato_ids):
        for contrato_id in contrato_ids:
            item_ids = self.pool.get('finan.contrato.vendedor').search(cr, uid, [('contrato_id', '=', contrato_id)])
            self.pool.get('finan.contrato.vendedor').write(cr, uid, item_ids, {'forca_ajuste': str(fields.datetime.now())})

    def _busca_contratos(self, cr, uid, ids):
        contrato_ids = []
        for cv_obj in self.browse(cr, uid, ids):
            if cv_obj.contrato_id.id not in contrato_ids:
                contrato_ids.append(cv_obj.contrato_id.id)

        return contrato_ids

    def create(self, cr, uid, dados, context={}):
        res = super(finan_contrato_vendedor, self).create(cr, uid, dados, context=context)

        contrato_ids = self.pool.get('finan.contrato.vendedor')._busca_contratos(cr, uid, [res])
        contrato_ids = self.pool.get('finan.contrato.vendedor')._ajusta_datas(cr, uid, contrato_ids)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_contrato_vendedor, self).write(cr, uid, ids, dados, context=context)

        if 'forca_ajuste' not in dados:
            contrato_ids = self.pool.get('finan.contrato.vendedor')._busca_contratos(cr, uid, ids)
            contrato_ids = self.pool.get('finan.contrato.vendedor')._ajusta_datas(cr, uid, contrato_ids)

        return res

    def unlink(self, cr, uid, ids, context={}):
        contrato_ids = self.pool.get('finan.contrato.vendedor')._busca_contratos(cr, uid, ids)

        res = super(finan_contrato_vendedor, self).unlink(cr, uid, ids, context=context)

        contrato_ids = self.pool.get('finan.contrato.vendedor')._ajusta_datas(cr, uid, contrato_ids)

        return res


finan_contrato_vendedor()