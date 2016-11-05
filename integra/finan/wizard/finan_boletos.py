# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
import base64
from pybrasil.febraban.boleto import gera_boletos_pdf
from pybrasil.febraban.boleto.boleto_pdf import ImpressoBoleto, ImpressoBoletoCarne
from pybrasil.base import Relato, BandaRelato, cm, mm
from pybrasil.base.relato.estilo import *
from pybrasil.base.relato.relato import LabelMargemEsquerda, LabelMargemDireita, Titulo, Campo, Texto, Descritivo
from pybrasil.base.relato.registra_fontes import *
from StringIO import StringIO
from geraldo.generators import PDFGenerator
from PyPDF2 import PdfFileWriter, PdfFileReader


class Enderecos(BandaRelato):
    def __init__(self, *args, **kwargs):
        super(Enderecos, self).__init__(*args, **kwargs)
        self.elements = []

        #
        # 1ª linha
        #
        lbl, fld = self.inclui_campo(nome='', titulo='', conteudo='endereco_cobranca', top=0 * cm, left=1 * cm, width=15 * cm, height=15 * cm)
        lbl.borders = False
        fld.borders = False

        self.height = 15 * cm


class ImpressoEndereco(Relato):
    def __init__(self, *args, **kwargs):
        super(ImpressoEndereco, self).__init__(*args, **kwargs)
        self.additional_fonts[FONTE_DEJAVU_SANS_MONO] = LISTA_FONTES_DEJAVU_SANS_MONO
        self.margin_bottom = 0.5 * cm

        self.band_detail = Enderecos()


class finan_boletos(osv.osv_memory):
    _description = u'Boletos de lançamentos'
    _name = 'finan.boletos'
    _inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'carteira_id': fields.many2one('finan.carteira', u'Carteira'),
        'data': fields.datetime(u'Data'),
        'com_endereco': fields.boolean(u'Com endereço de cobrança?'),
        'atualiza_valor': fields.boolean(u'Com valor atualizado?'),
        'taxa_boleto': fields.boolean(u'Com taxa de boleto?'),
        'enviar_email': fields.boolean(u'Enviar boleto por email?'),
        'carne': fields.boolean(u'Em formato de carnê?'),
    }

    _defaults = {
        'nome': lambda *a: 'boletos.pdf',
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'com_endereco': False,
        'atualiza_valor': False,
        'taxa_boleto': False,
        'enviar_email': False,
    }

    def gerar_boletos(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        carteira_id = context['carteira_id']
        data = context['data']
        com_endereco = context['com_endereco']
        atualiza_valor = context['atualiza_valor']
        boleto_valor_saldo = context.get('boleto_valor_saldo', False)
        taxa_boleto = context.get('taxa_boleto', False)
        enviar_email = context.get('enviar_email', False)
        carne = context.get('carne', False)

        #if not carteira_id:
            #osv.except_osv(u'Atenção', u'É preciso escolher uma carteira!')

        lancamento_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')

        #
        # Fazemos uma pré-validação das informações
        #
        if carteira_id:
            carteira_obj = self.pool.get('finan.carteira').browse(cr, uid, carteira_id)

        #
        # Ordenamos o boleto pelo número das notas, quando houver
        #
        sql = """
          select
          l.id
          from finan_lancamento l
          join res_partner p on p.id = l.partner_id
          left join sped_documento d on d.id = l.sped_documento_id
          where l.id in {lancamento_ids}
          order by
          p.razao_social, p.cnpj_cpf, d.numero, l.nosso_numero;
        """
          #d.numero, l.nosso_numero;

        sql = sql.format(lancamento_ids=str(tuple(lancamento_ids))).replace(',)', ')')
        cr.execute(sql)
        dados = cr.fetchall()
        lancamento_ids = []
        for id, in dados:
            lancamento_ids.append(id)

        lista_boletos = []
        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context):
            #if lancamento_obj.carteira_id and (lancamento_obj.carteira_id.id != carteira_obj.id):
                #raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de outra carteira! Documento nº ' + lancamento_obj.numero_documento)

            if (not lancamento_obj.carteira_id) and carteira_id:
                lancamento_obj.write({'carteira_id': carteira_obj.id})

            if enviar_email:
                lista_boletos.append(lancamento_obj.gerar_boleto(context={'atualizar': atualiza_valor, 'boleto_valor_saldo': boleto_valor_saldo, 'data': data, 'taxa_boleto': taxa_boleto}))
                lancamento_obj.enviar_email_boleto()
            else:
                lista_boletos.append(lancamento_obj.gerar_boleto(context={'atualizar': atualiza_valor, 'boleto_valor_saldo': boleto_valor_saldo, 'data': data, 'evita_pdf': True,'taxa_boleto': taxa_boleto}))

        if carne:
            pdf_boletos = gera_boletos_pdf(lista_boletos, classe_leiaute=ImpressoBoletoCarne)
        else:
            pdf_boletos = gera_boletos_pdf(lista_boletos)

        pdf = pdf_boletos

        if com_endereco:
            impresso_endereco = ImpressoEndereco()
            endereco_pdf = StringIO()

            impresso_endereco.queryset = lista_boletos
            impresso_endereco.generate_by(PDFGenerator, filename=endereco_pdf)

            pdf_endereco = endereco_pdf.getvalue()
            endereco_pdf.close()

            pdf_unico = PdfFileWriter()

            #
            # Monta o PDF com as Notas
            #
            arq_pdf_boletos = StringIO()
            arq_pdf_boletos.write(pdf_boletos)
            separa_paginas_boletos = PdfFileReader(arq_pdf_boletos)

            #
            # Monta o PDF com os endereços
            #
            arq_pdf_enderecos = StringIO()
            arq_pdf_enderecos.write(pdf_endereco)
            separa_paginas_enderecos = PdfFileReader(arq_pdf_enderecos)

            for i in range(separa_paginas_enderecos.numPages):
                pdf_unico.addPage(separa_paginas_boletos.getPage(i))
                pdf_unico.addPage(separa_paginas_enderecos.getPage(i))

            #
            # Gera 1 PDF com tudo junto
            #
            arq_pdf = StringIO()
            pdf_unico.write(arq_pdf)
            arq_pdf.seek(0)
            pdf = arq_pdf.read()

            arq_pdf_boletos.close()
            arq_pdf_enderecos.close()
            arq_pdf.close()

        if carteira_id:
            nome = 'boletos_' + carteira_obj.res_partner_bank_id.bank_name + '_' + str(data) + '.pdf'
        else:
            nome = 'boletos_' + str(data) + '.pdf'


        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


finan_boletos()
