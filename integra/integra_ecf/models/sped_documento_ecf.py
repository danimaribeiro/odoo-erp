# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje, data_hora_horario_brasilia
import base64
from ecf import ECF_PRE, ECF_PIT, ECF_PPA
from pybrasil.valor.decimal import Decimal as D
import os
from pybrasil.inscricao import limpa_formatacao
from time import time

class sped_documento(osv.Model):
    _inherit = 'sped.documento'
    _name = 'sped.documento'
    #_order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'nome_arquivo_ecf': fields.char(u'Nome arquivo', size=30),
        'arquivo_ecf': fields.binary(u'Arquivo'),
        'arquivo_texto_ecf': fields.text(u'Arquivo'),
    }

    _defaults = {
        #'data': fields.date.today,
        #'declaracao' : '1',
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
    }

    def _get_serie_padrao(self, cr, uid, context):
        ambiente_nfe = self._get_ambiente_nfe_padrao(cr, uid, context)
        tipo_emissao_nfe = self._get_tipo_emissao_nfe_padrao(cr, uid, context)
        modelo = self._get_modelo_padrao(cr, uid, context)
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        res =  super(sped_documento, self)._get_serie_padrao( cr, uid, context)

        if modelo == '2D':
            if company_obj.caixa_ecf:
                res = company_obj.caixa_ecf

        return res

    def prepara_exportacao(self, cr, uid, documento_obj):
        empresa = documento_obj.company_id.partner_id
        caminho_empresa = os.path.expanduser('~/sped/ecf/cnpj/')
        caixa = documento_obj.serie or '01'
        caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf) + '/' + caixa + '/')
        print(caminho_empresa)
        return caminho_empresa

    def prepara_importacao(self, cr, uid, documento_obj):
        empresa = documento_obj.company_id.partner_id
        caixa = documento_obj.serie or '01'
        caminho_empresa = os.path.expanduser('~/sped/ecf/cnpj/')
        caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(empresa.cnpj_cpf) + '/' + caixa + '/retorno/')
        print(caminho_empresa)
        return caminho_empresa

    def gera_ecf(self, cr, uid, ids, context={}):
        if not ids:
            return True

        employee_pool = self.pool.get('hr.employee')
        contato_ids = employee_pool.search(cr, uid, [('user_id', '=', uid)])

        for documento_obj in self.browse(cr, uid, ids):
            caminho_empresa = self.prepara_exportacao(cr, uid, documento_obj)
            print(caminho_empresa)

            partner_obj =  documento_obj.partner_id

            efc_pre = ECF_PRE()
            efc_pre.numero_pre_venda = documento_obj.id
            efc_pre.data_hora_emissao = data_hora_horario_brasilia(parse_datetime(parse_datetime(documento_obj.data_emissao)))
            efc_pre.codigo_externo_cliente = documento_obj.partner_id.id
            efc_pre.nome_cliente = partner_obj.razao_social
            efc_pre.cnpj_cpf_cliente = partner_obj.cnpj_cpf

            if documento_obj.payment_term_id.id:
                efc_pre.codigo_externo_plano_pagto = str(documento_obj.payment_term_id.id)
            else:
                efc_pre.codigo_externo_plano_pagto = ''

            efc_pre.sub_total = float(documento_obj.vr_produtos)
            efc_pre.valor_desconto = float(documento_obj.vr_desconto)
            efc_pre.valor_acrescimo = float(0)
            efc_pre.total_itens = float(documento_obj.vr_nf)
            efc_pre.codigo_externo_vendendor = ''

            if documento_obj.infcomplementar:
                efc_pre.observacao = documento_obj.infcomplementar

            if partner_obj.ie:
                efc_pre.rg_inscricao_estatual = partner_obj.ie or ''
            efc_pre.endereco = partner_obj.endereco or ''
            efc_pre.numero = partner_obj.numero or ''
            efc_pre.bairro = partner_obj.bairro or ''
            efc_pre.cidade = partner_obj.cidade or ''
            efc_pre.uf = partner_obj.estado or ''
            efc_pre.cep = partner_obj.cep
            efc_pre.nivel_credito = 9

            #
            # Para passar por todos os itens
            #
            arquivo_pit = ''
            if documento_obj.documentoitem_ids:
                sequencia = 1
                for item_obj in documento_obj.documentoitem_ids:
                    product_obj = item_obj.produto_id
                    unidade_obj = item_obj.uom_id
                    cfop = item_obj.cfop_id

                    if item_obj.produto_id.type != 'service':
                        efc_pri = ECF_PIT()
                        efc_pri.sequencia = sequencia
                        efc_pri.codigo_externo_produto = item_obj.produto_id.id
                        efc_pri.quantidade_produto = float(item_obj.quantidade)
                        efc_pri.preco_unitario = float(item_obj.vr_unitario)
                        efc_pri.valor_desconto = float(item_obj.vr_desconto)
                        efc_pri.valor_acrescimo = float(0)
                        efc_pri.valor_total = float(item_obj.vr_produtos)
                        efc_pri.codigo_barras = item_obj.produto_id.id
                        efc_pri.descricao_produto = product_obj.name_template
                        efc_pri.complemento_produto = ''
                        efc_pri.unidade_medida = unidade_obj.name

                        if item_obj.cst_icms == '00':
                            efc_pri.situacao_tributaria = 'T'

                        elif item_obj.cst_icms in ['10','60']:
                            efc_pri.situacao_tributaria = 'F'

                        elif item_obj.cst_icms == '41':
                            efc_pri.situacao_tributaria = 'N'

                        elif item_obj.cst_icms in ['30','40']:
                            efc_pri.situacao_tributaria = 'I'

                        if item_obj.vr_icms_proprio:
                            efc_pri.ICMS = float(item_obj.al_icms_proprio)

                        efc_pri.calcula_QTD = 'N'
                        efc_pri.bloqueia_QTD_frac = 'N'
                        efc_pri.bloqueia_QTD = 'N'
                        efc_pri.producao_propria = 'N'
                        efc_pri.QTD_estoque = ''
                        efc_pri.desc_adicional = ''
                        efc_pri.codvendedor = ''
                        efc_pri.nomevendedor = ''
                        efc_pri.gtin_contabil = ''

                        if item_obj.produto_id.ncm_id.ex:
                            efc_pri.ext_IPI = item_obj.produto_id.ncm_id.ex

                        efc_pri.gtin_tributavel = ''
                        efc_pri.ID_ICMS = ''
                        efc_pri.ID_IPI = ''
                        efc_pri.ID_ISSQN = ''
                        efc_pri.ID_II = ''
                        efc_pri.ID_PIS = ''
                        efc_pri.ID_PIS_CST = ''
                        efc_pri.ID_COFINS = ''
                        efc_pri.ID_COFINS_CST = ''
                        efc_pri.NCM = product_obj.ncm_id.codigo
                        arquivo_pit += efc_pri.registro_PIT()
                        sequencia += 1

                arquivo_ppa = ''
                if documento_obj.duplicata_ids:

                    for item_duplic in documento_obj.duplicata_ids:
                        efc_ppa = ECF_PPA()
                        efc_ppa.vencimento = data_hora_horario_brasilia(parse_datetime(parse_datetime(item_duplic.data_vencimento)))
                        efc_ppa.valor = item_duplic.valor
                        efc_ppa.obs = u'Parcela n ' + item_duplic.numero
                        arquivo_ppa += efc_ppa.registro_PPA()

            arquivo_texto = efc_pre.registro_PRE()
            arquivo_texto += arquivo_pit
            arquivo_texto += arquivo_ppa

            nome_arquivo =  str(documento_obj.id) + u'.djp'
            dados = {
                'nome_arquivo_ecf': nome_arquivo,
                'arquivo_texto_ecf': arquivo_texto[:-2],
                'arquivo_ecf': base64.encodestring(arquivo_texto[:-2]),
                'state': 'enviada',
            }
            open(caminho_empresa + nome_arquivo,'w').write(arquivo_texto)
            documento_obj.write(dados)


    def retorna_ecf(self, cr, uid, ids, context={}):
        if not ids:
            return True

        for documento_obj in self.browse(cr, uid, ids):
            caminho_empresa =  self.prepara_importacao(cr, uid, documento_obj)
            #caminho_empresa = '/home/william/Documentos/teste/'
            arquivos = os.listdir(caminho_empresa)
            arquivos.sort(reverse=True)
            cont = True

            for arquivo in arquivos:
                if not cont:
                    break

                retorno = open(caminho_empresa + arquivo,'r')

                for linha in retorno.readlines():
                    campos = linha.split('|')

                    if campos[0] == 'DOC':
                        if campos[25] == str(documento_obj.id) or campos[5] == 'CA':
                            self.corrige_ecf(cr, uid, ids, documento_obj, retorno, caminho_empresa, arquivo, context)
                            cont = False

    def corrige_ecf(self, cr, uid, ids, documento_obj, retorno, caminho_empresa, arquivo, context={}):
        retorno = open(caminho_empresa + arquivo,'r')
        for linha in retorno.readlines():
            campos = linha.split('|')
            if campos[0] == 'DOC':
                if campos[25] == str(documento_obj.id) or campos[4] == str(documento_obj.numero):
                    if campos[4] and campos[23] == 'N':

                        cupom = {}
                        cupom = {'numero': int(campos[4]),
                                 'state': 'autorizada',
                                 }
                        documento_obj.write(cupom)
                        for item_obj in documento_obj.documentoitem_ids:
                            recalculo = {'recalculo': int(time())}
                            item_obj.write(recalculo)
                            
                    elif campos[5] == 'CA' or campos[23] == 'S' : 
                        cupom = {}                                          
                        cupom = {'numero': int(campos[4]),                             
                                'state': 'cancelada',
                                'situacao': '02',
                                }                       
                        documento_obj.write(cupom)
                        
                if campos[11] and campos[5] == 'CA': 
                    campo = campos[11] 
                    if campo[19:] == str(documento_obj.numero).zfill(6):                     
                        cupom = {}                                          
                        cupom = {'numero': int(campos[4]),                             
                                 'state': 'cancelada',
                                 'situacao': '02',
                                }
                        documento_obj.write(cupom)

        return

class sped_documentoitem(osv.Model):
    _inherit = 'sped.documentoitem'
    _name = 'sped.documentoitem'


    _columns = {
        'recalculo': fields.integer(u'Recalculo'),
    }
sped_documentoitem()

