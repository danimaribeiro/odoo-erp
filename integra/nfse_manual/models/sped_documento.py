# -*- encoding: utf-8 -*-


from osv import osv, fields
from sped.models.trata_nfse import envia_nfse, grava_pdf
from pybrasil.sped.nfse.provedor.barueri.rps_barueri import REGISTRO_1, REGISTRO_2, REGISTRO_3, REGISTRO_9
from pybrasil.data import parse_datetime, hoje, data_hora_horario_brasilia
from pybrasil.sped.nfse.provedor.joinville.envia import processar_retorno
from decimal import Decimal as D
import base64

class sped_documento(osv.Model):
    _inherit = 'sped.documento'
    _name = 'sped.documento'

    _columns = {
        'nome_arquivo_nfse': fields.char(u'Nome arquivo', size=60),
        'arquivo_envio_nfse': fields.binary(u'Arquivo Envio'),
        'nome_retorno_nfse': fields.char(u'Arquivo', size=60),
        'arquivo_retorno_nfse': fields.binary(u'Arquivo Retorno'),
        'retorno_lote_id': fields.many2one('retorno.nfse.manual', u'Numero Lote', ondelete='restrict', select=True),
    }


    def action_enviar_nfse(self, cr, uid, ids, context={}):

        res = super(sped_documento, self).action_enviar_nfse(cr, uid, ids, context=context)

        id = ids[0]
        doc_obj = self.browse(cr, uid, id)

        if doc_obj.company_provedor_nfse == 'BARUERI':
            self.enviar_nfse_barueri(cr, uid, ids, context)


        return res

    def retorna_nfse(self, cr, uid, ids, context={}):
        res = {}
        for doc_obj in self.browse(cr, uid, ids):

            if not doc_obj.arquivo_retorno_nfse:
                raise osv.except_osv(u'Erro!', u'Nenhum arquivo informado!')

            xml = base64.decodestring(doc_obj.arquivo_retorno_nfse)

            if doc_obj.company_provedor_nfse == 'BARUERI':
                return

            else:
                nfes_retorno = processar_retorno(xml)
                if nfes_retorno:
                    for nfes in nfes_retorno:
                        print(nfes)

        return res


    def enviar_nfse_barueri(self, cr, uid, ids, context={}):
        if not ids:
            return True
        
        id = ids[0]
        for doc_obj in self.pool.get('sped.documento').browse(cr, uid, [id]):
            
            numero_linha = 1
            rps_registro1 = REGISTRO_1()

            rps_registro1.incricao_contribuinte = doc_obj.company_id.partner_id.im or ''
            rps_registro1.indentificador_remessa = 1
            
            arquivo_texto = rps_registro1.registro()

            for doc_obj in self.pool.get('sped.documento').browse(cr, uid, ids):
                
                rps_registro2 = REGISTRO_2()    
    
                rps_registro2.serie_rps = doc_obj.serie or ''
    
                if doc_obj.situacao == 'cancelada':
                    rps_registro2.numero_rps = 0
                else:
                    rps_registro2.numero_rps = doc_obj.numero_rps or 1
    
                rps_registro2.data_emissao_rps =  data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao_rps))
                rps_registro2.hora_rps =  data_hora_horario_brasilia(parse_datetime(doc_obj.data_emissao_rps))                
    
                if doc_obj.situacao == 'cancelada':
    
                    rps_registro2.situacao_rps = 'C'
                    if doc_obj.nota_substituida_id:
                        rps_registro2.codigo_motivo_cancelamento = '03'
                        rps_registro2.numero_nf_cancelada = doc_obj.nota_substituida_id.numero_rps or 0
                        rps_registro2.serie_nf_cancelada = doc_obj.nota_substituida_id.serie_rps or ''
                    else:
                        rps_registro2.codigo_motivo_cancelamento = '01'
                        rps_registro2.numero_nf_cancelada = 0
                        rps_registro2.serie_nf_cancelada = ''
    
                    rps_registro2.data_emissao_nfe_cancelada = doc_obj.nota_substituida_id.data_emissao_rps
                    rps_registro2.descricao_cancelamento = ''
                rps_registro2.codigo_servico_prestado = doc_obj.servico_id.cd_servico_barueri or 0
    
    
                if doc_obj.natureza_tributacao_nfse == '0':
                    rps_registro2.local_prestacao_servico = '1'
                else:
                    rps_registro2.local_prestacao_servico = '2'
    
                #
                # Prestador
                #
    
                rps_registro2.endereco_servico_prestado = doc_obj.company_id.partner_id.endereco or ''
                rps_registro2.numero_servico_prestado = doc_obj.company_id.partner_id.numero or ''
                rps_registro2.complemento_servico_prestado =  doc_obj.company_id.partner_id.complemento or ''
                rps_registro2.bairro_servico_prestado = doc_obj.company_id.partner_id.bairro or ''
                rps_registro2.cidade_servico_prestado = doc_obj.company_id.partner_id.municipio_id.nome or ''
                rps_registro2.uf_servico_prestado = doc_obj.company_id.partner_id.municipio_id.estado_id.uf or ''
                rps_registro2.cep_servico_prestado = doc_obj.company_id.partner_id.cep or ''
    
    
                for item_obj in doc_obj.documentoitem_ids:
                    rps_registro2.quantidade_servico_prestado = float(item_obj.quantidade)                    
                    rps_registro2.valor_servico_prestado = D(str(item_obj.vr_produtos)).quantize(D('0.01'))
                    
                vr_retencao = D(0)           
                     
                if doc_obj.pis_cofins_retido:                     
                    if doc_obj.vr_pis_retido > 0:
                        vr_retencao += D(str(doc_obj.vr_pis_retido)).quantize(D('0.01'))
                    
                    if doc_obj.vr_cofins_retido > 0:
                        vr_retencao += D(str(doc_obj.vr_cofins_retido)).quantize(D('0.01'))
                    
                if doc_obj.irrf_retido and doc_obj.vr_irrf > 0:                    
                    vr_retencao += D(str(doc_obj.vr_irrf)).quantize(D('0.01'))
    
                if doc_obj.csll_retido and doc_obj.vr_csll > 0:
                    vr_retencao += D(str(doc_obj.vr_csll)).quantize(D('0.01'))
    
                rps_registro2.valor_total_retencoes = vr_retencao or 0
    
                #
                # Tomador
                #
    
                if doc_obj.partner_id.contribuinte == '9':
                    rps_registro2.tomador_estrangeiro = '1'
                    if doc_obj.partner_id.municipio_id.pais_id.codigo_pais_barueri:
                        rps_registro2.pais_nacionalidade_tomador_estrangeiro = doc_obj.partner_id.municipio_id.pais_id.codigo_pais_barueri or ''
                else:
                    rps_registro2.tomador_estrangeiro = '2'
    
    
    
                #self.servico_exportacao = '2'
    
                rps_registro2.indicador_tomador = '2'
                rps_registro2.cpf_cnpj_tomador = doc_obj.partner_id.cnpj_cpf or ''
                rps_registro2.razao_social_tomador = doc_obj.partner_id.razao_social or ''
                rps_registro2.endereco_tomador =  doc_obj.partner_id.endereco or ''
                rps_registro2.numero_tomador = doc_obj.partner_id.numero or ''
                rps_registro2.bairro_tomador = doc_obj.partner_id.bairro or ''
                rps_registro2.cidade_tomador = doc_obj.partner_id.municipio_id.nome or ''
                rps_registro2.uf_tomador = doc_obj.partner_id.municipio_id.estado_id.uf or ''
                rps_registro2.cep_tomador = doc_obj.partner_id.cep or ''
                rps_registro2.email_tomador = doc_obj.partner_id.email_nfe or ''
    
    
                #rps_registro2.numero_fatura = 0
                #rps_registro2.valor_fatura = 0
                #rps_registro2.forma_pagamento = ''
    
    
                if doc_obj.infadfisco:
                    rps_registro2.discriminacao_servico = doc_obj.infadfisco.replace('\n', ' | ')
    
    
                rps_retencao = ''
                valor_total = D(0)
    
                if doc_obj.irrf_retido and doc_obj.vr_irrf > 0:
                    rps_registro3 = REGISTRO_3()
                    rps_registro3.codigo_outros_valores = '01'
                    rps_registro3.valor = D(str(doc_obj.vr_irrf)).quantize(D('0.01'))
                    rps_retencao += rps_registro3.registro()
                    valor_total += rps_registro3.valor
                    numero_linha += 1
    
                if doc_obj.pis_cofins_retido and doc_obj.vr_pis_retido > 0:
    
                    if doc_obj.vr_pis_retido:
                        rps_registro3 = REGISTRO_3()
                        rps_registro3.codigo_outros_valores = '02'
                        rps_registro3.valor = D(str(doc_obj.vr_pis_retido)).quantize(D('0.01'))
                        rps_retencao += rps_registro3.registro()
                        valor_total += rps_registro3.valor
                        numero_linha += 1
    
                    if doc_obj.vr_cofins_retido and doc_obj.vr_pis_retido > 0:
                        rps_registro3 = REGISTRO_3()
                        rps_registro3.codigo_outros_valores = '03'
                        rps_registro3.valor = D(str(doc_obj.vr_cofins_retido)).quantize(D('0.01'))
                        rps_retencao += rps_registro3.registro()
                        valor_total += rps_registro3.valor
                        numero_linha += 1
    
                if doc_obj.csll_retido and doc_obj.vr_csll > 0:
                    rps_registro3 = REGISTRO_3()
                    rps_registro3.codigo_outros_valores = '04'
                    rps_registro3.valor = D(str(doc_obj.vr_csll)).quantize(D('0.01'))
                    rps_retencao += rps_registro3.registro()
                    valor_total += rps_registro3.valor
                    numero_linha += 1
       

                arquivo_texto += rps_registro2.registro()
                numero_linha += 1 
                if rps_retencao:
                    arquivo_texto += rps_retencao
                

            rps_registro9 = REGISTRO_9()

            rps_registro9.numero_total_linha = numero_linha + 1
            rps_registro9.valor_total_servico = D(str(doc_obj.vr_nf)).quantize(D('0.01'))
            rps_registro9.valor_total_servico_registro3 = D(str(valor_total)).quantize(D('0.01'))

            arquivo_texto += rps_registro9.registro()

            nome_arquivo =  str(doc_obj.id) + u'.txt'
            dados = {
                'nome_arquivo_nfse': nome_arquivo,
                'arquivo_envio_nfse': base64.encodestring(arquivo_texto[:-2]),
                'state': 'a_enviar',
            }
            doc_obj.write(dados)

            print(arquivo_texto)

            return arquivo_texto

sped_documento()
