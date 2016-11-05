# -*- coding: utf-8 -*-

#from __future__ import (division, print_function, unicode_literals, absolute_import)


from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones


def localiza_participante(self, cr, uid, cnpj_cpf):
    cnpj_cpf = limpa_formatacao(cnpj_cpf)

    if len(cnpj_cpf) == 14:
        cnpj_cpf = formata_cnpj(cnpj_cpf)
    else:
        cnpj_cpf = formata_cpf(cnpj_cpf)

    participante_id = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf)])

    if participante_id:
        return participante_id[0]

    return False


def localiza_participante_nome(self, cr, uid, nome):
    participante_id = self.pool.get('res.partner').search(cr, uid, [('razao_social', '=', nome)])

    if participante_id:
        return participante_id[0]

    return False


def processa_participante(self, cr, uid, partnfe, endpartnfe):
    #
    # Identifica se é pessoa física, jurídica ou estrangeiro/não identificado
    #
    if len(partnfe.CNPJ.valor) == 14:
        participante_id = localiza_participante(self, cr, uid, partnfe.CNPJ.valor)

    elif len(partnfe.CPF.valor) == 11:
        participante_id = localiza_participante(self, cr, uid, partnfe.CPF.valor)

    else:
        participante_id = localiza_participante(self, cr, uid, partnfe.xNome.valor.upper())

    if participante_id:
        return participante_id

    #
    # Não encontrou, vamos criar
    #
    dados_participante = {
        'type': 'default',
        'name': partnfe.xNome.valor.upper(),
        'razao_social': partnfe.xNome.valor.upper(),
        'cnpj_cpf': '',
        'fantasia': '',
        'endereco': endpartnfe.xLgr.valor.upper(),
        'numero': endpartnfe.nro.valor.upper(),
        'complemento': endpartnfe.xCpl.valor.upper(),
        'bairro': endpartnfe.xBairro.valor.upper(),
        'municipio_id': '',
        'cep': unicode(endpartnfe.CEP.valor)[:5] + '-' + unicode(endpartnfe.CEP.valor)[5:],
        'fone': '',
        'phone': '',
        'email_nfe': '',
        'email': '',
        'contribuinte': '2' if partnfe.IE.valor in ['', 'ISENTO'] else '1',
        'ie': partnfe.IE.valor,
        'im': '',
        'suframa': '',
    }

    #
    # Dados que não estão no destinatário ou no emitente
    #
    try:
        dados_participante['fantasia'] = partnfe.xFant.valor.upper()
    except:
        dados_participante['fantasia'] = partnfe.xNome.valor.upper()

    try:
        fone = unicode(endpartnfe.fone.valor).upper()
        try:
            if valida_fone_internacional(fone) or valida_fone_fixo(fone):
                dados_participante['fone'] = formata_fone(fone)
            elif valida_fone_celular(fone):
                dados_participante['celular'] = formata_fone(fone)
        except:
            pass
    finally:
        dados_participante['phone'] = dados_participante['fone']

    try:
        try:
            dados_participante['email_nfe'] = partnfe.email.valor.lower()
        except:
            pass
    finally:
        dados_participante['email'] = dados_participante['email_nfe']

    try:
        dados_participante['im'] = partnfe.IM.valor.upper()
    except:
        pass

    try:
        dados_participante['suframa'] = formata_inscricao_estadual(partnfe.ISUF.valor.upper(), 'SUFRAMA')
    except:
        pass

    #
    # Vamos identificar o município, saber se o cara é estrangeiro ou não identificado
    #
    dados_participante['municipio_id'] = processa_municipio(self, cr, uid, endpartnfe)

    if unicode(endpartnfe.cPais.valor) != '1058':
        #
        # Não tem CNPJ nem CPF, é estrangeiro, vamos criar um CNPJ fictício
        #
        dados_participante['cnpj_cpf'] = 'EX' + dados_participante['razao_social'].replace(' ', '_').upper()
        dados_participante['cnpj_cpf'] = dados_participante['cnpj_cpf'][:18]

    else:
        if len(partnfe.CNPJ.valor) == 14:
            dados_participante['cnpj_cpf'] = formata_cnpj(partnfe.CNPJ.valor)

        elif len(partnfe.CPF.valor) == 11:
            dados_participante['cnpj_cpf'] = formata_cpf(partnfe.CPF.valor)

        else:
            #
            # Brasileiro não identificado, vamos criar um CPF fictício
            #
            dados_participante['cnpj_cpf'] = 'NI' + dados_participante['nome'].replace(' ', '_').upper()
            dados_participante['cnpj_cpf'] = dados_participante['cnpj_cpf'][:18]

    #
    # Criamos primeiro o partner_id
    #
    partner_id = self.pool.get('res.partner').create(cr, uid, dados_participante)
    dados_participante['partner_id'] = partner_id
    partner_address_id = self.pool.get('res.partner.address').create(cr, uid, dados_participante)

    return processa_participante(self, cr, uid, partnfe, endpartnfe)


def processa_municipio(self, cr, uid, endpartnfe):
    codigo_pais = unicode(endpartnfe.cPais.valor)
    #nome_pais = endpartnfe.xPais.valor
    codigo_municipio = unicode(endpartnfe.cMun.valor)
    #nome_municipio = endpartnfe.xMun.valor

    if codigo_pais != '1058':
        codigo_municipio = '9999999' + codigo_pais
    else:
        codigo_municipio = codigo_municipio + '0000'

    municipio_id = localiza_municipio(self, cr, uid, codigo_municipio)

    return municipio_id


def localiza_municipio(self, cr, uid, codigo):
    if len(codigo) == 7:
        codigo += '0000'

    municipio_id = self.pool.get('sped.municipio').search(cr, uid, [('codigo_ibge', '=', codigo)])

    if municipio_id:
        return municipio_id[0]

    return False
