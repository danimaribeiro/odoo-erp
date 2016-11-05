# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from pybrasil.febraban.banco import BANCO_CODIGO, Remessa


class finan_remessa_pagamento(osv.Model):
    _name = 'finan.remessa.pagamento'
    _description = u'Remessa de pagamento'
    _order = 'bank_id, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    _columns = {
        'bank_id': fields.many2one('res.partner.bank', u'Banco', required=True),
        'company_id': fields.many2one('res.company', u'Grupo/unidade'),
        'numero_arquivo': fields.integer(u'Número do arquivo'),
        'comando': fields.selection(((u'01', u'Registro'),), u'Comando'),
        'data': fields.datetime(u'Data e hora'),
        'remessa_item_ids': fields.one2many('finan.remessa.pagamento.item', 'remessa_id', u'Contas na remessa'),
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_remessa_pagamento_item', 'remessa_id', 'lancamento_id', u'Contas na remessa'),

    }

    _defaults = {
        'comando': '01',
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def onchange_bank_id(self, cr, uid, ids, bank_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores
        
        if not partner_bank_id:
            return res
        
        bank_obj = self.pool.get('res.partner.bank').browse(cr, uid, partner_bank_id)
        
        valores['company_id'] = bank_obj.company_id.parent_id.id
        
        return res
        

    def gerar_remessa(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        remessa_obj = self.browse(cr, uid, id)

        #if not remessa_obj.numero_arquivo:
            #numero_arquivo = int(remessa_obj.bank_id.ultimo_arquivo_remessa) + 1
            #self.write(cr, uid, [remessa_obj.id], {'numero_arquivo': str(numero_arquivo)})
            #self.pool.get('finan.carteira').write(cr, 1, [remessa_obj.bank_id.id], {'ultimo_arquivo_remessa': str(numero_arquivo)})
        #else:
        numero_arquivo = int(remessa_obj.numero_arquivo)

        #
        # Gera as contas
        #
        lista_contas = remessa_obj.lancamento_ids
        #for lancamento_obj in remessa_obj.lancamento_ids:
            #context['evita_pdf'] = True
            #conta = lancamento_obj.gerar_conta(context=context)
            #lista_contas.append(conta)

        #
        # Gera a remessa propriamente dita
        #
        remessa = Remessa()
        remessa.tipo = 'CNAB_500'
        #remessa.boletos = lista_contas
        remessa.sequencia = numero_arquivo
        remessa.data_hora = datetime.strptime(remessa_obj.data, '%Y-%m-%d %H:%M:%S')

        if len(lista_contas) == 0:
            raise osv.except_osv(u'Inválido!', u'Não existe remessa a gerar com os parâmetros informados!')

        nome_remessa = str(numero_arquivo).zfill(8) + '.rem'

        #
        # Nomenclatura bradesco
        #
        #if lista_contas[0].banco.codigo == '237':
        nome_remessa = 'PG' + remessa.data_hora.strftime('%d%m') + str(remessa.sequencia).zfill(2) + '.txt'

        #
        # Anexa a remessa ao registro da remessa
        #
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.remessa.pagamento'), ('res_id', '=', remessa_obj.id), ('name', '=', nome_remessa)])
        #
        # Apaga os contas anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(remessa.arquivo_remessa),
            'name': nome_remessa,
            'datas_fname': nome_remessa,
            'res_model': 'finan.remessa.pagamento',
            'res_id': remessa_obj.id,
            'file_type': 'text/plain',
        }
        attachment_pool.create(cr, uid, dados)

    def gerar_remessa_anexo(self, cr, uid, ids, context=None):
        for id in ids:
            self.gerar_remessa(cr, uid, id)


finan_remessa_pagamento()


class finan_remessa_pagamento_item(osv.Model):
    _name = 'finan.remessa.pagamento.item'
    _description = u'Item de remessa de pagamento'
    _order = 'remessa_id, lancamento_id'
    _rec_name = 'lancamento_id'

    _columns = {
        'remessa_id': fields.many2one(u'finan.remessa', u'Arquivo de remessa'),
        'lancamento_id': fields.many2one(u'finan.lancamento', u'Conta a pagar'),
        'data_vencimento': fields.related('lancamento_id', 'data_vencimento', type='date', relation='finan.lancamento', string=u'Data de vencimento', store=False),
        'nosso_numero': fields.related('lancamento_id', 'nosso_numero', type='char', relation='finan.lancamento', string=u'Nosso número', store=False),
    }


finan_remessa_pagamento_item()
