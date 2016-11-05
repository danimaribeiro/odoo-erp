# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64
from finan.wizard.finan_relatorio import Report
from pybrasil.base import DicionarioBrasil
from pybrasil.data import hoje, parse_datetime, formata_data, agora, dia_da_semana_por_extenso, data_por_extenso
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

TIPO = [
       ('A', 'Agenciador'),
       ('C', 'Corretor'),
       ('F', 'Funcionário'),
       ('E', 'Empresa'),
       ('O', 'Outros'),

]

class finan_numerario(osv.Model):
    _name = 'finan.numerario'
    _description = u'Solicitação de Numerário'
    _rec_name = 'codigo'
    _order = 'codigo desc'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = lancamento_obj.id

        return res
    
    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.company_id.partner_id.cnpj_cpf:
                res[obj.id] = obj.company_id.partner_id.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res

    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Requisição', store=True, select=False),
        'user_id': fields.many2one('res.users', u'Usuário'),
        'user_solicitante': fields.many2one('res.users', u'Usuário Solicitante'),
        'user_atribuido': fields.many2one('res.users', u'Usuário Atribuído'),
        'data_solicitacao': fields.datetime(u'Data solicitação'),
        'data_entrega': fields.date(u'Data entrega'),
        'data_pagamento': fields.date(u'Data Pagamento'),
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True, ondelete='restrict'),
        'gera_provissionamento': fields.boolean(u'gerar provisionamento'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', select=True, ondelete='restrict'),
        'project_id': fields.many2one('project.project', u'Projeto/empreendimento', select=True, ondelete='restrict'),
        'descricao': fields.text(u'Descrição'),
        'item_ids': fields.one2many('finan.numerario.valor', 'numerario_id', u'Itens'),
        'obs': fields.text(u'Observação'),
        'aprovado': fields.boolean(u'Aprovado'),
        'aprovador_id': fields.many2one('res.users', u'Aprovador'),
        'valor': fields.float(u'Valor'),
        'fornecedor_id': fields.many2one('res.partner', u'Fornecedor'),
        'product_id': fields.many2one('product.product', u'Solicitação'),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
    }

    _defaults = {
        #'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.numerario', context=c),
        'user_id': lambda obj, cr, uid, context: uid,
        'data_solicitacao': fields.datetime.now,
        'data_entrega': fields.datetime.now,
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores

        company_pool = self.pool.get('res.company')
        company_obj = company_pool.browse(cr, uid, company_id)

        if company_obj.partner_id:            
            valores['raiz_cnpj'] = company_obj.raiz_cnpj
        else:
            raise osv.except_osv(u'Inválido !', u'Não existe Cnpj/Cpf na Empresa selecionada!')

        return retorno


    def imprime_solicitacao(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Solicitação de Númerario', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_solicitacao_numerario.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid

        nome = 'REQUERIMENTO_' + str(rel_obj.id) + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.numerario'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'finan.numerario',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def aprova_solicitacao(self, cr, uid, ids, contexte={}):
        transacao_obj = self.pool.get('finan.lancamento')

        for numerario_obj in self.browse(cr, uid, ids):
            soma = D(0)
            for item_obj in  numerario_obj.item_ids:
                soma += D(item_obj.valor or 0)

            if soma != D(numerario_obj.valor):
                raise osv.except_osv(u'Erro!', u'O valor dos itens não bate com o valor total da solicitação!')

            i = 1
            for item_obj in  numerario_obj.item_ids:
                numero_documento = 'SN-' + str(numerario_obj.codigo).zfill(6) + '-'
                numero_documento += str(i).zfill(2) + '/'
                numero_documento += str(len(numerario_obj.item_ids)).zfill(2)

                i += 1

                if item_obj.res_partner_bank_id:
                    dados = {
                        'numerario_item_id': item_obj.id,
                        'tipo': 'T',
                        'res_partner_bank_id': numerario_obj.res_partner_bank_id.id,
                        'res_partner_bank_creditar_id': item_obj.res_partner_bank_id.id,
                        'data_documento': numerario_obj.data_solicitacao,
                        'data': numerario_obj.data_pagamento,
                        'data_quitacao': numerario_obj.data_pagamento,
                        'valor': item_obj.valor,
                        'valor_documento': item_obj.valor,
                        'partner_id': item_obj.partner_id.id,
                        'documento_id': item_obj.documento_id.id,
                        'conta_id': item_obj.conta_id.id,
                        'numero_documento': numero_documento,
                        'company_id': numerario_obj.company_id.id,
                    }
                    transacao_obj.create(cr, uid, dados)
                else:
                    dados = {
                        'numerario_item_id': item_obj.id,
                        'tipo': 'S',
                        'res_partner_bank_id': numerario_obj.res_partner_bank_id.id,
                        'data': numerario_obj.data_pagamento,
                        'data_quitacao': numerario_obj.data_pagamento,
                        'data_documento': numerario_obj.data_solicitacao,
                        'valor': item_obj.valor,
                        'valor_documento': item_obj.valor,
                        'partner_id': item_obj.partner_id.id,
                        'documento_id': item_obj.documento_id.id,
                        'conta_id': item_obj.conta_id.id,
                        'centrocusto_id': numerario_obj.centrocusto_id.id,
                        'numero_documento': numero_documento,
                        'company_id': numerario_obj.company_id.id,
                    }
                    transacao_obj.create(cr, uid, dados)

            numerario_obj.write({'aprovado': True, 'aprovador_id': uid})

    def _valida_total(self, cr, uid, ids):
        for numerario_obj in self.browse(cr, uid, ids):
            soma = D(0)
            for item_obj in  numerario_obj.item_ids:
                soma += D(item_obj.valor or 0)

            if soma != D(numerario_obj.valor):
                raise osv.except_osv(u'Erro!', u'O valor dos itens não bate com o valor total da solicitação!')

    def create(self, cr, uid, dados, context={}):
        res = super(finan_numerario, self).create(cr, uid, dados, context=context)

        self.pool.get('finan.numerario')._valida_total(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_numerario, self).write(cr, uid, ids, dados, context=context)

        self.pool.get('finan.numerario')._valida_total(cr, uid, ids)

        return res

    def copy(self, cr, uid, id, dados, context={}):
        dados['aprovado'] = False
        dados['aprovador_id'] = False

        return super(finan_numerario, self).copy(cr, uid, id, dados, context=context)

    def onchange_product_id(self, cr, uid, ids, product_id, context={}):
        if not product_id:
            return {}

        valores = {}
        res = {'value': valores}

        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)

        if product_obj.conta_despesa_id:
            valores['conta_id'] = product_obj.conta_despesa_id.id

        return res


finan_numerario()


class finan_numerario_valor(osv.Model):
    _name = 'finan.numerario.valor'
    _description = u'Solicitação Valores do Numerário'

    def _porcentagem(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for numval_obj in self.browse(cr, uid, ids):
            valor_original = D(numval_obj.numerario_id.valor or 0)

            if not valor_original:
                valor = 100
            else:
                valor = D(numval_obj.valor or 0) / valor_original * 100

            res[numval_obj.id] = valor

        return res

    _columns = {
        'numerario_id': fields.many2one('finan.numerario', u'Numerário', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', u'Nome'),
        'fornecedor_id': fields.many2one('res.partner', u'Fornecedor'),
        'conta_id': fields.many2one('finan.conta', u'Conta Financeira', select=True, ondelete='restrict'),
        'documento_id': fields.many2one('finan.documento', u'Tipo do documento', select=True, ondelete='restrict'),
        'product_id': fields.many2one('product.product', u'Solicitação'),
        'tipo': fields.selection(TIPO, u'Tipo', select=True),
        'valor': fields.float(u'Valor'),
        'porcentagem': fields.function(_porcentagem, type='float', string=u'Porcentagem'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Adiantamento', select=True, ondelete='restrict'),
        'raiz_cnpj': fields.char(u'Raiz do CNPJ', size=10 ),
    }

    _defaults = {
        'valor': 0,
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context={}):
        if not product_id:
            return {}

        valores = {}
        res = {'value': valores}

        product_obj = self.pool.get('product.product').browse(cr, uid, product_id)

        if product_obj.conta_despesa_id:
            valores['conta_id'] = product_obj.conta_despesa_id.id

        return res


finan_numerario_valor()
