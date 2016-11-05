# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.base import tira_acentos
from StringIO import StringIO
from zipfile import ZipFile
import sh
import base64
import os


TABELAS = (
    ('hr.contract', u'RH - Contrato'),
    ('hr.employee', u'RH - Funcionário'),
    ('hr.payslip', u'RH - Pagamento/Rescisão/Férias/13º'),
    ('hr.payroll.structure', u'RH - Estrutura de Salário'),
)


class lo_modelo(orm.Model):
    _name = 'lo.modelo'
    _description = 'Modelo de impresso'
    _order = 'nome, tabela'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Nome', size=60, required=True, select=True),
        'nome_arquivo': fields.char(u'Nome do arquivo', size=255),
        'arquivo': fields.binary(u'Arquivo'),
        'tabela': fields.selection(TABELAS, u'Tabela'),
    }

    def _trata_nome_arquivo(self, dados):
        if 'nome_arquivo' in dados:
            nome_arquivo = tira_acentos(dados['nome_arquivo'].decode('utf-8'))
            nome_arquivo = nome_arquivo.lower()
            nome_arquivo = nome_arquivo.replace(u' ', u'_')
            dados['nome_arquivo'] = nome_arquivo

        return dados

    def _trata_arquivo(self, dados):
        if 'nome_arquivo' in dados and 'arquivo' in dados:
            nome_arquivo = dados['nome_arquivo']

            #
            # Caso o arquivo não seja no formato ODT, converter
            #
            if not nome_arquivo.endswith('.odt') and 'arquivo' in dados:
                extensao = nome_arquivo.split('.')[-1]

                #
                # Salva o arquivo no formato original
                #
                doc = file('/tmp/lo_modelo.' + extensao, 'w')
                doc.write(base64.decodestring(dados['arquivo']))
                doc.close()

                #
                # Converte para ODT
                #
                print(sh.libreoffice('--headless', '--invisible', '--convert-to', 'odt', '--outdir', '/tmp', '/tmp/lo_modelo.' + extensao))
                odt = file('/tmp/lo_modelo.odt', 'r')
                dados['arquivo'] = base64.encodestring(odt.read())
                odt.close()
                os.remove('/tmp/lo_modelo.' + extensao)
                os.remove('/tmp/lo_modelo.odt')
                nome_arquivo = nome_arquivo.replace('.' + extensao, '.odt')
                dados['nome_arquivo'] = nome_arquivo

        return dados

    def create(self, cr, uid, dados, context={}):
        dados = self._trata_nome_arquivo(dados)
        dados = self._trata_arquivo(dados)

        res = super(lo_modelo, self).create(cr, uid, dados, context=context)
        return res

    def write(self, cr, uid, ids, dados, context={}):
        dados = self._trata_nome_arquivo(dados)
        dados = self._trata_arquivo(dados)

        res = super(lo_modelo, self).write(cr, uid, ids, dados, context=context)
        return res


lo_modelo()
