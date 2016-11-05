# -*- coding: utf-8 -*-


from osv import fields, orm , osv
from integra_rh.constantes_rh import *
from pybrasil.data import agora
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    def imprime_recisao_patrimonial(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        rescisao_obj = self.browse(cr, uid, id)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_rescisao_contrato_trabalho.jrxml')
        recibo = 'termo_rescisao.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        #Imprime termo de Homologação

        relh = Report('Termo de Homologação de Rescisão', cr, uid)
        relh.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_homologacao_de_rescisao_de_contrato_de_trabalho_patrimonial.jrxml')
        reciboh = 'termo_homologacao_rescisao.pdf'

        relh.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        relh.parametros['USER_ID'] = int(uid)

        pdf, formato = relh.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', reciboh)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': reciboh,
            'datas_fname': reciboh,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        #Imprime termo de Quitação

        relq = Report('Termo de Homologação de Rescisão', cr, uid)
        relq.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'termo_de_quitacao_de_rescisao_de_contrato_de_trabalho_patrimonial.jrxml')
        reciboq = 'termo_quitacao_rescisao.pdf'

        relq.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        relq.parametros['USER_ID'] = int(uid)

        pdf, formato = relq.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', id), ('name', '=', reciboq)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': reciboq,
            'datas_fname': reciboq,
            'res_model': 'hr.payslip',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def imprime_recibo_pagamento(self, cr, uid, ids, context={}):
        context['exibe_ferias'] = 'S'
        return super(hr_payslip, self).imprime_recibo_pagamento(cr, uid, ids, context=context)


hr_payslip()

class hr_payslip_input(osv.Model):    
    _name = 'hr.payslip.input'
    _inherit = 'hr.payslip.input'
    
    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Metas Comerciais', ondelete='restrict')
    }
    


class hr_holerite(osv.osv_memory):
    _name = 'hr.holerite'
    _inherit = 'hr.holerite'

    def gera_holerites(self, cr, uid, ids, context={}):
        context['exibe_ferias'] = 'S'
        return super(hr_holerite, self).gera_holerites(cr, uid, ids, context=context)


hr_holerite()
