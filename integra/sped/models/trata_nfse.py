# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import os
import base64
from osv import osv
from decimal import Decimal as D
from pybrasil.ibge import MUNICIPIO_IBGE
from pybrasil.sped.nfse import *
from pybrasil.sped.nfse.provedor.abrasf import envia_rps as envia_rps_abrasf
from pybrasil.sped.nfse.provedor.ginfes import envia_rps as envia_rps_ginfes, envia_consulta_situacao_rps as envia_consulta_situacao_rps_ginfes, cancela_nota as cancela_nota_ginfes
from pybrasil.sped.nfse.provedor.nota_carioca import envia_rps as envia_rps_carioca, envia_consulta_rps as envia_consulta_rps_carioca
from pybrasil.sped.nfse.provedor.betha import envia_consulta_rps as envia_consulta_rps_betha, envia_rps as envia_rps_betha, envia_consulta_situacao_rps as envia_consulta_situacao_rps_betha, cancela_nota as cancela_nota_betha
from pybrasil.sped.nfse.provedor.boanota import envia_consulta_rps as envia_consulta_rps_boanota, envia_rps as envia_rps_boanota, envia_consulta_situacao_rps as envia_consulta_situacao_rps_boanota, cancela_nota as cancela_nota_boanota
from pybrasil.sped.nfse.provedor.publica import envia_consulta_rps as envia_consulta_rps_publica, envia_rps as envia_rps_publica, envia_consulta_situacao_rps as envia_consulta_situacao_rps_publica, cancela_nota as cancela_nota_publica
from pybrasil.sped.nfse.provedor.ipm import gera_rps as gera_rps_ipm, envia_rps as envia_rps_ipm #envia_consulta_rps as envia_consulta_rps_ipm, envia_rps as envia_rps_ipm, envia_consulta_situacao_rps as envia_consulta_situacao_rps_ipm, cancela_nota as cancela_nota_ipm
from pybrasil.sped.nfse.provedor.prodam import gera_rps as gera_rps_prodam, envia_rps as envia_rps_prodam #envia_consulta_rps as envia_consulta_rps_ipm, envia_rps as envia_rps_ipm, envia_consulta_situacao_rps as envia_consulta_situacao_rps_ipm, cancela_nota as cancela_nota_ipm
from pybrasil.sped.nfse.provedor.joao_pessoa import gera_rps as gera_rps_joao_pessoa, envia_rps as envia_rps_joao_pessoa
from pybrasil.sped.nfse.provedor.neogrid import gera_rps as gera_rps_neogrid, envia_consulta_rps as envia_consulta_rps_neogrid
from pybrasil.sped.nfse.provedor.webiss import envia_rps as envia_rps_webiss, envia_consulta_rps as envia_consulta_rps_webiss
from pybrasil.sped.nfse.provedor.foz_iguacu import envia_rps as envia_rps_foz_iguacu, envia_consulta_rps as envia_consulta_rps_foz_iguacu
from pybrasil.sped.nfse.provedor.govbr import envia_rps as envia_rps_govbr, envia_consulta_rps as envia_consulta_rps_govbr
from pybrasil.sped.base import Certificado
from pybrasil.valor import formata_valor
from sped.constante_tributaria import *
from pybrasil.inscricao import limpa_formatacao
from pybrasil.data import data_hora_horario_brasilia, fuso_horario_sistema, HB, UTC, parse_datetime
from mako.template import Template
from datetime import datetime
from pybrasil.base import DicionarioBrasil
from encodings.utf_8 import encode

certificado = Certificado()


