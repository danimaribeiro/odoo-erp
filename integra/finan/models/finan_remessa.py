# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from pybrasil.febraban.banco import BANCO_CODIGO, Remessa
from pybrasil.febraban.boleto import (Boleto, gera_boletos_pdf)


class finan_remessa(osv.Model):
    _name = 'finan.remessa'
    _description = 'Remessa de cobrança'
    _order = 'carteira_id, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    _columns = {
        'carteira_id': fields.many2one('finan.carteira', u'Carteira', required=True),
        'numero_arquivo': fields.integer(u'Número do arquivo'),
        'comando': fields.selection(((u'01', u'Registro'),), u'Comando'),
        'data': fields.datetime(u'Data e hora'),
        'remessa_item_ids': fields.one2many('finan.remessa_item', 'remessa_id', u'Boletos na remessa'),
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_remessa_item', 'remessa_id', 'lancamento_id', u'Boletos na remessa'),

    }

    _defaults = {
        'comando': '01',
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    def gerar_remessa(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        remessa_obj = self.browse(cr, uid, id)

        if not remessa_obj.numero_arquivo:
            numero_arquivo = int(remessa_obj.carteira_id.ultimo_arquivo_remessa) + 1
            self.write(cr, uid, [remessa_obj.id], {'numero_arquivo': str(numero_arquivo)})
            self.pool.get('finan.carteira').write(cr, 1, [remessa_obj.carteira_id.id], {'ultimo_arquivo_remessa': str(numero_arquivo)})
        else:
            numero_arquivo = int(remessa_obj.numero_arquivo)

        #
        # Gera os boletos
        #
        lista_boletos = []
        for lancamento_obj in remessa_obj.lancamento_ids:
            context['evita_pdf'] = True
            boleto = lancamento_obj.gerar_boleto(context=context)
            lista_boletos.append(boleto)

        #
        # Gera a remessa propriamente dita
        #
        remessa = Remessa()
        remessa.tipo = 'CNAB_400'
        remessa.boletos = lista_boletos
        remessa.sequencia = numero_arquivo
        remessa.data_hora = datetime.strptime(remessa_obj.data, '%Y-%m-%d %H:%M:%S')

        if len(lista_boletos) == 0:
            raise osv.except_osv(u'Inválido!', u'Não existe remessa a gerar com os parâmetros informados!')

        nome_remessa = str(numero_arquivo).zfill(8) + '.rem'

        #
        # Nomenclatura bradesco
        #
        if lista_boletos[0].banco.codigo == '237':
            nome_remessa = 'CB' + remessa.data_hora.strftime('%d%m') + str(remessa.sequencia).zfill(2) + '.txt'
        elif lista_boletos[0].banco.codigo == '104':
            nome_remessa = 'E' + str(numero_arquivo).zfill(8) + '.REM'
        
        if lista_boletos[0].banco.codigo == '085':
            remessa.tipo = 'CNAB_240'
            

        #
        # Anexa a remessa ao registro da remessa
        #
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.remessa'), ('res_id', '=', remessa_obj.id), ('name', '=', nome_remessa)])
        #
        # Apaga os boletos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(remessa.arquivo_remessa),
            'name': nome_remessa,
            'datas_fname': nome_remessa,
            'res_model': 'finan.remessa',
            'res_id': remessa_obj.id,
            'file_type': 'text/plain',
        }
        attachment_pool.create(cr, uid, dados)


        #pdf = gera_boletos_pdf(lista_boletos)
        #nome_boleto = 'boletos_' + remessa_obj.carteira_id.res_partner_bank_id.bank_name + '_' + str(remessa_obj.data) + '.pdf'

        ##
        ## Anexa os boletos em PDF ao registro da remessa
        ##
        #attachment_pool = self.pool.get('ir.attachment')
        #attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.remessa'), ('res_id', '=', remessa_obj.id), ('name', '=', nome_boleto)])
        ##
        ## Apaga os boletos anteriores com o mesmo nome
        ##
        #attachment_pool.unlink(cr, uid, attachment_ids)

        #dados = {
            #'datas': base64.encodestring(pdf),
            #'name': nome_boleto,
            #'datas_fname': nome_boleto,
            #'res_model': 'finan.remessa',
            #'res_id': remessa_obj.id,
            #'file_type': 'application/pdf',
        #}
        #attachment_pool.create(cr, uid, dados)


    def gerar_remessa_anexo(self, cr, uid, ids, context=None):
        for id in ids:
            self.gerar_remessa(cr, uid, id)


finan_remessa()


class finan_remessa_item(osv.Model):
    _name = 'finan.remessa_item'
    _description = 'Item de remessa de cobrança'
    _order = 'remessa_id, lancamento_id'
    _rec_name = 'lancamento_id'

    _columns = {
        'remessa_id': fields.many2one(u'finan.remessa', u'Arquivo de remessa'),
        'lancamento_id': fields.many2one(u'finan.lancamento', u'Boleto'),
        'data_vencimento': fields.related('lancamento_id', 'data_vencimento', type='date', relation='finan.lancamento', string=u'Data de vencimento', store=False),
        'nosso_numero': fields.related('lancamento_id', 'nosso_numero', type='char', relation='finan.lancamento', string=u'Nosso número', store=False),
    }


finan_remessa_item()
