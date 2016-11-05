# -*- coding: utf-8 -*-


from osv import fields, osv
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime, hoje, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D

TIPO_SINDICATO = [
    ('L',u'Laboral'),
    ('P', u'Patronal'),
]

TIPO_ENTIDADE = [
    ('S', u'Sindicato'),
    ('F', u'Federação'),
    ('C', u'Confedereção'),
    ('E', u'CEES'),
]

TIPO_ACORDO = [
    ('CC', u'Convensão coletiva'),
    ('DI', u'Dissidio'),
    ('AC', u'Acordo coletivo'),
    ('CCP', u'Comissão de conc.previa - CCP'),
]

MENSALISTA_HORISTA = [
    ('1', u'Mensalista'),
    ('2', u'Horista'),
]

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

def mes_passado():
    hoje = parse_datetime(fields.date.today())
    mes_passado = hoje + relativedelta(months=-1)
    return mes_passado.year, mes_passado.month


class hr_sindicato(osv.Model):
    _name = 'hr.sindicato'
    _description = u'Sindicatos'
    _rec_name = 'sigla'
    _order = 'ano, mes '

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Sindicato'),
        'sigla': fields.related('partner_id', 'name', type='char', string=u'Sigla'),
        'codigo_trct': fields.related('partner_id', 'codigo_sindical', type='char', string=u'Cod.TRCT'),
        'nome_trct': fields.related('partner_id', 'razao_social', type='char', string=u'Nome TRCT'),

        'tipo_sindicato': fields.selection(TIPO_SINDICATO, u'Tipo Sindicato'),
        'tipo_entidade': fields.selection(TIPO_ENTIDADE, u'Tipo Entidade'),
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês do dissídio', select=True),
        'cct_ids': fields.one2many('hr.sindicato.cct', 'sindicato_id', u'Conveçôes coletivas', ondelete='cascade'),
        'cargo_piso_ids': fields.one2many('hr.sindicato.piso.funcao', 'sindicato_id', u'Cargos e pisos', ondelete='cascade'),
        'rubrica_cargo_ids': fields.one2many('hr.sindicato.rubrica.cargo', 'sindicato_id', u'Rubrica fixas por cargo', ondelete='cascade'),
        'rubrica_faixa_ids': fields.one2many('hr.sindicato.rubrica.faixa.salarial', 'sindicato_id', u'Rubrica fixas por faixa salarial', ondelete='cascade'),
        'rubrica_anos_contrato_ids': fields.one2many('hr.sindicato.rubrica.anos.contrato', 'sindicato_id', u'Rubrica fixas por anos de contrato', ondelete='cascade'),
        'contribuicao_patronal_ids': fields.one2many('hr.sindicato.contribuicao.patronal', 'sindicato_id', u'Contribuição patronal sindical', ondelete='cascade'),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]).zfill(2),
        'tipo_sindicato': 'L',
        'tipo_entidade': 'S',
    }

    _sql_constraints = [
        ('partner_id_unique', 'unique(partner_id)',
            u'O Fornecedor não pode se repetir!'),
    ]

    def busca_sindicato(self, cr, uid, ids, partner_id, context={}):
        if not partner_id:
            return {}

        if not partner_id:
            return {}

        partner_pool = self.pool.get('res.partner')
        partner_obj = partner_pool.browse(cr, uid, partner_id)

        retorno = {}
        valores = {}
        retorno['value'] = valores
        valores['sigla'] = partner_obj.name
        valores['codigo_trct'] = partner_obj.codigo_sindical
        valores['nome_trct'] = partner_obj.razao_social
        return retorno



hr_sindicato()

class hr_sindicato_cct(osv.Model):
    _name = 'hr.sindicato.cct'
    _description = u'Convesão Coletiva'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'ano': fields.integer(u'Ano base', select=True),
        'data_acordo': fields.date(u'Data acordo'),
        'numero_processo': fields.char(u'Nº processo', size=30),
        'vara': fields.char(u'Vara', size=30),
        'tipo_acordo': fields.selection(TIPO_ACORDO, u'Tipo Acordo'),
    }

    _defaults = {
    'ano': lambda *args, **kwargs: mes_passado()[0],
    'data_acordo': fields.datetime.now(),
    'tipo_acordo': 'CC',
    }

