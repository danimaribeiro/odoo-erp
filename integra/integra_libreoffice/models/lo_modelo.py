# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
from pybrasil.base import tira_acentos
from StringIO import StringIO
from zipfile import ZipFile
import sh
import base64
import os
from campos_patrimonial import *
from mako.template import Template

from integra_libreoffice.py3o.template import Template as Template_Novo
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
import pybrasil


TABELAS = (
    ('hr.contract', u'RH - Contrato'),
    #('hr.employee', u'RH - Funcionário'),
    ('hr.payslip', u'RH - Pagamento/Rescisão/Férias/13º'),
    ('finan.contrato', u'Finan - Contratos'),
    ('sale.order', u'Vendas - Contratos'),
)

FORMATOS = (
    ('doc', u'Microsoft Word (.doc)'),
    ('odt', u'Open Document Text (.odt)'),
    ('pdf', u'PDF (.pdf)'),
)

AVISO_PREVIO = (
    ('T', u'Trabalhado'),
    ('I', u'Indenizado'),
    #('hr.employee', u'RH - Funcionário'),
    #('hr.payslip', u'RH - Pagamento/Rescisão/Férias/13º'),
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
        'formato': fields.selection(FORMATOS, u'Formato de saída'),
        'aviso_previo': fields.selection(AVISO_PREVIO, u'Aviso prévio'),
    }

    _defaults = {
        'formato': 'doc',
    }

    def _trata_nome_arquivo(self, dados):
        if 'nome_arquivo' in dados and dados['nome_arquivo']:
            nome_arquivo = tira_acentos(dados['nome_arquivo'].decode('utf-8'))
            nome_arquivo = nome_arquivo.lower()
            nome_arquivo = nome_arquivo.replace(u' ', u'_')
            dados['nome_arquivo'] = nome_arquivo

        return dados

    def _trata_arquivo(self, dados):
        if 'nome_arquivo' in dados and 'arquivo' in dados and dados['nome_arquivo'] and dados['arquivo']:
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

    def _aplica_template(self, cr, uid, ids, texto, novas_variaveis, dados):
        texto = texto.decode('utf-8')

        #
        # Ajusta os campos
        #
        texto = troca_campo(texto, novas_variaveis)

        #
        # Acresenta as tags de template do Mako
        #
        template_imports = [
            'import pybrasil',
            'import math',
            'from pybrasil.base import (tira_acentos, primeira_maiuscula, escape_xml)',
            'from pybrasil.data import (DIA_DA_SEMANA, DIA_DA_SEMANA_ABREVIADO, MES, MES_ABREVIADO, data_por_extenso, dia_da_semana_por_extenso, dia_da_semana_por_extenso_abreviado, mes_por_extenso, mes_por_extenso_abreviado, seculo, seculo_por_extenso, hora_por_extenso, hora_por_extenso_aproximada, formata_data, ParserInfoBrasil, parse_datetime, UTC, HB, fuso_horario_sistema, data_hora_horario_brasilia, agora, hoje, ontem, amanha, mes_passado, mes_que_vem, ano_passado, ano_que_vem, semana_passada, semana_que_vem, primeiro_dia_mes, ultimo_dia_mes, idade)',
            'from pybrasil.valor import (numero_por_extenso, numero_por_extenso_ordinal, numero_por_extenso_unidade, valor_por_extenso, valor_por_extenso_ordinal, valor_por_extenso_unidade, formata_valor)',
        ]
        template = Template(texto.encode('utf-8'), imports=template_imports, input_encoding='utf-8', output_encoding='utf-8', strict_undefined=True)
        texto = template.render(**dados)


        return texto

    def gera_modelo(self, cr, uid, ids, dados, formato='doc', novas_variaveis={}, context={}):
        modelo_obj = self.browse(cr, uid, ids[0])
        print('arquivo lido', modelo_obj.nome)

        if modelo_obj.formato:
            formato = modelo_obj.formato

        #
        # Abre o modelo ODT como arquivo ZIP
        #
        arq = StringIO()
        arq.write(base64.decodestring(modelo_obj.arquivo))
        arq.seek(0)
        z = ZipFile(arq, mode='r')

        #
        # Guarda o conteúdo de todos os arquivos no ODT
        #
        arquivos = {}
        for nome_arq in z.namelist():
            arquivos[nome_arq] = z.read(nome_arq)
        z.close()
        arq.close()

        print('vai renderizar', modelo_obj.nome)
        arquivos['content.xml'] = modelo_obj._aplica_template(arquivos['content.xml'], novas_variaveis, dados)
        arquivos['styles.xml'] = modelo_obj._aplica_template(arquivos['styles.xml'], novas_variaveis, dados)
        print('renderizacao concluida', modelo_obj.nome)

        #
        # Recria o zip com o novo conteúdo
        #
        arq = StringIO()
        z = ZipFile(arq, mode='w')
        for nome_arq in arquivos:
            z.writestr(nome_arq, arquivos[nome_arq])
        z.close()
        arq.seek(0)
        file('/tmp/novo.odt', 'w').write(arq.read())
        arq.close()

        #
        # Converte para doc
        #
        sh.libreoffice('--headless', '--invisible', '--convert-to', formato, '--outdir', '/tmp', '/tmp/novo.odt')

        #
        # Le o arquivo convertido
        #
        arq = file('/tmp/novo.' + formato, 'r').read()

        os.remove('/tmp/novo.odt')
        os.remove('/tmp/novo.' + formato)

        return base64.encodestring(arq)

    def gera_modelo_novo(self, cr, uid, ids, dados, formato='doc', novas_variaveis={}, context={}):
        modelo_obj = self.browse(cr, uid, ids[0])
        print('arquivo lido', modelo_obj.nome)

        if modelo_obj.formato:
            formato = modelo_obj.formato

        arq = StringIO()
        arq.write(base64.decodestring(modelo_obj.arquivo))

        t = Template_Novo(arq, '/tmp/novo.odt')
        t.render(dados)
        print(dados)

        sh.libreoffice('--headless', '--invisible', '--convert-to', formato, '--outdir', '/tmp', '/tmp/novo.odt')

        arq = file('/tmp/novo.' + formato, 'r').read()

        os.remove('/tmp/novo.odt')
        os.remove('/tmp/novo.' + formato)

        return base64.encodestring(arq)

    def gera_modelo_novo_avulso(self, cr, uid, nome_arquivo, dados, formato='xlsx', context={}):
        t = Template_Novo(nome_arquivo, '/tmp/novo.odt')
        t.render(dados)

        sh.libreoffice('--headless', '--invisible', '--convert-to', formato, '--outdir', '/tmp', '/tmp/novo.odt')

        arq = file('/tmp/novo.' + formato, 'r').read()

        os.remove('/tmp/novo.odt')
        os.remove('/tmp/novo.' + formato)

        return base64.encodestring(arq)


lo_modelo()
