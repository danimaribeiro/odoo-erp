# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals


from osv import osv, fields
from sped.models.trata_nfe import grava_arquivo
from pybrasil.data import agora, UTC, data_hora_horario_brasilia, parse_datetime
from pybrasil.inscricao import limpa_formatacao, formata_cnpj
from datetime import datetime
from importa_xml import identifica_xml
from importa_documento import processa_documento
from ultimo_nsu import prepara_certificado


SITUACAO_DFE = [
    ['1', u'Autorizado'],
    ['2', u'Denegado'],
    ['3', u'Cancelado'],
]

SITUACAO_MANIFESTACAO = [
    ['0', u'Sem manifestação'],
    ['1', u'Operação confirmada'],
    ['2', u'Operação desconhecida'],
    ['3', u'Operação não realizada'],
    ['4', u'Operação reconhecida (ciente)'],
]


class sped_distribuicao_dfe(osv.Model):
    _name = 'sped.distribuicao_dfe'
    _order = 'data_emissao desc'
    _rec_name = 'chave'
    _description = u'Controle do distribuição de DF-e'

    _columns = {
       'company_id': fields.many2one('res.company', u'Empresa/unidade'),
       'cnpj': fields.char(u'CNPJ emissor', size=18, select=True),
       'chave': fields.char(u'Chave', size=44, select=True),
       'serie': fields.char(u'Série', size=3, select=True),
       'numero': fields.integer(u'Número', select=True),
       'nome': fields.char(u'Emissor', size=60),
       'ie': fields.char(u'Inscrição estadual', size=18),
       'data_emissao': fields.date(u'Data de emissão', select=True),
       'nsu': fields.char(u'NSU', size=25, select=True),
       'data_autorizacao': fields.datetime(u'Data de autorização', select=True),
       'data_cancelamento': fields.datetime(u'Data de cancelamento', select=True),
       'digest_value': fields.char(u'Digest Value', size=28),
       'situacao_dfe': fields.selection(SITUACAO_DFE, u'Situacação DF-e', select=True),
       'situacao_manifestacao': fields.selection(SITUACAO_MANIFESTACAO, u'Situacação DF-e', select=True),
       'data_manifestacao': fields.datetime(u'Data da manifestação'),
       'justificativa': fields.char(u'Justificativa', size=255),
       'partner_id': fields.many2one('res.partner', u'Fornecedor'),
       'documento_id': fields.many2one('sped.documento', u'Documento'),
       'xml_autorizacao': fields.text(u'XML de autorização'),
       #'xml_cancelamento': fields.text(u'XML de cancelamento'),
       'documento_original_id': fields.many2one('sped.documento', u'Documento de remessa/transferência/venda original'),
    }

    def manifestar_destinatario(self, cr, uid, ids, context={}):
        if not ids:
            return

        for dd_obj in self.browse(cr, uid, ids):
            dd_obj.ambiente_nfe = '1'
            processador = prepara_certificado(self, cr, uid, dd_obj)
            cnpj = limpa_formatacao(dd_obj.company_id.partner_id.cnpj_cpf)

            #
            # Assume que, se a situação atual for sem manifestação,
            # a manifestação padrão é Confirmar a operação
            #
            if dd_obj.situacao_manifestacao in ['0', '1']:
                processo = processador.confirmar_operacao_evento(
                    cnpj=cnpj,
                    chave_nfe=dd_obj.chave,
                )
                #print('processo.envio.original')
                #print(processo.envio.original)
                #print('processo.resposta.original')
                #print(processo.resposta.original)

                if processo.resposta.cStat.valor == '128':
                    dd_obj.write({'situacao_manifestacao': '1', 'data_manifestacao': str(datetime.now())})
                    #
                    # Já logo em seguida faz o download do xml em questão
                    #
                    self.pool.get('sped.distribuicao_dfe').download_nfe(cr, uid, [dd_obj.id])

            elif dd_obj.situacao_manifestacao == '2':
                processo = processador.desconhecer_operacao_evento(
                    cnpj=cnpj,
                    chave_nfe=dd_obj.chave,
                )

                if processo.resposta.cStat.valor == '128':
                    dd_obj.write({'situacao_manifestacao': '2', 'data_manifestacao': str(datetime.now())})

            elif dd_obj.situacao_manifestacao == '3':
                if len(dd_obj.justificativa) < 15:
                    continue

                processo = processador.nao_realizar_operacao_evento(
                    cnpj=cnpj,
                    chave_nfe=dd_obj.chave,
                    justificativa=dd_obj.justificativa,
                )

                if processo.resposta.cStat.valor == '128':
                    dd_obj.write({'situacao_manifestacao': '3', 'data_manifestacao': str(datetime.now())})

            elif dd_obj.situacao_manifestacao == '2':
                processo = processador.desconhecer_operacao_evento(
                    cnpj=cnpj,
                    chave_nfe=dd_obj.chave,
                )

                if processo.resposta.cStat.valor == '128':
                    dd_obj.write({'situacao_manifestacao': '2', 'data_manifestacao': str(datetime.now())})

    def download_nfe(self, cr, uid, ids, context={}):
        if not ids:
            return

        for dd_obj in self.browse(cr, uid, ids):
            dd_obj.ambiente_nfe = '1'
            processador = prepara_certificado(self, cr, uid, dd_obj)
            cnpj = limpa_formatacao(dd_obj.company_id.partner_id.cnpj_cpf)

            processo = processador.baixar_notas_destinadas(cnpj=cnpj, lista_chaves=[dd_obj.chave])
            #print(processo.resposta.xml)

            #
            # Conseguiu baixar o xml
            #
            if processo.resposta.cStat.valor == '139':

                if '<cStat>632</cStat>' in processo.resposta.xml:
                    dd_obj.write({'justificativa': processo.resposta.retNFe[0].xMotivo.valor})

                else:
                    xml = processo.resposta.retNFe[0].procNFe.valor
                    xml = u'<?xml version="1.0" encoding="utf-8"?>' + xml
                    xml = xml.encode('utf-8')

                    nome_arquivo = processo.resposta.retNFe[0].chNFe.valor + '-proc-nfe.xml'
                    grava_arquivo(self, cr, uid, dd_obj, nome_arquivo, xml, tabela='sped.distribuicao_dfe')

                    nome_arquivo = processo.resposta.retNFe[0].chNFe.valor + '-nfe.xml'
                    grava_arquivo(self, cr, uid, dd_obj, nome_arquivo, xml, tabela='sped.distribuicao_dfe')

                    dd_obj.write({'xml_autorizacao': xml})

                    cr.commit()

                    self.pool.get('sped.distribuicao_dfe').importa_nfe(cr, uid, [dd_obj.id])

    def importa_nfe(self, cr, uid, ids, context={}):
        if not ids:
            return

        for dd_obj in self.browse(cr, uid, ids):
            if not dd_obj.xml_autorizacao:
                continue

            procnfe, tipo = identifica_xml(dd_obj.xml_autorizacao, cria_instancia=True)

            if procnfe is not None:
                doc_id = processa_documento(self, cr, uid, dd_obj.company_id.id, procnfe.NFe, '55', dd_obj)

                if doc_id:
                    dd_obj.write({'documento_id': doc_id})


sped_distribuicao_dfe()
