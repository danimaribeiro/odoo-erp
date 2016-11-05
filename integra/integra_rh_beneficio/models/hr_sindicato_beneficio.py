# -*- coding: utf-8 -*-


from osv import fields, osv
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from pybrasil.data import parse_datetime, formata_data, ultimo_dia_mes



class hr_sindicato_beneficio(osv.Model):
    _name = 'hr.sindicato.beneficio'    
    _description = u'Beneficios por Sindicado'
   
    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'nome': fields.char(u'Nome', size=60),
        'data_inicial': fields.date(u'Data inicial', select=True),
        'data_final': fields.date(u'Data final', select=True),        
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'jobs_ids': fields.many2many('hr.job', 'sindicato_beneficio_job', 'sindicato_beneficio_id', 'job_id', string=u'Sindicato Benefícios Cargos'),        
        'item_ids': fields.one2many('hr.sindicato.beneficio.item', 'sindicato_beneficio_id', u''),
    }

    _defaults = {
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        #'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],    
    }
    
    def create(self, cr, uid, dados, context={}):
        print(dados)
        if 'sindicato_id' in dados:
            sindicato_id = dados['sindicato_id']
            beneficios_ids = self.search(cr, uid, args=[('sindicato_id','=', sindicato_id)])
            
            for beneficio_obj in self.browse(cr, uid, beneficios_ids):                
                if beneficio_obj.rule_id.id == dados['rule_id'] and not beneficio_obj.data_final:
                    raise osv.except_osv(u'Inválido!', u'Não há data final no benefício: ' + beneficio_obj.nome + u'!')
                 
                elif beneficio_obj.rule_id.id == dados['rule_id'] and dados['data_inicial'] <= beneficio_obj.data_final:
                    raise osv.except_osv(u'Inválido!', u'Data inicial menor que data final do Beneficio: ' + beneficio_obj.nome + u'!')
                    

        return super(hr_sindicato_beneficio, self).create(cr, uid, dados, context=context)
    
    def write(self, cr, uid, ids, dados, context={}):
        
        if 'rule_id' in dados:
            for beneficio_obj in self.browse(cr, uid, ids): 
                                  
                if beneficio_obj.rule_id.id == dados['rule_id'] and not beneficio_obj.data_final:
                    raise osv.except_osv(u'Inválido!', u'Não há data final no benefício: ' + beneficio_obj.nome + u'!')
                 
                elif beneficio_obj.rule_id.id == dados['rule_id'] and 'data_inicial' in dados:
                    if dados['data_inicial'] <= beneficio_obj.data_final:
                        raise osv.except_osv(u'Inválido!', u'Data inicial menor que data final do Beneficio: ' + beneficio_obj.nome + u'!')
         
        return super(hr_sindicato_beneficio, self).write(cr, uid, ids, dados, context=context)
    

hr_sindicato_beneficio()

class hr_sindicato_beneficio_item(osv.Model):
    _name = 'hr.sindicato.beneficio.item'    
    _description = u'Beneficios por Sindicado Itens'
    _order = 'salario_ate'
   
    _columns = {
        'sindicato_beneficio_id': fields.many2one('hr.sindicato.beneficio', u'Sindicato Benefício'),
        'salario_de': fields.float(u'Salario de'),
        'salario_ate': fields.float(u'Salario até'),
        'vr_fixo_mes': fields.float(u'Valor fixo mês'),
        'vr_fixo_dia_util': fields.float(u'Valor fixo dia útil'),
        'vr_percentual': fields.float(u'Percentual'),        
    }

    _defaults = {
              
    }
    
    
hr_sindicato_beneficio_item()