#!/env/python2
# -*- coding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals

from Crypto.Cipher import AES
import socket
from pkcs7 import PKCS7Encoder
from pybrasil.valor.decimal import Decimal as D
from pybrasil.inscricao import limpa_formatacao


class Moni(object):
    TIPO = (
        ('1', 'Residencial'),
        ('2', 'Comercial'),
        ('3', 'Industrial'),
        ('4', 'Patrimônio público'),
        ('5', 'Veraneio'),
        ('6', 'Condomínio'),
    )

    COMANDO = (
        ('0101', 'Cadastra (inclui/altera) cliente'),
        ('0102', 'Excluir cliente'),
        ('0103', 'Cancelar cliente'),
        ('0104', 'Ativar cliente'),
        ('0104', 'Ativar cliente'),
    )

    CHAVE_MONI = '\x9f\xb0\x11\xff\x40\x85\xb5\x93\xf7\x73\xff\x3a\x98\xd6\x3f\xdc'

    def __init__(self):
        #
        # Dados do cliente
        #
        self.contrato_id = ''
        self.cnpj_cpf = ''
        self.ie_rg = ''
        self.chave_moni = ''
        self.razao_social = ''
        self.fantasia = ''
        self.tipo = '1'
        self.endereco = ''
        self.numero = ''
        self.bairro = ''
        self.cep = ''
        self.contato = ''
        self.cidade = ''
        self.estado = ''
        self.fone = []
        self.cortesia = False
        self.valor = D(0)
        self.dia_vencimento = '5'
        self.periodo = '01'
        self.numero_contrato = ''
        #
        # Campos do Moni
        #
        self.moni_id = ''
        self.particao = ''
        self.codigo_cliente = ''
        self.codigo_empresa = ''
        self.empresa = ''

        #
        # Comando
        #
        self.comando = '0101'

        #
        # Para cancelamento
        #
        self.data_cancelamento = None
        self.motivo_cancelamento = ''

        #
        # Comunicação
        #
        self.host = '127.0.0.1'
        self.porta = 26151

    def _criptografa(self, mensagem):
        #
        # Cripografamos a mensagem
        #
        texto = PKCS7Encoder().encode(mensagem)
        #print(texto)
        cifra = AES.new(self.CHAVE_MONI)
        texto = cifra.encrypt(texto)
        return texto

    def _envio(self, cabecalho, texto):
        #
        # Dividimos a mensagens em partes de 256 caracteres
        #
        mensagens = [cabecalho, texto]
        print('tamanho', len(texto))
        while len(mensagens[-1]) > 256:
            m = mensagens[-1]
            mensagens[-1] = m[:256]
            mensagens.append(m[256:])

        print('m', len(mensagens))
        res = True

        #
        # Criamos a conexão a cada envio, fechando em seguida
        #
        conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexao.connect((self.host, self.porta))

        for m in mensagens:
            print(len(m), 'tamanho')
            conexao.send(m)
            dados = conexao.recv(1)

            print('dados', dados)
            if dados != '1':
                res = False
                break

        conexao.close()

        return res

    def cabecalho(self, mensagem):
        texto = self.comando
        texto += str(len(mensagem)).zfill(6)
        texto += 'IEAOUM'
        return texto

    def cadastra_cliente(self):
        #mensagem = str(self.contrato_id).ljust(20)
        mensagem = str(self.numero_contrato).ljust(20)
        mensagem += str(self.moni_id).ljust(10)
        mensagem += self.fantasia.ljust(100)[:100]
        mensagem += self.razao_social.ljust(100)[:100]
        mensagem += self.tipo.ljust(1)[0]
        mensagem += self.endereco.ljust(80)[:80]
        mensagem += self.numero.ljust(6)[:6]
        mensagem += self.bairro.ljust(30)[:30]
        mensagem += limpa_formatacao(self.cep).zfill(8)[:8]
        mensagem += self.contato.ljust(15)[:15]

        if len(self.cnpj_cpf) == 18:
            mensagem += ''.ljust(11)
            mensagem += ''.ljust(20)
            mensagem += limpa_formatacao(self.cnpj_cpf).zfill(14)[:14]
            mensagem += limpa_formatacao(self.ie_rg).ljust(25)[:25]

        else:
            mensagem += limpa_formatacao(self.cnpj_cpf).zfill(11)[:11]
            mensagem += limpa_formatacao(self.ie_rg).ljust(20)[:20]
            mensagem += ''.ljust(14)
            mensagem += ''.ljust(25)

        mensagem += self.cidade.ljust(40)[:40]
        mensagem += self.estado.ljust(2)[:2]

        if self.fone:
            mensagem += str(len(self.fone)).zfill(2)
            for fone in self.fone:
                mensagem += limpa_formatacao(fone.replace(')', '000').replace('(', '0')).zfill(14)[:14]

        else:
            mensagem += ''.zfill(16)

        mensagem += '1' if self.cortesia else '0'
        mensagem += str(int(self.valor * 100)).zfill(8)
        mensagem += str(self.dia_vencimento).zfill(2)[:2]
        mensagem += str(self.periodo).zfill(2)[:2]
        mensagem += self.codigo_cliente.zfill(4)[:4]
        mensagem += str(self.particao).zfill(2)[:2]
        mensagem += str(self.codigo_empresa).zfill(5)[:5]
        mensagem += self.empresa.ljust(60)[:60]
        #mensagem += str(self.numero_contrato).ljust(30)[:30]
        mensagem += str(self.contrato_id).ljust(30)[:30]
        mensagem += 'IEAOUM'

        cabecalho = self.cabecalho(mensagem)
        cabecalho = self._criptografa(cabecalho)

        mensagem = self._criptografa(mensagem)

        res = self._envio(cabecalho, mensagem)
        return res


if __name__ == '__main__':
    moni = Moni()

    #moni.cnpj_cpf = '02.544.208/0001-05'
    #moni.ie_rg = '123'
    moni.cnpj_cpf = '249.383.128-40'
    moni.ie_rg = 'rg teste'
    moni.fantasia = 'Integra 0341'
    moni.razao_social = 'Integra 0341'
    moni.contrato_id = 1
    moni.fone = ['(47) 3026-3527', '(47) 9655-4415']
    moni.endereco = 'Av. Juscelino Kubitschek'
    moni.numero = '410'
    moni.bairro = 'Centro'
    moni.cidade = 'Joinville'
    moni.estado = 'SC'
    moni.cep = '89520-365'
    moni.numero_contrato = '2016-0001'
    moni.valor = D('123.45')
    moni.contato = 'Ari'

    #
    # Campos para a Integração com o Moni
    #
    moni.moni_id = '341'
    moni.codigo_cliente = '4'
    moni.particao = '1'
    moni.codigo_empresa = '1'
    moni.empresa = 'PROTTEGE'
    moni.host = '191.34.76.227'

    print(moni.cadastra_cliente())

#teste = '\xba \x78 \xc9 \x24 \x36 \xd7 \x7e \x1a \x7c \x03 \x1c \x33 \xc5 \x1e \xb0 \x23 \x27\xc7\x93\xbc\x53\xea\x62\xde\x61\x03\x1f\xfc\xef\x66\xb1\x4d'
        #'\xba x    \xc9 $    6    \xd7 ~    \x1a |    \x03 \x1c 3    \xc5 \x1e \xb0 #
#print(cifra.decrypt(teste))
