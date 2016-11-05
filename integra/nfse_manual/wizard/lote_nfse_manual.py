# -*- encoding: utf-8 -*-


from osv import osv, fields
from sped.models.trata_nfse import grava_pdf, monta_nfse
from pybrasil.sped.nfse.provedor.barueri.rps_barueri import REGISTRO_1, REGISTRO_2, REGISTRO_3, REGISTRO_9
from pybrasil.data import parse_datetime, hoje, data_hora_horario_brasilia
from pybrasil.sped.nfse.provedor.joinville.envia import processar_retorno
from pybrasil.sped.nfse.provedor.joinville import envia_rps as envia_rps_joinville
from decimal import Decimal as D
import base64


class lote_nfse_manual(osv.osv_memory):
    _name = 'lote.nfse.manual'
    _description = 'Lote de NFSE Manual'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome_arquivo_nfse'
    _order = 'nome_arquivo_nfse'

    _columns = {
        'nome_arquivo_nfse': fields.char(u'Nome arquivo', 60, readonly=True),
        'arquivo_envio_nfse': fields.binary(u'Arquivo Envio', readonly=True),
    }


    def action_enviar_nfse(self, cr, uid, ids, context={}):
        if 'active_ids' in context:
            notas = context['active_ids']

        #
        # Reordena os ids para ficarem em ordem do RPS
        #
        nfse_obj = self.pool.get('sped.documento')
        ids_ordenados = nfse_obj.search(cr, uid, [('id', 'in', notas)], order='numero_rps')

        print(ids, notas, ids_ordenados)

        lista_notas = []
        lista_notas_barueri = []
        ultimo_lote_nfse = 0
        if ids_ordenados:
            for id in ids_ordenados:                
                doc_obj = nfse_obj.browse(cr, uid, id)
                provedor_nfse = doc_obj.company_id.provedor_nfse
                if doc_obj.company_id.provedor_nfse not in ('JOINVILLE', 'BARUERI') or doc_obj.state in ['autorizada']:
                    continue

                company_obj = doc_obj.company_id
                if company_obj.matriz_id:
                    company_obj = company_obj.matriz_id
                ultimo_lote_nfse = company_obj.ultimo_lote_nfse or 0

                doc_obj.write({'numero_lote_rps': 0, 'numero_protocolo_nfse': '', 'resposta_nfse': ''})
                doc_obj = nfse_obj.browse(cr, uid, id)              
                doc_obj = monta_nfse(self, cr, uid, doc_obj)
                lista_notas.append(doc_obj)
                lista_notas_barueri.append(id)

        numero_lote_rps = ultimo_lote_nfse + 1
        
        if provedor_nfse == 'JOINVILLE':
            resposta_envia_rps = envia_rps_joinville(cr, uid, lista_notas, numero_lote_rps, certificado='')
            nome_arquivo_rps = u'RPS_LOTE_' + str(numero_lote_rps) + u'.xml'
            self.write(cr, uid, ids, {'nome_arquivo_nfse': nome_arquivo_rps, 'arquivo_envio_nfse': base64.encodestring(resposta_envia_rps)})
            self.pool.get('res.company').write(cr, 1, [company_obj.id], {'ultimo_lote_nfse': numero_lote_rps})
            cr.commit()
            
        elif provedor_nfse == 'BARUERI':
            resposta_envia_rps = nfse_obj.enviar_nfse_barueri(cr, uid, lista_notas_barueri)
            nome_arquivo_rps = u'RPS_LOTE_' + str(numero_lote_rps) + u'.txt'
            self.write(cr, uid, ids, {'nome_arquivo_nfse': nome_arquivo_rps, 'arquivo_envio_nfse': base64.encodestring(resposta_envia_rps)})
            self.pool.get('res.company').write(cr, 1, [company_obj.id], {'ultimo_lote_nfse': numero_lote_rps})
            cr.commit()




lote_nfse_manual()
