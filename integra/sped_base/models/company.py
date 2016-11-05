# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class res_company(osv.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.cnpj_cpf:
                res[obj.id] = obj.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    _columns = {
        'cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', string=u'CNPJ', store=True),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True),
        'photo': fields.text(string=u'Logo Base64'),
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
    }

    def copy(self, cr, uid, id, dados, context={}):
        #if 'name' not in dados:
        c_obj = self.pool.get('res.company').browse(cr, uid, id)
        dados['name'] = c_obj.name.strip() + u' (cópia)'
        dados['partner_id'] = False

        return super(res_company, self).copy(cr, uid, id, default=dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'logo' in dados:
            dados['photo'] = dados['logo']
        return super(res_company, self).write(cr, uid, ids, dados, context=context)

res_company()
