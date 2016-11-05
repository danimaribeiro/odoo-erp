# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals

import os
from pysped.nfe.processador_nfe import ProcessadorNFe
from osv import osv, fields
#from sped.models.trata_nfe import prepara_certificado
from pybrasil.inscricao import limpa_formatacao, formata_cnpj
from pybrasil.data import agora, UTC, data_hora_horario_brasilia, parse_datetime
from pysped.nfe.leiaute import CONS_NFE_TODAS, CONS_NFE_EMISSAO_TODOS_EMITENTES
from dateutil.relativedelta import relativedelta


def prepara_certificado(self, cr, uid, doc_obj):
    empresa = doc_obj.company_id.partner_id
    caminho_empresa = os.path.expanduser('~/sped')
    caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf))


    processador = ProcessadorNFe()
    processador.danfe.nome_sistema = 'Integra 6.2'
    processador.salvar_arquivos = False
    #processador.danfe.site = 'http://www.ERPIntegra.com.br'
    processador.caminho = os.path.join(caminho_empresa, 'nfe')
    processador.estado  = empresa.municipio_id.estado_id.uf
    processador.ambiente = int(doc_obj.ambiente_nfe)
    #processador.contingencia_SCAN = doc_obj.tipo_emissao_nfe != '1'

    processador.certificado.arquivo = open(os.path.join(caminho_empresa, 'certificado_caminho.txt')).read().strip()
    processador.certificado.senha   = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip()

    if os.path.exists(os.path.join(caminho_empresa, 'logo_caminho.txt')):
        processador.danfe.logo = open(os.path.join(caminho_empresa, 'logo_caminho.txt')).read().strip()

    return processador


class sped_ultimo_nsu(osv.Model):
    _name = 'sped.ultimo_nsu'
    _description = u'Controle do último NSU'

    _columns = {
       'company_id': fields.many2one('res.company', u'Empresa/unidade'),
       'ultimo_nsu': fields.char(u'Último NSU', size=25, select=True),
       'ultima_consulta': fields.datetime(u'Última consulta'),
    }

    def busca_documentos(self, cr, uid, ids, contex={}):
        if not ids:
            return

        dist_dfe_pool = self.pool.get('sped.distribuicao_dfe')
        partner_pool = self.pool.get('res.partner')

        for uu_obj in self.browse(cr, uid, ids):
            uu_obj.ambiente_nfe = '1'
            processador = prepara_certificado(self, cr, uid, uu_obj)
            cnpj = limpa_formatacao(uu_obj.company_id.partner_id.cnpj_cpf)

            processo = processador.consultar_notas_destinadas(
                cnpj=cnpj,
                ultimo_nsu=uu_obj.ultimo_nsu or '0',
                tipo_nfe=CONS_NFE_TODAS,
                tipo_emissao=CONS_NFE_EMISSAO_TODOS_EMITENTES,
            )

            #print(processo.envio.xml.encode('utf-8'))
            #print('resposta')
            #print(processo.resposta.original.encode('utf-8'))

            #
            # Nenhum documento encontrado
            #
            if processo.resposta.cStat.valor == '137':
                uu_obj.write({'ultimo_nsu': processo.resposta.ultNSU.valor, 'ultima_consulta': str(UTC.normalize(agora()))})

            #
            # Consumo indevido, não tem mais documentos para retornar, deve esperar
            # 1 hora para a próxima execução
            #
            if processo.resposta.cStat.valor == '656':
                uu_obj.write({'ultima_consulta': str(UTC.normalize(agora()))})
                cron_id = self.pool.get('ir.cron').search(cr, 1, [('function', '=', 'acao_demorada_busca_documentos')])
                if cron_id is not None and len(cron_id):
                    cron_obj = self.pool.get('ir.cron').browse(cr, 1, cron_id[0])
                    nova_execucao = parse_datetime(cron_obj.nextcall + ' GMT')
                    nova_execucao += relativedelta(hours=+1)
                    nova_execucao = UTC.normalize(nova_execucao)
                    cron_obj.write({'nextcall': str(nova_execucao)[:19]})

            elif processo.resposta.cStat.valor == '138':
                uu_obj.write({'ultimo_nsu': processo.resposta.ultNSU.valor, 'ultima_consulta': str(UTC.normalize(agora()))})

                for rn in processo.resposta.resNFe:
                    cnpj = formata_cnpj(rn.CNPJ.valor)
                    data_autorizacao = parse_datetime(rn.dhRecbto.valor)
                    data_autorizacao = UTC.normalize(data_autorizacao)
                    dados = {
                        'company_id': uu_obj.company_id.id,
                        'cnpj': cnpj,
                        'nome': rn.xNome.valor,
                        'ie': rn.IE.valor,
                        'data_emissao': str(rn.dEmi.valor),
                        'nsu': rn.NSU.valor,
                        'data_autorizacao': str(data_autorizacao),
                        'digest_value': rn.digVal.valor,
                        'situacao_dfe': rn.cSitNFe.valor,
                        'situacao_manifestacao': rn.cSitConf.valor,
                        'chave': rn.chNFe.valor,
                    }

                    if rn.chNFe.valor:
                        dados['serie'] = rn.chNFe.valor[22:25]
                        dados['numero'] = int(rn.chNFe.valor[25:34])

                    partner_ids = partner_pool.search(cr, uid, [('cnpj_cpf', '=', cnpj)])
                    if partner_ids:
                        dados['partner_id'] = partner_ids[0]

                    dist_dfe_pool.create(cr, uid, dados)

    def acao_demorada_busca_documentos(self, cr, uid, ids=[], context={}):
        if not ids:
            ids = self.pool.get('sped.ultimo_nsu').search(cr, uid, [])

        self.pool.get('sped.ultimo_nsu').busca_documentos(cr, uid, ids, context)


sped_ultimo_nsu()
