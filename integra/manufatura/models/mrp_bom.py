# -*- coding: utf-8 -*-

import os
import base64
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data, agora
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from collections import OrderedDict

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class mrp_bom(osv.osv):
    _name = 'mrp.bom'
    _inherit = 'mrp.bom'    
    
    _columns = {
    }
    
    _defaults = {
    
    }
    
    def imprime_lista_materiais(self, cr, uid, ids, context={}):
        if not ids:
            return False

        total = D(0)
        linhas = []
        for produto_obj in self.browse(cr, uid, ids):
            
            for componentes_obj in produto_obj.bom_lines:       
                linha = DicionarioBrasil()
                linha['codigo'] = componentes_obj.product_id.default_code or ''
                linha['descricao'] = componentes_obj.product_id.name or ''                                    
                linha['unidade_medida'] = componentes_obj.product_id.uom_id.name
                linha['quantidade'] = formata_valor(componentes_obj.product_qty)                
                linha['vr_unitario'] = formata_valor(componentes_obj.product_id.standard_price)
                vr_total = D(componentes_obj.product_id.standard_price) * D(componentes_obj.product_qty)     
                linha['vr_total'] = formata_valor(vr_total)
                total += vr_total
                linhas.append(linha)
            
            dados = {
                'titulo': u'Ficha Técnica',
                'empresa': produto_obj.company_id.partner_id.name,
                'data': formata_data(agora()),
                'produto': produto_obj.name,
                'linhas': linhas,
                'total': formata_valor(total),
            }
    
            nome_arquivo = JASPER_BASE_DIR + 'mrp_listagem_materiais.ods'
    
            planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)
    
            nome_relatorio = u'Ficha_Tecnica_' + produto_obj.name + '.xlsx'
            
            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'mrp.bom'), ('res_id', '=', produto_obj.id), ('name', '=', nome_relatorio)])
            #
            # Apaga os recibos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': planilha,
                'name': nome_relatorio,
                'datas_fname': nome_relatorio,
                'res_model': 'mrp.bom',
                'res_id': produto_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

            
        return True
    
mrp_bom()

