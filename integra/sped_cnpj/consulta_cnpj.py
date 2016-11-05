# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals


import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import base64


def _separa_campo(soup, table, td, b):
    tables = soup.html.body.findAll('table')
    tds = tables[table].findAll('td')
    bs = tds[td].findAll('b')
    campo = unicode(bs[b]).strip('<b>').strip('</b>').strip()
    campo = campo.replace('&amp;', '&')

    while '  ' in campo:
        campo = campo.replace('  ', ' ')

    return campo


def _separa_cnae(campo):
    cnae = campo.split(u' ')[0]
    cnae = cnae.replace(u'.', u'').replace(u'-', u'')
    cnae = cnae[:7]

    return cnae


def _separa_cnaes(soup, retorno):
    # CNAE principal
    cnae = _separa_cnae(_separa_campo(soup, 7, 0, 0))

    retorno['cnae'] = [cnae]

    tables = soup.html.body.findAll('table')
    tds = tables[8].findAll('td')
    bs = tds[0].findAll('b')

    for i in range(len(bs)):
        cnae = _separa_campo(soup, 8, 0, i)
        if cnae[0] != 'N':
            cnae = _separa_cnae(cnae)
            #print(cnae)
            retorno['cnae'] += [cnae]


def cookie_receita():
    url = 'http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp'

    con = urllib2.urlopen(url)
    pagina = con.read().decode('iso8859-1')
    # Separa o cookie da sessão
    cookies = con.info()['set-cookie']
    cookie = cookies.split(';')[0]
    con.close()

    #
    # Pega o campo que tem o certificado do captcha
    #
    certificado_captcha = pagina.split("<input type=hidden id=viewstate name=viewstate value='")[1]
    certificado_captcha = certificado_captcha.split("'>")[0]

    #
    # Pega o link do captcha
    #
    link_captcha = pagina.split(u"<img border='0' id='imgcaptcha' alt='Imagem com os caracteres anti robô' src='")[1]
    link_captcha = 'http://www.receita.fazenda.gov.br' + link_captcha.split("'>")[0]
    link_captcha = link_captcha.replace('&amp;', '&')
    #print(link_captcha)

    cabecalho = {
        'Cookie': cookie,
        'Refererer': 'http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp'
    }

    req = urllib2.Request(link_captcha, headers=cabecalho, origin_req_host='www.receita.fazenda.gov.br')
    resp = urllib2.urlopen(req)
    #print(resp.info())
    imagem = base64.b64encode(resp.read())

    #arq = open('captcha.jpg', 'w')
    #arq.write(imagem)
    #arq.close()

    #print('Cookie', cookie)
    #print('Certificado captcha', certificado_captcha)

    dados = {
        'cookie': cookie,
        'certificado_captcha': certificado_captcha,
        'imagem': imagem,
    }

    #print(dados)

    return dados


def executa_consulta(cookie_receita=None, cnpj_consultar=None, certificado_captcha=None, texto_captcha=None):
    url = 'http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/valida.asp'

    cookie = cookie_receita
    cabecalho = {
        'Cookie': 'flag=1; ' + cookie,
        'Refererer': 'http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp'
    }

    cnpj = cnpj_consultar.replace('.', '').replace('/', '').replace('-', '').strip()
    idLetra = texto_captcha

    dados = {
        'origem': 'comprovante',
        'cnpj': cnpj,
        'captcha': idLetra,
        'captchaAudio': '',
        'viewstate': certificado_captcha,
        'submit1': 'Consultar',
        'search_type': 'cnpj',
    }

    retorno = {}

    try:
        req = urllib2.Request(url, data=urllib.urlencode(dados), headers=cabecalho)
        resp = urllib2.urlopen(req)
        texto = resp.read().decode('iso8859-1')


    #arq = open('resposta_cnpj.html', 'w')
    #arq.write(texto.encode('iso8859-1'))
    #arq.close()
    #print(texto)
    #resp.close()
    except (UnicodeDecodeError,):
        retorno['cnpj_nao_existe'] = True
        return retorno

    if 'Erro' in texto:
        retorno['erro_letras'] = True
        return retorno

    soup = BeautifulSoup(texto, fromEncoding='iso-8859-1')

    # Separa os campos
    retorno['cnpj']        = _separa_campo(soup,  4, 0, 0)
    retorno['matriz']      = _separa_campo(soup,  4, 0, 1)
    retorno['nome']        = _separa_campo(soup,  5, 0, 0)
    retorno['fantasia']    = _separa_campo(soup,  6, 0, 0)

    if u'*' in retorno['fantasia']:
        retorno['fantasia'] = retorno['nome']

    _separa_cnaes(soup, retorno)

    retorno['natureza']    = _separa_campo(soup,  9, 0, 0)
    retorno['endereco']    = _separa_campo(soup, 10, 0, 0)
    retorno['numero']      = _separa_campo(soup, 10, 2, 0)
    retorno['complemento'] = _separa_campo(soup, 10, 4, 0)
    retorno['cep']         = _separa_campo(soup, 11, 0, 0).replace(u'.', u'')
    retorno['bairro']      = _separa_campo(soup, 11, 2, 0)
    retorno['cidade']      = _separa_campo(soup, 11, 4, 0)
    retorno['estado']      = _separa_campo(soup, 11, 6, 0)
    #retorno[u'situacao']    = _separa_campo(soup, 12, 0, 0)
    #retorno[u'dt_situacao'] = _separa_campo(soup, 12, 2, 0)
    #retorno[u'mt_situacao'] = _separa_campo(soup, 12, 4, 0)

    return retorno
