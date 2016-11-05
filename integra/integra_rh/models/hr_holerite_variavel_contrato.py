#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date

from osv import fields, osv


MESES = (
    ('01', u'janeiro'),
    ('02', u'fevereiro'),
    ('03', u'março'),
    ('04', u'abril'),
    ('05', u'maio'),
    ('06', u'junho'),
    ('07', u'julho'),
    ('08', u'agosto'),
    ('09', u'setembro'),
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


class hr_holerite_variavel_contrato(osv.osv_memory):
    _name = 'hr.holerite_variavel_contrato'
    _description = u'Variáveis do holerite - contrato'
    _order = 'contract_id, data_inicial, data_final'
    _rec_name = 'contract_id'

    def _set_input_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente as entradas
        #
        if not isinstance(ids, list):
            if ids:
                ids = [ids]
            else:
                ids = []

        if len(valor_campo) and len(ids):
            for variavel_obj in self.browse(cr, uid, ids):
                for operacao, entrada_id, valores in valor_campo:
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
                        self.pool.get('hr.payslip.input').write(cr, uid, [entrada_id], valores)
                    elif operacao == 0:
                        self.pool.get('hr.payslip.input').create(cr, uid, valores)
                    elif operacao == 2:
                        entrada_obj = self.pool.get('hr.payslip.input').browse(cr, uid, entrada_id)
                        if not entrada_obj.payslip_id:
                            self.pool.get('hr.payslip.input').unlink(cr, uid, [entrada_id])

    def _get_input_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        
        for variavel_obj in self.browse(cr, uid, ids):
            variavel_obj = self.browse(cr, uid, ids[0])
            data_inicial = variavel_obj.data_inicial
            data_final = variavel_obj.data_final

            sql = """
                select
                        v.id
                        
                from
                    hr_payslip_input v
                    left join hr_payslip h on h.id = v.payslip_id
                    left join hr_contract c on c.id = v.contract_id
                    left join res_company cc on cc.id = c.company_id
                    
                where
                    ((
                        (h.id is null or (h.tipo != 'R' and coalesce(h.simulacao, False) = False))
                        and v.data_inicial >= '{data_inicial}' 
                        and v.data_final <= '{data_final}' 
                    )
                    or
                    (   h.id is not null and coalesce(h.simulacao, False) = False and h.tipo = 'R'
                        and h.data_afastamento between '{data_inicial}' and '{data_final}'
                    ))
            """
            filtro = {
                'data_inicial': variavel_obj.data_inicial,
                'data_final': variavel_obj.data_final,
            }
            
            if variavel_obj.contract_id:
                sql += """
                    and v.contract_id = {contract_id}
                """
                filtro['contract_id'] = variavel_obj.contract_id.id

            if variavel_obj.company_id:
                sql += """
                    and (cc.id = {company_id} or cc.parent_id = {company_id})
                """
                filtro['company_id'] = variavel_obj.company_id.id

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()
        
            input_ids = []
            
            for id, in dados:
                input_ids.append(id)

            res[variavel_obj.id] = input_ids
            
        return res

    _columns = {
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'input_ids': fields.function(_get_input_ids, method=True, type='one2many', string=u'Entradas variáveis', relation='hr.payslip.input', fnct_inv=_set_input_ids),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_atual()[0],
        'mes': lambda *args, **kwargs: str(mes_atual()[1]).zfill(2),
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[1],
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.payslip', context=c),
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

    def busca_entradas(self, cr, uid, ids, context={}):
        valores = {}
        retorno = {'value': valores}

        if 'ano' not in context or 'mes' not in context:
            return retorno

        ano = context['ano']
        mes = context['mes']

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        #valores['input_ids'] = self._get_input_ids(cr, uid, ids, 'input_ids', context=context)

        return retorno


hr_holerite_variavel_contrato()
