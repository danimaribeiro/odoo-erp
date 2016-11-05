# -*- coding: utf-8 -*-


from osv import fields, osv
from tools.safe_eval import safe_eval as eval
from edi import EDIMixin
import os
from datetime import datetime
from pybrasil.base import tira_acentos
from pybrasil.valor.decimal import Decimal as D
from integra_rh.constantes_rh import *
from pybrasil.data import parse_datetime, primeiro_dia_mes, ultimo_dia_mes, hoje


TIPO_MEDIA = [
    ('valor', u'Valor'),
    ('quantidade', u'Quantidade'),
    ('calculada', u'Calcula normalmente'),
    ('afastamento', u'Dias de afastamento'),
    ('valor_ultimos_meses', u'Valor dos últimos meses'),
    ('quantidade_ultimos_meses', u'Quantidade dos últimos meses'),
]

SINAL_CATEGORIA = [
    ('-', u'Dedução'),
    ('+', u'Provento'),
    ('0', u'Base de cálculo/demonstrativo'),
]

TIPO_RUBRICA = [
    ('1', u'Vencimento'),
    ('2', u'Desconto'),
    ('3', u'Informativa'),
    ('4', u'Informativa dedutora'),
]

TIPO_INCIDENCIA_INSS = [
    ('00', u'Não é base de cálculo'),
    ('11', u'Mensal'),
    ('12', u'13º salário'),
    ('21', u'Salário maternidade'),
    ('22', u'Salário maternidade - 13º salário'),
    #
    # continua...
    #
]

TIPO_INCIDENCIA_IRRF = [
    ('00', u'Não é base do IRRF'),
]

CAMPOS_ADMIN = ['name',
    'code',
    'category_id',
    'sinal',
    'sequence',
    'active',
    'company_id',
    'manual',
    'exige_valor',
    'manual_horas',
    'afastamento',
    'codigo_afastamento',
    'estrutura_afastamento_id',
    'tipo_media',
    'ignora_media_13',
    'regra_holerite_anterior_id',
    'regra_saldo_devedor_id',
    'rubrica_rescisao_id',
    'calculo_padrao',
    'data_alteracao_padrao',
    'condition_select',
    'condition_python',
    'condition_range',
    'condition_range_min',
    'condition_range_max',
    'amount_select',
    'amount_percentage_base',
    'quantity',
    'amount_fix',
    'amount_percentage',
    'amount_python_compute',
    'register_id',
    'struct_ids',
    'child_ids',
    'input_ids',
]


