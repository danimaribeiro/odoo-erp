# -*- encoding: utf-8 -*-


from osv import osv, fields
from pybrasil.sped.nfse.provedor.joinville.envia import processar_retorno 
from decimal import Decimal as D
import base64
from sped.models.cfop import sped_cfop

class retorno_nfse_manual(osv.Model):
    _name = 'retorno.nfse.manual'
    _description = 'Retorno Lote de NFSE Manual'
    _rec_name = 'data'
    _order = 'id desc'
     
    _columns = {
        'data': fields.date(u'Data'),
        'numero_lote': fields.integer(u'Lote'),
        'arquivo_retorno_nfse': fields.binary(u'Arquivo Retorno'),
        'documento_ids': fields.one2many('sped.documento', 'retorno_lote_id', u'Notas Fiscais'),
    }
    
    _defaults = {        
        'numero_lote': 0,
    }
    
      
    def retorna_nfse(self, cr, uid, ids, context={}):
        nfse_pool = self.pool.get('sped.documento')
        
        res = {}
        for doc_obj in self.browse(cr, uid, ids):
        
            if not doc_obj.arquivo_retorno_nfse:
                raise osv.except_osv(u'Erro!', u'Nenhum arquivo informado!')

            xml = base64.decodestring(doc_obj.arquivo_retorno_nfse)
         
            nfes_retorno = processar_retorno(xml)
            print(nfes_retorno)
            if nfes_retorno:
                for nfe_retorno in nfes_retorno:
                    numero_lote = nfe_retorno.numero_lote 
                    data_processamento = nfe_retorno.data_processamento  
                    
                    for rps in nfe_retorno.rps:            
                        nfse_id = nfse_pool.search(cr, 1, args=[('numero_rps', '=', rps.numero),
                                                      ('serie', '=', rps.serie),
                                                      ('modelo', '=', 'SE'),
                                                      ('state', '!=', 'autorizada'),    
                                                      ('company_id.cnpj_cpf', '=', nfe_retorno.documento)],
                                              limit=1,
                                              order='numero_rps DESC'                                       
                                              )
                        if nfse_id:
                            nfse_obj = nfse_pool.browse(cr, uid , nfse_id[0]) 
                            dados = {
                                     'numero': rps.nfem_numero,
                                     'state': 'autorizada',
                                     'numero_protocolo_nfe': rps.nfem_codigo_verificacao,
                                     'resposta_nfse': nfe_retorno.observacao,                                                     
                                     'retorno_lote_id': doc_obj.id,                                                     
                                     }
                            nfse_obj.write(dados)
                            
                    doc_obj.write({'numero_lote': numero_lote, 'data': data_processamento})
        return res 


retorno_nfse_manual()
