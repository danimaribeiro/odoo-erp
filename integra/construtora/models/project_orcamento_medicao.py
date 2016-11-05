# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
import os
import base64
from finan.wizard.finan_relatorio import Report
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class project_orcamento_medicao(osv.Model):
    _name = 'project.orcamento.medicao'
    _description = u'Projeto Medição'
    _rec_name = 'data'
    _order = 'id desc'

    _columns = {
        'orcamento_id': fields.many2one('project.orcamento', u'Orçamento', ondelete='restrict'),
        'data': fields.date(u'Data'),
        'etapa_id': fields.many2one('project.orcamento.etapa', u'Etapa'),
        'item_ids': fields.one2many('project.orcamento.medicao.item', 'medicao_id', u'Itens do Orçamento Medição'),               
    }

    _defaults = {
        'data': fields.datetime.now,
    }
    
    def buscar_itens(self, cr, uid, ids, context={}):       
        item_pool = self.pool.get('project.orcamento.medicao.item')
        
        medicao_obj = self.browse(cr, uid, ids[0])
        
        for item_obj in medicao_obj.item_ids:
            item_obj.unlink()
            
        orcamento_obj = medicao_obj.orcamento_id        
        
        for item_obj in orcamento_obj.item_ids:
            dados = {
                'medicao_id': medicao_obj.id,
                'orcamento_item_id': item_obj.id,
            }
            item_pool.create(cr, uid,dados )
        
        return True  
    
    def imprime_medicao(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report(u'Medição do Projeto', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_orcamento_projeto.jrxml')
        rel.parametros['ORCAMENTO_ID'] = id
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()
        nome_documento =  u'Medicao_Projeto.' + rel_obj.formato

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'project.orcamento.medicao'), ('res_id', '=', id), ('name', '=', nome_documento)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_documento,
            'datas_fname': nome_documento,
            'res_model': 'project.orcamento',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True  
  
project_orcamento_medicao()

class project_orcamento_medicao_item(osv.Model):    
    _name = 'project.orcamento.medicao.item'
    _description = u'Orçamento do Projeto Medição Item'
    _rec_name = 'orcamento_item_id'    
    
    def _get_planejada(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            
            soma = D('0')
            if item_obj.orcamento_item_id:
                orcamento_item_obj = item_obj.orcamento_item_id
                
                for planejamento_obj in orcamento_item_obj.planejamento_ids:
                    soma += planejamento_obj.quantidade

            soma = soma.quantize(D('0.01'))

            res[item_obj.id] = soma

        return res
    
    def _get_acumulada(self, cr, uid, ids, nome_campo, args, context={}):
        res = {}
        
        for item_obj in self.browse(cr, uid, ids):
            
            soma = D('0')
            
            sql = """
                select 
                coalesce(sum(pm.quantidade_medida),0) as quantidade
                
                from project_orcamento_medicao m
                join project_orcamento_medicao_item pm on pm.medicao_id = m.id
                where    
                pm.orcamento_item_id = {orcamento_item_id}                            
                and m.data <= '{data}';""" 
            
            sql = sql.format(data=item_obj.data,orcamento_item_id=item_obj.orcamento_item_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            for valor in dados:
                soma += valor[0]
      
            soma = soma.quantize(D('0.01'))

            res[item_obj.id] = soma

        return res
       
    _columns = {
        'medicao_id': fields.many2one('project.orcamento.medicao', u'Projeto Medição', ondelete='cascade'),
        'data': fields.related('medicao_id', 'data',  type='date', string=u'Data', store=True),
        'orcamento_item_id': fields.many2one('project.orcamento.item', u'Itens do Orçamento'),
        'codigo_completo': fields.related('orcamento_item_id','codigo_completo',  type='char', string=u'Código completo', store=True), 
        'uom_id': fields.related('orcamento_item_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', store=True),
        'etapa_id': fields.related('orcamento_item_id', 'etapa_id', type='many2one', relation='project.orcamento.etapa', string=u'Etapa', store=True),
        'quantidade': fields.related('orcamento_item_id','quantidade',  type='float', string=u'Quantidade', store=True),
        'quantidade_planejada': fields.function(_get_planejada, type='float', string=u'Quantidade Planejada', store=True, digits=(18, 2)),              
        'quantidade_medida': fields.float(u'Quantidade Medida'),              
        'percentual': fields.float(u'% Média'),                                
        'acumulada': fields.function(_get_acumulada, type='float', string=u'Acumulada', store=True, digits=(18, 2)),              
    }
    
    def onchange_quantidade_media(self, cr, uid, ids, quantidade, quantidade_medida=0, percentual=0, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        quantidade = D(quantidade or 0)
        quantidade_medida = D(quantidade_medida or 0)
        percentual = D(percentual or 0)

        if percentual:
            quantidade_medida = D(quantidade or 0) * percentual / D(100)          
            valores['quantidade_medida'] = quantidade_medida

        else: 
            percentual = quantidade_medida / D(quantidade or 0) * D(100)
            valores['percentual'] = percentual
            
        return res

project_orcamento_medicao_item()
