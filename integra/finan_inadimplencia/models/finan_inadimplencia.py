# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
import os
from osv import osv, fields
from pybrasil.base import DicionarioBrasil
from pybrasil.data import hoje, parse_datetime, formata_data, agora, dia_da_semana_por_extenso, data_por_extenso
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor



class finan_inadimplencia(osv.osv_memory):
    _name = 'finan.inadimplencia'

    _columns = {
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_inadimplencia_lancamentos', 'inadimplencia_id', 'lancamento_id', string=u'Lançamentos'),
        'modelo_id': fields.many2one('lo.modelo', u'Modelo de carta', required=True),
        'name': fields.char(u'Name', size=10),
    }

    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')

        for inadimplencia_obj in self.browse(cr, uid, ids):
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.inadimplencia'), ('res_id', '=', inadimplencia_obj.id)])
            attachment_pool.unlink(cr, uid, attachment_ids)

            #
            # Primeiro, acumulamos os valores necessários
            #
            clientes = {}

            for lanc_obj in inadimplencia_obj.lancamento_ids:
                if lanc_obj.partner_id.id not in clientes:
                    clientes[lanc_obj.partner_id.id] = DicionarioBrasil()
                    cliente = clientes[lanc_obj.partner_id.id]
                    cliente['cliente'] = lanc_obj.partner_id
                    cliente['lancamentos'] = []

                clientes[lanc_obj.partner_id.id]['lancamentos'].append(lanc_obj)

            #
            # Agora, para cada cliente, montamos o documento
            #
            for cliente_id in clientes:
                cliente = clientes[cliente_id]
                texto = u''

                i = 1
                total = D(0)
                for lanc_obj in cliente['lancamentos']:
                    texto += u'; doc. nº '
                    texto += lanc_obj.numero_documento.strip()
                    texto += u', vencimento '
                    texto += formata_data(lanc_obj.data_vencimento)
                    texto += u', valor '
                    texto += formata_valor(lanc_obj.valor_documento)
                    total += D(lanc_obj.valor_documento)
                    cliente['NUM_DOC_' + str(i)] = lanc_obj.numero_documento.strip()
                    cliente['DATA_DOC_' + str(i)] = formata_data(lanc_obj.data_vencimento)
                    cliente['VALOR_DOC_' + str(i)] = formata_valor(lanc_obj.valor_documento)
                    i += 1

                while i <= 20:
                    cliente['NUM_DOC_' + str(i)] = ''
                    cliente['DATA_DOC_' + str(i)] = ''
                    cliente['VALOR_DOC_' + str(i)] = ''
                    i += 1

                if len(texto):
                    texto = texto[2:]

                cliente['texto'] = texto
                cliente['valor_devido'] = formata_valor(total)
                data = dia_da_semana_por_extenso(hoje())
                data += u', '
                data = data_por_extenso(hoje())
                cliente['data'] = data

                #
                # Apaga os recibos anteriores com o mesmo nome
                #
                modelo_obj = inadimplencia_obj.modelo_id
                nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                nome_arquivo += '_' + cliente.cliente.razao_social.upper().replace(' ', '-')
                nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                nome_arquivo += '.'
                nome_arquivo += modelo_obj.formato or 'doc'

                arquivo = modelo_obj.gera_modelo(cliente)

                dados = {
                    'datas': arquivo,
                    'name': nome_arquivo,
                    'datas_fname': nome_arquivo,
                    'res_model': 'finan.inadimplencia',
                    'res_id': inadimplencia_obj.id,
                    'file_type': 'application/pdf',
                }
                attachment_pool.create(cr, uid, dados)

            return


finan_inadimplencia()