def monta_nfse(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)
    #
    # Bibliotecas importadas para serem usadas nos templates
    #
    template_imports = [
        'import pybrasil',
        'import math',
        'from pybrasil.base import (tira_acentos, primeira_maiuscula)',
        'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
        'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade, formata_valor)',
        'from pybrasil.valor.decimal import Decimal as D',
    ]


    prestador = Prestador()
    prestador.nome = doc_obj.company_id.partner_id.razao_social or ''
    prestador.cnpj_cpf = doc_obj.company_id.partner_id.cnpj_cpf or ''
    prestador.im = doc_obj.company_id.partner_id.im or ''
    prestador.endereco = doc_obj.company_id.partner_id.endereco or ''
    prestador.numero = doc_obj.company_id.partner_id.numero or ''
    prestador.complemento = doc_obj.company_id.partner_id.complemento or ''
    prestador.bairro = doc_obj.company_id.partner_id.bairro or ''
    prestador.municipio = MUNICIPIO_IBGE[doc_obj.company_id.partner_id.municipio_id.codigo_ibge[:7]]
    prestador.cep = doc_obj.company_id.partner_id.cep or ''
    prestador.ie = doc_obj.company_id.partner_id.ie or ''
    prestador.email = doc_obj.company_id.partner_id.email_nfe or ''
    prestador.fone = doc_obj.company_id.partner_id.fone or ''
    prestador.celular = doc_obj.company_id.partner_id.celular or ''
    prestador.cnae = doc_obj.company_id.partner_id.cnae_id.codigo or ''

    if doc_obj.company_id.regime_tributario == '1':
        prestador.regime_tributario = 'SIMPLES'
    elif doc_obj.company_id.regime_tributario == '2':
        prestador.regime_tributario = 'SIMPLES_EXCESSO'
    elif doc_obj.company_id.regime_tributario == '3':
        prestador.regime_tributario = 'LUCRO_PRESUMIDO'
    else:
        prestador.regime_tributario = 'LUCRO_REAL'

    if certificado.logo:
        prestador.arquivo_logo = certificado.logo

    tomador = Tomador()
    tomador.nome = doc_obj.partner_id.razao_social or ''
    tomador.cnpj_cpf = doc_obj.partner_id.cnpj_cpf or ''
    tomador.im = doc_obj.partner_id.im or ''
    tomador.endereco = doc_obj.partner_id.endereco or ''
    tomador.numero = doc_obj.partner_id.numero or ''
    tomador.complemento = doc_obj.partner_id.complemento or ''
    tomador.bairro = doc_obj.partner_id.bairro or ''
    if not doc_obj.partner_id.municipio_id:
        raise osv.except_osv(u'Erro!', u'Cliente “{nome}” sem município cadastrado!'.format(nome=doc_obj.partner_id.name) )
    elif doc_obj.partner_id.municipio_id.codigo_ibge[:7] not in MUNICIPIO_IBGE :
        raise osv.except_osv(u'Erro!', u'Código de IBGE {codigo_ibge} incorreto para o município {nome}'.format(codigo_ibge = doc_obj.partner_id.municipio_id.codigo_ibge, nome=doc_obj.partner_id.municipio_id.nome) )
    else:
        tomador.municipio = MUNICIPIO_IBGE[doc_obj.partner_id.municipio_id.codigo_ibge[:7]]
    tomador.cep = doc_obj.partner_id.cep or ''
    tomador.ie = doc_obj.partner_id.ie or ''

    email_dest = doc_obj.partner_id.email_nfe or ''
    tomador.email = email_dest[:60]

    tomador.fone = doc_obj.partner_id.fone or ''
    tomador.celular = doc_obj.partner_id.celular or ''
    #print(tomador.ie, 'inscricao estadual', doc_obj.partner_id.ie)

    nfse = NFSe()
    nfse.fuso_horario = fuso_horario_sistema()
    nfse.prestador = prestador
    nfse.tomador = tomador
    nfse.serie = doc_obj.serie or ''

    if doc_obj.company_id.provedor_nfse in ['WEBISS','GOVBR']:
        nfse.numero = D(doc_obj.numero_prefeitura or -1)
        print(nfse.numero)
    else:
        nfse.numero = doc_obj.numero or -1

    nfse.data_hora_emissao = doc_obj.data_emissao
    nfse.data_hora_fato_gerador = doc_obj.data_emissao_rps
    nfse.rps.serie = doc_obj.serie_rps or ''

    if doc_obj.company_id.provedor_nfse == 'IPM':
        nfse.rps.numero = doc_obj.id or 0
    else:
        nfse.rps.numero = doc_obj.numero_rps or 0

    #print('data_emissao_rps', doc_obj.data_emissao_rps)
    nfse.rps.data_hora_emissao = doc_obj.data_emissao_rps
    nfse.codigo_verificacao = doc_obj.codigo_verificacao_nfse or ''
    nfse.link_verificacao = doc_obj.link_verificacao_nfse or ''
    nfse.natureza_operacao = int(doc_obj.natureza_tributacao_nfse or 0)

    if doc_obj.municipio_fato_gerador_id:
        nfse.municipio_fato_gerador = MUNICIPIO_IBGE[doc_obj.municipio_fato_gerador_id.codigo_ibge[:7]]
    else:
        nfse.municipio_fato_gerador = tomador.municipio

    if doc_obj.company_id.partner_id.municipio_id.codigo_ibge in ['35503080000','35498050000','33045570000','41083040000','41240530000'] and doc_obj.servico_id.codigo_servico_municipio:
        nfse.servico_municipio = doc_obj.servico_id.codigo_servico_municipio
    else:
        nfse.servico_municipio = False
        nfse.servico = doc_obj.servico_id.codigo

    nfse.valor.servico = D(str(doc_obj.vr_produtos)).quantize(D('0.01'))
    nfse.valor.bc_iss = D(str(doc_obj.bc_iss)).quantize(D('0.01'))
    nfse.valor.al_iss = D(str(doc_obj.documentoitem_ids[0].al_iss)).quantize(D('0.01'))
    vr_iss = D(str(doc_obj.vr_iss)).quantize(D('0.01'))
    nfse.valor.vr_iss = vr_iss
    iss_diferenca_centavos = False

    if doc_obj.company_id.provedor_nfse == 'IPM':
        #
        # O IPM valida o total do ISS sobre o valor total da nota, em alguns
        # casos isso dá diferença de 1 centavo; ajustamos isso aqui
        #
        vr_iss = nfse.valor.bc_iss
        vr_iss *= nfse.valor.al_iss / D(100)
        vr_iss = vr_iss.quantize(D('0.01'))

        if vr_iss != nfse.valor.vr_iss:
            iss_diferenca_centavos = True
            cr.execute("update sped_documento set vr_iss = {vr_iss} where id = {doc_id};".format(doc_id=doc_obj.id, vr_iss=vr_iss))
            doc_obj.vr_iss = vr_iss
            nfse.valor.vr_iss = vr_iss

    if doc_obj.iss_retido:
        nfse.valor.retido.iss = D(str(doc_obj.vr_iss_retido)).quantize(D('0.01'))

        if iss_diferenca_centavos and doc_obj.company_id.provedor_nfse == 'IPM':
            nfse.valor.retido.iss = vr_iss
            cr.execute("update sped_documento set vr_iss_retido = {vr_iss} where id = {doc_id};".format(doc_id=doc_obj.id, vr_iss=vr_iss))
            doc_obj.vr_iss_retido = vr_iss

    if doc_obj.pis_cofins_retido:
        nfse.valor.retido.al_pis = D(str(doc_obj.al_pis_retido)).quantize(D('0.01'))
        nfse.valor.retido.pis = D(str(doc_obj.vr_pis_retido)).quantize(D('0.01'))
        nfse.valor.retido.al_cofins = D(str(doc_obj.al_cofins_retido)).quantize(D('0.01'))
        nfse.valor.retido.cofins = D(str(doc_obj.vr_cofins_retido)).quantize(D('0.01'))

    if doc_obj.csll_retido:
        nfse.valor.retido.al_csll = D(str(doc_obj.al_csll)).quantize(D('0.01'))
        nfse.valor.retido.csll = D(str(doc_obj.vr_csll)).quantize(D('0.01'))

    if doc_obj.irrf_retido:
        nfse.valor.retido.al_ir = D(str(doc_obj.al_irrf)).quantize(D('0.01'))
        nfse.valor.retido.ir = D(str(doc_obj.vr_irrf)).quantize(D('0.01'))

    if doc_obj.previdencia_retido:
        nfse.valor.retido.al_inss = D(str(doc_obj.al_previdencia)).quantize(D('0.01'))
        nfse.valor.retido.inss = D(str(doc_obj.vr_previdencia)).quantize(D('0.01'))

    nfse.valor.liquido = D(str(doc_obj.vr_fatura)).quantize(D('0.01'))
    nfse.obs = doc_obj.infadfisco or ''

    #
    # Informação complementar
    #
    dados = {
        'nf': doc_obj,
        'doc_obj': doc_obj,
    }

    #
    # Trata a data de vencimento
    #
    if doc_obj.finan_lancamento_id:
        dados['data_vencimento'] = doc_obj.finan_lancamento_id.data_vencimento
    else:
        dados['data_vencimento'] = doc_obj.data_emissao_brasilia

    template = Template(nfse.obs.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
    nfse.obs = template.render(**dados)
    nfse.obs = nfse.obs.decode('utf-8')

    if doc_obj.compra_contrato:
        nfse.obs += '\n' + doc_obj.compra_contrato

    nfse.obs += u'\nNatureza da operação: ' + dict(NATUREZA_TRIBUTACAO_NFSE)[doc_obj.natureza_tributacao_nfse or '0']
    nfse.obs += u'\nLocal de prestação do serviço: ' + nfse.municipio_fato_gerador.nome + ' - ' + nfse.municipio_fato_gerador.estado.sigla
    if doc_obj.vr_ibpt:
        nfse.obs += u'\nValor aproximado dos tributos com base na Lei 12.741/2012 - R$ ' + formata_valor(doc_obj.vr_ibpt or 0) + ' - Fonte: IBPT'
    nfse.obs += '\n' + nfse.link_verificacao


    #
    # Adiciona os dados da conta para depósito, quando houver
    #
    if hasattr(doc_obj, 'finan_contrato_id') and doc_obj.finan_contrato_id and (not doc_obj.finan_contrato_id.carteira_id) and doc_obj.finan_contrato_id.res_partner_bank_id:
        nfse.obs += '\n<strong>Dados da conta para depósito: '
        conta_obj = doc_obj.finan_contrato_id.res_partner_bank_id
        nfse.obs += conta_obj.bank_name or ''
        nfse.obs += ', ag. '
        nfse.obs += conta_obj.agencia or ''

        if conta_obj.agencia_digito:
            nfse.obs += '-'
            nfse.obs += conta_obj.agencia_digito or ''

        nfse.obs += ', c/c '
        nfse.obs += conta_obj.acc_number or ''

        if conta_obj.conta_digito:
            nfse.obs += '-'
            nfse.obs += conta_obj.conta_digito or ''

        if conta_obj.partner_id and conta_obj.partner_id.cnpj_cpf:
            if len(conta_obj.partner_id.cnpj_cpf) > 14:
                nfse.obs += ', CNPJ '
            else:
                nfse.obs += ', CPF '

            nfse.obs += conta_obj.partner_id.cnpj_cpf or ''

        nfse.obs += '</strong>'


    nfse.itens = []

    descricao = u''

    for item_obj in doc_obj.documentoitem_ids:
        item = ItemNFSe()
        item.quantidade = D(str(item_obj.quantidade)).quantize(D('0.01'))
        item.vr_unitario = D(str(item_obj.vr_unitario)).quantize(D('0.01'))
        item.vr_servico = D(str(item_obj.vr_produtos)).quantize(D('0.01'))
        item.iss_retido = doc_obj.iss_retido or False
        descricao += '- ' + item_obj.produto_id.name
        descricao += ': R$ ' + formata_valor(item.vr_servico) + '\n'
        item.descricao = item_obj.produto_id.name
        nfse.itens.append(item)

    if doc_obj.modelo == 'RL' and not ('PATRIMONIAL' in cr.dbname.upper() or 'TESTE_' in cr.dbname.upper()):
        descricao = u''

    if doc_obj.infcomplementar:
        descricao += doc_obj.infcomplementar

    descricao = descricao.strip()

    if descricao[-1] == ';':
        descricao = descricao[:-2]

    nfse.descricao = descricao

    template = Template(nfse.descricao.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
    nfse.descricao = template.render(**dados)
    nfse.descricao = nfse.descricao.decode('utf-8')

    nfse.fuso_horario = HB

    if doc_obj.nota_substituida_id:
        nfse.nfse_substituida.numero = doc_obj.nota_substituida_id.numero_rps or 0
        nfse.nfse_substituida.serie = doc_obj.nota_substituida_id.serie_rps or ''


    #
    # Condição de pagamento e parcelas
    #
    if getattr(doc_obj, 'finan_lancamento_id', False):
        nfse.condicao_pagamento = 'A PRAZO'
        parcela = Parcela()
        parcela.numero = 1
        parcela.data_vencimento = parse_datetime(doc_obj.finan_lancamento_id.data_vencimento).date()
        parcela.valor = doc_obj.vr_fatura
        nfse.parcelas.append(parcela)

    else:
        if len(doc_obj.duplicata_ids) == 0 or (len(doc_obj.duplicata_ids) == 1 and doc_obj.duplicata_ids[0].data_vencimento == doc_obj.data_emissao_brasilia):
            nfse.condicao_pagamento = 'A VISTA'

        else:
            nfse.condicao_pagamento = 'A PRAZO'
            i = 1
            for dup_obj in doc_obj.duplicata_ids:
                parcela = Parcela()
                parcela.numero = i
                i += 1
                parcela.data_vencimento = parse_datetime(dup_obj.data_vencimento).date()
                parcela.valor = D(str(dup_obj.valor)).quantize(D('0.01'))
                nfse.parcelas.append(parcela)

    return nfse


def prepara_certificado(self, cr, uid, doc_obj):
    partner_obj = doc_obj.company_id.partner_id
    caminho_empresa = os.path.expanduser('~/sped')
    caminho_empresa = os.path.join(caminho_empresa, limpa_formatacao(partner_obj.cnpj_cpf))

    try:
        certificado.arquivo = open(os.path.join(caminho_empresa, 'certificado_caminho.txt')).read().strip().replace('\n', '').encode('utf-8')
    except:
        pass

    if doc_obj.company_id.provedor_nfse == 'IPM':
        try:
            certificado.senha = open(os.path.join(caminho_empresa, 'certificado_senha_ipm.txt')).read().strip().replace('\n', '').encode('utf-8')
        except:
            try:
                certificado.senha = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip().replace('\n', '').encode('utf-8')
            except:
                pass

    else:
        try:
            certificado.senha = open(os.path.join(caminho_empresa, 'certificado_senha.txt')).read().strip().replace('\n', '').encode('utf-8')
        except:
            pass

    if doc_obj.modelo == 'SE':
        if os.path.exists(os.path.join(caminho_empresa, 'logo_nfse_caminho.txt')):
            certificado.logo = open(os.path.join(caminho_empresa, 'logo_nfse_caminho.txt')).read().strip()

    elif doc_obj.modelo == 'RL':
        if os.path.exists(os.path.join(caminho_empresa, 'logo_recibo_caminho.txt')):
            certificado.logo = open(os.path.join(caminho_empresa, 'logo_recibo_caminho.txt')).read().strip()


def envia_nfse(self, cr, uid, doc_obj):
    prepara_certificado(self, cr, uid, doc_obj)
    nfse = monta_nfse(self, cr, uid, doc_obj)
    producao = doc_obj.ambiente_nfe == AMBIENTE_NFE_PRODUCAO

    doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
    company_obj = self.pool.get('res.company').browse(cr, 1, doc_obj.company_id.id)
    if company_obj.matriz_id:
        company_obj = company_obj.matriz_id

    ultimo_lote_nfse = company_obj.ultimo_lote_nfse or 0
    numero_lote_rps = ultimo_lote_nfse + 1
    #print('numero_lote_rps', numero_lote_rps)
    doc_obj.write({'numero_lote_rps': numero_lote_rps})

    self.pool.get('res.company').write(cr, 1, [company_obj.id], {'ultimo_lote_nfse': numero_lote_rps})
    cr.commit()
    print('provedor', company_obj.provedor_nfse, company_obj.provedor_nfse == 'NEOGRID')

    if company_obj.provedor_nfse == 'BETHA':
        try:
            resposta_envia_rps = envia_rps_betha([nfse], numero_lote_rps, certificado, producao)
        except:
            resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsEnvioResponse.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res
        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'ABRASF':
        try:
            resposta_envia_rps = envia_rps_abrasf([nfse], numero_lote_rps, certificado, producao, municipio=company_obj.partner_id.municipio_id.codigo_ibge)
        except:
            resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsEnvioResponse.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res
        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'GINFES':
        #try:
        resposta_envia_rps = envia_rps_ginfes([nfse], numero_lote_rps, certificado, producao, municipio=company_obj.partner_id.municipio_id.codigo_ibge)
        #except:
            #resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            resposta_nfse = u''
            if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Codigo: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo + '\r\n'

            if '<Mensagem>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Mensagem: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\r\n'

            if '<Correcao>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += u'Correção: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Correcao + '\r\n'

            res = doc_obj.write({'resposta_nfse': resposta_nfse, 'state': 'rejeitada'})
            cr.commit()
            return res

        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'NOTA_CARIOCA':
        #try:
        resposta_envia_rps = envia_rps_carioca([nfse], numero_lote_rps, certificado, producao)
        #except:
        #    resposta_envia_rps = ''
        #print(resposta_envia_rps.como_xml_em_texto)

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            resposta_nfse = u''
            if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Codigo: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo + '\r\n'

            if '<Mensagem>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Mensagem: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\r\n'

            if '<Correcao>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += u'Correção: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Correcao + '\r\n'

            res = doc_obj.write({'resposta_nfse': resposta_nfse, 'state': 'rejeitada'})
            cr.commit()
            return res

        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'WEBISS':

        try:
            resposta_envia_rps = envia_rps_webiss([nfse], numero_lote_rps, certificado, producao, municipio=company_obj.partner_id.municipio_id.codigo_ibge)
        except:
            resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            resposta_nfse = u''
            if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Codigo: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo + '\r\n'

            if '<Mensagem>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Mensagem: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\r\n'

            if '<Correcao>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += u'Correção: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Correcao + '\r\n'

            res = doc_obj.write({'resposta_nfse': resposta_nfse, 'state': 'rejeitada'})
            cr.commit()
            return res

        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'GOVBR':

        #try:
        resposta_envia_rps = envia_rps_govbr([nfse], numero_lote_rps, certificado, producao)
        #except:
        #    resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            resposta_nfse = u''
            if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Codigo: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo + '\r\n'

            if '<Mensagem>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Mensagem: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\r\n'

            if '<Correcao>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += u'Correção: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Correcao + '\r\n'

            res = doc_obj.write({'resposta_nfse': resposta_nfse, 'state': 'rejeitada'})
            cr.commit()
            return res

        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'FOZ_IGUACU':

        #try:
        resposta_envia_rps = envia_rps_foz_iguacu([nfse], numero_lote_rps, certificado, producao)
        #except:
        #    resposta_envia_rps = ''

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.EnviarLoteRpsResposta.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            resposta_nfse = u''
            if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Codigo: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo + '\r\n'

            if '<Mensagem>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += 'Mensagem: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\r\n'

            if '<Correcao>' in resposta_envia_rps.como_xml_em_texto:
                resposta_nfse += u'Correção: ' + resposta_envia_rps.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Correcao + '\r\n'

            res = doc_obj.write({'resposta_nfse': resposta_nfse, 'state': 'rejeitada'})
            cr.commit()
            return res

        else:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'BOANOTA':
        resposta_envia_rps = envia_rps_boanota([nfse], numero_lote_rps, certificado, producao)

        print(resposta_envia_rps)

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res
        if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            codigo_erro = u''

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo, (list, tuple)):
                for codigo in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo:
                    codigo_erro += u'\nErro: ' + codigo + '\n'
            else:
                codigo_erro = u'\nErro: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo + '\n'

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem, (list, tuple)):
                for mensagem in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem:
                    codigo_erro += u'\nMensagem: ' + mensagem + '\n'
            else:
                codigo_erro += u'\nMensagem: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\n'

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao, (list, tuple)):
                for correcao in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao:
                    codigo_erro += u'\nCorreção: ' + correcao + '\n'
            else:
                codigo_erro += u'\nCorreção: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao  + '\n'

            res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
            return res
        else :
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'PUBLICA':
        resposta_envia_rps = envia_rps_publica([nfse], numero_lote_rps, certificado, producao)

        #print(resposta_envia_rps)

        if isinstance(resposta_envia_rps, DicionarioBrasil) and '<Protocolo>' in resposta_envia_rps.como_xml_em_texto:
            protocolo = resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.Protocolo
            res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
            cr.commit()
            return res
        if '<Codigo>' in resposta_envia_rps.como_xml_em_texto:
            codigo_erro = u''

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo, (list, tuple)):
                for codigo in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo:
                    codigo_erro += u'\nErro: ' + codigo + '\n'
            else:
                codigo_erro = u'\nErro: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Codigo + '\n'

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem, (list, tuple)):
                for mensagem in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem:
                    codigo_erro += u'\nMensagem: ' + mensagem + '\n'
            else:
                codigo_erro += u'\nMensagem: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Mensagem + '\n'

            if isinstance(resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao, (list, tuple)):
                for correcao in resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao:
                    codigo_erro += u'\nCorreção: ' + correcao + '\n'
            else:
                codigo_erro += u'\nCorreção: ' + resposta_envia_rps.RecepcionarLoteRpsResponse.RecepcionarLoteRpsResult.ListaMensagemRetorno.MensagemRetorno.Correcao  + '\n'

            res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
            return res
        else :
            res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
            cr.commit()
            return res

    elif company_obj.provedor_nfse == 'IPM':
        try:
            resposta_envia_rps = envia_rps_ipm([nfse], numero_lote_rps, certificado, producao)

        except:
            resposta_envia_rps = ''

        if '<cod_verificador_autenticidade></cod_verificador_autenticidade>' in resposta_envia_rps.como_xml_em_texto:
            codigo_erro = u''

            if isinstance(resposta_envia_rps.retorno.mensagem.codigo, (list, tuple)):
                for codigo in resposta_envia_rps.retorno.mensagem.codigo:
                    codigo_erro += codigo + '\n'
            else:
                codigo_erro = resposta_envia_rps.retorno.mensagem.codigo

            res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
            return res

        elif '<cod_verificador_autenticidade>' in resposta_envia_rps.como_xml_em_texto:
            retorno = resposta_envia_rps.retorno
            nfse.codigo_verificacao = retorno.cod_verificador_autenticidade
            nfse.numero = retorno.numero_nfse.inteiro
            nfse.serie = retorno.serie_nfse
            nfse.data_hora_emissao = str(parse_datetime(retorno.data_nfse).date()) + ' ' + retorno.hora_nfse
            nfse.fuso_horario = fuso_horario_sistema()
            nfse.link_verificacao = retorno.link_nfse

            #if doc_obj.nota_substituida_id:
                #doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                #if doc_obj.nota_substituida_id.finan_lancamento_id:
                    #doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

            doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
            doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
            grava_pdf(self, cr, uid, doc_obj)
            res = doc_obj.write({'state': 'autorizada'})
            cr.commit()
            return res


            #print(gera_rps_ipm([nfse], numero_lote_rps))

    elif company_obj.provedor_nfse == 'PRODAM':
        resposta_envia_rps = envia_rps_prodam([nfse], numero_lote_rps, certificado, producao, municipio=company_obj.partner_id.municipio_id.codigo_ibge)

        if isinstance(resposta_envia_rps, DicionarioBrasil):
            retorno = resposta_envia_rps.EnvioLoteRPSResponse.RetornoXML.RetornoEnvioLoteRPS

            if '<Sucesso>true</Sucesso>' in resposta_envia_rps.como_xml_em_texto:
                nfse.codigo_verificacao = retorno.ChaveNFeRPS.ChaveNFe.CodigoVerificacao
                nfse.numero = retorno.ChaveNFeRPS.ChaveNFe.NumeroNFe.inteiro
                #nfse.serie = retorno.serie_nfse
                nfse.data_hora_emissao = str(parse_datetime(retorno.Cabecalho.InformacoesLote.DataEnvioLote.replace('T', ' ')))
                nfse.fuso_horario = fuso_horario_sistema()

                if company_obj.partner_id.municipio_id.codigo_ibge == '42024040000':
                    nfse.link_verificacao = 'https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx?inscricao={a}&nf={b}&verificacao={c}'.format(a=doc_obj.company_id.partner_id.im,b=nfse.numero,c=nfse.codigo_verificacao)
                else:
                    nfse.link_verificacao = 'http://nfse.blumenau.sc.gov.br/BL0101/verificacao.aspx'

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

    elif company_obj.provedor_nfse == 'JOAO_PESSOA':
        resposta_envia_rps = envia_rps_joao_pessoa([nfse], numero_lote_rps, certificado, producao)

        if isinstance(resposta_envia_rps, DicionarioBrasil):
            if '<Protocolo>' in resposta_envia_rps.como_xml_em_texto or '<nfse:Protocolo>' in resposta_envia_rps.como_xml_em_texto:
                protocolo = resposta_envia_rps.RecepcionarLoteRpsResponse.EnviarLoteRpsResposta.Protocolo
                res = doc_obj.write({'numero_protocolo_nfse': protocolo, 'state': 'enviada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_envia_rps.como_xml_em_texto or '<nfse:Codigo>' in resposta_envia_rps.como_xml_em_texto:
                codigo_erro = u'\nErro: '

                codigo_erro += resposta_envia_rps.RecepcionarLoteRpsResponse.outputXML.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Codigo or ''
                codigo_erro += '\n'
                codigo_erro += resposta_envia_rps.RecepcionarLoteRpsResponse.outputXML.EnviarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno.Mensagem or ''

                res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                return res

            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA RESPOSTA DA PREFEITURA', 'state': 'rejeitada'})
                cr.commit()
                return res

                #nfse.codigo_verificacao = retorno.ChaveNFeRPS.ChaveNFe.CodigoVerificacao
                #nfse.numero = retorno.ChaveNFeRPS.ChaveNFe.NumeroNFe.inteiro
                ##nfse.serie = retorno.serie_nfse
                #nfse.data_hora_emissao = str(parse_datetime(retorno.Cabecalho.InformacoesLote.DataEnvioLote.replace('T', ' ')))
                #nfse.fuso_horario = fuso_horario_sistema()
                #nfse.link_verificacao = 'http://nfse.blumenau.sc.gov.br/BL0101/verificacao.aspx'

                #if doc_obj.finan_lancamento_id:
                    #doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                #doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                #doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                #grava_pdf(self, cr, uid, doc_obj)
                #res = doc_obj.write({'state': 'autorizada'})
                #cr.commit()
                #return res

    elif company_obj.provedor_nfse == 'NEOGRID':
        gera_rps_neogrid([nfse], numero_lote_rps, certificado)
        res = doc_obj.write({'numero_protocolo_nfse': doc_obj.numero_lote_rps, 'state': 'enviada'})
        cr.commit()
        return res


def consulta_nfse(self, cr, uid, doc_obj):
    nfse = monta_nfse(self, cr, uid, doc_obj)
    prepara_certificado(self, cr, uid, doc_obj)
    producao = doc_obj.ambiente_nfe == AMBIENTE_NFE_PRODUCAO

    company_obj = self.pool.get('res.company').browse(cr, 1, doc_obj.company_id.id)
    if company_obj.matriz_id:
        company_obj = company_obj.matriz_id

    if company_obj.provedor_nfse == 'NEOGRID':
        resposta_consulta_situacao_rps = envia_consulta_rps_neogrid(doc_obj.numero_rps)

        if isinstance(resposta_consulta_situacao_rps, basestring):
            res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
            cr.commit()
            return res

        print('resposta_consulta_situacao_rps')
        #print(resposta_consulta_situacao_rps.como_xml_em_texto)
        retorno = resposta_consulta_situacao_rps.procNeoGridNFSe.NeoGrid.retNeoGridNFSe
        print(retorno.como_xml_em_texto)
        nfse.codigo_verificacao = retorno.cVerificaNFSe
        nfse.numero = retorno.nNFSe.inteiro
        nfse.data_hora_emissao = retorno.dtEmisNFSe
        nfse.protocolo = retorno.nProt
        nfse.fuso_horario = fuso_horario_sistema()
        nfse.link_verificacao = 'https://sispmjp.joaopessoa.pb.gov.br:8080/nfse/'

        if doc_obj.finan_lancamento_id:
            doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

        doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao, 'numero_protocolo_nfse': nfse.protocolo})
        doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
        grava_pdf(self, cr, uid, doc_obj)
        res = doc_obj.write({'state': 'autorizada'})
        cr.commit()
        return res

    elif doc_obj.numero_protocolo_nfse:
        prestador = nfse.prestador
        protocolo = doc_obj.numero_protocolo_nfse

        if company_obj.provedor_nfse == 'BETHA':
            try:
                resposta_consulta_situacao_rps = envia_consulta_situacao_rps_betha(protocolo, prestador, certificado, producao)
            except:
                resposta_consulta_situacao_rps = ''

            if resposta_consulta_situacao_rps == '' or 'env:Fault' in resposta_consulta_situacao_rps.como_xml_em_texto:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res


            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarSituacaoLoteRpsEnvioResponse.ConsultarSituacaoLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno

                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res

            elif '<Situacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarSituacaoLoteRpsEnvioResponse.ConsultarSituacaoLoteRpsResposta
                situacao = mensagem_retorno.Situacao

                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')

                if situacao == '1':
                    codigo_erro += u'\nSituação 1 - não recebida'

                elif situacao == '2':
                    codigo_erro += u'\nSituação 2 - aguardando processamento'

                elif situacao == '3':
                    codigo_erro += u'\nSituação 3 - rejeitada'

                elif situacao == '4':
                    codigo_erro += u'\nSituação 4 - autorizada'

                doc_obj.write({'resposta_nfse': codigo_erro})
                cr.commit()

                if situacao in ['3', '4']:
                    return _consulta_nfse(self, cr, uid, doc_obj, nfse, producao, prestador, protocolo, company_obj.provedor_nfse)

        elif company_obj.provedor_nfse == 'GINFES':
            try:
                resposta_consulta_situacao_rps = envia_consulta_situacao_rps_ginfes(doc_obj.id, protocolo, prestador, certificado, producao)
            except:
                resposta_consulta_situacao_rps = ''

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

            elif '<CodigoVerificacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                infnfse = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaNfse.CompNfse.Nfse.InfNfse
                nfse.codigo_verificacao = infnfse.CodigoVerificacao
                nfse.numero = infnfse.Numero.inteiro
                nfse.data_hora_emissao = infnfse.DataEmissao
                nfse.fuso_horario = fuso_horario_sistema()

                if doc_obj.nota_substituida_id:
                    doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                    if doc_obj.nota_substituida_id.finan_lancamento_id:
                        doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})


                nfse.link_verificacao = 'http://visualizar.ginfes.com.br/report/consultarNota?__report=nfs_ver9&cdVerificacao={verificacao}&numNota={numero}&cnpjPrestador={cnpj}'.format(verificacao=nfse.codigo_verificacao, numero=nfse.numero, cnpj=nfse.prestador.cnpj_cpf)

                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno

                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res
            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

        elif company_obj.provedor_nfse == 'NOTA_CARIOCA':
            try:
                resposta_consulta_situacao_rps = envia_consulta_rps_carioca(protocolo, prestador, certificado, producao)
            except:
                resposta_consulta_situacao_rps = ''
            #print(resposta_consulta_situacao_rps.como_xml_em_texto)

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

            elif '<CodigoVerificacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                infnfse = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaNfse.CompNfse.Nfse.InfNfse
                nfse.codigo_verificacao = infnfse.CodigoVerificacao
                nfse.numero = infnfse.Numero.inteiro
                nfse.data_hora_emissao = infnfse.DataEmissao
                nfse.fuso_horario = fuso_horario_sistema()

                if doc_obj.nota_substituida_id:
                    doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                    if doc_obj.nota_substituida_id.finan_lancamento_id:
                        doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                nfse.link_verificacao = 'https://notacarioca.rio.gov.br/nfse.aspx?inscricao={im}&nf={numero}&cod={verificacao}'.replace(numero=nfse.numero, im=nfe.prestador.im, verificacao=nfse.codigo_verificacao.replace('-', ''))

                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:

                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                codigo_erro += u'\r\n'

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res
            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

        elif company_obj.provedor_nfse == 'FOZ_IGUACU':
            try:
                resposta_consulta_situacao_rps = envia_consulta_rps_foz_iguacu(protocolo, prestador, certificado, producao)
            except:
                resposta_consulta_situacao_rps = ''

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

            elif '<CodigoVerificacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                infnfse = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaNfse.CompNfse.Nfse.InfNfse
                nfse.codigo_verificacao = infnfse.CodigoVerificacao
                nfse.numero = infnfse.Numero.inteiro
                nfse.data_hora_emissao = infnfse.DataEmissao
                nfse.fuso_horario = fuso_horario_sistema()

                if doc_obj.nota_substituida_id:
                    doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                    if doc_obj.nota_substituida_id.finan_lancamento_id:
                        doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                nfse.link_verificacao = ''#'https://notacarioca.rio.gov.br/nfse.aspx?inscricao={im}&nf={numero}&cod={verificacao}'.replace(numero=nfse.numero, im=nfe.prestador.im, verificacao=nfse.codigo_verificacao.replace('-', ''))

                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:

                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                codigo_erro += u'\r\n'

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res
            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res



        elif company_obj.provedor_nfse == 'WEBISS':
            #try:
            resposta_consulta_situacao_rps = envia_consulta_rps_webiss(protocolo, prestador, certificado, producao)
            #except:
            #    resposta_consulta_situacao_rps = ''
            #print(resposta_consulta_situacao_rps.como_xml_em_texto)

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS - RPS EM PROCESSAMENTO'})
                cr.commit()
                return res

            elif '<CodigoVerificacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                infnfse = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaNfse.CompNfse.Nfse.InfNfse
                nfse.codigo_verificacao = infnfse.CodigoVerificacao
                numero = str(infnfse.Numero.inteiro)
                nfse.data_hora_emissao = str(parse_datetime(infnfse.DataEmissao.replace('T', ' ')))
                nfse.fuso_horario = fuso_horario_sistema()

                if str(numero) > 10:
                    numero_prefeitura = float(numero)
                    nfse.numero = int(numero[4:])
                else:
                    numero_prefeitura = float(numero)
                    nfse.numero = int(numero)

                if doc_obj.nota_substituida_id:
                    doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                    if doc_obj.nota_substituida_id.finan_lancamento_id:
                        doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                #nfse.link_verificacao = 'https://notacarioca.rio.gov.br/nfse.aspx?inscricao={im}&nf={numero}&cod={verificacao}'.replace(numero=nfse.numero, im=nfe.prestador.im, verificacao=nfse.codigo_verificacao.replace('-', ''))
                nfse.link_verificacao = ''

                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'numero_prefeitura': numero_prefeitura, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:

                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                codigo_erro += u'\r\n'

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res
            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

        elif company_obj.provedor_nfse == 'GOVBR':
            #try:
            resposta_consulta_situacao_rps = envia_consulta_rps_govbr(protocolo, prestador, certificado, producao)
            #except:
            #    resposta_consulta_situacao_rps = ''
            #print(resposta_consulta_situacao_rps.como_xml_em_texto)

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

            elif '<CodigoVerificacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                infnfse = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaNfse.CompNfse.Nfse.InfNfse
                nfse.codigo_verificacao = infnfse.CodigoVerificacao
                numero = str(infnfse.Numero.inteiro)
                nfse.data_hora_emissao = infnfse.DataEmissao
                nfse.fuso_horario = fuso_horario_sistema()

                if str(numero) > 10:
                    numero_prefeitura = float(numero)
                    nfse.numero = int(numero[4:])
                else:
                    numero_prefeitura = float(numero)
                    nfse.numero = int(numero)

                if doc_obj.nota_substituida_id:
                    doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                    if doc_obj.nota_substituida_id.finan_lancamento_id:
                        doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

                if doc_obj.finan_lancamento_id:
                    doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})

                nfse.link_verificacao = ''#'https://notacarioca.rio.gov.br/nfse.aspx?inscricao={im}&nf={numero}&cod={verificacao}'.replace(numero=nfse.numero, im=nfe.prestador.im, verificacao=nfse.codigo_verificacao.replace('-', ''))


                doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'numero_prefeitura': numero_prefeitura, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
                doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
                grava_pdf(self, cr, uid, doc_obj)
                res = doc_obj.write({'state': 'autorizada'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:

                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                codigo_erro += u'\r\n'

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res
            else:
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res


        elif company_obj.provedor_nfse == 'BOANOTA':
            resposta_consulta_situacao_rps = envia_consulta_situacao_rps_boanota(protocolo, prestador, certificado, producao)

            if resposta_consulta_situacao_rps == '':
                res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DA SITUAÇÃO DO RPS'})
                cr.commit()
                return res

            elif '<Codigo>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarSituacaoLoteRpsResponse.ConsultarSituacaoLoteRpsResult.ListaMensagemRetorno.MensagemRetorno

                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao

                if mensagem_retorno.Codigo == 'E92':
                    #
                    # Nota ainda não processada
                    #
                    res = doc_obj.write({'resposta_nfse': codigo_erro})
                    cr.commit()
                    return res

                else:
                    res = doc_obj.write({'resposta_nfse': codigo_erro, 'state': 'rejeitada'})
                    cr.commit()
                    return res

            elif '<Situacao>' in resposta_consulta_situacao_rps.como_xml_em_texto:
                mensagem_retorno = resposta_consulta_situacao_rps.ConsultarSituacaoLoteRpsResponse.ConsultarSituacaoLoteRpsResult
                situacao = mensagem_retorno.Situacao

                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')

                if situacao == '1':
                    codigo_erro += u'\nSituação 1 - não recebida'

                elif situacao == '2':
                    codigo_erro += u'\nSituação 2 - aguardando processamento'

                elif situacao == '3':
                    codigo_erro += u'\nSituação 3 - rejeitada'

                elif situacao == '4':
                    codigo_erro += u'\nSituação 4 - autorizada'

                doc_obj.write({'resposta_nfse': codigo_erro})
                cr.commit()

                #if situacao in ['3', '4']:
                #    return _consulta_nfse(self, cr, uid, doc_obj, nfse, producao, prestador, protocolo, company_obj.provedor_nfse )


def _consulta_nfse(self, cr, uid, doc_obj, nfse, producao, prestador, protocolo, provedor_nfse):

    if provedor_nfse == 'BETHA':
        try:
            resposta_consulta_rps = envia_consulta_rps_betha(protocolo, prestador, certificado, producao)
        except:
            resposta_consulta_rps = ''

        if resposta_consulta_rps == '' or 'env:Fault' in resposta_consulta_rps.como_xml_em_texto:
            res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DO RPS'})
            cr.commit()
            return res

        elif '<CodigoVerificacao>' in resposta_consulta_rps.como_xml_em_texto:
            infnfse = resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaNfse.ComplNfse.Nfse.InfNfse
            nfse.codigo_verificacao = infnfse.CodigoVerificacao
            nfse.numero = infnfse.Numero.inteiro
            nfse.data_hora_emissao = infnfse.DataEmissao
            nfse.fuso_horario = fuso_horario_sistema()
            nfse.link_verificacao = infnfse.OutrasInformacoes

            if doc_obj.nota_substituida_id:
                doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                if doc_obj.nota_substituida_id.finan_lancamento_id:
                    doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})


            doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
            doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
            grava_pdf(self, cr, uid, doc_obj)
            res = doc_obj.write({'state': 'autorizada'})
            cr.commit()
            return res

        elif '<ListaNfse></ListaNfse>' in resposta_consulta_rps.como_xml_em_texto:

            if isinstance(resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaMensagemRetorno, list):
                pass
            else:
                mensagem_retorno = resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                doc_obj.write({'state': 'rejeitada', 'resposta_nfse': codigo_erro})
                cr.commit()

            return True

    elif provedor_nfse == 'BOANOTA':

        resposta_consulta_rps = envia_consulta_rps_boanota(protocolo, prestador, certificado, producao)

        if resposta_consulta_rps == '':
            res = doc_obj.write({'resposta_nfse': u'FALHA NA CONSULTA DO RPS'})
            cr.commit()
            return res

        elif '<CodigoVerificacao>' in resposta_consulta_rps.como_xml_em_texto:
            infnfse = resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaNfse.ComplNfse.Nfse.InfNfse
            nfse.codigo_verificacao = infnfse.CodigoVerificacao
            nfse.numero = infnfse.Numero.inteiro
            nfse.data_hora_emissao = infnfse.DataEmissao
            nfse.fuso_horario = fuso_horario_sistema()
            nfse.link_verificacao = infnfse.OutrasInformacoes

            if doc_obj.nota_substituida_id:
                doc_obj.nota_substituida_id.write({'situacao': '02', 'data_cancelamento': nfse.data_hora_emissao_iso_utc, 'state': 'cancelada'})
                if doc_obj.nota_substituida_id.finan_lancamento_id:
                    doc_obj.nota_substituida_id.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})

            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'numero_documento': str(nfse.numero)})


            doc_obj.write({'codigo_verificacao_nfse': nfse.codigo_verificacao, 'numero': nfse.numero, 'data_emissao': nfse.data_hora_emissao_iso_utc, 'link_verificacao_nfse': nfse.link_verificacao})
            doc_obj = self.pool.get('sped.documento').browse(cr, uid, doc_obj.id)
            grava_pdf(self, cr, uid, doc_obj)
            res = doc_obj.write({'state': 'autorizada'})
            cr.commit()
            return res

        elif '<ListaNfse></ListaNfse>' in resposta_consulta_rps.como_xml_em_texto:

            if isinstance(resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaMensagemRetorno, list):
                pass
            else:
                mensagem_retorno = resposta_consulta_rps.ConsultarLoteRpsEnvioResponse.ConsultarLoteRpsResposta.ListaMensagemRetorno.MensagemRetorno
                codigo_erro = u'Data e hora da consulta: ' + data_hora_horario_brasilia(datetime.now()).strftime('%a, %d-%b-%Y, %H:%M:%S').decode('utf-8')
                codigo_erro += u'\nCódigo do erro: ' + mensagem_retorno.Codigo
                codigo_erro += u'\nMensagem: ' + mensagem_retorno.Mensagem
                codigo_erro += u'\nCorreção: ' + mensagem_retorno.Correcao
                doc_obj.write({'state': 'rejeitada', 'resposta_nfse': codigo_erro})
                cr.commit()

            return True



def grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo):
    dados = {
        'datas': base64.encodestring(conteudo_arquivo),
        'name': nome_arquivo,
        'datas_fname': nome_arquivo,
        'res_model': 'sped.documento',
        'res_id': doc_obj.id,
    }

    attachment_pool = self.pool.get('ir.attachment')

    #exclui_arquivo(self, cr, uid, doc_obj, nome_arquivo)
    anexo_ids = attachment_pool.search(cr, uid, [
        ('res_model', '=', 'sped.documento'),
        ('res_id', '=', doc_obj.id),
        ('name', '=', nome_arquivo),
    ])

    if anexo_ids:
        attachment_pool.write(cr, uid, anexo_ids, dados)
        anexo = anexo_ids
    else:
        anexo = attachment_pool.create(cr, uid, dados)

    cr.commit()
    return anexo


def exclui_arquivo(self, cr, uid, doc_obj, nome_arquivo):
    attachment_pool = self.pool.get('ir.attachment')

    anexo_ids = attachment_pool.search(cr, uid, [
        ('res_model', '=', 'sped.documento'),
        ('res_id', '=', doc_obj.id),
        ('name', '=', nome_arquivo),
    ])

    return attachment_pool.unlink(cr, uid, anexo_ids)


def grava_pdf(self, cr, uid, doc_obj):
    nfse = monta_nfse(self, cr, uid, doc_obj)

    if hasattr(doc_obj, 'finan_lancamento_id') and doc_obj.finan_lancamento_id and doc_obj.finan_lancamento_id.carteira_id:
        if (not getattr(doc_obj, 'finan_contrato_id', False)) or (not getattr(doc_obj.finan_contrato_id, 'nf_sem_boleto', False)):
            boleto = doc_obj.finan_lancamento_id.gerar_boleto()
            nfse.descricao = nfse.descricao.replace('\n', ' | ')
            nfse.boleto = boleto

    elif doc_obj.duplicata_ids:
        dup_obj = doc_obj.duplicata_ids[0]

        if hasattr(dup_obj, 'finan_lancamento_id') and dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.carteira_id:
            boleto = dup_obj.finan_lancamento_id.gerar_boleto()
            nfse.descricao = nfse.descricao.replace('\n', ' | ')
            nfse.boleto = boleto

    gera_nfse_pdf([nfse])
    pdf = nfse.pdf

    nome_arquivo = 'nfse_' + doc_obj.serie + '_' + str(doc_obj.numero) + '.pdf'
    conteudo_arquivo = pdf

    if doc_obj.numero != -1:
        exclui_arquivo(self, cr, uid, doc_obj, 'nfse_' + doc_obj.serie + '_-1.pdf')

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo)
    return anexo


