#-*- coding:utf-8 -*-

from osv import fields, osv
from pybrasil.data import mes_passado
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date



MESES = (
    ('1', u'janeiro'),
    ('2', u'fevereiro'),
    ('3', u'março'),
    ('4', u'abril'),
    ('5', u'maio'),
    ('6', u'junho'),
    ('7', u'julho'),
    ('8', u'agosto'),
    ('9', u'setembro'),
    ('10', u'outubro'),
    ('11', u'novembro'),
    ('12', u'dezembro'),
)

MESES_DIC = dict(MESES)

def mes_atual():
    hoje = parse_datetime(fields.date.today())
    return hoje.year, hoje.month


def mes_seguinte():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=+1)
    return mes_passado.year, mes_passado.month


def mes_passado():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=-1)
    return mes_passado.year, mes_passado.month


def primeiro_ultimo_dia_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = primeiro_dia + relativedelta(months=+1, days=-1)
    return str(primeiro_dia)[:10], str(ultimo_dia)[:10]


class hr_turno_calendario(osv.Model):
    _name = 'hr.turno.calendario'
    _description = u'Turno Calendário'    
    _rec_name = 'nome'
    _order = 'mes desc, ano desc'
    
    def set_data_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente os lançamentos conciliados
        #
        
        if not isinstance(ids, list):
            ids = [ids]
            
        if len(valor_campo) and ids:
            
            for calendario_obj in self.browse(cr, uid, ids):
                for operacao, data_id, valores in valor_campo:
                    #
                    # Cada lanc_item tem o seguinte formato
                    # [operacao, id_original, valores_dos_campos]
                    #
                    # operacao pode ser:
                    # 0 - criar novo registro (no caso aqui, vai ser ignorado)
                    # 1 - alterar o registro
                    # 2 - excluir o registro (também vai ser ignorado)
                    # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
                    # 4 - vincular a um registro existente
                    #
                    if operacao == 1:
                        #
                        # Ajusta o banco e a data de crédito para a data do lançamento do saldo
                        
                        self.pool.get('hr.turno.calendario.data').write(cr, uid, [data_id], valores)
    
    
    def _get_datas(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}
        
        for obj in self.browse(cr, uid, ids):
            turno_id = obj.turno_id.id
            data_inicial, data_final = primeiro_ultimo_dia_mes(obj.ano, int(obj.mes))
            
            datas = self.pool.get('hr.turno.calendario.data').search(cr, uid, 
                                                                        [('data', '>=', data_inicial),
                                                                         ('data', '<=', data_final),
                                                                         ('turno_id','=', turno_id)])
            
            if len(datas):
                res[obj.id] = datas
            else:
                res[obj.id] = False
       
        return res
    
                  
    _columns = {               
        'turno_id': fields.many2one('hr.turno', u'Turno', ondelete='restrict'),        
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'partner_id': fields.related('turno_id','partner_id',  type='many2one', string=u'Cliente', relation='res.partner', store=True),            
        'jornada_id': fields.related('turno_id','jornada_id',  type='many2one', string=u'Jornanda de Trabalho', relation='hr.jornada', store=True),
        'department_id': fields.related('turno_id', 'department_id', type='many2one', string=u'Departamento', relation='hr.department', store=True),           
        'data_ids': fields.function(_get_datas, type='one2many', relation='hr.turno.calendario.data', method=True, string='Turno Calendário Data', fnct_inv=set_data_ids),
             
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
    }
    
    _sql_constraints = [
        ('turno_id_mes_ano_unique', 'unique(turno_id, mes, ano)',
            u'O turno, mes e o ano não podem se repetir!'),
    ]
    
    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')
        
        return retorno
    
    def busca_descricao(self, cr, uid, ids, turno_id, context={}):
        if not turno_id:
            return {}

        if not turno_id:
            return {}

        turno_pool = self.pool.get('hr.turno')
        turno_obj = turno_pool.browse(cr, uid, turno_id)

        retorno = {}
        valores = {}
        retorno['value'] = valores
        valores['partner_id'] = turno_obj.partner_id.id
        valores['jornada_id'] = turno_obj.jornada_id.id
        valores['department_id'] = turno_obj.department_id.id
        return retorno
        
    def monta_escala(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('hr.turno.calendario.data')
        
        for turno_obj in self.browse(cr, uid, ids):                    
                        
            data_inicial, data_final = primeiro_ultimo_dia_mes(turno_obj.ano, int(turno_obj.mes))

            dados = {
                'calendario_turno_id': turno_obj.id, 
                'turno_id': turno_obj.turno_id.id,                
            }
            
            data = parse_datetime(data_inicial).date()
            data_final = parse_datetime(data_final).date()
            turno_id = turno_obj.turno_id.id
                               
            while data <= data_final:
            
                dados['data'] = str(data)[:10]
                
                res = item_pool.search(cr, uid, [('data', '=', data),
                                                 ('turno_id','=', turno_id)])
                
                if not res:                    
                    item_pool.create(cr, uid, dados)

                data += relativedelta(days=+1)

            
        return


hr_turno_calendario()


class hr_turno_calendario_data(osv.Model):
    _name = 'hr.turno.calendario.data'
    _description = u'Turno Calendário Data'    
    
    _columns = {
        'calendario_turno_id': fields.many2one('hr.turno.calendario', u'Turno Calendário', ondelete='cascade'),
        'turno_id': fields.many2one('hr.turno', u'Turno'),
        'data': fields.date(u'Data'),
        'funcionario_trabalha_id': fields.many2one('hr.contract', u'Funcionário'),
        'funcionario_folga_id': fields.many2one('hr.contract', u'Funcionário Folga'),
        'funcionario_falta_id': fields.many2one('hr.contract', u'Funcionário Falta'),      
        'vr_hora': fields.float(u'Valor Hora'),                    
        'ocorrencia': fields.text(u'Ocorrência'),                    
        'rule_id': fields.many2one('hr.salary.rule', u'Justificativa da falta'),
    }

    _defaults = {
        'data': fields.date.today,
    }
    
    _sql_constraints = [
        ('data_turno_unique', 'unique(data, turno_id)',
            u'A Data e Turno não podem se repetir!'),
    ]

hr_turno_calendario_data()


class hr_fucionario_calendario(osv.Model):
    _name = 'hr.funcionario.calendario'
    _description = u'Funcionário Calendário'    
    _rec_name = 'ano, mes'
    _order = 'mes desc, ano desc'
    
    
    def set_data_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente os lançamentos conciliados
        #
        
        if not isinstance(ids, list):
            ids = [ids]
            
        if len(valor_campo) and ids:
            
            for calendario_obj in self.browse(cr, uid, ids):
                for operacao, data_id, valores in valor_campo:
                    #
                    # Cada lanc_item tem o seguinte formato
                    # [operacao, id_original, valores_dos_campos]
                    #
                    # operacao pode ser:
                    # 0 - criar novo registro (no caso aqui, vai ser ignorado)
                    # 1 - alterar o registro
                    # 2 - excluir o registro (também vai ser ignorado)
                    # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
                    # 4 - vincular a um registro existente
                    #
                    if operacao == 1:
                        #
                        # Ajusta o banco e a data de crédito para a data do lançamento do saldo
                        #
                                           
                        self.pool.get('hr.turno.calendario.data').write(cr, uid, [data_id], valores)

    def _get_datas(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}
        
        for obj in self.browse(cr, uid, ids):
            contract_id = obj.contract_id.id
            data_inicial, data_final = primeiro_ultimo_dia_mes(obj.ano, int(obj.mes))
            
            datas = self.pool.get('hr.turno.calendario.data').search(cr, uid, 
                                                                        [('data', '>=', data_inicial),
                                                                         ('data', '<=', data_final),
                                                                          '|', '|',
                                                                        ('funcionario_trabalha_id','=', contract_id),
                                                                        ('funcionario_folga_id','=', contract_id),                                                                        
                                                                        ('funcionario_falta_id','=', contract_id)]),
            
            if len(datas):
                res[obj.id] = datas[0]
            else:
                res[obj.id] = False
       
        return res

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'contract_id': fields.many2one('hr.contract', u'Funcionário', ondelete='restrict'),
        'unidade_salario': fields.related('contract_id', 'unidade_salario', type='char', string=u'Unidade do salário'),
        'data_ids': fields.function(_get_datas, type='one2many', relation='hr.turno.calendario.data', method=True, string='Turno Calendário Data', fnct_inv=set_data_ids),
        'turno_id': fields.many2one('hr.turno', u'Turno', ondelete='restrict'),        
        'partner_id': fields.related('turno_id','partner_id',  type='many2one', string=u'Cliente', relation='res.partner', store=True),            
        'jornada_id': fields.related('turno_id','jornada_id',  type='many2one', string=u'Jornanda de Trabalho', relation='hr.jornada', store=True),
        'department_id': fields.related('turno_id', 'department_id', type='many2one', string=u'Departamento', relation='hr.department', store=True),
        'trabalha_dia_1': fields.boolean(u'Trabalha no dia 1º?'),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'trabalha_dia_1': True,
    }
    
    _sql_constraints = [
        ('contract_id_mes_ano_unique', 'unique(contract_id, mes, ano)',
            u'O Funcionário, Mês e Ano não podem se repetir!'),
    ]
    
    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')
        
        return retorno
    
    def onchange_contract_id(self, cr, uid, ids, contract_id, context={}):
        if not contract_id:
            return {}
        
        contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)
        
        res = {
            'value': {
                'unidade_salario': contract_obj.unidade_salario,
            }
        }
            
        return res
    
    def monta_escala(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('hr.turno.calendario.data')
    
        for turno_obj in self.browse(cr, uid, ids):
            data_inicial, data_final = primeiro_ultimo_dia_mes(turno_obj.ano, int(turno_obj.mes))

            
            data = parse_datetime(data_inicial).date()
            data_final = parse_datetime(data_final).date()
            contract_id = turno_obj.contract_id.id
                               
            i = 1
            while data <= data_final:
                dados = {
                    'funcionario_trabalha_id': turno_obj.contract_id.id,
                    'turno_id': turno_obj.turno_id.id,
                    'data': str(data)[:10],
                }
                
                #
                # Jornada em escala
                #
                if turno_obj.contract_id.jornada_tipo != '1':
                    #
                    # Considera quantos dias tem o ciclo de cada escala
                    #
                    if turno_obj.contract_id.jornada_escala == '1':
                        #
                        # 12 × 36 = 12 + 36 = 24h = 2 dias (trabalha 12 horas, folga 36, totalizando 2 dias no ciclo)
                        # na escala, significa que ele trabalha dia sim, dia não
                        #
                        if turno_obj.trabalha_dia_1:
                            if i % 2 == 0:
                                dados = {
                                    'funcionario_folga_id': turno_obj.contract_id.id,
                                    'turno_id': turno_obj.turno_id.id,
                                    'data': str(data)[:10],
                                }
                            else:
                                dados = {
                                    'funcionario_trabalha_id': turno_obj.contract_id.id,
                                    'turno_id': turno_obj.turno_id.id,
                                    'data': str(data)[:10],
                                }
                        else:
                            if i % 2 == 0:
                                dados = {
                                    'funcionario_trabalha_id': turno_obj.contract_id.id,
                                    'turno_id': turno_obj.turno_id.id,
                                    'data': str(data)[:10],
                                }
                            else:
                                dados = {
                                    'funcionario_folga_id': turno_obj.contract_id.id,
                                    'turno_id': turno_obj.turno_id.id,
                                    'data': str(data)[:10],
                                }
                        
                    elif turno_obj.contract_id.jornada_escala == '2':
                        #
                        # 24 × 72 = 24 + 72 = 96h = 4 dias (trabalha 24 horas, folga 72, totalizando 4 dias no ciclo)
                        # na escala, significa que ele trabalha dia sim, 3 dias não
                        #
                        dias_ciclo = 4.0
                    elif turno_obj.contract_id.jornada_escala == '3':
                        #
                        # 6 × 18 = 6 + 18 = 24h = 1 dia (trabalha 6 horas, folga 18, totalizando 1 dia no ciclo)
                        # na escala, significa que ele trabalha todo dia
                        #
                        pass
                i += 1
                
                busca = [
                    ('data', '=', data),
                    '|', 
                    ('funcionario_trabalha_id','=', contract_id),
                    '|',                    
                    ('funcionario_folga_id','=', contract_id),                                                                        
                    ('funcionario_falta_id','=', contract_id)
                ]
                res = item_pool.search(cr, uid, busca)
                
                #
                # Não existe cadastro do funcionário
                #
                if not res:
                    #
                    # Vamos verificar se existe pelo menos cadastro para o turno
                    #
                    busca = [
                        ('data', '=', data),
                        ('turno_id', '=', turno_obj.turno_id.id),
                    ]
                    res = item_pool.search(cr, uid, busca)
                    
                    if not res:
                        item_pool.create(cr, uid, dados)
                    
                if res:    
                    item_obj = item_pool.browse(cr, uid, res[0])
                    
                    
                    if 'funcionario_trabalha_id' in dados:
                        if item_obj.funcionario_folga_id and item_obj.funcionario_folga_id.id == dados['funcionario_trabalha_id']:
                            dados['funcionario_folga_id'] = False
                        
                    elif 'funcionario_folga_id' in dados:
                        if item_obj.funcionario_trabalha_id and item_obj.funcionario_trabalha_id.id == dados['funcionario_folga_id']:
                            dados['funcionario_trabalha_id'] = False
                        
                    item_obj.write(dados)

                data += relativedelta(days=+1)
            
        return

    def busca_descricao(self, cr, uid, ids, turno_id, context={}):
        if not turno_id:
            return {}

        if not turno_id:
            return {}

        turno_pool = self.pool.get('hr.turno')
        turno_obj = turno_pool.browse(cr, uid, turno_id)

        retorno = {}
        valores = {}
        retorno['value'] = valores
        valores['partner_id'] = turno_obj.partner_id.id
        valores['jornada_id'] = turno_obj.jornada_id.id
        valores['department_id'] = turno_obj.department_id.id
        return retorno
    

hr_turno_calendario()