class hr_salary_rule(osv.Model, EDIMixin):
    _name = 'hr.salary.rule'
    _description = u'Rubrica de salário'
    _inherit = 'hr.salary.rule'
    _order = 'name'
    _rec_name = 'descricao'

    def _get_descricao(self, cr, uid, ids, prop, unknow_none, context={}):
        if not len(ids):
            return {}

        res = {}
        for rule_obj in self.browse(cr, uid, ids):
            nome = '[' + str(rule_obj.id).zfill(4) + ']'

            #if rule_obj.participante_id:
                #participante_obj = rule_obj.participante_id[0]
            if rule_obj.name:
                nome += ' ' + rule_obj.name

            res[rule_obj.id] = nome

        return res

    def _procura_descricao(self, cr, uid, obj, nome_campo, args, context=None):
        texto = args[0][2]

        codigo = 0
        if texto.isdigit():
            codigo = int(texto)

        if codigo:
            procura = [
                '|',
                ('id', '=', codigo),
                '|',
                ('name', 'ilike', texto),
                ('code', 'ilike', texto)
            ]
        else:
            procura = [
                '|',
                ('name', 'ilike', texto),
                ('code', 'ilike', texto)
            ]

        return procura

    def _get_pk(self, cr, uid, ids, prop, unknow_none, context={}):
        if not len(ids):
            return {}

        res = {}

        for id in ids:
            res[id] = id

        return res

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for regra_obj in self.browse(cr, uid, ids):
            res[regra_obj.id] = regra_obj.id

        return res

    _columns = {
        'sequence': fields.float(u'Sequência de cálculo', select=True),
        'calculo_padrao': fields.boolean(u'Cálculo padrão do sistema?'),
        'data_alteracao_padrao': fields.datetime(u'Data de alteração do cálculo padrão'),

        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=True, select=True),
        'descricao': fields.function(_get_descricao, type='char', string=u'Rubrica', fnct_search=_procura_descricao),
        'name':fields.char(u'Nome', size=256, required=True, readonly=False, select=True),
        'code':fields.char(u'Variável', size=64, required=True, help='', select=True),
        'manual': fields.boolean(u'Lançamento manual?'),
        'exige_valor': fields.boolean(u'Exige valor manual?'),
        'manual_horas': fields.boolean(u'Valor manual lançado em horas?'),
        #'codigo_esocial_tabela_03_id': fields.many2one('esocial.tabela_03', 'Codigo eSocial', help="Seliciona a Rubrica do eSocial para este Item"),
        #'opcional': fields.boolean('Regra opcional?'),
        'afastamento': fields.boolean(u'Afastamento?'),
        'codigo_afastamento': fields.selection(TIPO_AFASTAMENTO, u'Código de afastamento'),
        'estrutura_afastamento_id': fields.many2one('hr.payroll.structure', 'Estrutura de afastamento'),
        'tipo_media': fields.selection(TIPO_MEDIA, u'Média para férias/13º'),
        'ignora_media_13': fields.boolean(u'Ignora média no 13º?'),
        'regra_holerite_anterior_id': fields.many2one('hr.salary.rule', u'Transforma do holerite anterior'),
        'pk': fields.function(_get_pk, type='integer', string=u'PK'),
        'sinal': fields.related('category_id', 'sinal', type='char', size=1, string=u'Sinal', store=True, select=True),
        'regra_saldo_devedor_id': fields.many2one('hr.salary.rule', u'Rubrica para ajuste de saldo devedor'),
        'rubrica_rescisao_id': fields.many2one('hr.rubrica.rescisao', u'Rubrica para Rescisão'),

        'condition_select': fields.selection([('none', 'Always True'),('range', 'Range'), ('python', 'Python Expression'), ('manual', u'Manual')], "Condition Based on", required=True),
        #'condition_range':fields.char('Range Based on',size=1024, readonly=False, help='This will be used to compute the % fields values; in general it is on basic, but you can also use categories code fields in lowercase as a variable names (hra, ma, lta, etc.) and the variable basic.'),
        #'condition_python':fields.text('Python Condition', required=True, readonly=False, help='Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.'),#old name = conditions
        #'condition_range_min': fields.float('Minimum Range', required=False, help="The minimum amount, applied for this rule."),
        #'condition_range_max': fields.float('Maximum Range', required=False, help="The maximum amount, applied for this rule."),
        'amount_select':fields.selection([
            ('percentage','Percentage (%)'),
            ('fix','Fixed Amount'),
            ('code','Python Code'),
            ('manual', u'Manual'),
        ],'Amount Type', select=True, required=True, help="The computation method for the rule amount."),
        #'amount_fix': fields.float('Fixed Amount', digits_compute=dp.get_precision('Payroll'),),
        #'amount_percentage': fields.float('Percentage (%)', digits_compute=dp.get_precision('Payroll Rate'), help='For example, enter 50.0 to apply a percentage of 50%'),
        #'amount_python_compute':fields.text('Python Code'),
        #'amount_percentage_base':fields.char('Percentage based on',size=1024, required=False, readonly=False, help='result will be affected to a variable'),

        'struct_ids':fields.many2many('hr.payroll.structure', 'hr_structure_salary_rule_rel', 'rule_id', 'struct_id', u'Estruturas de salário'),
    }

    _defaults = {
        'ignora_media_13': False,
        'manual': True,
        'exige_valor': True,
        'afastamento': False,
        'condition_select': 'manual',
        'amount_select': 'manual',
        'amount_python_compute':
u'''
result_rate = 100.0
result_qty = 1.0
result = 0.0''',
        'condition_python':
u'''
result_rate = 100.0
result_qty = 1.0
result = 0.0''',
    }

    def create(self, cr, uid, dados, context={}):
        #
        # Coloca tudo em maiúsculas somente na hr_salary_rule
        # Isso é necessário pois a payslip_line herda daqui, e lá
        # os códigos *não* podem ser todos em maiúsculas
        #
        if self._table == 'hr_salary_rule':
            if 'code' in dados:
                dados['code'] = tira_acentos(unicode(dados['code'].upper().replace(' ', '_')))
                if dados['code'][0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    dados['code'] = 'R_' + dados['code']

            if uid != 1:
                raise osv.except_osv(u'ATENÇÃO!', u'Você Não ter permissão de para criar rubricas!')

        res = super(hr_salary_rule, self).create(cr, uid, dados, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Coloca tudo em maiúsculas somente na hr_salary_rule
        # Isso é necessário pois a payslip_line herda daqui, e lá
        # os códigos *não* podem ser todos em maiúsculas
        #
        if self._table == 'hr_salary_rule':

            if 'code' in dados:
                dados['code'] = tira_acentos(unicode(dados['code'].upper().replace(' ', '_')))
                if dados['code'][0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    dados['code'] = 'R_' + dados['code']

        #if 'sequence' in dados:
            #raise osv.except_osv(u'Erro!', u'Não é permitido alterar a sequência de cálculo da rubrica')

            if uid != 1:
                for campo in dados :
                    if campo in CAMPOS_ADMIN:
                        raise osv.except_osv(u'ATENÇÃO!', u'Você Não ter permissão de para editar rubricas!')

        res = super(hr_salary_rule, self).write(cr, uid, ids, dados, context=context)

        return res

    def unlink(self, cr, uid, ids, context={}):

        if self._table == 'hr_salary_rule':
            if uid != 1:
                raise osv.except_osv(u'ATENÇÃO!', u'Você Não ter permissão de para editar rubricas!')

        res = super(hr_salary_rule, self).unlink(cr, uid, ids, context=context)

        return res

    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        """
        :param rule_id: id of rule to compute
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """

        #
        # Pega todos os float do localdict e converte para Decimal
        #
        localdict['Decimal'] = D
        localdict['D'] = D
        localdict['primeiro_dia_mes'] = primeiro_dia_mes
        localdict['ultimo_dia_mes'] = ultimo_dia_mes
        localdict['parse_datetime'] = parse_datetime
        localdict['hoje'] = hoje

        #
        # Inicializa retornos
        #
        valor = D(0)
        quantidade = D(0)
        porcentagem = D(100)
        aparece_no_holerite = True
        forca_valor = None
        forca_quantidade = None
        forca_porcentagem = None
        forca_total = None
        categoria_id = None
        simulacao_id = None

        for item, valor in localdict.iteritems():
            if isinstance(valor, float):
                localdict[item] = D(valor)

        rule = self.browse(cr, uid, rule_id, context=context)
        if rule.amount_select == 'fix':
            try:
                valor = D(rule.amount_fix)
                quantidade = D(eval(rule.quantity, localdict))
                aparece_no_holerite = rule.appears_on_payslip
            except:
                raise osv.except_osv(u'Erro!', u'Quantidade incorreta difinida para a rubrica %s (%s)' % (rule.name, rule.code))

        elif rule.amount_select == 'percentage':
            try:
                valor = D(eval(rule.amount_percentage_base, localdict))
                quantidade = D(eval(rule.quantity, localdict))
                porcentagem = D(rule.amount_percentage)
                aparece_no_holerite = rule.appears_on_payslip
            except:
                raise osv.except_osv(u'Erro!', u'Porcentagem incorreta difinida para a rubrica %s (%s)' % (rule.name, rule.code))

        else:
            #try:
            if rule.amount_select == 'manual':
                rule.amount_python_compute = 'result = variavel.%s.valor' % rule.code.strip()

            print('vai calcular', rule.code, rule.id)
            eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
            #try:
                #eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
            #except:
                #raise osv.except_osv(u'Erro!', u'Calculando a rubrica {rubrica} ({codigo}) para o funcionário {funcionario}'.format(rubrica=rule.name, codigo=rule.code, funcionario=localdict['contrato'].employee_id.nome))

            valor = D(localdict.get('result', localdict.get('retorna_valor', D(0))))

            if localdict.get('holerite', False) and getattr(localdict['holerite'], 'pagamento_dobro', False) and rule.sinal == '+' and rule.code != 'FERIAS_1_3':
                if getattr(localdict['holerite'], 'pagamento_dobro_dias', 30) != 30:
                    pagamento_dobro_dias = D(getattr(localdict['holerite'], 'pagamento_dobro_dias', 30) or 0) / D(30)
                    valor += (valor * pagamento_dobro_dias)
                else:
                    valor = valor * 2

            quantidade = D(localdict.get('result_qty', localdict.get('retorna_quantidade', D(1))))
            porcentagem = D(localdict.get('result_rate', localdict.get('retorna_porcentagem', D(100))))

            aparece_no_holerite = localdict.get('aparece_no_holerite', rule.appears_on_payslip)

            forca_valor = localdict.get('forca_valor', None)
            forca_quantidade = localdict.get('forca_quantidade', None)
            forca_porcentagem = localdict.get('forca_porcentagem', None)
            forca_total = localdict.get('forca_total', None)
            categoria_id = localdict.get('categoria_id', None)
            simulacao_id = localdict.get('simulacao_id', None)

        #
        # 1ª parcela do 13º, divide tudo por 2, menos os DSR_
        #
        if 'holerite' in localdict:
            holerite_obj = localdict['holerite']
            if holerite_obj.tipo == 'D' and ('-12-' not in holerite_obj.date_from) and (not holerite_obj.dias_aviso_previo) and (not holerite_obj.simulacao) and (not holerite_obj.provisao):
                if rule.category_id.sinal == '+':
                    valor = valor / D(2)

        return valor, quantidade, porcentagem, aparece_no_holerite, forca_valor, forca_quantidade, forca_porcentagem, forca_total, categoria_id, simulacao_id

    def satisfy_condition(self, cr, uid, rule_id, localdict, context=None):
        """
        @param rule_id: id of hr.salary.rule to be tested
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the given contract. Return False otherwise.
        """
        rule = self.browse(cr, uid, rule_id, context=context)

        if rule.condition_select == 'none':
            return True
        elif rule.condition_select == 'range':
            try:
                result = eval(rule.condition_range, localdict)
                return rule.condition_range_min <=  result and result <= rule.condition_range_max or False
            except:
                raise osv.except_osv(_('Error'), _('Wrong range condition defined for salary rule %s (%s)')% (rule.name, rule.code))
        else: #python code
            if rule.condition_select == 'manual':
                rule.condition_python = 'result = variavel.%s and variavel.%s.valor > 0' % (rule.code, rule.code)

            print('vai avaliar', rule.code, rule.id)
            eval(rule.condition_python, localdict, mode='exec', nocopy=True)
            #try:
                #eval(rule.condition_python, localdict, mode='exec', nocopy=True)
            #except:
                #raise osv.except_osv(u'Erro!', u'Verificando a rubrica {rubrica} ({codigo}) para o funcionário {funcionario}'.format(rubrica=rule.name, codigo=rule.code, funcionario=localdict['contrato'].employee_id.nome))

            return 'result' in localdict and localdict['result'] or False

    def exporta_json(self, cr, uid, ids, context={}):
        ids = self.search(cr, uid, [], order='id')
        objs = self.browse(cr, uid, ids)
        modelo = {
            #'id': False,
            'code': False,
            'name': False,
            'manual': False,
            'exige_valor': False,
            'afastamento': False,
            #'estrutura_afastamento_id': False,
            'tipo_media': False,
            #'regra_holerite_anterior_id': False,
            'descricao': False,
            'sinal': False,
            'condition_select': False,
            'condition_range': False,
            'condition_python': False,
            'condition_range_min': False,
            'condition_range_max': False,
            'amount_select': False,
            'amount_fix': False,
            'amount_percentage': False,
            'amount_python_compute': False,
            'amount_percentage_base': False,
            'sequence': False,
            #'register_id': False,
            'appears_on_payslip': False,
            'active': False,
            'category_id': False,
            'pk': False,
        }
        json = super(hr_salary_rule, self).edi_export(cr, uid, objs, modelo)
        nome_arquivo = os.path.expanduser('~/regras.json')
        #print(nome_arquivo)
        open(nome_arquivo, 'w').write(unicode(json).encode('utf-8'))
        #print('regras no arquivo', len(json))

        #print(json)
        return True

    def importa_json(self, cr, uid, ids, context={}):
        nome_arquivo = os.path.expanduser('~/regras.json')
        json = open(nome_arquivo, 'r').read().decode('utf-8')
        json = eval(json)
        ##print('regras no arquivo', len(json))
        regra_pool = self.pool.get('hr.salary.rule')
        categ_pool = self.pool.get('hr.salary.rule.category')

        for regra_dic in json:
            id = regra_dic['pk']
            id = int(id)
            regra_dic['id'] = id
            categ_id = regra_dic['category_id'][1]
            categ_id = categ_pool.search(cr, uid, [('name', '=', categ_id)])

            #print(regra_dic['code'], id, categ_id)
            if len(categ_id) >= 1:
                regra_dic['category_id'] = categ_id[0]
            else:
                regra_dic['category_id'] = False

            ids = regra_pool.search(cr, uid, [('id', '=', id)])

            if len(ids) >= 1:
                regra_obj = regra_pool.browse(cr, uid, id)
                regra_obj.write(regra_dic)

            else:
                regra_pool.create(cr, uid, regra_dic)

            #print(regra_dic)

        return True

    def onchange_category_id(self, cr, uid, ids, category_id):
        res = {}
        valores = {}
        res['value'] = valores

        if not category_id:
            return res

        categoria_obj = self.pool.get('hr.salary.rule.category').browse(cr, uid, category_id)
        valores['sinal'] = categoria_obj.sinal

        return res

    def onchange_calculo_padrao(self, cr, uid, ids, calculo_padrao, codigo, context={}):
        rubrica_pool = self.pool.get('hr.salary.rule')

        if (not codigo) or (not calculo_padrao):
            return

        res = {}
        valores = rubrica_pool.busca_calculos_padrao(cr, uid, codigo)
        res['value'] = valores

        return res

    def busca_calculos_padrao(self, cr, uid, codigo=None):
        rubrica_pool = self.pool.get('hr.salary.rule')

        caminho = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(caminho, 'rubrica')

        if codigo:
            rubricas_padrao = [codigo]

        else:
            rubricas_padrao = os.listdir(caminho)

        for rubrica in rubricas_padrao:
            caminho_rubrica = os.path.join(caminho, rubrica)
            arquivo_condicao = os.path.join(caminho_rubrica, 'condicao.py')
            arquivo_calculo = os.path.join(caminho_rubrica, 'calculo.py')

            #print(arquivo_condicao)
            #print(arquivo_calculo)

            if os.path.exists(arquivo_condicao):
                alteracao_condicao = datetime.fromtimestamp(os.path.getmtime(arquivo_condicao))
                condicao = file(arquivo_condicao, 'r').read().decode('utf-8')
            else:
                condicao = u'''#
# Cálculo manual (via variáveis)
#
result = variavel.{rubrica}
'''.format(rubrica=rubrica)

            if os.path.exists(arquivo_calculo):
                alteracao_calculo = datetime.fromtimestamp(os.path.getmtime(arquivo_calculo))
                calculo = file(arquivo_calculo, 'r').read().decode('utf-8')
            else:
                calculo = u'''#
# Cálculo manual (via variáveis)
#
result = variavel.{rubrica}.valor
'''.format(rubrica=rubrica)

            data_alteracao = alteracao_condicao
            if alteracao_calculo < data_alteracao:
                data_alteracao = alteracao_calculo

            #
            # Agora que temos o cálculo padrão, setamos nas rubricas que são padrão
            #
            busca = [
                ('code', '=', rubrica),
                ('calculo_padrao', '=', True),
                ('data_alteracao_padrao', '=', False),
                ('data_alteracao_padrao', '<', str(data_alteracao))
            ]
            rubrica_alterar_ids = rubrica_pool.search(cr, 1, busca)
            dados = {
                'condition_select': 'python',
                'condition_python': condicao,
                'amount_select': 'code',
                'amount_python_compute': calculo,
                'data_alteracao_padrao': str(data_alteracao),
            }
            rubrica_pool.write(cr, 1, rubrica_alterar_ids, dados)

        if codigo:
            return dados