def cancela_nfse(self, cr, uid, doc_obj):
    nfse = monta_nfse(self, cr, uid, doc_obj)

    prepara_certificado(self, cr, uid, doc_obj)
    producao = doc_obj.ambiente_nfe == AMBIENTE_NFE_PRODUCAO

    company_obj = self.pool.get('res.company').browse(cr, 1, doc_obj.company_id.id)
    if company_obj.matriz_id:
        company_obj = company_obj.matriz_id

    if company_obj.provedor_nfse == 'BETHA':
        try:
            resposta_cancelamento = cancela_nota_betha(nfse, certificado, producao)
        except:
            resposta_cancelamento = ''

        if resposta_cancelamento == '':
            res = doc_obj.write({'resposta_nfse': u'FALHA NO CANCELAMENTO'})
            cr.commit()
            return res

        elif '<InfConfirmacaoCancelamento>' in resposta_cancelamento.como_xml_em_texto:
            nfse.data_cancelamento = resposta_cancelamento.CancelarNfseEnvioResponse.CancelarNfseReposta.Cancelamento.Confirmacao.InfConfirmacaoCancelamento.DataHora

            nfse.fuso_horario = 'UTC'
            data_cancelamento = nfse.data_cancelamento_iso_utc

            doc_obj.write({'data_cancelamento': data_cancelamento, 'situacao': '02'})
            cr.commit()

            #
            # Desvincula o financeiro e volta para provisionado
            #
            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})
            cr.commit()
    if company_obj.provedor_nfse == 'GINFES':

        resposta_cancelamento = cancela_nota_ginfes(nfse, certificado, producao)
        #except:
        #    resposta_cancelamento = ''

        if resposta_cancelamento == '':
            res = doc_obj.write({'resposta_nfse': u'FALHA NO CANCELAMENTO'})
            cr.commit()
            return res

        elif '<InfConfirmacaoCancelamento>' in resposta_cancelamento.como_xml_em_texto:
            nfse.data_cancelamento = resposta_cancelamento.CancelarNfseEnvioResponse.CancelarNfseReposta.Cancelamento.Confirmacao.InfConfirmacaoCancelamento.DataHora

            nfse.fuso_horario = 'UTC'
            data_cancelamento = nfse.data_cancelamento_iso_utc

            doc_obj.write({'data_cancelamento': data_cancelamento, 'situacao': '02'})
            cr.commit()

            #
            # Desvincula o financeiro e volta para provisionado
            #
            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})
            cr.commit()

    if company_obj.provedor_nfse == 'BOANOTA':

        resposta_cancelamento = cancela_nota_boanota(nfse, certificado, producao)

        print(resposta_cancelamento.como_xml_em_texto)

        if resposta_cancelamento == '':
            res = doc_obj.write({'resposta_nfse': u'FALHA NO CANCELAMENTO'})
            cr.commit()
            return res

        elif '<InfConfirmacaoCancelamento>' in resposta_cancelamento.como_xml_em_texto:
            nfse.data_cancelamento = resposta_cancelamento.CancelarNfseEnvioResponse.CancelarNfseReposta.Cancelamento.Confirmacao.InfConfirmacaoCancelamento.DataHora

            nfse.fuso_horario = 'UTC'
            data_cancelamento = nfse.data_cancelamento_iso_utc

            doc_obj.write({'data_cancelamento': data_cancelamento, 'situacao': '02'})
            cr.commit()

            #
            # Desvincula o financeiro e volta para provisionado
            #
            if doc_obj.finan_lancamento_id:
                doc_obj.finan_lancamento_id.write({'provisionado': True, 'sped_documento_id': False})
            cr.commit()

    return True


