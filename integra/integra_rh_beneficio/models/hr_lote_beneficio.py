# -*- coding: utf-8 -*-


from osv import fields, osv
#from pybrasil.data import parse_datetime
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from integra_rh.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, formata_data, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import *
import base64


class hr_lote_beneficio(osv.Model):
    _name = 'hr.lote.beneficio'
    _description = u'Lotes de Benefícios'
    _rec_name = 'company_id'
    _order = 'ano desc, mes desc, company_id'

    def get_contract_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        contrato_pool = self.pool.get('hr.contract')

        for lote_holerite_obj in self.browse(cr, uid, ids):
            dados = {
                'data_inicial': lote_holerite_obj.data_inicial,
                'data_final': lote_holerite_obj.data_final,
                'company_id': lote_holerite_obj.company_id.id,                
                'categoria_trabalhador': "''",                
            }            
            
            #
            # Elimina do lote os pro-labore ('722') e RPA ('701','702','703')
            #
            dados['categoria_trabalhador'] = "'722','701','702','703'"

            sql = """
                select distinct 
                    c.id,
                    ee.nome

                from
                    hr_contract c
                    join res_company e on e.id = c.company_id
                    join hr_employee ee on ee.id = c.employee_id
                    join hr_contract_linha_transporte t on t.contract_id = c.id

                where
                    c.date_start <= '{data_final}' and
                    (c.date_end is null or c.date_end > '{data_final}')
                    and (e.id = {company_id} or e.parent_id = {company_id})
                    and c.categoria_trabalhador not in ({categoria_trabalhador})                    
            """
            
            if lote_holerite_obj.contract_id:
                sql += """
                    and c.id = {contract_id}
                """.format(contract_id=lote_holerite_obj.contract_id.id)
            

            sql += """
                order by
                    ee.nome;
            """

            sql = sql.format(**dados)
            
            cr.execute(sql)
            contrato_ids_lista = cr.fetchall()
            contrato_ids = []
            for dados in contrato_ids_lista:
                contrato_ids.append(dados[0])
            
            res[lote_holerite_obj.id] = contrato_ids

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Unidade/Empresa', select=True),
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'data_inicial': fields.date(u'Data inicial', select=True),
        'data_final': fields.date(u'Data final', select=True),
        'contract_id': fields.many2one('hr.contract', u'Contrato', select=True),
        'tipo': fields.selection([['VT', u'Vale Transporte'], ['VA', u'Vale Alimentação'], ['VR', u'Vale Refeição']], u'Tipo', select=True),
        
        'contract_ids': fields.function(get_contract_ids, type='one2many', relation='hr.contract', method=True, string=u'Contratos a gerar'),
        
        'beneficio_linha_ids': fields.one2many('hr.lote.beneficio.linha', 'lote_id', u'Vale transporte a gerar'),
        
        'variavel_ids': fields.one2many('hr.lote.beneficio.varivel', 'lote_id', u'Vale transporte gerado'),
        
        #'payslip_ids': fields.function(get_payslip_ids, type='one2many', relation='hr.payslip', method=True, string=u'Holerites gerados'),

        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],
        'tipo': 'VT',        
    }

    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        return retorno
    
    
    def create(self, cr, uid, dados, context={}):    
        data_inicial = dados['data_inicial']
        data_final = dados['data_final']
        
        if data_inicial[5:7] != data_final[5:7]:        
            raise osv.except_osv(u'Inválido !', u'Datas devem estar no mesmo mês!')                    

        return super(hr_lote_beneficio, self).create(cr, uid, dados, context=context)
    
    def write(self, cr, uid, ids, dados, context={}):
        
        if 'data_inicial' in dados and 'data_final' in dados:            
                if dados['data_inicial'][5:7] != dados['data_final'][5:7]:
                    raise osv.except_osv(u'Inválido !', u'Datas devem estar no mesmo mês!')                    
                            
        if 'data_inicial' in dados:            
            for lote_obj in self.browse(cr, uid, ids):
                if dados['data_inicial'][5:7] != lote_obj.data_final[5:7]:
                    raise osv.except_osv(u'Inválido !', u'Datas devem estar no mesmo mês!')                    
                                            
        if 'data_final' in dados:
            for lote_obj in self.browse(cr, uid, ids):                 
                if lote_obj.data_inicial[5:7] != dados['data_final'][5:7]:        
                    raise osv.except_osv(u'Inválido !', u'Datas devem estar no mesmo mês!')                    
               
        return super(hr_lote_beneficio, self).write(cr, uid, ids, dados, context=context)

    def atualizar_dados(self, cr, uid, ids, context={}):
        lote_id = ids[0]

        lote_obj = self.browse(cr, uid, lote_id)

        if lote_obj.tipo == 'VT':
            
            cr.execute('delete from hr_lote_beneficio_linha where lote_id = {id}'.format(id=lote_obj.id)) 
                        
            for contract_obj in lote_obj.contract_ids:
                linha_pool = self.pool.get('hr.lote.beneficio.linha')
                
                dias_uteis = contract_obj.dias_uteis(lote_obj.data_inicial, lote_obj.data_final)
                
                for linha_obj in contract_obj.linha_transporte_ids:
                    total_vale = linha_obj.vr_total * dias_uteis
                    
                    dados = {
                        'lote_id': lote_obj.id,
                        'contract_id': contract_obj.id,
                        'linha_id': linha_obj.linha_id.id,
                        'vr_unitario_dia': linha_obj.vr_unitario,
                        'quantidade_dia': linha_obj.quantidade,
                        'vr_dia': linha_obj.vr_total,
                        'dias_uteis': str(dias_uteis),
                        'vr_total':total_vale 
                    }                    
                    
                    linha_pool.create(cr, uid, dados)
                    
        return 

    def gerar_vale(self, cr, uid, ids, context={}):
        lote_vale_id = ids[0]
        lote_vale_obj = self.browse(cr, uid, lote_vale_id)

        res = {}
        valores = {}
        res['value'] = valores
        
        cr.execute('delete from hr_lote_beneficio_varivel where lote_id = {id}'.format(id=lote_vale_obj.id))

        if lote_vale_obj.tipo == 'VT':
            valores = self._gera_vale_transporte(cr, uid, ids, lote_vale_obj, context)
       
        return res
    
    def _gera_vale_transporte(self, cr, uid, ids, lote_vale_obj, context={}):
        contract_pool = self.pool.get('hr.contract')
        sindicato_pool = self.pool.get('hr.sindicato')
        variavel_pool = self.pool.get('hr.lote.beneficio.varivel')
        
        sql = """
            select 
                lote_id,
                contract_id, 
                lt.rule_id as rubrica_id,               
                dias_uteis,
                sum(lb.vr_total) as vr_total                
                
            from hr_lote_beneficio_linha lb
            join hr_linha_transporte lt on lt.id = lb.linha_id
            
            where 
            
            lb.lote_id = {lote_id}
                
            group by 
                lote_id,
                lb.contract_id,
                lt.rule_id,
                dias_uteis

            """
        
        sql = sql.format(lote_id=lote_vale_obj.id)            
        cr.execute(sql)
        dados = cr.fetchall()
        
        if not dados:
            raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

        for lote_id, contract_id, rubrica_id, dias_uteis, vr_total in dados:
            
            contract_obj = contract_pool.browse(cr, uid, contract_id)      
                                    
            sindicato_id = sindicato_pool.search(cr, uid, args=[('partner_id','=', contract_obj.sindicato_id.id)], limit=1)
                        
            if not sindicato_id:
                raise osv.except_osv(u'Erro!', u'Este Sindicato não está cadastrado!')
            
            sindicato_obj = sindicato_pool.browse(cr, uid, sindicato_id[0])
                    
            if not sindicato_obj.beneficio_ids:
                raise osv.except_osv(u'Erro!', u'Não existe benefécios ao funcionário: ' + contract_obj.employee_id.nome + u', vinculado ao sindicato: ' + sindicato_obj.partner_id.name +  u' f!')
            
            regra_beneficio_obj = None
            for beneficio_obj in sindicato_obj.beneficio_ids:
                
                if beneficio_obj.rule_id.id == rubrica_id:  
                    if not beneficio_obj.data_final:
                        regra_beneficio_obj = beneficio_obj 
                        break
                    elif lote_vale_obj.data_final <= beneficio_obj.data_final:
                        regra_beneficio_obj = beneficio_obj 
                        break
            
            if regra_beneficio_obj is None:            
                raise osv.except_osv(u'Erro!', u'Não existe benefécios ao funcionário: ' + contract_obj.employee_id.nome + u', vinculado ao sindicato: ' + sindicato_obj.partner_id.name +  u' f!')
            
            regra_item_obj = None            
                   
            for item_obj in regra_beneficio_obj.item_ids:
                
                if contract_obj.wage >= item_obj.salario_de and contract_obj.wage <= item_obj.salario_ate:
                    regra_item_obj = item_obj
                    break                
            
            if regra_item_obj is None:            
                raise osv.except_osv(u'Erro!', u'Não existe benefécios ao funcionário: ' + contract_obj.employee_id.nome + u', vinculado ao sindicato: ' + sindicato_obj.partner_id.name +  u' f!')
            
            dias_saldo_salario = 30 - int(lote_vale_obj.data_inicial[8:10]) + 1
            salario = D(contract_obj.wage) * dias_saldo_salario / D(30)
            
            if regra_item_obj.vr_fixo_mes:
                valor_desc = regra_item_obj.vr_fixo_mes
                
            elif regra_item_obj.vr_fixo_dia_util:
                valor_desc = D(regra_item_obj.vr_fixo_dia_util) * dias_uteis
                
            else:      
                valor_desc = D(regra_item_obj.vr_percentual) * salario / 100   
                
            dados = {
                'lote_id': lote_id,
                'contract_id': contract_id,
                'sindicato_id': sindicato_obj.id, 
                'ano': lote_vale_obj.ano,
                'mes': lote_vale_obj.mes,
                'data_inicial': lote_vale_obj.data_inicial,
                'data_final':  lote_vale_obj.data_final,                  
                'salario_contratual': contract_obj.wage,
                'salario': salario,
                'dias_saldo_salario': dias_saldo_salario,                
                'vr_fixo_mes': regra_item_obj.vr_fixo_mes,
                'vr_fixo_dia_util': D(regra_item_obj.vr_fixo_dia_util), 
                'vr_percentual': D(regra_item_obj.vr_percentual),       
                'vr_total': vr_total,
                'vr_descontado':  valor_desc,                                                           
            }
            variavel_pool.create(cr, uid, dados)   
            

