# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import fields, osv
import os
import base64
from pybrasil.sped.nfse import gera_nfse_pdf, gera_recibo_locacao_pdf
from ..models.trata_nfse import monta_nfse
from ..models.trata_nfe import monta_nfe
from StringIO import StringIO
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from pysped.nfe.processador_nfe import ProcessadorNFe


class sped_nfse_pdf(osv.osv_memory):
    _description = u'Impressão de NFS-e'
    _name = 'sped.nfse_pdf'
    #_inherit = 'ir.wizard.screen'
    _rec_name = 'nome'
    _order = 'nome'

    _columns = {
        'nome': fields.char(u'Nome do arquivo', 60, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'somente_sem_email': fields.boolean(u'Somente dos cliente que não têm email para envio automático?'),
    }

    _defaults = {
        'nome': '',
        'somente_sem_email': False,
    }

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
        order by p.razao_social, p.cnpj_cpf, d.numero;
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
            lista_notas.append(nota)

        pdf = gera_nfse_pdf(lista_notas, arquivo_unico=True)

        return pdf

    def _gerar_danfes(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        doc_ids = context['active_ids']
        doc_pool = self.pool.get('sped.documento')

        pdf_obj = self.browse(cr, uid, ids[0])
        if pdf_obj.somente_sem_email:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', '55'), ('emissao', '=', '0'), ('id', 'in', doc_ids), ('partner_id.email_nfe', '=', False)], order='numero')

        else:
            doc_ids = doc_pool.search(cr, uid, [('modelo', '=', '55'), ('emissao', '=', '0'), ('id', 'in', doc_ids)], order='numero')

        if not doc_ids:
            return []

        processador = ProcessadorNFe()
        processador.danfe.nome_sistema = 'Integra 6.2'

        lista_notas = []
        for doc_obj in doc_pool.browse(cr, uid, doc_ids, context=context):
            #
            # Caso a nota seja autorizada, buscar o DANFE nos anexos
            #
            if doc_obj.state in ['autorizada', 'denegada', 'cancelada']:
                lista_documentos_id = self.pool.get('ir.attachment').search(cr, 1, args=[
                    ('res_model', '=', 'sped.documento'),
                    ('res_id', '=', doc_obj.id),
                    ('name', '=', doc_obj.chave + '.pdf'),
                ])

                if lista_documentos_id:
                    doc_xml_obj = self.pool.get('ir.attachment').browse(cr, 1, lista_documentos_id[0])
                    pdf = base64.decodestring(doc_xml_obj.datas)
                    lista_notas.append(pdf)

            else:
                nota = monta_nfe(self, cr, uid, doc_obj)
                lista_notas.append(nota.pdf)

        return lista_notas

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
          d.id
        from sped_documento d
        join res_partner p on p.id = d.partner_id
        where d.id in ***
        order by p.razao_social, p.cnpj_cpf, d.numero;
        '''
        sql = sql.replace('***', str(doc_ids).replace('[', '(').replace(']', ')'))
        print(sql)
        cr.execute(sql.replace('***', str(doc_ids).replace('[', '(').replace(']', ')')))
        doc_ids = cr.fetchall()
        lista_ids = []
        for doc_id, in doc_ids:
            lista_ids.append(doc_id)

        lista_notas = []
        for doc_obj in doc_pool.browse(cr, uid, lista_ids, context=context):
            nota = monta_nfse(self, cr, uid, doc_obj)
            lista_notas.append(nota)

        pdf = gera_recibo_locacao_pdf(lista_notas, arquivo_unico=True)

        return pdf

    def gerar_pdf_documentos(self, cr, uid, ids, context={}):
        pdf_nfe = self._gerar_danfes(cr, uid, ids, context=context)
        pdf_nfse = self._gerar_notas(cr, uid, ids, context=context)
        pdf_recibo = self._gerar_recibos_locacao(cr, uid, ids, context=context)

        #pdf_unico = PdfFileWriter()
        pdf_unico = PdfFileMerger()

        #
        # Monta o PDF com os DANFEs
        #
        for danfe in pdf_nfe:
            arq_pdf_danfes = StringIO()
            arq_pdf_danfes.write(danfe)
            pdf_unico.append(PdfFileReader(arq_pdf_danfes))
            #separa_paginas = PdfFileReader(arq_pdf_danfes)
            #for i in range(separa_paginas.numPages):
                #pdf_unico.addPage(separa_paginas.getPage(i))
            arq_pdf_danfes.close()

        #
        # Monta o PDF com as Notas
        #
        if pdf_nfse is not None:
            arq_pdf_notas = StringIO()
            arq_pdf_notas.write(pdf_nfse)
            pdf_unico.append(PdfFileReader(arq_pdf_notas))
            #separa_paginas = PdfFileReader(arq_pdf_notas)
            #for i in range(separa_paginas.numPages):
                #pdf_unico.addPage(separa_paginas.getPage(i))
            arq_pdf_notas.close()

        #
        # Monta o PDF com os recibos
        #
        if pdf_recibo is not None:
            arq_pdf_recibos = StringIO()
            arq_pdf_recibos.write(pdf_recibo)
            pdf_unico.append(PdfFileReader(arq_pdf_recibos))
            #separa_paginas = PdfFileReader(arq_pdf_recibos)
            #for i in range(separa_paginas.numPages):
                #pdf_unico.addPage(separa_paginas.getPage(i))
            arq_pdf_recibos.close()

        #
        # Gera 1 PDF com tudo junto
        #
        arq_pdf = StringIO()
        pdf_unico.write(arq_pdf)
        arq_pdf.seek(0)
        pdf = arq_pdf.read()
        arq_pdf.close()

        self.write(cr, uid, ids, {'nome': 'notas_recibos.pdf', 'arquivo': base64.encodestring(pdf)})


sped_nfse_pdf()