hr_sindicato_cct()

class hr_sindicato_piso_funcao(osv.Model):
    _name = 'hr.sindicato.piso.funcao'
    _description = u'Cargos e Pisos'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'job_id': fields.many2one('hr.job', u'Cargo'),
        'data_inicio': fields.date(u'Data Inicio'),
        'carga_horaria_preferencial': fields.integer(u'Carga horaria preferencial'),
        'piso_salarial_mes': fields.float(u'Piso salarial mês'),
        'piso_salarial_hora': fields.float(u'Piso salarial hora'),
    }

    _defaults = {
        'data_inicio': fields.datetime.now(),
        'piso_salarial_hora': D('0'),
        'piso_salarial_mes': D('0'),
    }

hr_sindicato_piso_funcao()

class hr_sindicato_rubrica_cargo(osv.Model):
    _name = 'hr.sindicato.rubrica.cargo'
    _description = u'Rubricas Fixas por Cargo'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica', required=True),
        'job_id': fields.many2one('hr.job', u'Cargo'),
        'data_inicio': fields.date(u'Data Inicio'),
        'data_fim': fields.date(u'Data Fim'),
        'referencia_rule_id': fields.many2one('hr.salary.rule', u'Referencia', required=True),
        'quantidade': fields.float(u'Quantidade'),
        'porcentagem': fields.float(u'Porcentagem'),
        'valor': fields.float(u'Valor'),
    }

    _defaults = {
        'quantidade': 0,
        'porcentagem': 0,
        'valor': D('0'),
    }

hr_sindicato_rubrica_cargo()

class hr_sindicato_rubrica_faixa_salarial(osv.Model):
    _name = 'hr.sindicato.rubrica.faixa.salarial'
    _description = u'Rubricas Fixas por Faixa Salarial'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica', required=True),
        'mensalista_horista': fields.selection(MENSALISTA_HORISTA, u'Mensalista/horista', required=True),
        'salario_inicial': fields.float(u'Salário inicial'),
        'salario_final': fields.float(u'Salário final'),
        'data_inicio': fields.date(u'Data Inicio'),
        'data_fim': fields.date(u'Data Fim'),
        'referencia_rule_id': fields.many2one('hr.salary.rule', u'Referencia', required=True),
        'quantidade': fields.float(u'Quantidade'),
        'porcentagem': fields.float(u'Porcentagem'),
        'valor': fields.float(u'Valor'),
    }

    _defaults = {
        'mensalista_horista': '1',
        'salario_inicial': D('0'),
        'salario_final': D('0'),
        'quantidade': 0,
        'porcentagem': 0,
        'valor': D('0'),
    }

hr_sindicato_rubrica_faixa_salarial()

class hr_sindicato_rubrica_anos_contrato(osv.Model):
    _name = 'hr.sindicato.rubrica.anos.contrato'
    _description = u'Rubricas Fixas por Anos Contrato'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica', required=True),
        'ano': fields.integer(u'Ano', select=True),
        'data_inicio': fields.date(u'Data Inicio'),
        'data_fim': fields.date(u'Data Fim'),
        'referencia_rule_id': fields.many2one('hr.salary.rule', u'Referencia', required=True),
        'quantidade': fields.float(u'Quantidade'),
        'porcentagem': fields.float(u'Porcentagem'),
        'valor': fields.float(u'Valor'),
    }

    _defaults = {
        'quantidade': 0,
        'porcentagem': 0,
        'valor': D('0'),
        'ano': lambda *args, **kwargs: mes_passado()[0],
    }

hr_sindicato_rubrica_anos_contrato()

class hr_sindicato_contribuicao_patronal(osv.Model):
    _name = 'hr.sindicato.contribuicao.patronal'
    _description = u'Contribuição Patronal Sindical'

    _columns = {
        'sindicato_id': fields.many2one('hr.sindicato', u'Sindicato'),
        'classe_capital_social': fields.float(u'Classe capital social'),
        'aliquota': fields.float(u'Aliquota'),
        'parcela_adicional': fields.float(u'Parcela adcional'),
    }

    _defaults = {
        'classe_capital_social': D('0'),
        'aliquota': 0,
        'parcela_adicional': D('0'),
    }

hr_sindicato_contribuicao_patronal()
