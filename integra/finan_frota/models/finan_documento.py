# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields


class finan_documento(orm.Model):
    _name = 'finan.documento'
    _inherit = 'finan.documento'

    _columns = {
        'eh_ipva': fields.boolean(u'IPVA'),
        'eh_licenciamento': fields.boolean(u'Licenciamento'),
        'eh_dpvat': fields.boolean(u'DPAV'),
        'partner_id': fields.many2one('res.partner', u'Fornecedor'),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira'),
    }

    def create(self, cr, uid, dados, context={}):
        res = super(finan_documento, self).create(cr, uid, dados, context)
        id = res

        if 'eh_ipva' in dados and dados['eh_ipva']:
            cr.execute('update finan_documento set eh_ipva = False where id != {doc_id};'.format(doc_id=id))

        if 'eh_licenciamento' in dados and dados['eh_licenciamento']:
            cr.execute('update finan_documento set eh_licenciamento = False where id != {doc_id};'.format(doc_id=id))

        if 'eh_dpvat' in dados and dados['eh_dpvat']:
            cr.execute('update finan_documento set eh_dpvat = False where id != {doc_id};'.format(doc_id=id))

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_documento, self).write(cr, uid, ids, dados, context)

        id = ids[0]

        if 'eh_ipva' in dados and dados['eh_ipva']:
            cr.execute('update finan_documento set eh_ipva = False where id != {doc_id};'.format(doc_id=id))

        if 'eh_licenciamento' in dados and dados['eh_licenciamento']:
            cr.execute('update finan_documento set eh_licenciamento = False where id != {doc_id};'.format(doc_id=id))

        if 'eh_dpvat' in dados and dados['eh_dpvat']:
            cr.execute('update finan_documento set eh_dpvat = False where id != {doc_id};'.format(doc_id=id))

        return res


finan_documento()