hr_lote_beneficio()

class hr_lote_beneficio_linha(osv.Model):
    _name = 'hr.lote.beneficio.linha'
    _description = u'Lotes de Benefícios Linhas'
    _rec_name = 'lote_id'
    _order = 'lote_id'
    
    _columns = {
        'lote_id': fields.many2one('hr.lote.beneficio', u'Lote Beneficio', ondelete='cascade'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'linha_id': fields.many2one('hr.linha.transporte', u'Linha de transporte'),
        'vr_unitario_dia': fields.float(u'Valor unit. VT'),
        'quantidade_dia': fields.float(u'Quantidade VT'),
        'vr_dia': fields.float(u'Valor por dia'),
        'dias_uteis': fields.integer(u'Dias úteis'),
        'vr_total': fields.float(u'Valor total'),
    }    
           
hr_lote_beneficio_linha()


class hr_lote_beneficio_variavel(osv.Model):
    _name = 'hr.lote.beneficio.varivel'
    _description = u'Lotes de Benefícios Variáveis'
    _rec_name = 'lote_id'
    _order = 'lote_id'
    
    _columns = {
        'lote_id': fields.many2one('hr.lote.beneficio', u'Lote Beneficio', ondelete='cascade'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'data_inicial': fields.date(u'Data inicial', select=True),
        'data_final': fields.date(u'Data final', select=True),  
        'salario_contratual': fields.float(u'Salário contratual'),
        'salario': fields.float(u'Salário'),
        'dias_saldo_salario': fields.float(u'Dias saldo salário'),
        'vr_fixo_mes': fields.float(u'Valor fixo mês'),
        'vr_fixo_dia_util': fields.float(u'Valor fixo dia útil'),
        'vr_percentual': fields.float(u'Percentual'),              
        'vr_total': fields.float(u'Valor total'),
        'vr_descontado': fields.float(u'Valor descontado'),        
        'input_id': fields.many2one('hr.payslip.input', u'Pay slip input'),
    }    
           
hr_lote_beneficio_variavel()

