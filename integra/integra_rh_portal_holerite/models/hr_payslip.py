# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from finan.wizard.finan_relatorio import Report
import os
import base64


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class hr_payslip(osv.Model):
    _inherit = 'hr.payslip'
    
    _columns = {
        'liberado_portal': fields.boolean(u'Liberado no portal?'),
    }

    def liberar_portal(self, cr, uid, ids, context={}):
        portal_pool = self.pool.get('hr.payslip.portal')
        users_pool = self.pool.get('res.users')
        
        for holerite_obj in self.browse(cr, uid, ids):
            if holerite_obj.liberado_portal:
                continue
            
            if holerite_obj.state != 'done':
                continue
            
            if holerite_obj.simulacao:
                continue
            
            if holerite_obj.provisao:
                continue

            jah_existe = portal_pool.search(cr, uid, [('payslip_id', '=', holerite_obj.id)])
            
            if len(jah_existe):
                continue
            
            dados = {
                'payslip_id': holerite_obj.id,
                'contract_id': holerite_obj.contract_id.id,
                'employee_id': holerite_obj.contract_id.employee_id.id,
                'cpf': holerite_obj.contract_id.employee_id.cpf,
                'descricao': holerite_obj.descricao,
                'nome_arquivo': holerite_obj.descricao.replace(' ', '_').strip() + '.pdf',
            }
            
            rel = Report('Recibo de Pagamento', cr, uid)

            if holerite_obj.contract_id.categoria_trabalhador in ["701", "702", "703"]:
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_rpa.jrxml')
            elif holerite_obj.tipo == 'N':
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_duas_vias.jrxml')
            elif holerite_obj.tipo == 'D':
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_pagamento_duas_vias.jrxml')
            elif holerite_obj.tipo == 'F':
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'recibo_ferias.jrxml')

            rel.parametros['REGISTRO_IDS'] = '(' + str(holerite_obj.id) + ')'

            pdf, formato = rel.execute()
            
            dados['arquivo'] = base64.encodestring(pdf)
            
            portal_pool.create(cr, uid, dados)
            users_pool.cria_usuario_compartilhamento_holerite(cr, uid, holerite_obj)


hr_payslip()
