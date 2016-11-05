# -*- coding: utf-8 -*-


from osv import fields, orm
from pybrasil.inscricao import limpa_formatacao, formata_cnpj, valida_cnpj


class hr_tabela_rat(orm.Model):
    _name = 'hr.tabela.rat'
    _description = u'Tabela RAT'
    _order = 'raiz_cnpj, ano desc'

    def _aliquota_final(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}
        for obj in self.browse(cr, uid, ids):
            obj.aliquota_final = float(obj.aliquota_rat * obj.ajuste_fap)
            res[obj.id] = obj.aliquota_final

        return res

    _columns = {
        'raiz_cnpj': fields.char(u'Raiz CNPJ', 18, select=True),
        'ano': fields.integer(u'Ano', select=True),
        'aliquota_rat': fields.float(u'Alíquota RAT', digits=(8, 4)),
        'ajuste_fap': fields.float(u'Ajuste FAP', digits=(8, 4)),
        'aliquota_outras_entidades': fields.float(u'Alíquota outras entidades', digits=(8, 4)),
        'aliquota_final': fields.function(_aliquota_final, string=u'Aliquota Final', method=True, type='float', digits=(8, 4), store=True)
    }
    
    def onchange_cnpj_cpf(self, cr, uid, ids, cnpj_cpf, context={}):
        if not cnpj_cpf:
            return {}

        if not valida_cnpj(cnpj_cpf):
            raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

        cnpj_cpf = limpa_formatacao(cnpj_cpf)
        cnpj_cpf = formata_cnpj(cnpj_cpf)

        return {'value': {'raiz_cnpj': cnpj_cpf}}
    
    def create(self, cr, uid, dados, context={}):
        if 'raiz_cnpj' in dados and dados['raiz_cnpj']:
            cnpj_cpf = limpa_formatacao(dados['raiz_cnpj'])

            if not valida_cnpj(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

                dados['raiz_cnpj'] = formata_cnpj(cnpj_cpf)
                
        return super(hr_tabela_rat, self).create(cr, uid, dados, context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'raiz_cnpj' in dados and dados['raiz_cnpj']:
            cnpj_cpf = limpa_formatacao(dados['raiz_cnpj'])

            if not valida_cnpj(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

                dados['raiz_cnpj'] = formata_cnpj(cnpj_cpf)
                
        return super(hr_tabela_rat, self).write(cr, uid, ids, dados, context)


hr_tabela_rat()
