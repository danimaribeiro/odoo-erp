# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
import base64
from pybrasil.sped.nfse import gera_recibo_locacao_pdf, gera_nfse_pdf
from sped.models.trata_nfse import monta_nfse
from datetime import datetime
from pybrasil.febraban.boleto import gera_boletos_pdf
from pybrasil.febraban.boleto.boleto_pdf import ImpressoBoleto
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
        lbl, fld = self.inclui_campo(nome='', titulo='', conteudo='boleto.endereco_cobranca', top=0 * cm, left=1 * cm, width=15 * cm, height=15 * cm)
        lbl.borders = False
        fld.borders = False

        self.height = 15 * cm


class ImpressoEndereco(Relato):
    def __init__(self, *args, **kwargs):
        super(ImpressoEndereco, self).__init__(*args, **kwargs)
        self.additional_fonts[FONTE_DEJAVU_SANS_MONO] = LISTA_FONTES_DEJAVU_SANS_MONO
        self.margin_bottom = 0.5 * cm

        self.band_detail = Enderecos()


class sped_nfse_pdf(osv.osv_memory):
    _description = u'Impressão de NFS-e'
    _name = 'sped.nfse_pdf'
    _inherit = 'sped.nfse_pdf'

    def _gerar_recibos_locacao(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        doc_ids = context['active_ids']
        doc_pool = self.pool.get('sped.documento')

        pdf_obj = self.browse(cr, uid, ids[0])
        if pdf_obj.somente_sem_email:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'RL'), ('emissao', '=', '0'), ('id', 'in', doc_ids), ('partner_id.email_nfe', '=', False)], order='numero')

        else:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'RL'), ('emissao', '=', '0'), ('id', 'in', doc_ids)], order='numero')

        if not doc_ids:
            return None

        sql = u'''
        select
          d.id, p.razao_social
        from sped_documento d
        join res_partner p on p.id = d.partner_id
        where d.id in ***
        order by p.name, p.razao_social, p.cnpj_cpf, d.numero;
        '''
        sql = sql.replace('***', str(doc_ids).replace('[', '(').replace(']', ')'))

        cr.execute(sql.replace('***', str(doc_ids).replace('[', '(').replace(']', ')')))
        doc_ids = cr.fetchall()

        lista_ids = []
        for doc_id, razao_social in doc_ids:
            lista_ids.append(doc_id)

        lista_notas = []
        for doc_obj in doc_pool.browse(cr, uid, lista_ids, context=context):
            nota = monta_nfse(self, cr, uid, doc_obj)

            if doc_obj.finan_lancamento_id:
                if doc_obj.finan_lancamento_id.carteira_id:
                    boleto = doc_obj.finan_lancamento_id.gerar_boleto(context={'evita_pdf': True})
                    print('boleto')
                    print(boleto)
                    nota.boleto = boleto
                #else:
                    #raise osv.except_osv(u'Erro!', u'O documento nº %s não tem vinculada uma carteira para a emissão dos boletos!!' % doc_obj.numero)


            elif doc_obj.duplicata_ids:
                dup_obj = doc_obj.duplicata_ids[0]

                if dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.carteira_id:
                    boleto = dup_obj.finan_lancamento_id.gerar_boleto(context={'evita_pdf': True})
                    nota.boleto = boleto

            lista_notas.append(nota)

        pdf = gera_recibo_locacao_pdf(lista_notas, arquivo_unico=True)

        return pdf

    def _gerar_notas(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        doc_ids = context['active_ids']
        doc_pool = self.pool.get('sped.documento')

        sql = u'''
        select
          d.id
        from sped_documento d
        join res_partner p on p.id = d.partner_id
        where d.id in ***
        order by p.name, p.razao_social, p.cnpj_cpf, d.numero;
        '''

        pdf_obj = self.browse(cr, uid, ids[0])
        if pdf_obj.somente_sem_email:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'SE'), ('emissao', '=', '0'), ('id', 'in', doc_ids), ('partner_id.email_nfe', '=', False)], order='numero')

        else:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', 'SE'), ('emissao', '=', '0'), ('id', 'in', doc_ids)], order='numero')

        if not doc_ids:
            return None

        cr.execute(sql.replace('***', str(doc_ids).replace('[', '(').replace(']', ')')))
        doc_ids = cr.fetchall()
        lista_ids = []
        for doc_id, in doc_ids:
            lista_ids.append(doc_id)

        lista_notas = []
        for doc_obj in doc_pool.browse(cr, uid, lista_ids, context=context):
            nota = monta_nfse(self, cr, uid, doc_obj)

            if doc_obj.finan_lancamento_id and doc_obj.finan_lancamento_id.carteira_id:
                boleto = doc_obj.finan_lancamento_id.gerar_boleto(context={'evita_pdf': True})
                nota.descricao = nota.descricao.replace('\n', ' | ')
                nota.boleto = boleto

            elif doc_obj.duplicata_ids:
                dup_obj = doc_obj.duplicata_ids[0]

                if dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.carteira_id:
                    boleto = dup_obj.finan_lancamento_id.gerar_boleto(context={'evita_pdf': True})
                    nota.boleto = boleto

            lista_notas.append(nota)

        pdf_notas = gera_nfse_pdf(lista_notas, arquivo_unico=True)
        pdf = pdf_notas

        #if com_endereco:
        #if hasattr(lista_notas[0], 'boleto') and hasattr(lista_notas[0].boleto, 'endereco_cobranca'):
        if cr.dbname.upper() == 'PATRIMONIAL':
            impresso_endereco = ImpressoEndereco()
            endereco_pdf = StringIO()

            impresso_endereco.queryset = lista_notas
            impresso_endereco.generate_by(PDFGenerator, filename=endereco_pdf)

            pdf_endereco = endereco_pdf.getvalue()
            endereco_pdf.close()

            pdf_unico = PdfFileWriter()

            #
            # Monta o PDF com as Notas
            #
            arq_pdf_boletos = StringIO()
            arq_pdf_boletos.write(pdf_notas)
            separa_paginas_boletos = PdfFileReader(arq_pdf_boletos)

            #
            # Monta o PDF com os endereços
            #
            arq_pdf_enderecos = StringIO()
            arq_pdf_enderecos.write(pdf_endereco)
            separa_paginas_enderecos = PdfFileReader(arq_pdf_enderecos)

            for i in range(separa_paginas_enderecos.numPages):
                pdf_unico.addPage(separa_paginas_boletos.getPage(i))
                print('tamanho da pagina do endereco')
                print(separa_paginas_enderecos.getPage(i).extractText())
                if len(separa_paginas_enderecos.getPage(i).extractText()) > 0:
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

        return pdf


sped_nfse_pdf()
