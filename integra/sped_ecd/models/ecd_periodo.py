# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes, ano_que_vem
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
import base64
import os
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta


PERMITIR_LANCAMENTO = [
    ('1', u'Aberto'),
    ('2', u'Avisa'),
    ('3', u'Não Permitir'),
]

SITUACAO = [
    ('A', u'Aberto'),
    ('F', u'Fechado'),
]

class ecd_periodo(osv.Model):
    _description = u'Ecd Periodo Contábil'
    _name = 'ecd.periodo'
    _rec_name = 'nome'
    _order = 'data_inicial desc'

    _columns = {
        'nome': fields.char(u'Descrição', size=60),
        'company_id': fields.many2one('res.company',u'Empresas', ondelete='restrict'),
        'cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'Cnpj', store=True),        
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'), 
        'permitir_lancamento': fields.selection(PERMITIR_LANCAMENTO, u'Permitir Lançamento'),                   
        'situacao': fields.selection(SITUACAO, u'situação'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),                     
    }

    _defaults = {            
        'permitir_lancamento': '1',
        'situacao': 'A',    
    }
    
    def on_change_data_inicial(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        
        retorno = {}
        valores = {}
        retorno['value'] = valores
        
        sql = """
            select 
                data_final
            from
                ecd_periodo 
            where
                cnpj_cpf = '{cnpj_cpf}'
                
            order by
                cnpj_cpf,
                data_final desc
            limit 1
                
        """
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf)
        cr.execute(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'ATENÇÃO!', u'Não existe periodo contabíl no Cnpj selecionado!') 
                                             
        for data_anterior in dados:   
            data_inicial = parse_datetime(data_anterior[0]).date() + relativedelta(days=+1)                
            data_final = parse_datetime(data_anterior[0]).date() + relativedelta(years=+1)                
            valores['data_inicial'] = str(data_inicial)[:10]
            valores['data_final'] = str(data_final)[:10]
                                 
        return retorno
    
    def create(self, cr, uid, vals, context={}):    
        self.verifica_data_final(cr, uid, [], vals)               
        res = super(ecd_periodo, self).create(cr, uid, vals, context)
        
        return res

    def write(self, cr, uid, ids, vals, context={}):
        self.verifica_data_final(cr, uid, ids, vals)    
        res = super(ecd_periodo, self).write(cr, uid, ids, vals, context)

        return res
    
    def verifica_data_final(self, cr, uid, ids, vals, context=None):            
        
        if ids:
            id = ids[0]
            periodo_obj = self.browse(cr, uid, id)              
            company_id = periodo_obj.company_id.id
            data_inicial = periodo_obj.data_inicial
            data_final = periodo_obj.data_final
        else:
            company_id = vals.get('company_id')    
            data_inicial = vals.get('data_inicial')
            data_final = vals.get('data_final')
                    
        data_inicial = parse_datetime(data_inicial).date()
        data_final = parse_datetime(data_final).date()        
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        
        sql = """
            select 
                data_final
            from
                ecd_periodo 
            where
                cnpj_cpf = '{cnpj_cpf}' """
        if ids:
            sql +="""
                and id != """ + str(id)
                 
        sql +="""                 
            order by
                cnpj_cpf,
                data_final desc
            limit 1
                
        """
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf)
        cr.execute(sql)

        dados = cr.fetchall()                                                
        for data_anterior in dados:            
            data_anterior = parse_datetime(data_anterior[0]).date()
            
            if data_inicial <= data_anterior or  data_final <= data_anterior:
                raise osv.except_osv(u'Inválido!', u'Data inicial ou final devem ser maior que ' + formata_data(data_anterior) + u'!')
        
        sql = """
            select
                l.data
            from ecd_lancamento_contabil l
            where 
                l.data <= '{data_inicial}'
                and l.saldo_inicial = true
                and l.cnpj_cpf = '{cnpj_cpf}' """ 
        if ids:
            sql +="""
                and l.id != """ + str(id)
        sql +="""                 
            order by
                l.cnpj_cpf,
                l.data desc
            limit 1                
        """                 
        
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf,data_inicial=data_inicial)
        cr.execute(sql)
        dados = cr.fetchall()
        for data_anterior in dados:            
            data_anterior = parse_datetime(data_anterior[0]).date()
            raise osv.except_osv(u'Inválido!', u'Data Inicial Menor que a Data do Saldo Inicial: ' + formata_data(data_anterior) + u'!')                                      
                                 
        return True
    
ecd_periodo()