def grava_pdf_recibo_locacao(self, cr, uid, doc_obj, boleto=None):
    nfse = monta_nfse(self, cr, uid, doc_obj)

    if boleto:
        nfse.boleto = boleto

    elif hasattr(doc_obj, 'finan_lancamento_id') and doc_obj.finan_lancamento_id and doc_obj.finan_lancamento_id.carteira_id:
        if (not getattr(doc_obj, 'finan_contrato_id', False)) or (not getattr(doc_obj.finan_contrato_id, 'nf_sem_boleto', False)):
            boleto = doc_obj.finan_lancamento_id.gerar_boleto()
            nfse.descricao = nfse.descricao.replace('\n', ' | ')
            nfse.boleto = boleto

    elif doc_obj.duplicata_ids:
        dup_obj = doc_obj.duplicata_ids[0]

        if hasattr(dup_obj, 'finan_lancamento_id') and dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.carteira_id:
            boleto = dup_obj.finan_lancamento_id.gerar_boleto()
            nfse.descricao = nfse.descricao.replace('\n', ' | ')
            nfse.boleto = boleto

    nfse.obs = u'INSS dispensado conforme IN nº 971 de 13/11/2009, art. 177, parágrafo único; '
    nfse.obs += u'IRF dispensado conforme lei nº 9.430/1996, art. 67; '
    nfse.obs += u'CSLL, PIS e COFINS dispensados conforme lei nº 10.925/2004; '
    nfse.obs += u'Emissão de nota fiscal dispensada conforme lei complementar nº 116/2003'

    if doc_obj.infadfisco:
        nfse.obs += '; '
        nfse.obs += doc_obj.infadfisco

    if 'PATRIMONIAL' in cr.dbname.upper() or 'TESTE_' in cr.dbname.upper():
        gera_recibo_locacao_pdf([nfse])
        nome_arquivo = 'recibo_locacao_' + str(doc_obj.numero) + '.pdf'
    else:
        gera_recibo_locacao_pdf([nfse], titulo_fatura=True)
        nome_arquivo = 'fatura_locacao_' + str(doc_obj.numero) + '.pdf'

    pdf = nfse.pdf

    conteudo_arquivo = pdf

    anexo = grava_arquivo(self, cr, uid, doc_obj, nome_arquivo, conteudo_arquivo)
    return anexo, pdf
