# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from pybrasil.data import hoje


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', select=True, ondelete='restrict'),
        'eh_ipva': fields.boolean(u'IPVA'),
        'eh_licenciamento': fields.boolean(u'Licenciamento'),
        'eh_dpvat': fields.boolean(u'DPVAT'),
    }

    def create(self, cr, uid, dados, context={}):
        doc_pool = self.pool.get('finan.documento')
        vei_pool = self.pool.get('frota.veiculo')

        if 'veiculo_id' in dados and dados['veiculo_id']:
            vei_obj = vei_pool.browse(cr, 1, dados['veiculo_id'])
            dados['company_id'] = vei_obj.res_company_id.id

            if vei_obj.centrocusto_id:
                dados['centrocusto_id'] = vei_obj.centrocusto_id.id

            if 'eh_ipva' in dados:
                doc_ipva_id = doc_pool.search(cr, 1, [('eh_ipva', '=', True)])

                if not doc_ipva_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o IPVA!')

                doc_ipva_obj = doc_pool.browse(cr, 1, doc_ipva_id[0])

                if not doc_ipva_obj.partner_id or not doc_ipva_obj.conta_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o IPVA!')

                dados['documento_id'] = doc_ipva_obj.id
                dados['partner_id'] = doc_ipva_obj.partner_id.id
                dados['conta_id'] = doc_ipva_obj.conta_id.id
                dados['numero_documento'] = u'IPVA ' + dados['data_vencimento'] + u' ' + (vei_obj.placa or '')
                dados['data_documento'] = str(hoje())

            elif 'eh_dpvat' in dados:
                doc_dpvat_id = doc_pool.search(cr, 1, [('eh_dpvat', '=', True)])

                if not doc_dpvat_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o DPVAT!')

                doc_dpvat_obj = doc_pool.browse(cr, 1, doc_dpvat_id[0])

                if not doc_dpvat_obj.partner_id or not doc_dpvat_obj.conta_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o DPVAT!')

                dados['documento_id'] = doc_dpvat_obj.id
                dados['partner_id'] = doc_dpvat_obj.partner_id.id
                dados['conta_id'] = doc_dpvat_obj.conta_id.id
                dados['numero_documento'] = u'DPVAT ' + dados['data_vencimento'] + u' ' + (vei_obj.placa or '')
                dados['data_documento'] = str(hoje())

            elif 'eh_licenciamento' in dados:
                doc_licenciamento_id = doc_pool.search(cr, 1, [('eh_licenciamento', '=', True)])

                if not doc_licenciamento_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o Licenciamento!')

                doc_licenciamento_obj = doc_pool.browse(cr, 1, doc_licenciamento_id[0])

                if not doc_licenciamento_obj.partner_id or not doc_licenciamento_obj.conta_id:
                    raise osv.except_osv(u'Erro!', u'O financeiro precisa configurar o tipo de documento para o Licenciamento!')

                dados['documento_id'] = doc_licenciamento_obj.id
                dados['partner_id'] = doc_licenciamento_obj.partner_id.id
                dados['conta_id'] = doc_licenciamento_obj.conta_id.id
                dados['numero_documento'] = u'Licenc. ' + dados['data_vencimento'] + u' ' + (vei_obj.placa or '')
                dados['data_documento'] = str(hoje())

            if vei_obj.centrocusto_id:
                rateio_dados = self.onchange_centrocusto_id(cr, uid, [], dados['centrocusto_id'], dados['valor_documento'], 0, dados['company_id'], dados['conta_id'], dados['partner_id'], dados['data_vencimento'], dados['data_documento'], context={'veiculo_id': dados['veiculo_id']})
                if 'value' in rateio_dados and 'rateio_ids' in rateio_dados['value']:
                    dados['rateio_ids'] = []
                    for rateio in rateio_dados['value']['rateio_ids']:
                        dados['rateio_ids'].append([0, False, rateio])

        res = super(finan_lancamento, self).create(cr, uid, dados, context)
        return res


finan_lancamento()
