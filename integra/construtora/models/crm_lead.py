# -*- coding: utf-8 -*-

from osv import osv, fields
from const_imovel import *
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional)


#class crm_lead_imovel(osv.Model):
    #_name = 'crm.lead.imovel'
    #_description = u'Imóveis do prospecto'

    #_columns = {
        #'lead_id': fields.many2one('crm.lead', u'Prospecto', ondelete='cascade'),
        #'imovel_id': fields.many2one('const.imovel', u'Imóvel', ondelete='cascade'),
    #}


#crm_lead_imovel()


class crm_lead(osv.Model):
    _name = 'crm.lead'
    _inherit = ['const.imovel', 'crm.lead']
    _rec_name = 'name'

    _columns = {
        'fone_contato': fields.related('partner_id', 'fone', type='char', string=u'Fone'),
        'celular_contato': fields.related('partner_id', 'celular', type='char', string=u'Celular'),
        'motivo_id': fields.many2one('crm.motivo', u'Motivo', ondelete='restrict'),
        'imovel_busca_ids': fields.many2many('const.imovel', 'crm_lead_imovel_busca', 'lead_id', 'imovel_id', u'Imóveis'),
        'imovel_exibe_busca_ids': fields.many2many('const.imovel', 'crm_lead_imovel_busca', 'lead_id', 'imovel_id', u'Imóveis'),
        'imovel_ids': fields.many2many('const.imovel', 'crm_lead_imovel', 'lead_id', 'imovel_id', u'Imóveis'),
        'imovel_exibe_ids': fields.many2many('const.imovel', 'crm_lead_imovel', 'lead_id', 'imovel_id', u'Imóveis'),
        'codigo': fields.char(u'Código', size=20, required=False),
        'valor_documento_from': fields.float(u'De valor'),
        'valor_documento_to': fields.float(u'A valor'),
        'finan_contrato_ids': fields.one2many('finan.contrato', 'crm_lead_id', u'Propostas'),
    }

    _defaults = {
        'tipo': False,
        'situacao': 'D',
        'propriedade': False,
    }

    def buscar_imoveis(self, cr, uid, ids, context={}):
        for lead_obj in self.browse(cr, uid, ids, context=context):
            busca = []

            if lead_obj.tipo:
                busca.append(['tipo', '=', lead_obj.tipo])

            if lead_obj.situacao:
                busca.append(['situacao', '=', lead_obj.situacao])

            if lead_obj.propriedade:
                busca.append(['propriedade', '=', lead_obj.propriedade])

            if lead_obj.zoneamento_item_id:
                busca.append(['zoneamento_item_id', '=', lead_obj.zoneamento_item_id.id])

            if lead_obj.codigo:
                busca.append(['codigo', '=', lead_obj.codigo])

            if lead_obj.descricao:
                busca.append(['descricao', 'ilike', lead_obj.descricao])

            if lead_obj.valor_documento_from:
                busca.append(['valor_venda', '>=', lead_obj.valor_documento_from])

            if lead_obj.valor_documento_to:
                busca.append(['valor_venda', '<=', lead_obj.valor_documento_to])

            if lead_obj.proprietario_id:
                busca.append(['proprietario_id', '=', lead_obj.proprietario_id.id])

            if lead_obj.endereco:
                busca.append(['endereco', 'ilike', lead_obj.endereco])

            if lead_obj.bairro:
                busca.append(['bairro', 'ilike', lead_obj.bairro])

            if lead_obj.municipio_id:
                busca.append(['municipio_id', '=', lead_obj.municipio_id.id])

            if lead_obj.ponto_referencia:
                busca.append(['ponto_referencia', 'ilike', lead_obj.ponto_referencia])

            if lead_obj.condominio:
                busca.append(['condominio', 'ilike', lead_obj.condominio])

            if lead_obj.suite:
                busca.append(['suite', '=', lead_obj.suite])

            if lead_obj.quarto:
                busca.append(['quarto', '=', lead_obj.quarto])

            if lead_obj.garagem:
                busca.append(['garagem', '=', lead_obj.garagem])

            if len(busca):
                imovel_pool = self.pool.get('const.imovel')
                imovel_ids = imovel_pool.search(cr, uid, busca)

                jah_tem = []
                for imovel_obj in lead_obj.imovel_busca_ids:
                    jah_tem.append(imovel_obj.id)

                for imovel_id in imovel_ids:
                    if not imovel_id in jah_tem:
                        jah_tem.append(imovel_id)

                cr.execute('delete from crm_lead_imovel_busca where lead_id = ' + str(lead_obj.id) + ';')

                for imovel_id in jah_tem:
                    cr.execute('insert into crm_lead_imovel_busca (lead_id, imovel_id) values ({lead_id}, {imovel_id});'.format(lead_id=lead_obj.id, imovel_id=imovel_id))


        return {}

    def nada(self, cr, uid, ids, context={}):
        return {}

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        res = {}

        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                res = {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            res = {'value': {'fone_contato': fone}}

        elif celular is not None and celular:
            if not valida_fone_internacional(celular) and not valida_fone_celular(celular):
                res = {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            celular = formata_fone(celular)
            res = {'value': {'celular_contato': celular}}

        print(res)
        return res

    def onchange_contato_id(self, cr, uid, ids, contato_id, context={}):
        res = {}

        if contato_id:
            valores = {}
            res['value'] = valores

            contato_obj = self.pool.get('res.partner').browse(cr, uid, contato_id)

            valores['fone_contato'] = contato_obj.fone
            valores['celular_contato'] = contato_obj.celular

        return res


crm_lead()
