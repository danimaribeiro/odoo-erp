# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class res_partner_bank(orm.Model):
    _name = 'res.partner.bank'
    _inherit = 'res.partner.bank'
    _rec_name = 'descricao'

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        #bank_type_obj = self.pool.get('res.partner.bank.type')
        res = []
        #for val in self.browse(cr, uid, ids, context=context):
            #result = val.acc_number
            #if val.state:
                #type_ids = bank_type_obj.search(cr, uid, [('code','=',val.state)])
                #if type_ids:
                    #t = bank_type_obj.browse(cr, uid, type_ids[0], context=context)
                    #try:
                        ## avoid the default format_layout to result in "False: ..."
                        #if not val._data[val.id]['bank_name']:
                            #val._data[val.id]['bank_name'] = _('BANK')
                        #result = t.format_layout % val._data[val.id]
                    #except:
                        #result += ' [Formatting Error]'
                        #raise
            #res.append((val.id, result))

        for banco_obj in self.browse(cr, uid, ids):
            texto = banco_obj.bank_name or ''
            texto += ' - ' + (banco_obj.agencia or '')
            texto += '/' + (banco_obj.acc_number or '')

            if banco_obj.partner_id:
                texto += ' - ' + banco_obj.partner_id.name

            res += [(banco_obj.id, texto)]

        return res

    def name_search(self, cr, uid, texto='', args=None, operador='ilike', context={}, limit=100):
        procura = [
            '|', '|', '|', '|',
             ('bank_name', 'ilike', texto),
            ('agencia', 'ilike', texto),
            ('acc_number', 'ilike', texto),
            ('state', 'ilike', texto),
            ('partner_id.name', 'ilike', texto),
        ]

        #cnpj_cpf = None
        #if context.get('default_cnpj_cpf', False):
            #cnpj_cpf = context['default_cnpj_cpf']
        #elif context.get('default_cnpj', False):
            #cnpj_cpf = context['default_cnpj']

        #if cnpj_cpf:
            #print('cnpj_cpf', cnpj_cpf)

            #if len(cnpj_cpf) == 18:
                #procura = ['&', ('partner_id.cnpj_cpf', 'ilike', cnpj_cpf[:10])] + procura

            #else:
                #procura = ['&', ('partner_id.cnpj_cpf', '=', cnpj_cpf)] + procura

        procura +=  args

        ids = self.pool.get('res.partner.bank').search(cr, uid, procura, context=context, limit=limit)

        res = self.pool.get('res.partner.bank').name_get(cr, uid, ids, context)

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context={}):
        if not len(ids):
            return {}

        res = []
        for banco_obj in self.browse(cr, uid, ids):
            texto = banco_obj.bank_name or ''
            texto += ' - ' + banco_obj.agencia or ''
            texto += '/' + banco_obj.acc_number or ''

            if banco_obj.partner_id:
                texto += ' - ' + banco_obj.partner_id.name or ''

            res += [(banco_obj.id, texto + ' xxx')]

        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context={}):
        texto = args[0][2]

        procura = [
            ('bank_name', 'ilike', texto),
            ('agencia', 'ilike', texto),
            ('acc_number', 'ilike', texto),
            ('state', 'ilike', texto),
            ('partner_id.name', 'ilike', texto),
        ]

        print('args', args)

        if context.get('default_raiz_cnpj', False):
            procura += [('partner_id.cnpj_cpf', 'ilike', context.get('default_raiz_cnpj'))]

        return procura

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.cnpj_cpf:
                res[obj.id] = obj.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    def _get_tipo_funcao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        if not len(ids):
            return {}

        tipo_pool = self.pool.get('res.partner.bank.type')

        res = {}
        for banco_obj in self.browse(cr, uid, ids):

            res[banco_obj.id] = u''

            tipo_ids = tipo_pool.search(cr, uid, [('code', '=', banco_obj.state)])
            if tipo_ids:
                tipo_obj = tipo_pool.browse(cr, uid, tipo_ids[0])
                res[banco_obj.id] = tipo_obj.name or u''

        return res

    def _procura_tipo(self, cr, uid, modelo, nome_campo, domain, context={}):
        print(domain)
        texto = domain[0][2]
        operador = domain[0][1]

        if ' ' not in texto:
            res = [('state', operador, texto)]
        else:
            palavras = texto.split()
            pesquisa = []
            for palavra in palavras:
                pesquisa.append(['state', operador, palavra])

            tam = len(pesquisa)
            res = ['|'] * (tam - 1)
            res += pesquisa

        print(res)

        return res

    _columns = {
        'conta_digito': fields.char(u'Conta - dígito', size=1),
        'agencia': fields.char(u'Agência', size=5),
        'agencia_digito': fields.char(u'Agência - dígito', size=1),
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', store=True, select=True),  #, fnct_search=_procura_nome),
        'descricao': fields.function(_get_nome_funcao, type='char', string=u'Descrição', store=True, fnct_search=_procura_nome),
        'saldo_inicial': fields.float(u'Saldo inicial'),
        'data_saldo_inicial': fields.date(u'Data do saldo inicial'),
        'cnpj_cpf': fields.related('partner_id', 'cnpj_cpf', type='char', string=u'CNPJ/CPF', store=True, select=True),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True, select=True),
        'name': fields.char(u'Nome', size=64, required=True, translate=False, select=True),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira/contábil'),
        'tipo': fields.function(_get_tipo_funcao, type='char', string=u'Tipo', store=False, select=True, fnct_search=_procura_tipo),
        'codigo_convenio': fields.char(u'Código do convênio no banco', size=10),
    }

    _defaults = {
        'state': 'bank',
    }


res_partner_bank()



class res_partner_bank_type(orm.Model):
    _description='Bank Account Type'
    _name = 'res.partner.bank.type'
    _order = 'name'
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=False, select=True),
        'code': fields.char('Code', size=64, required=True, select=True),
        'field_ids': fields.one2many('res.partner.bank.type.field', 'bank_type_id', 'Type fields'),
        'format_layout': fields.text('Format Layout', translate=False)
    }
    _defaults = {
        'format_layout': lambda *args: "%(bank_name)s: %(acc_number)s"
    }


res_partner_bank_type()


class res_partner_bank_type_fields(orm.Model):
    _description='Bank type fields'
    _name = 'res.partner.bank.type.field'
    _order = 'name'
    _columns = {
        'name': fields.char('Field Name', size=64, required=True, translate=False, select=True),
        'bank_type_id': fields.many2one('res.partner.bank.type', 'Bank Type', required=True, ondelete='cascade'),
        'required': fields.boolean('Required'),
        'readonly': fields.boolean('Readonly'),
        'size': fields.integer('Max. Size'),
    }


res_partner_bank_type_fields()



class res_bank(orm.Model):
    _description = 'Bank'
    _name = 'res.bank'
    _inherit = 'res.bank'
    _order = 'descricao'
    _rec_name = 'descricao'

    def _descricao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for banco_obj in self.browse(cr, uid, ids, context=context):
            texto = banco_obj.bic or ''
            texto += ' - '
            texto +=  banco_obj.name or ''

            res[banco_obj.id] = texto

        return res

    _columns = {
        'descricao': fields.function(_descricao, type='char', size=128, string=u'Descrição', store=True, select=True),
    }


res_bank()
