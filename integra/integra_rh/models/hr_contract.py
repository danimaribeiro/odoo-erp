# -*- coding: utf-8 -*-


from osv import fields, osv
from hr_employee import ESTADO
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from pybrasil.data import data_hora_horario_brasilia, parse_datetime, agora, hoje as hoje_brasil, formata_data, idade_meses, idade, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import decimal
from consulta_feriados import dias_sem_feriado, feriados_no_periodo
from hr_payslip_input import primeiro_ultimo_dia_mes
from finan.wizard.finan_relatorio import Report
import os
import base64
from hr_payslip_input import  primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from tools.translate import _
from pybrasil.feriado import conta_feriados_sem_domingo, data_eh_feriado
from integra_rh.constantes_rh import *

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

SEGUNDA = 0
TERCA = 1
QUARTA = 2
QUINTA = 3
SEXTA = 4
SABADO = 5
DOMINGO = 6

###TIPO_ADMISSAO = [
    ###('1', u'Admissão'),
    ###('2', u'Transferência de empresa no mesmo grupo econômico'),
    ###('3', u'Admissão por sucessão, incorporação ou fusão'),
    ###('4', u'Trabalhador cedido'),
###]

###INDICATIVO_ADMISSAO = [
    ###('1', u'Normal'),
    ###('2', u'Decorrente de ação fiscal'),
    ###('3', u'Decorrente de decisão judicial'),
###]

###REGIME_TRABALHISTA = [
    ###('1', u'CLT - Consolidação das Leis de Trabalho'),
    ###('2', u'RJU - Regime Jurídico Único'),
    ###('3', u'RJP - Regime Jurídico Próprio'),
###]

###REGIME_PREVIDENCIARIO = [
    ###('1', u'RGPS - Regime Geral da Previdência Social'),
    ###('2', u'RPPS - Regime Próprio de Previdência Social'),
    ###('3', u'RPPE - Regime Próprio de Previdência Social no Exterior'),
###]

###NATUREZA_ATIVIDADE = [
    ###('1', u'Trabalhador urbano'),
    ###('2', u'Trabalhador rural'),
###]

###UNIDADE_SALARIO = [
    ###('1', u'Por hora'),
    ####('2', u'Por dia'),
    ####('3', u'Por semana'),
    ###('4', u'Por mês'),
    ####('5', u'Por tarefa'),
###]

###TIPO_CONTRATO = [
    ###('1', u'Prazo indeterminado'),
    ###('2', u'Prazo determinado'),
###]

###CATEGORIA_TRABALHADOR = [
    ###('101', u'Empregado – Geral'),
    ###('102', u'Empregado – Trabalhador Rural por Pequeno Prazo da Lei 11.718/2008'),
    ###('103', u'Empregado – Aprendiz'),
    ###('104', u'Empregado – Doméstico'),
    ###('105', u'Empregado – contrato a termo firmado nos termos da Lei 9601/98'),
    ###('106', u'Empregado – contrato por prazo determinado nos termos da Lei 6019/74'),
    ###('107', u'Trabalhador não vinculado ao RGPS com direito ao FGTS'),
    ###('201', u'Trabalhador Avulso – Portuário'),
    ###('202', u'Trabalhador Avulso – Não Portuário (Informação do Sindicato)'),
    ###('203', u'Trabalhador Avulso – Não Portuário (Informação do Contratante)'),
    ###('301', u'Servidor Público – Titular de Cargo Efetivo'),
    ###('302', u'Servidor Público – Ocupante de Cargo exclusivo em comissão'),
    ###('303', u'Servidor Público – Exercente de Mandato Eletivo'),
    ###('304', u'Servidor Público – Agente Público'),
    ###('305', u'Servidor Público vinculado a RPPS indicado para conselho ou órgão representativo, na condição de representante do governo, órgão ou entidade da administração pública'),
    ###('401', u'Dirigente Sindical – Em relação a Remuneração Recebida no Sindicato'),
    ###('701', u'Contrib. Individual – Autônomo contratado por Empresas em geral'),
    ###('702', u'Contrib. Individual – Autônomo contratado por Contrib. Individual, por pessoa física em geral, ou por missão diplomática e repartição consular de carreira estrangeiras'),
    ###('703', u'Contrib. Individual – Autônomo contratado por Entidade Beneficente de Assistência Social isenta da cota patronal'),
    ###('704', u'Excluído.'),
    ###('711', u'Contrib. Individual – Transportador autônomo contratado por Empresas em geral'),
    ###('712', u'Contrib. Individual – Transportador autônomo contratado por Contrib. Individual, por pessoa física em geral, ou por missão diplomática e repartição consular de carreira estrangeiras'),
    ###('713', u'Contrib. Individual – Transportador autônomo contratado por Entidade Beneficente de Assistência Social isenta da cota patronal'),
    ###('721', u'Contrib. Individual – Diretor não empregado com FGTS'),
    ###('722', u'Contrib. Individual – Diretor não empregado sem FGTS'),
    ###('731', u'Contrib. Individual – Cooperado que presta serviços a empresa por intermédio de cooperativa de trabalho'),
    ###('732', u'Contrib. Individual – Cooperado que presta serviços a Entidade Beneficente de Assistência Social isenta da cota patronal ou para pessoa física'),
    ###('733', u'Contrib. Individual – Cooperado eleito para direção da Cooperativa'),
    ###('734', u'Contrib. Individual – Transportador Cooperado que presta serviços a empresa por intermédio de cooperativa de trabalho'),
    ###('735', u'Contrib. Individual – Transportador Cooperado que presta serviços a Entidade Beneficente de Assistência Social isenta da cota patronal ou para pessoa física'),
    ###('736', u'Contrib. Individual – Transportador Cooperado eleito para direção da Cooperativa'),
    ###('741', u'Contrib. Individual – Cooperado filiado a cooperativa de produção'),
    ###('751', u'Contrib. Individual – Micro Empreendedor Individual, quando contratado por PJ'),
    ###('901', u'Estagiário'),
###]

###TIPO_ESCALA = [
    ###('1', u'12 × 36'),
    ###('2', u'24 × 72'),
    ###('3', u'6 × 18'),
###]

###TIPO_JORNADA = [
    ###('1', u'Padrão'),
    ####('2', u'Turno fixo'),
    ####
    #### Turno flexível removido devido a dificuldade de determinar
    #### quantas vezer o funcionário trabalha no turno no mês
    ####
    ####('3', u'Turno flexível'),
    ###('4', u'Especial/escala'),
###]


TEMPO_EXPERIENCIA = [
    ('30+30', '30 + 30'),
    ('30+60', '30 + 60'),
    ('45+45', '45 + 45'),
    ('60+30', '60 + 30'),
]

MOTIVO_CONTRATACAO = [
    ('novo', 'Nova vaga'),
    ('substituicao', 'Substituição'),
    ('temporario', 'Temporário'),
]


class hr_contract(osv.Model):
    _name = 'hr.contract'
    _description = 'Contract'
    _inherit = 'hr.contract'
    _order = 'employee_nome, date_end desc'
    _rec_name = 'descricao'

    def onchange_employee_id(self, cursor, user_id, ids, employee_id, context=None):
        valores = {}
        retorno = {'value': valores}

        employee_obj = self.pool.get('hr.employee').browse(cursor, user_id, employee_id)

        valores['employee_endereco'] = employee_obj.endereco
        valores['employee_numero'] = employee_obj.numero
        valores['employee_complemento'] = employee_obj.complemento
        valores['employee_bairro'] = employee_obj.bairro
        valores['employee_municipio_id'] = employee_obj.municipio_id.id
        valores['employee_cep'] = employee_obj.cep
        valores['employee_fone'] = employee_obj.fone
        valores['employee_celular'] = employee_obj.celular
        valores['employee_email'] = employee_obj.email

        return retorno

    def onchange_acha_estrutura(self, cr, uid, ids, employee_id, struct_id, rubrica_manual_ids):
        valores = {}
        retorno = {'value': valores}
        contract_pool = self.pool.get('hr.contract')
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), ('date_end', '=', False)])

        if contract_ids:
            if len(contract_ids) > 1:
                raise osv.except_osv(u'Inválido!', u'Há mais de 1 contrato ativo para o funcionário!')

            contract_id = contract_ids[0]
            #valores['contract_id'] = contract_id
            contract_obj = contract_pool.browse(cr, uid, contract_id)
            valores['struct_id'] = contract_obj.struct_id.id
            valores['rubrica_manual_ids'] = contract_obj.rubrica_manual_ids.id

        return retorno

    def onchange_data_experiencia(self, cr, uid, ids, tempo_primeira_experiencia, tempo_segunda_experiencia, date_start):
        valores = {}
        retorno = {'value': valores}
        data_inicio = parse_datetime(date_start).date()

        if int(tempo_primeira_experiencia) > 0:
            variavel_final_prim = data_inicio + relativedelta(days=int(tempo_primeira_experiencia)-1)
            valores['final_prim_esperiencia'] = str(variavel_final_prim)

        if int(tempo_segunda_experiencia) > 0:
            variavel_final_seg = variavel_final_prim + relativedelta(days=int(tempo_segunda_experiencia))
            valores['final_seg_esperiencia'] = str(variavel_final_seg)

        return retorno

    def onchange_date_start(self, cr, uid, ids, date_start):
        valores = {}
        retorno = {'value': valores}
        data_inicio = parse_datetime(date_start).date()

        valores['data_opcao_fgts'] = str(data_inicio)

        return retorno

    def onchange_contract_id(self, cr, uid, ids, qtde_horas_mes_trab, unidade_salario, wage, context=None):
        if unidade_salario < "4":
            variavel_salario_para_calculo = wage * qtde_horas_mes_trab
        else:
            variavel_salario_para_calculo = wage

        res = {
            'value': {
                'valor_salario_para_calculo': variavel_salario_para_calculo,
            }
        }

        return res

    def _salario(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            res[contrato_obj.id] = contrato_obj.wage

        return res

    def _salario_hora(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Por hora, não faz nada
            #
            if contrato_obj.unidade_salario == '1':
                res[contrato_obj.id] = contrato_obj.wage

            #elif contrato_obj.unidade_salario == '2':
            #elif contrato_obj.unidade_salario == '3':
            elif contrato_obj.unidade_salario == '4':
                if contrato_obj.horas_mensalista > 0:
                #if contrato_obj.job_id and contrato_obj.job_id.horas_mensalista:
                    #salario_hora = contrato_obj.wage / contrato_obj.job_id.horas_mensalista
                    salario_hora = contrato_obj.wage / contrato_obj.horas_mensalista
                else:
                    salario_hora = contrato_obj.wage / 220.0

                res[contrato_obj.id] = D(salario_hora)

            #elif contrato_obj.unidade_salario == '5':

        return res

    def _salario_mes(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Por hora, não faz nada
            #
            if contrato_obj.unidade_salario == '1':
                if contrato_obj.horas_mensalista > 0:
                    salario_mes = contrato_obj.wage * contrato_obj.horas_mensalista
                else:
                    salario_mes = contrato_obj.wage * 220.0

                res[contrato_obj.id] = D(salario_mes)

            #elif contrato_obj.unidade_salario == '2':
            #elif contrato_obj.unidade_salario == '3':
            elif contrato_obj.unidade_salario == '4':
                res[contrato_obj.id] = contrato_obj.wage

            #elif contrato_obj.unidade_salario == '5':

        return res

    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for contract_obj in self.browse(cr, uid, ids):

            nome = u'[' + unicode(contract_obj.name.strip()) + u'] '
            nome += contract_obj.employee_id.nome + ' - '
            nome += contract_obj.company_id.name
            if contract_obj.date_end:
                nome += ' R. ' + formata_data(contract_obj.date_end)

            res[contract_obj.id] = nome

        return res

    def _procura_descricao(self, cr, uid, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|',
            ('name', 'ilike', texto),
            ('employee_id.nome', 'ilike', texto),
        ]

        return procura

    def onchange_seguro_desemprego(self, cr, uid, ids, seguro_desemprego, context={}):
        if seguro_desemprego == False:
            return {}
        else:
            warning = {
                'title': _('Warning!'),
                'message' : _('Funcionário em Seguro Desemprego. Gerar CAGED!.')
            }
            return {'warning': warning}

    def _data_dissidio_sindicato(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        sindicato_pool = self.pool.get('hr.sindicato')

        for contrato_obj in self.browse(cr, uid, ids, context=context):
            res[contrato_obj.id] = False

            if not contrato_obj.sindicato_id:
                continue

            sindicato_ids = sindicato_pool.search(cr, 1, [('partner_id', '=', contrato_obj.sindicato_id.id)])

            if not sindicato_ids:
                continue

            sindicato_obj = sindicato_pool.browse(cr, 1, sindicato_ids[0])

            if (not sindicato_obj.mes):
                continue

            data_dissidio = fields.date.today()[:4] + '-'
            data_dissidio += sindicato_obj.mes
            data_dissidio += '-01'

            res[contrato_obj.id] = data_dissidio

        return res

    _columns = {
        'descricao': fields.function(_descricao, type='char', string=u'Funcionário', fnct_search=_procura_descricao),
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict', select=True),
        'parent_company_id': fields.related('company_id', 'parent_id', type='many2one', relation='res.company', string=u'Empresa mãe', store=True, select=True),
        'tipo_admissao': fields.selection(TIPO_ADMISSAO, u'Tipo de admissão'),
        'data_transf': fields.date( u'Data Transferência'),
        'contrato_transf_id': fields.many2one('hr.contract', u'Contrato transferido'),
        'indicativo_admissao': fields.selection(INDICATIVO_ADMISSAO, u'Indicativo da admissão'),
        'primeiro_emprego': fields.boolean(u'Primeiro emprego?'),
        'regime_trabalhista': fields.selection(REGIME_TRABALHISTA, u'Regime trabalhista'),
        'regime_previdenciario': fields.selection(REGIME_PREVIDENCIARIO, u'Regime previdenciário'),
        'natureza_atividade': fields.selection(NATUREZA_ATIVIDADE, u'Natureza da atividade'),
        'categoria_trabalhador': fields.selection(CATEGORIA_TRABALHADOR, u'Categoria do trabalhador'),
        'codigo_cargo': fields.char(u'Código do cargo', size=30),
        #'salario': fields.float(u'Salário', digits=(18, 2)),
        'unidade_salario': fields.selection(UNIDADE_SALARIO, u'Unidade do salário'),
        'salario_variavel': fields.float(u'Salário variável', digits=(18, 2)),
        'unidade_salario_variavel': fields.selection(UNIDADE_SALARIO, u'Unidade do salário variável'),
        'tipo_contrato': fields.selection(TIPO_CONTRATO, u'Tipo do contrato'),
        'department_id': fields.many2one('hr.department', 'Departmento/lotação', ondelete='restrict'),
        'lotacao_id': fields.many2one('res.partner', 'Lotação/cliente/fornecedor', ondelete='restrict'),
        'sindicato_id': fields.many2one('res.partner', u'Filiação sindical', ondelete='restrict'),

        'numero_processo_judicial': fields.char(u'Nº processo judicial', size=20),
        'obs_processo_judicial': fields.text(u'Obs processo judicial'),
        'advogado_autor_processo': fields.char(u'Advogado do autor do processo', size=60),
        'advogado_empresa': fields.char(u'Advogado da empresa', size=60),

        'optante_fgts': fields.boolean(u'Optante pelo FGTS?'),
        'data_opcao_fgts': fields.date(u'Data de opção pelo FGTS'),

        'cnpj_empregador_anterior': fields.char(u'CNPJ do empregador anterior', size=14),
        'matricula_anterior': fields.char(u'Matrícula anterior', size=30),
        'data_inicio_vinculo_anterior': fields.date(u'Data de admissão no vínculo anterior'),
        'obs_anterior': fields.text(u'Observações do vínculo anterior', size=255),

        'cnpj_empregador_cedente': fields.char(u'CNPJ do empregador cedente', size=14),
        'matricula_cedente': fields.char(u'Matrícula cedente', size=30),
        'data_inicio_vinculo_cedente': fields.date(u'Data de admissão no vínculo cedente'),
        'onus_cedente': fields.selection([('1', '1'), ('2', '2'), ('3', '3')], u'Ônus para o cedente'),

        'data_atestado_saude': fields.date(u'Data do atestado de saúde ocupacional'),
        'medico_atestado_saude_nome': fields.char(u'Nome do médico encarregado', size=80),
        'medico_atestado_saude_crm_numero': fields.char(u'CRM nº', size=8),
        'medico_atestado_saude_crm_estado': fields.selection(ESTADO, 'Estado do CRM'),
        'exame_ids': fields.one2many('hr.contract_exame', 'contract_id', 'Exames'),
        'curso_ids': fields.one2many('hr.contract.curso.treinamento', 'contract_id', u'Curso e Treinamentos'),

        'jornada_tipo': fields.selection(TIPO_JORNADA, 'Tipo de jornada de trabalho'),
        'jornada_segunda_a_sexta_id': fields.many2one('hr.jornada', u'Jornada padrão de segunda a sexta-feira', ondelete='restrict'),
        'jornada_segunda_id': fields.many2one('hr.jornada', u'Jornada na segunda-feira', ondelete='restrict'),
        'jornada_terca_id': fields.many2one('hr.jornada', u'Jornada na terça-feira', ondelete='restrict'),
        'jornada_quarta_id': fields.many2one('hr.jornada', u'Jornada na quarta-feira', ondelete='restrict'),
        'jornada_quinta_id': fields.many2one('hr.jornada', u'Jornada na quinta-feira', ondelete='restrict'),
        'jornada_sexta_id': fields.many2one('hr.jornada', u'Jornada na sexta-feira', ondelete='restrict'),
        'jornada_sabado_id': fields.many2one('hr.jornada', u'Jornada no sábado', ondelete='restrict'),
        'jornada_domingo_id': fields.many2one('hr.jornada', u'Jornada no domingo', ondelete='restrict'),
        'jornada_turno': fields.integer(u'Turno'),
        'jornada_turno_id': fields.many2one('hr.jornada', u'Jornada turno flexível', ondelete='restrict'),
        'jornada_escala': fields.selection(TIPO_ESCALA, u'Escala'),
        'jornada_escala_id': fields.many2one('hr.jornada', u'Jornada escala', ondelete='restrict'),

        'tempo_primeira_experiencia': fields.integer(u'Tempo em dias do 1º período experiência'),
        'data_termino_primeira_experiencia': fields.date(u'Término do 1º período de experiência'),
        'tempo_segunda_experiencia': fields.integer(u'Tempo em dias do 2º período experiência'),
        'data_termino_segunda_experiencia': fields.date(u'Término do 2º período de experiência'),
        #'periodo_calculo': fields.integer(u'Periodo do Calculo')
        #
        # Itens variáveis
        #
        'qtde_horas_dia_trab': fields.float(u'Qtde Horas Trabalhadas no dia', digits=(5, 2)),
        'qtde_horas_mes_trab': fields.float(u'Qtde Horas Trabalhados no mês', digits=(5, 2)),
        'valor_salario_para_calculo': fields.float(u'Salário para calculo', digits=(18, 2)),
        'final_prim_esperiencia': fields.date(u'Data Primeira Experiência'),
        'final_seg_esperiencia': fields.date(u'Data Segunda Experiência'),
        'salario': fields.function(_salario, type='float', method=True, string=u'Salário', digits=(18, 2)),
        'horas_mensalista': fields.float(u'Horas de trabalho no mês'),
        #'horas_mensalista': fields.related('job_id', 'horas_mensalista', type='int', string=u'Horas de trabalho no mês', store=True),
        #'salario_hora': fields.function(_salario_hora, type='float', method=True, string=u'Salário hora', digits=(21, 10)),
        #'salario_mes': fields.function(_salario_mes, type='float', method=True, string=u'Salário mês', digits=(21, 10)),

        'regra_ids': fields.one2many('hr.contract_regra', 'contract_id', string=u'Regras especiais'),
        'holerite_ids': fields.one2many('hr.payslip', 'contract_id', string=u'Holerites'),
        'holerite_ferias_ids': fields.one2many('hr.payslip', 'contract_id', string=u'Holerites de férias', domain=[('tipo', '=', 'F')]),
        'ferias_ids': fields.one2many('hr.contract_ferias', 'contract_id', string=u'Controle de férias'),
        'falta_ids': fields.one2many('hr.falta', 'contract_id', string=u'Faltas'),
        'afastamento_ids': fields.one2many('hr.afastamento', 'contract_id', string=u'Afastamentos'),

        'motivo_contratacao': fields.selection(MOTIVO_CONTRATACAO, u'Motivo da contratação'),

        'name': fields.char(u'Matrícula', size=64, required=False),
        #'employee_id': fields.many2one('hr.employee', "Employee", required=True),
        #'department_id': fields.related('employee_id','department_id', type='many2one', relation='hr.department', string="Department", readonly=True),
        #'type_id': fields.many2one('hr.contract.type', "Contract Type", required=True),
        #'job_id': fields.many2one('hr.job', 'Job Title'),
        #'date_start': fields.date('Start Date', required=True),
        #'date_end': fields.date('End Date'),
        #'trial_date_start': fields.date('Trial Start Date'),
        #'trial_date_end': fields.date('Trial End Date'),
        #'working_hours': fields.many2one('resource.calendar','Working Schedule'),
        #'wage': fields.float('Wage', digits=(16,2), required=True, help="Basic Salary of the employee"),
        #'advantages': fields.text('Advantages'),
        #'notes': fields.text('Notes'),
        #'permit_no': fields.char('Work Permit No', hr.variavel.folhasize=256, required=False, readonly=False),
        #'visa_no': fields.char('Visa No', size=64, required=False, readonly=False),
        #'visa_expire': fields.date('Visa Expire Date'),


        #
        # Dados do funcionaário
        #
        'employee_nome': fields.related('employee_id', 'nome', type='char', string=u'Nome', store=True, select=True),
        'employee_endereco': fields.related('employee_id', 'endereco', type='char', string=u'Endereço'),
        'employee_numero': fields.related('employee_id', 'numero', type='char', string=u'nº'),
        'employee_complemento': fields.related('employee_id', 'complemento', type='char', string=u'Complemento'),
        'employee_bairro': fields.related('employee_id', 'bairro', type='char', string=u'Bairro'),
        'employee_municipio_id': fields.related('employee_id', 'municipio_id', type='many2one', relation='sped.municipio', string=u'Município'),
        'employee_cep': fields.related('employee_id', 'cep', type='char', string=u'CEP'),
        'employee_fone': fields.related('employee_id', 'fone', type='char', string=u'Fone'),
        'employee_celular': fields.related('employee_id', 'celular', type='char', string=u'Celular'),
        'employee_email': fields.related('employee_id', 'email', type='char', string=u'Email'),
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'seguro_desemprego': fields.boolean(u'Em Seguro Desemprego?'),

        'data_dissidio_sindicato': fields.function(_data_dissidio_sindicato, type='date', string=u'Data do dissídio'),
    }

    #def _get_type(self, cr, uid, context=None):
        #type_ids = self.pool.get('hr.contract.type').search(cr, uid, [('name', '=', 'Employee')])
        #return type_ids and type_ids[0] or False

    _defaults = {
        'tipo_admissao': '1',
        'indicativo_admissao': '1',
        'primeiro_emprego': False,
        'regime_trabalhista': '1',
        'regime_previdenciario': '1',
        'natureza_atividade': '1',
        'unidade_salario': '4',
        'salario_variavel': 0.00,
        'unidade_salario_variavel': '4',
        'tipo_contrato': '1',
        'categoria_trabalhador': '101',
        'optante_fgts': True,
        'onus_cedente': False,
        'jornada_tipo': '1',
        'optante_fgts': True,
        'date_end': False,
        'motivo_contratacao': 'novo',
        'horas_mensalista': 220,
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'seguro_desemprego': False,
        'mes': '01',
    }

    def piso_salarial(self, cr, uid, ids, data_inicial, data_final, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Piso salarial vem do cargo
            # buscamos a alteração mais recente em relação ao período calculado
            #
            cargo_atual = contrato_obj.job_id
            for alteracao_obj in contrato_obj.alteracao_cargo_ids:
                if alteracao_obj.data_alteracao <= data_inicial:
                    cargo_atual = alteracao_obj.job_id
                    break

            piso_salarial = cargo_atual.piso_salarial(data_inicial, data_final)
            res[contrato_obj.id] = piso_salarial

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def salario_hora(self, cr, uid, ids, data_inicial, data_final, arredonda=False, piso=False, context={}):
        res = {}

        #print('salario hora', data_inicial, data_final)

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Salário hora vem calculado da remuneração
            # buscamos a alteração mais recente em relação ao período calculado
            #
            remuneracao_atual = contrato_obj
            for alteracao_obj in contrato_obj.alteracao_remuneracao_ids:
                #print(alteracao_obj, alteracao_obj.wage, alteracao_obj.data_alteracao, data_inicial, alteracao_obj.data_alteracao <= data_inicial)
                if alteracao_obj.data_alteracao <= data_final:
                    remuneracao_atual = alteracao_obj
                    break

            #print(remuneracao_atual, remuneracao_atual.wage, remuneracao_atual.data_alteracao)

            if piso:
                piso_salarial = contrato_obj.piso_salarial(data_inicial, data_final)

                #if remuneracao_atual.horas_mensalista > 0:
                    #salario_hora = piso_salarial / remuneracao_atual.horas_mensalista
                if contrato_obj.job_id.horas_mensalista > 0:
                    salario_hora = piso_salarial / contrato_obj.job_id.horas_mensalista
                else:
                    salario_hora = piso_salarial / 220.0

                salario_hora = D(salario_hora)

                if arredonda:
                    salario_hora = salario_hora.quantize(D('0.01'))

                res[contrato_obj.id] = D(salario_hora)

                continue

            #
            # Por hora, não faz nada
            #
            if remuneracao_atual.unidade_salario == '1':
                res[contrato_obj.id] = remuneracao_atual.wage

            #elif contrato_obj.unidade_salario == '2':
            #elif contrato_obj.unidade_salario == '3':
            elif remuneracao_atual.unidade_salario == '4':
                if remuneracao_atual.horas_mensalista > 0:
                #if contrato_obj.job_id and contrato_obj.job_id.horas_mensalista:
                    #salario_hora = contrato_obj.wage / contrato_obj.job_id.horas_mensalista
                    salario_hora = remuneracao_atual.wage / remuneracao_atual.horas_mensalista
                else:
                    salario_hora = remuneracao_atual.wage / 220.0

                salario_hora = D(salario_hora)

                if arredonda:
                    salario_hora = salario_hora.quantize(D('0.01'))

                res[contrato_obj.id] = D(salario_hora)

            #elif contrato_obj.unidade_salario == '5':

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def salario_mes(self, cr, uid, ids, data_inicial, data_final, arredonda=False, piso=False, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Salário hora vem calculado da remuneração
            # buscamos a alteração mais recente em relação ao período calculado
            #
            remuneracao_atual = contrato_obj
            for alteracao_obj in contrato_obj.alteracao_remuneracao_ids:
                if alteracao_obj.data_alteracao <= data_final:
                    remuneracao_atual = alteracao_obj
                    break

            if piso:
                salario_mes = contrato_obj.piso_salarial(data_inicial, data_final)
                res[contrato_obj.id] = salario_mes

                continue

            #
            # Por hora, não faz nada
            #
            if remuneracao_atual.unidade_salario == '1':
                if remuneracao_atual.horas_mensalista > 0:
                    salario_mes = remuneracao_atual.wage * remuneracao_atual.horas_mensalista
                else:
                    salario_mes = remuneracao_atual.wage * 220.0

                salario_mes = D(salario_mes)

                if arredonda:
                    salario_mes = salario_mes.quantize(D('0.01'))

                res[contrato_obj.id] = D(salario_mes)

            #elif contrato_obj.unidade_salario == '2':
            #elif contrato_obj.unidade_salario == '3':
            elif remuneracao_atual.unidade_salario == '4':
                res[contrato_obj.id] = remuneracao_atual.wage

            #elif contrato_obj.unidade_salario == '5':

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def salario_dia(self, cr, uid, ids, data_inicial, data_final, arredonda=False, piso=False, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Salário dia é o salário mês dividido por 30 dias, sempre
            # independente do número de dias no mês
            #
            salario_mes = contrato_obj.salario_mes(data_inicial, data_final, arredonda=arredonda, piso=piso)
            salario_dia = D(salario_mes) / D('30.00')

            if arredonda:
                salario_dia = salario_dia.quantize(D('0.01'))

            res[contrato_obj.id] = D(salario_dia)

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def salario_2_dias_e_meio(self, cr, uid, ids, data_inicial, data_final, arredonda=False, piso=False, context={}):
        res = {}

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Salário dia é o salário mês dividido por 30 dias, sempre
            # independente do número de dias no mês
            #
            salario_mes = contrato_obj.salario_mes(data_inicial, data_final, arredonda=arredonda, piso=piso)
            salario_25 = D(salario_mes) / D('12.00')

            if arredonda:
                salario_25 = salario_25.quantize(D('0.01'))

            res[contrato_obj.id] = D(salario_25)

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def _soma_hora_noturna(self, jornada_obj, dias_semana_mes, dias_semana_jornada):
        horas_noturnas = 0

        for dia_semana in dias_semana_jornada:
            horas_noturnas += jornada_obj.horas_noturnas * dias_semana_mes[dia_semana]

        return horas_noturnas

    def _soma_dias_semana_intervalo(self, data_inicial, data_final):
        dias_semana = {
            SEGUNDA: 0,
            TERCA: 0,
            QUARTA: 0,
            QUINTA: 0,
            SEXTA: 0,
            SABADO: 0,
            DOMINGO: 0,
        }

        data_inicial = parse_datetime(data_inicial).date()
        data_final = parse_datetime(data_final).date()
        di = data_inicial.toordinal()
        df = data_final.toordinal()

        while di <= df:
            dia_semana = datetime.fromordinal(di).weekday()
            dias_semana[dia_semana] += 1
            di += 1

        return dias_semana

    def horas_dia(self, cr, uid, ids, data_inicial, data_final, context={}):

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            horas_dia = D(0)

            #
            # Horas noturnas vem calculado da jornada
            # buscamos a alteração mais recente em relação ao período calculado
            #
            jornada_atual = contrato_obj
            for alteracao_obj in contrato_obj.alteracao_jornada_ids:
                if alteracao_obj.data_alteracao <= data_inicial:
                    jornada_atual = alteracao_obj
                    break

            #
            # Jornada padrão
            #
            if jornada_atual.jornada_tipo == '1':
                if jornada_atual.jornada_segunda_a_sexta_id:
                    #horas_dia += jornada_atual.jornada_segunda_a_sexta_id.horas_totais
                    horas_dia += D(jornada_atual.jornada_segunda_a_sexta_id.horas) * 5

                if jornada_atual.jornada_sabado_id:
                    #horas_dia += jornada_atual.jornada_sabado_id.horas_totais
                    horas_dia += D(jornada_atual.jornada_sabado_id.horas)

                horas_dia /= D('5.5')
                horas_dia = D(contrato_obj.horas_mensalista) / D(30)

            #
            # Turno variável
            #
            elif jornada_atual.jornada_tipo == '2':
                if jornada_atual.jornada_segunda_id:
                    horas_noturnas += jornada_atual.jornada_segunda_id.horas_totais

                if jornada_atual.jornada_terca_id:
                    horas_noturnas += jornada_atual.jornada_terca_id.horas_totais

                if jornada_atual.jornada_quarta_id:
                    horas_noturnas += jornada_atual.jornada_quarta_id.horas_totais

                if jornada_atual.jornada_quinta_id:
                    horas_noturnas += jornada_atual.jornada_quinta_id.horas_totais

                if jornada_atual.jornada_sexta_id:
                    horas_noturnas += jornada_atual.jornada_sexta_id.horas_totais

                if jornada_atual.jornada_sabado_id:
                    horas_noturnas += jornada_atual.jornada_sabado_id.horas_totais

                if jornada_atual.jornada_domingo_id:
                    horas_noturnas += jornada_atual.jornada_domingo_id.horas_totais

            #
            # Turno flexível
            #
            #elif jornada_atual.jornada_tipo == '3':
                #jornada_turno_id

            #
            # Escala
            #
            elif jornada_atual.jornada_tipo == '4':
                if (not jornada_atual.jornada_escala) or (not jornada_atual.jornada_escala_id):
                    raise osv.except_osv(u'Erro no cadastro!', u'Funcionário em regime de escala sem definição de escala!')

                horas_dia = jornada_atual.jornada_escala_id.horas_totais

                #
                # Considera quantos dias tem o ciclo de cada escala
                #
                if jornada_atual.jornada_escala == '1':
                    #
                    # 12 × 36 = 12 + 36 = 24h = 2 dias (trabalha 12 horas, folga 36, totalizando 2 dias no ciclo)
                    #
                    dias_ciclo = 2.0
                elif jornada_atual.jornada_escala == '2':
                    #
                    # 24 × 72 = 24 + 72 = 96h = 4 dias (trabalha 24 horas, folga 72, totalizando 4 dias no ciclo)
                    #
                    dias_ciclo = 4.0
                elif jornada_atual.jornada_escala == '3':
                    #
                    # 6 × 18 = 6 + 18 = 24h = 1 dia (trabalha 6 horas, folga 18, totalizando 1 dia no ciclo)
                    #
                    dias_ciclo = 1.0

                horas_dia /= D(dias_ciclo)
                horas_dia = D(220) / D(30)

            res[contrato_obj.id] = horas_dia

        if len(ids) == 1:
            res = res.values()[0]

        return res


    def horas_noturnas(self, cr, uid, ids, data_inicial, data_final, context={}):

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            horas_noturnas = 0
            dias_a_considerar = 0

            total_horas_noturnas = 0
            total_dias_a_considerar = 0


            #
            # Horas noturnas vem calculado da jornada
            # buscamos a alteração mais recente em relação ao período calculado
            #
            lista_jornadas = []

            ultima_data = None
            for alteracao_obj in contrato_obj.alteracao_jornada_ids:
                if ultima_data is not None and ultima_data <= data_inicial:
                    break

                if alteracao_obj.data_alteracao >= data_inicial and alteracao_obj.data_alteracao <= data_final:
                    lista_jornadas.append(alteracao_obj)

                    if ultima_data is None or ultima_data < alteracao_obj.data_alteracao:
                        ultima_data = alteracao_obj.data_alteracao

                    continue

                elif alteracao_obj.data_alteracao <= data_inicial :
                    lista_jornadas.append(alteracao_obj)

                    if ultima_data is None or ultima_data < alteracao_obj.data_alteracao:
                        ultima_data = alteracao_obj.data_alteracao

                    break

            if len(lista_jornadas) == 0:
                lista_jornadas = [contrato_obj]

            print('lista_jornadas')
            print(lista_jornadas)

            for jornada_atual in lista_jornadas:
                if getattr(jornada_atual, 'data_alteracao', False) >= data_inicial:
                    dias_semana = self._soma_dias_semana_intervalo(jornada_atual.data_alteracao, data_final)

                    if jornada_atual.data_alteracao != data_inicial:
                        data_final = str(parse_datetime(jornada_atual.data_alteracao).date() + relativedelta(days=-1))

                else:
                    dias_semana = self._soma_dias_semana_intervalo(data_inicial, data_final)

                #
                # Jornada padrão
                #
                if jornada_atual.jornada_tipo == '1':
                    if jornada_atual.jornada_segunda_a_sexta_id:

                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_segunda_a_sexta_id, dias_semana, [SEGUNDA, TERCA, QUARTA, QUINTA, SEXTA])
                    if jornada_atual.jornada_sabado_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_sabado_id, dias_semana, [SABADO])

                #
                # Turno variável
                #
                elif jornada_atual.jornada_tipo == '2':
                    if jornada_atual.jornada_segunda_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_segunda_id, dias_semana, [SEGUNDA])

                    if jornada_atual.jornada_terca_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_terca_id, dias_semana, [TERCA])

                    if jornada_atual.jornada_quarta_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_quarta_id, dias_semana, [QUARTA])

                    if jornada_atual.jornada_quinta_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_quinta_id, dias_semana, [QUINTA])

                    if jornada_atual.jornada_sexta_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_sexta_id, dias_semana, [SEXTA])

                    if jornada_atual.jornada_sabado_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_sabado_id, dias_semana, [SABADO])

                    if jornada_atual.jornada_domingo_id:
                        horas_noturnas += self._soma_hora_noturna(jornada_atual.jornada_domingo_id, dias_semana, [DOMINGO])

                #
                # Turno flexível
                #
                #elif jornada_atual.jornada_tipo == '3':
                    #jornada_turno_id

                #
                # Escala
                #
                elif jornada_atual.jornada_tipo == '4':
                    if (not jornada_atual.jornada_escala) or (not jornada_atual.jornada_escala_id):
                        raise osv.except_osv(u'Erro no cadastro!', u'Funcionário em regime de escala sem definição de escala!')

                    #
                    # Considera quantos dias tem o ciclo de cada escala
                    #
                    if jornada_atual.jornada_escala == '1':
                        #
                        # 12 × 36 = 12 + 36 = 24h = 2 dias (trabalha 12 horas, folga 36, totalizando 2 dias no ciclo)
                        #
                        dias_ciclo = 2.0
                    elif jornada_atual.jornada_escala == '2':
                        #
                        # 24 × 72 = 24 + 72 = 96h = 4 dias (trabalha 24 horas, folga 72, totalizando 4 dias no ciclo)
                        #
                        dias_ciclo = 4.0
                    elif jornada_atual.jornada_escala == '3':
                        #
                        # 6 × 18 = 6 + 18 = 24h = 1 dia (trabalha 6 horas, folga 18, totalizando 1 dia no ciclo)
                        #
                        dias_ciclo = 1.0

                    data_inicial_intervalo = parse_datetime(data_inicial).date()
                    data_final_intervalo = parse_datetime(data_final).date()
                    intervalo = data_final_intervalo - data_inicial_intervalo
                    dias_intervalo = intervalo.days + 1
                    print('data_inicial_intervalo, data_final_intervalo, dias_intervalo')
                    print(data_inicial_intervalo, data_final_intervalo, dias_intervalo)

                    dias_a_considerar = dias_intervalo / dias_ciclo

                    #
                    # Ajusta de acordo com a escala
                    #
                    if jornada_atual.jornada_escala in ['1', '2']:
                        if int(dias_a_considerar) != dias_a_considerar:
                            dias_a_considerar = D(int(dias_a_considerar) + 1)

                    dias_a_considerar += D(int(dias_a_considerar))

                    #
                    # subtrai os dias que são feriados, considerando
                    # a empresa com quem o contrato foi feito
                    #

                    horas_noturnas += jornada_atual.jornada_escala_id.horas_noturnas * dias_a_considerar

                    total_horas_noturnas += horas_noturnas
                    total_dias_a_considerar += dias_a_considerar

                    print('total_horas_noturnas', 'total_dias_a_considerar')
                    print(total_horas_noturnas, total_dias_a_considerar)

            res[contrato_obj.id] = total_horas_noturnas, total_dias_a_considerar

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def horas_intrajornada(self, cr, uid, ids, data_inicial, data_final, context={}):
        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            horas_intrajornada = 0
            dias_a_considerar = 0

            #
            # Horas noturnas vem calculado da jornada
            # buscamos a alteração mais recente em relação ao período calculado
            #
            jornada_atual = contrato_obj
            for alteracao_obj in contrato_obj.alteracao_jornada_ids:
                if alteracao_obj.data_alteracao <= data_inicial:
                    jornada_atual = alteracao_obj
                    break

            #
            # Jornada padrão
            #
            if jornada_atual.jornada_tipo == '1':
                pass

            #
            # Turno variável
            #
            elif jornada_atual.jornada_tipo == '2':
                pass

            #
            # Turno flexível
            #
            #elif jornada_atual.jornada_tipo == '3':
                #jornada_turno_id

            #
            # Escala
            #
            elif jornada_atual.jornada_tipo == '4':
                #
                # Considera quantos dias tem o ciclo de cada escala
                #
                if jornada_atual.jornada_escala == '1':
                    #
                    # 12 × 36 = 12 + 36 = 24h = 2 dias (trabalha 12 horas, folga 36, totalizando 2 dias no ciclo)
                    #
                    dias_ciclo = 2.0
                elif jornada_atual.jornada_escala == '2':
                    #
                    # 24 × 72 = 24 + 72 = 96h = 4 dias (trabalha 24 horas, folga 72, totalizando 4 dias no ciclo)
                    #
                    dias_ciclo = 4.0
                elif jornada_atual.jornada_escala == '3':
                    #
                    # 6 × 18 = 6 + 18 = 24h = 1 dia (trabalha 6 horas, folga 18, totalizando 1 dia no ciclo)
                    #
                    dias_ciclo = 1.0

                data_inicial = parse_datetime(data_inicial).date()
                data_final = parse_datetime(data_final).date()
                intervalo = data_final - data_inicial
                dias_intervalo = intervalo.days + 1

                dias_a_considerar = dias_intervalo / dias_ciclo

                #
                # Ajusta de acordo com a escala
                #
                if jornada_atual.jornada_escala in ['1', '2']:
                    if int(dias_a_considerar) != dias_a_considerar:
                        dias_a_considerar = D(int(dias_a_considerar) + 1)

                dias_a_considerar = D(int(dias_a_considerar))

                #
                # 6 × 18 não paga intrajornada, e os que pagam é 1 hora para cada dia de trabalho
                # no ciclo
                #
                if jornada_atual.jornada_escala != '3':
                    horas_intrajornada = dias_a_considerar

            res[contrato_obj.id] = horas_intrajornada, dias_a_considerar

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def dias_domingos_feriados(self, cr, uid, ids, data_inicial, data_final, context={}):
        dias_semana = self._soma_dias_semana_intervalo(data_inicial, data_final)

        domingos = dias_semana[DOMINGO]
        #print('domingos', domingos)
        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            feriados = conta_feriados_sem_domingo(data_inicial, data_final, estado=contrato_obj.company_id.partner_id.municipio_id.estado_id.uf, municipio=contrato_obj.company_id.partner_id.municipio_id.nome)
            res[contrato_obj.id] = D(domingos + feriados)

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def dias_descanso_semanal_remunerado(self, cr, uid, ids, data_inicial, data_final, context={}):
        dias_semana = self._soma_dias_semana_intervalo(data_inicial, data_final)

        dias_uteis = dias_semana[SEGUNDA] + dias_semana[TERCA] + dias_semana[QUARTA] + dias_semana[QUINTA] + dias_semana[SEXTA] + dias_semana[SABADO]

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            domingos_e_feriados = contrato_obj.dias_domingos_feriados(data_inicial, data_final, context)
            feriados_dias_uteis = conta_feriados_sem_domingo(data_inicial, data_final, estado=contrato_obj.company_id.partner_id.municipio_id.estado_id.uf, municipio=contrato_obj.company_id.partner_id.municipio_id.nome)
            if (D(dias_uteis) - D(feriados_dias_uteis)) > 0:
                res[contrato_obj.id] = D(domingos_e_feriados) / (D(dias_uteis) - D(feriados_dias_uteis))
            else:
                res[contrato_obj.id] = D(0)

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def dias_DSR(self, cr, uid, ids, data_inicial, data_final, perdidos_falta=False, total_mes=False, context={}):
        #
        # Busca todas as semanas (de segunda a domingo, ou até a data final)
        # e depois, elimina as semanas que não tem um domingo ou feriado nela
        #
        semanas = {}
        data_inicial_semana = parse_datetime(data_inicial).date()

        if data_inicial_semana.weekday() > 0:
            data_inicial_semana += relativedelta(days=data_inicial_semana.weekday()*-1)

        data_final_semana = parse_datetime(data_final).date()
        data = data_inicial_semana
        while data <= data_final_semana:
            semana = data.isocalendar()[1]

            if not semana in semanas:
                semanas[semana] = []

            semanas[semana].append(data)
            data += relativedelta(days=+1)

        semanas_com_domingo_ou_feriado = {}
        feriado = 0
        contrato_obj = self.pool.get('hr.contract').browse(cr, uid, ids[0])
        for semana in semanas:
            tem_domingo = False
            for dia in semanas[semana]:
                tem_domingo = dia.weekday() == 6

                #print(dia)
                if dia.weekday() != 6 and data_eh_feriado(dia, estado=contrato_obj.company_id.partner_id.municipio_id.estado_id.uf, municipio=contrato_obj.company_id.partner_id.municipio_id.nome):
                    #print('eh feriado')
                    semana_feriado = (semana * 100) + feriado
                    feriado += 1
                    semanas_com_domingo_ou_feriado[semana_feriado] = semanas[semana]

            if tem_domingo:
                semanas_com_domingo_ou_feriado[semana] = semanas[semana]

        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Faltas e suspensões, se tiver, perdem o DSR
            #
            falta_ids = self.pool.get('hr.falta').search(cr, uid, [('contract_id', '=', contrato_obj.id), ('data', '>=', data_inicial), ('data', '<=', data_final), ('tipo', 'in', ('F', 'S'))])

            semanas_com_falta = []
            dias_dsr = len(semanas_com_domingo_ou_feriado)
            if len(falta_ids) > 0:
                for falta_obj in self.pool.get('hr.falta').browse(cr, uid, falta_ids):
                    for semana in semanas_com_domingo_ou_feriado:
                        dia_falta = parse_datetime(falta_obj.data).date()
                        #print(dia_falta, semanas_com_domingo_ou_feriado[semana], dias_dsr)
                        if dia_falta in semanas_com_domingo_ou_feriado[semana] and semana not in semanas_com_falta:
                            dias_dsr -= 1
                            semanas_com_falta.append(semana)
                            continue

            if perdidos_falta:
                res[contrato_obj.id] = D(len(semanas_com_falta))
            elif total_mes:
                res[contrato_obj.id] = D(len(semanas_com_domingo_ou_feriado))
            else:
                res[contrato_obj.id] = D(len(semanas_com_domingo_ou_feriado) - len(semanas_com_falta))

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def dias_uteis(self, cr, uid, ids, data_inicial, data_final, context={}):
        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            dias_uteis = 0
            estado = contrato_obj.company_id.partner_id.municipio_id.estado_id.uf
            municipio = contrato_obj.company_id.partner_id.municipio_id.nome
            feriados = feriados_no_periodo(data_inicial, data_final, estado, municipio)

            #
            # Horas noturnas vem calculado da jornada
            # buscamos a alteração mais recente em relação ao período calculado
            #
            jornada_atual = contrato_obj
            for alteracao_obj in contrato_obj.alteracao_jornada_ids:
                if alteracao_obj.data_alteracao <= data_inicial:
                    jornada_atual = alteracao_obj
                    break

            #
            # Jornada padrão
            #
            if jornada_atual.jornada_tipo == '1':
                if jornada_atual.jornada_segunda_a_sexta_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [SEGUNDA, TERCA, QUARTA, QUINTA, SEXTA])

                if jornada_atual.jornada_sabado_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [SABADO])

            #
            # Turno variável
            #
            elif jornada_atual.jornada_tipo == '2':
                if jornada_atual.jornada_segunda_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [SEGUNDA])

                if jornada_atual.jornada_terca_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [TERCA])

                if jornada_atual.jornada_quarta_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [QUARTA])

                if jornada_atual.jornada_quinta_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [QUINTA])

                if jornada_atual.jornada_sexta_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [SEXTA])

                if jornada_atual.jornada_sabado_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [SABADO])

                if jornada_atual.jornada_domingo_id:
                    dias_uteis += dias_sem_feriado(data_inicial, data_final, estado, municipio, [DOMINGO])

            #
            # Turno flexível
            #
            #elif jornada_atual.jornada_tipo == '3':
                #jornada_turno_id

            #
            # Escala
            #
            elif jornada_atual.jornada_tipo == '4':
                #
                # Considera quantos dias tem o ciclo de cada escala
                #
                if jornada_atual.jornada_escala == '1':
                    #
                    # 12 × 36 = 12 + 36 = 24h = 2 dias (trabalha 12 horas, folga 36, totalizando 2 dias no ciclo)
                    #
                    dias_ciclo = 2
                elif jornada_atual.jornada_escala == '2':
                    #
                    # 24 × 72 = 24 + 72 = 96h = 4 dias (trabalha 24 horas, folga 72, totalizando 4 dias no ciclo)
                    #
                    dias_ciclo = 4
                elif jornada_atual.jornada_escala == '3':
                    #
                    # 6 × 18 = 6 + 18 = 24h = 1 dia (trabalha 6 horas, folga 18, totalizando 1 dia no ciclo)
                    #
                    dias_ciclo = 1

                data_inicial = parse_datetime(data_inicial).date().toordinal()
                data_final = parse_datetime(data_final).date().toordinal()

                data = data_inicial
                conta_ciclo = 1
                while data <= data_final:
                    if conta_ciclo == 1:
                        if not feriados[data]:
                            dias_uteis += 1

                    conta_ciclo += 1
                    if conta_ciclo > dias_ciclo:
                        conta_ciclo = 1

                    data += 1

            res[contrato_obj.id] = dias_uteis

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def faltas(self, cr, uid, ids, data_inicial, data_final, tipo='F', context={}):
        res = {}
        for contrato_obj in self.browse(cr, uid, ids):
            falta_ids = self.pool.get('hr.falta').search(cr, uid, [('contract_id', '=', contrato_obj.id), ('data', '>=', data_inicial), ('data', '<=', data_final), ('tipo', '=', tipo)])

            res[contrato_obj.id] = len(falta_ids)

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def suspensoes(self, cr, uid, ids, data_inicial, data_final, context={}):
        return self.pool.get('hr.contract').faltas(cr, uid, ids, data_inicial, data_final, tipo='S', context=context)

    def advertencias(self, cr, uid, ids, data_inicial, data_final, context={}):
        return self.pool.get('hr.contract').faltas(cr, uid, ids, data_inicial, data_final, tipo='A', context=context)

    def acao_demorada_recalcula_ferias(self, cr, uid, ids=[], context={}, data_provisao=False):
        contract_pool = self.pool.get('hr.contract')

        contrato_ids = context.get('active_ids', [])

        if not contrato_ids:
            contrato_ids = contract_pool.search(cr, uid, [])

        for contrato_obj in self.browse(cr, uid, contrato_ids):
            contrato_obj.recalcula_ferias(context=context, data_rescisao=False, data_provisao=data_provisao)

    def dias_afastamento(self, cr, uid, contrato_obj, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, ferias=False, context={}):
        afastamento_pool = self.pool.get('hr.afastamento')
        afastamento_ids = afastamento_pool.search(cr, uid, [('employee_id', '=', contrato_obj.employee_id.id)], order='data_inicial, data_final')

        afastamentos = 0
        data_retorno = False
        for afastamento_obj in afastamento_pool.browse(cr, uid, afastamento_ids):
            if ferias and afastamento_obj.rule_id.code in ('LICENCA_MATERNIDADE', 'LICENCA_PATERNIDADE'):
                continue

            data_inicial = parse_datetime(afastamento_obj.data_inicial).date()

            if data_inicial > data_final_periodo_aquisitivo:
                continue

            if data_inicial <= data_inicial_periodo_aquisitivo:
                data_inicial = data_inicial_periodo_aquisitivo

            if not afastamento_obj.data_final:
                data_final = hoje_brasil()
            else:
                data_final = parse_datetime(afastamento_obj.data_final).date() + relativedelta(days=-1)

                if (not data_retorno) or data_retorno < data_final:
                    data_retorno = parse_datetime(afastamento_obj.data_final).date()

                    if data_retorno > data_final_periodo_aquisitivo:
                        data_retorno = False

            if data_final >= data_final_periodo_aquisitivo:
                data_final = data_final_periodo_aquisitivo

            dias_afastamento = data_final.toordinal() - data_inicial.toordinal() + 1

            if dias_afastamento > 0:
                afastamentos += dias_afastamento
            else:
                data_retorno = False

        return afastamentos, data_retorno

    def recalcula_ferias(self, cr, uid, ids, context={}, data_rescisao=False, data_provisao=False, data_rescisao_projetada=False):
        holerite_pool = self.pool.get('hr.payslip')
        afastamento_pool = self.pool.get('hr.afastamento')
        ferias_pool = self.pool.get('hr.contract_ferias')

        #data_provisao = '2015-09-30'

        #print('data_provisao')
        #print(data_provisao)

        if data_provisao:
            data_provisao = parse_datetime(data_provisao).date()
        else:
            data_provisao = None

        for contrato_obj in self.browse(cr, uid, ids):
            for ferias_obj in contrato_obj.ferias_ids:
                ferias_obj.unlink()

            #print('data_rescisao', data_rescisao, contrato_obj.id)
            if data_rescisao:
                data_rescisao = parse_datetime(data_rescisao).date()
            elif contrato_obj.date_end:
                data_rescisao = parse_datetime(contrato_obj.date_end).date()
            else:
                data_rescisao = None

            print('data_rescisao', data_rescisao)

            #
            # Busca o primeiro período de gozo, se houver
            #
            primeiras_ferias = False
            if len(contrato_obj.holerite_ferias_ids) > 0:
                if data_provisao:
                    ferias_ids = holerite_pool.search(cr, 1, [('tipo', '=', 'F'), ('contract_id', '=', contrato_obj.id), ('simulacao', '=', False), ('date_from', '<=', str(data_provisao)[:10])], order='date_from, date_to', limit=1)

                else:
                    ferias_ids = holerite_pool.search(cr, 1, [('tipo', '=', 'F'), ('contract_id', '=', contrato_obj.id), ('simulacao', '=', False)], order='date_from, date_to', limit=1)

                if len(ferias_ids):
                    primeiras_ferias = holerite_pool.browse(cr, 1, ferias_ids[0])
                    data_inicial_periodo_aquisitivo = parse_datetime(primeiras_ferias.data_inicio_periodo_aquisitivo).date()
                    data_final_periodo_aquisitivo = parse_datetime(primeiras_ferias.data_fim_periodo_aquisitivo).date()

            if not primeiras_ferias:
                data_inicial_periodo_aquisitivo = parse_datetime(contrato_obj.date_start).date()

                if data_rescisao_projetada:
                    data_inicial_periodo_aquisitivo = parse_datetime(data_rescisao_projetada).date()

                data_final_periodo_aquisitivo = data_inicial_periodo_aquisitivo
                data_final_periodo_aquisitivo += relativedelta(years=+1, days=-1)

                if data_rescisao and data_final_periodo_aquisitivo > data_rescisao:
                    data_final_periodo_aquisitivo = data_rescisao
                elif data_provisao and data_final_periodo_aquisitivo > data_provisao:
                    data_final_periodo_aquisitivo = data_provisao

            if data_rescisao:
                hoje = data_rescisao
            elif data_provisao:
                hoje = data_provisao
                #print('provisao')
                #print(data_provisao, data_final_periodo_aquisitivo, data_inicial_periodo_aquisitivo)
            else:
                hoje = hoje_brasil()

            while data_inicial_periodo_aquisitivo <= hoje:
                print('periodo aquisitivo atual', data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, hoje, data_inicial_periodo_aquisitivo <= hoje)
                afastamento_anterior, retorno_anterior = self.dias_afastamento(cr, uid, contrato_obj, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, ferias=True)

                if data_final_periodo_aquisitivo > hoje:
                    data_final_periodo_aquisitivo = hoje

                self.lanca_periodo_aquisitivo(cr, uid, contrato_obj, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, data_provisao, data_rescisao)

                #print('afastamento')
                #print(afastamento_anterior, retorno_anterior)

                #
                # Próximo período aquisitivo
                #
                data_inicial_periodo_aquisitivo = data_final_periodo_aquisitivo + relativedelta(days=+1)
                data_final_periodo_aquisitivo = data_inicial_periodo_aquisitivo + relativedelta(years=+1, days=-1)

                if data_rescisao and data_final_periodo_aquisitivo > data_rescisao:
                    data_final_periodo_aquisitivo = data_rescisao
                elif data_final_periodo_aquisitivo > hoje:
                    data_final_periodo_aquisitivo = hoje

                #print('periodo aquisitivo final')
                #print(data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo)

                #
                # Reinicia a contagem dos períodos aquisitivos quando houver afastamento
                # anterior maior de 180 e data de retorno, e não houver afastamento
                # em sequencia
                #
                if afastamento_anterior > 180 and retorno_anterior:
                    proximo_afastamento_ids = self.pool.get('hr.afastamento').search(cr, uid, [('employee_id', '=', contrato_obj.employee_id.id), ('data_inicial', '=', str(retorno_anterior))])

                    if len(proximo_afastamento_ids) == 0:
                        data_inicial_periodo_aquisitivo = retorno_anterior
                        data_final_periodo_aquisitivo = data_inicial_periodo_aquisitivo + relativedelta(years=+1, days=-1)

                        if data_final_periodo_aquisitivo > hoje:
                            data_final_periodo_aquisitivo = hoje

                print('proximo periodo aquisitivo', data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, hoje, data_inicial_periodo_aquisitivo <= hoje)

    def lanca_periodo_aquisitivo(self, cr, uid, contrato_obj, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, data_provisao, data_rescisao=False):
        holerite_pool = self.pool.get('hr.payslip')
        falta_pool = self.pool.get('hr.falta')
        ferias_pool = self.pool.get('hr.contract_ferias')

        data_inicial_periodo_concessivo = data_final_periodo_aquisitivo + relativedelta(days=+1)
        data_final_periodo_concessivo = data_inicial_periodo_concessivo + relativedelta(years=+1, days=-1)

        data_limite_gozo = data_final_periodo_concessivo + relativedelta(days=-30)
        data_limite_aviso = data_limite_gozo + relativedelta(months=-1)
        pagamento_dobro = False

        if contrato_obj.unidade_salario == '1':
            falta_ids = []

        else:
            #
            # Faltas e advertências podem causar a perda ou diminuição do período
            #
            falta_ids = falta_pool.search(cr, uid, [('contract_id', '=', contrato_obj.id), ('data', '>=', str(data_inicial_periodo_aquisitivo)), ('data', '<=', str(data_final_periodo_aquisitivo)), ('tipo', 'in', ('F', 'S'))])

        faltas = len(falta_ids)

        afastamentos, data_retorno = self.dias_afastamento(cr, uid, contrato_obj, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo, ferias=True)

        saldo_dias = 30

        perdido_afastamento = False
        if afastamentos > 180:
            saldo_dias = 0
            perdido_afastamento = True
        elif faltas >= 6 and faltas <= 14:
            saldo_dias = 24
        elif faltas >= 15 and faltas <= 23:
            saldo_dias = 18
        elif faltas >= 24 and faltas <= 32:
            saldo_dias = 12
        elif faltas > 32:
            saldo_dias = 0

        #
        # Verifica se o período aquisitivo foi gozado
        #
        # Para considerar as férias adiantadas, verifica somente a data de início
        # do período aquisitivo
        #
        #holerite_ferias_ids = holerite_pool.search(cr, uid, [('tipo', '=', 'F'), ('contract_id', '=', contrato_obj.id), ('data_inicio_periodo_aquisitivo', '=', str(data_inicial_periodo_aquisitivo)), ('data_fim_periodo_aquisitivo', '=', str(data_final_periodo_aquisitivo))])

        if data_provisao:
            holerite_ferias_ids = holerite_pool.search(cr, uid, [('tipo', '=', 'F'), ('contract_id', '=', contrato_obj.id), ('data_inicio_periodo_aquisitivo', '=', str(data_inicial_periodo_aquisitivo)), ('simulacao', '=', False), ('provisao', '=', False), ('date_from', '<=', str(data_provisao)[:10])])

        else:
            holerite_ferias_ids = holerite_pool.search(cr, uid, [('tipo', '=', 'F'), ('contract_id', '=', contrato_obj.id), ('data_inicio_periodo_aquisitivo', '=', str(data_inicial_periodo_aquisitivo)), ('simulacao', '=', False), ('provisao', '=', False)])

        if len(holerite_ferias_ids):
            for holerite_ferias_obj in holerite_pool.browse(cr, uid, holerite_ferias_ids):
                #
                # Férias são proporcionais quando o período aquisitivo não for de 1 ano exato
                # mesmo que seja por só 1 dia
                #
                data_proporcional = data_inicial_periodo_aquisitivo + relativedelta(years=+1, days=-1)
                #proporcional = data_final_periodo_aquisitivo != data_proporcional
                proporcional = holerite_ferias_obj.data_fim_periodo_aquisitivo != str(data_proporcional)

                dados = {
                    'contract_id': contrato_obj.id,
                    'data_inicial_periodo_aquisitivo': str(data_inicial_periodo_aquisitivo),
                    'data_final_periodo_aquisitivo': str(data_final_periodo_aquisitivo),
                    'data_inicial_periodo_concessivo': str(data_inicial_periodo_concessivo),
                    'data_final_periodo_concessivo': str(data_final_periodo_concessivo),
                    'data_inicial_periodo_gozo': holerite_ferias_obj.date_from,
                    'data_final_periodo_gozo': holerite_ferias_obj.date_to,
                    'data_aviso': holerite_ferias_obj.data_aviso_ferias,
                    'dias': holerite_ferias_obj.dias_ferias,
                    'saldo_dias': holerite_ferias_obj.saldo_ferias,
                    'faltas': faltas,
                    'afastamentos': afastamentos,
                    'proporcional': proporcional,
                    'data_limite_pagamento': str(parse_datetime(holerite_ferias_obj.date_from).date() + relativedelta(days=-3)),
                    'abono': holerite_ferias_obj.abono_pecuniario_ferias,
                }
                #print('saldo_dias', saldo_dias)
                saldo_dias -= holerite_ferias_obj.dias_ferias
                dados['saldo_dias'] = saldo_dias
                #print('saldo_dias', saldo_dias)

                if holerite_ferias_obj.abono_pecuniario_ferias:
                    saldo_dias = 0
                    dados['saldo_dias'] = 0

                ferias_pool.create(cr, uid, dados)

            if saldo_dias != 0:
                dados = {
                    'contract_id': contrato_obj.id,
                    'data_inicial_periodo_aquisitivo': str(data_inicial_periodo_aquisitivo),
                    'data_final_periodo_aquisitivo': str(data_final_periodo_aquisitivo),
                    'data_inicial_periodo_concessivo': str(data_inicial_periodo_concessivo),
                    'data_final_periodo_concessivo': str(data_final_periodo_concessivo),
                    'data_limite_gozo': str(data_limite_gozo),
                    'data_limite_aviso': str(data_limite_aviso),
                    'data_limite_pagamento': str(data_limite_gozo + relativedelta(days=-3)),
                    'saldo_dias': saldo_dias,
                    'faltas': faltas,
                    'afastamentos': afastamentos,
                }
                ferias_pool.create(cr, uid, dados)

        else:
            #
            # É período que não foi lançado
            #
            dias_corridos = data_final_periodo_aquisitivo.toordinal() - data_inicial_periodo_aquisitivo.toordinal() + 1
            avos = D(dias_corridos) / D('30')
            print('dias corridos, avos, aquisitivo', dias_corridos, avos, data_inicial_periodo_aquisitivo, data_final_periodo_aquisitivo)
            #print('concessivo', data_inicial_periodo_concessivo, data_final_periodo_concessivo)

            #quinze_dias = False
            #if data_final_periodo_aquisitivo.day >= 15 and int(avos) < 12:
            #    quinze_dias = True
            quinze_dias = ((avos - int(avos)) * 30) >= 15

            ###
            ### até 15 dias trabalhados no mês (30 dias) dá direito ao X avos
            ### ou seja, se a 1ª casa decimal do "avos" for maior que 5, arredonda para cima
            ###
            ##quinze_dias = str(avos)
            ##if '.' not in quinze_dias:
                ##quinze_dias = False
            ##else:
                ##quinze_dias = quinze_dias.split('.')[1][0]
                ##quinze_dias = quinze_dias >= '5'

                ####
                #### Porém, mede a data do final do período, e conta se somente for >= dia 15
                ####
                ###quinze_dias = data_final_periodo_aquisitivo.day >= 15

            if quinze_dias:
                avos = int(avos) + 1
            else:
                avos = int(avos)

            print('saldo_dias, avos', saldo_dias, avos)
            saldo_dias = saldo_dias * (avos / D(12))
            print('saldo_dias, avos', saldo_dias, avos)

            #
            # Férias em dobro é quando venceu o período concessivo
            #
            pagamento_dobro = saldo_dias > 0 and data_final_periodo_concessivo < hoje_brasil()

            #
            # Férias são proporcionais quando o período aquisitivo não for de 1 ano exato
            # mesmo que seja por só 1 dia
            #
            proporcional = False
            vencida = False
            if pagamento_dobro:
                vencida = True

            elif saldo_dias > 0:
                #data_proporcional = data_inicial_periodo_aquisitivo + relativedelta(years=+1, days=-1)
                #proporcional = data_final_periodo_aquisitivo < data_proporcional
                proporcional = avos < 12

                if not proporcional:
                    vencida = True

                #print(data_proporcional, proporcional, vencida)

            elif saldo_dias == 0 and data_final_periodo_aquisitivo == hoje_brasil():
                proporcional = True

            dados = {
                'contract_id': contrato_obj.id,
                'data_inicial_periodo_aquisitivo': str(data_inicial_periodo_aquisitivo),
                'data_final_periodo_aquisitivo': str(data_final_periodo_aquisitivo),
                'data_inicial_periodo_concessivo': str(data_inicial_periodo_concessivo),
                'data_final_periodo_concessivo': str(data_final_periodo_concessivo),
                'data_limite_gozo': str(data_limite_gozo),
                'data_limite_aviso': str(data_limite_aviso),
                'data_limite_pagamento': str(data_limite_gozo + relativedelta(days=-3)),
                'saldo_dias': saldo_dias,
                'faltas': faltas,
                'afastamentos': afastamentos,
                'avos': avos,
                'proporcional': proporcional,
                'pagamento_dobro': pagamento_dobro,
                'vencida': vencida,
                'perdido_afastamento': perdido_afastamento,
            }

            if data_rescisao and (str(data_rescisao)[:7] == contrato_obj.date_start[:7]):
                dados['media_inclui_mes'] = True

            print('dados das novas ferias')
            print(dados)
            ferias_pool.create(cr, uid, dados)

    def ferias_vencidas(self, cr, uid, ids, data_inicial, data_final, exclui_simulacao=True, mantem_provisao=False, data_rescisao=False, data_provisao=False, calcula=True, soh_busca_valor=False, context={}):
        return self.ferias_proporcionais(cr, uid, ids, data_inicial, data_final, tipo='V', exclui_simulacao=exclui_simulacao, mantem_provisao=mantem_provisao, data_rescisao=data_rescisao, data_provisao=data_provisao, calcula=calcula, soh_busca_valor=soh_busca_valor, context=context)

    def ferias_proporcionais(self, cr, uid, ids, data_inicial, data_final, tipo='P', exclui_simulacao=True, mantem_provisao=False, data_rescisao=False, data_provisao=False, calcula=True, soh_busca_valor=False, aviso_previo=False,  context={}):
        res = {}
        holerite_pool = self.pool.get('hr.payslip')

        for contrato_obj in self.browse(cr, uid, ids):
            if aviso_previo:
                self.recalcula_ferias(cr, uid, [contrato_obj.id], data_rescisao=data_final, data_rescisao_projetada=data_rescisao)
            else:
                self.recalcula_ferias(cr, uid, [contrato_obj.id], data_rescisao=data_rescisao, data_provisao=data_provisao)

            if tipo == 'P':
                ferias_proporcionais_ids = self.pool.get('hr.contract_ferias').search(cr, uid, [('contract_id', '=', contrato_obj.id), ('proporcional', '=', True), ('saldo_dias', '>', 0)])
            else:
                ferias_proporcionais_ids = self.pool.get('hr.contract_ferias').search(cr, uid, [('contract_id', '=', contrato_obj.id), ('vencida', '=', True), ('saldo_dias', '>', 0)])

            valor_proporcional = 0
            dias_proporcionais = 0
            holerite_id = None

            for ferias_obj in self.pool.get('hr.contract_ferias').browse(cr, uid, ferias_proporcionais_ids):
                dados = {
                    'employee_id': contrato_obj.employee_id.id,
                    'contract_id': contrato_obj.id,
                    'struct_id': contrato_obj.struct_id.estrutura_ferias_id.id,
                    'tipo_ferias': 'N',
                    'tipo': 'F',
                    'data_inicio_periodo_aquisitivo': ferias_obj.data_inicial_periodo_aquisitivo,
                    'data_fim_periodo_aquisitivo': ferias_obj.data_final_periodo_aquisitivo,
                    'date_from': data_inicial,
                    'date_to': data_final,
                    'dias_ferias': ferias_obj.saldo_dias,
                    'data_aviso_ferias': data_inicial,
                    'simulacao': True,
                    'provisao': False,
                    'contract_ferias_id': ferias_obj.id,
                    'vencida': ferias_obj.vencida,
                    'proporcional': ferias_obj.proporcional,
                    'pagamento_dobro': ferias_obj.pagamento_dobro,
                }

                dias_proporcionais += ferias_obj.saldo_dias

                if ferias_obj.data_final_periodo_aquisitivo > data_final:
                    dados['data_fim_periodo_aquisitivo'] = data_final
                    dados['dias_ferias'] -= D('2.5')
                    dias_proporcionais -= D('2.5')

                #
                # Verifica se já existe uma simulação anterior
                #
                if mantem_provisao:
                    dados['provisao'] = True

                    busca = [
                        ['simulacao', '=', True],
                        ['provisao', '=', True],
                        ['employee_id', '=', contrato_obj.employee_id.id],
                        ['contract_id', '=', contrato_obj.id],
                        ['tipo', '=', 'F'],
                        ['data_inicio_periodo_aquisitivo', '=', ferias_obj.data_inicial_periodo_aquisitivo],
                        ['data_fim_periodo_aquisitivo', '=', ferias_obj.data_final_periodo_aquisitivo],
                        ['date_to', '=', data_provisao]
                    ]
                else:
                    busca = [
                        ['simulacao', '=', True],
                        ['provisao', '=', False],
                        ['employee_id', '=', contrato_obj.employee_id.id],
                        ['contract_id', '=', contrato_obj.id],
                        ['tipo', '=', 'F'],
                        ['data_inicio_periodo_aquisitivo', '=', ferias_obj.data_inicial_periodo_aquisitivo],
                        ['data_fim_periodo_aquisitivo', '=', ferias_obj.data_final_periodo_aquisitivo],
                    ]

                holerite_id = holerite_pool.search(cr, uid, busca)

                #print('dados das ferias')
                #print(dados)
                #print(holerite_id)

                ja_existe = True
                if not holerite_id:
                    ja_existe = False

                    holerite_id = holerite_pool.create(cr, uid, dados)
                else:
                    holerite_id = holerite_id[0]

                holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

                #
                # Na rescisão, não
                #
                if not soh_busca_valor:
                    holerite_obj.compute_sheet()

                #
                # Depois do cálculo, pega o valor Bruto
                #
                for linha_holerite_obj in holerite_obj.line_ids:
                    if linha_holerite_obj.code == 'BRUTO':
                        valor_proporcional += linha_holerite_obj.total

                #
                # Exclui o cálculo
                #
                if not mantem_provisao:
                    if exclui_simulacao and (not ja_existe):
                        holerite_obj.unlink()

                #print(dados)
                #print(valor_proporcional)

            if exclui_simulacao or (not holerite_id):
                res[contrato_obj.id] = (dias_proporcionais, valor_proporcional, False)
            else:
                res[contrato_obj.id] = (dias_proporcionais, valor_proporcional, holerite_obj.id)

            #self.recalcula_ferias(cr, uid, [contrato_obj.id])

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def ferias_pos_aumento(self, cr, uid, ids, data_inicial, data_final, data_rescisao=False, calcula=True, soh_busca_valor=False, context={}):
        holerite_pool = self.pool.get('hr.payslip')

        for contrato_obj in self.pool.get('hr.contract').browse(cr, uid, ids):
            filtro = {
                'contract_id': contrato_obj.id,
                'data_inicial': data_inicial,
                'data_final': data_final,
            }

            #
            # Verifica se houve férias no período calculado
            #
            sql = """
            select
                h.id,
                h.data_aviso_ferias

            from
                hr_payslip h

            where
                h.contract_id = {contract_id}
                and h.tipo = 'F'
                and (h.simulacao is null or h.simulacao = False)
                and (
                    h.date_from between '{data_inicial}' and '{data_final}'
                    or h.date_to between '{data_inicial}' and '{data_final}'
                );
            """
            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # Não houve férias no período
            #
            if not len(dados):
                return False

            ferias_id = dados[0][0]
            data_aviso_ferias = dados[0][1]
            filtro['data_aviso_ferias'] = data_aviso_ferias

            #
            # Se houve, vamos verificar se há alteração contratual de remuneração
            # no período
            #
            sql = """
            select
                ca.id

            from
                hr_contract_alteracao ca

            where
                ca.contract_id = {contract_id}
                and ca.tipo_alteracao = 'R'
                and (
                    ca.data_alteracao between '{data_inicial}' and '{data_final}'
                    or ca.data_alteracao >= '{data_aviso_ferias}'
                );
            """
            sql = sql.format(**filtro)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # Não houve alteração de remuneração no período
            #
            #print('1', dados)
            if not len(dados):
                #
                # Se não houve aumento no período, verificamos se na folha anterior
                # houve o pagamento de diferença de férias por aumento, proporcional
                #
                data_inicial_anterior = parse_datetime(data_final) + relativedelta(day=1, months=-1)
                data_final_anterior = ultimo_dia_mes(data_inicial_anterior)
                filtro['data_inicial_anterior'] = data_inicial_anterior
                filtro['data_final_anterior'] = data_final_anterior

                sql = """
                select
                    h.id

                from
                    hr_payslip h
                    join hr_payslip_line hl on hl.slip_id = h.id
                    join hr_salary_rule r on r.id = hl.salary_rule_id

                where
                    h.tipo = 'N'
                    and coalesce(h.simulacao, False) = False
                    and (h.provisao is null or h.provisao = False)
                    and h.contract_id = {contract_id}
                    and h.date_from >= '{data_inicial_anterior}'
                    and h.date_to <= '{data_final_anterior}'
                    and r.code = 'FERIAS_POS_AUMENTO';
                """
                sql = sql.format(**filtro)
                cr.execute(sql)
                dados = cr.fetchall()

                if not len(dados):
                    return False

            #
            # Houve alteração, ou houve alteração no período anterior,
            # vamos simular exatamente as mesmas férias
            #
            ferias_original = holerite_pool.browse(cr, uid, ferias_id)
            filtro['data_inicial'] = ferias_original.date_from
            filtro['data_final'] = ferias_original.date_to

            #print(filtro)

            sql = """
            select
                h.id

            from
                hr_payslip h

            where
                h.contract_id = {contract_id}
                and h.tipo = 'F'
                and h.simulacao = True
                and (h.provisao is null or h.provisao = False)
                and h.date_from = '{data_inicial}'
                and h.date_to = '{data_final}';
            """
            sql = sql.format(**filtro)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # Já tem calculado, retorna o valor da diferença dos proventos, por dia de férias
            #
            #print('2', dados)
            if len(dados) and len(dados[0]):
                ferias_simuladas_id = dados[0][0]
            else:
                dados = {
                    'contract_id': contrato_obj.id,
                    'employee_id': contrato_obj.employee_id.id,
                    'company_id': contrato_obj.company_id.id,
                    'tipo': 'F',
                    'simulacao': True,
                    'struct_id': ferias_original.struct_id.id,
                    'tipo_ferias': ferias_original.tipo_ferias,
                    'data_inicio_periodo_aquisitivo': ferias_original.data_inicio_periodo_aquisitivo,
                    'data_fim_periodo_aquisitivo': ferias_original.data_fim_periodo_aquisitivo,
                    'vencida': ferias_original.vencida,
                    'proporcional': ferias_original.proporcional,
                    'pagamento_dobro': ferias_original.pagamento_dobro,
                    'date_from': ferias_original.date_from,
                    'date_to': ferias_original.date_to,
                    'abono_pecuniario_ferias': ferias_original.abono_pecuniario_ferias,
                    'dias_ferias': ferias_original.dias_ferias,
                    'data_aviso_ferias': ferias_original.data_aviso_ferias,
                }
                ferias_simuladas_id = holerite_pool.create(cr, uid, dados)

            #
            # Agora que já temos o valor, retornamos o valor da diferença por dia de férias
            #
            holerite_pool.compute_sheet(cr, uid, [ferias_simuladas_id])
            ferias_simuladas = holerite_pool.browse(cr, uid, ferias_simuladas_id)

            valor = D(ferias_simuladas.proventos or 0) - D(ferias_original.proventos or 0)
            #print('valor', valor)
            if valor < 0:
                valor = D(0)

            if ferias_simuladas.abono_pecuniario_ferias:
                ferias_simuladas.dias_ferias += 10

            valor /= D(ferias_simuladas.dias_ferias)

            return valor, ferias_simuladas_id


    _SQL_HOLERITE_AFASTADO = u'''
    select t.id
    from (
    select
        h.id,
        h.dias_afastamento - coalesce((select sum(coalesce(hl.quantity, 0)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code in ('AUX_DOENCA_15', 'AUX_ACIDENTE_TRABALHO_15', 'LICENCA_MATERNIDADE')), 0) as dias_afastamento

    from
             hr_payslip h
        join hr_contract c on c.id = h.contract_id

    where
            h.tipo = 'N'
        and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
        and c.id in ({contract_id})
    ) t
    where
        t.dias_afastamento > 15;
    '''

    _SQL_FALTAS_PERDA_AVO_DECIMO = u'''
    select
        to_char(f.data, 'yyyy-mm'),
        count(*)

    from hr_falta f

    where f.contract_id in ({contract_id})
    and f.tipo in ('F', 'S')
    and f.data between '{data_inicial}' and '{data_final}'

    group by
    1

    having count(*) >= 16;
    '''

    def decimo_terceiro_proporcional(self, cr, uid, ids, data_inicial, data_final, calcula=False, retorna_datas=False, inclui_mes=False, mantem_calculo=False, simulacao=True, provisao=False, data_rescisao=False, dias_aviso_previo=0, soh_busca_valor=False, context={}):
        res = {}
        holerite_pool = self.pool.get('hr.payslip')

        date_from = data_inicial
        date_to = data_final

        #print('data_inicial', 'data_final', 'calcula', 'retorna_datas', 'inclui_mes', 'mantem_calculo', 'simulacao', 'provisao', 'data_rescisao', 'dias_aviso_previo')
        #print(data_inicial, data_final, calcula, retorna_datas, inclui_mes, mantem_calculo, simulacao, provisao, data_rescisao, dias_aviso_previo)

        for contrato_obj in self.browse(cr, uid, ids):
            data_final = parse_datetime(data_final).date()
            data_inicial = date(data_final.year, 1, 1)
            ultimo_dia_ano = date(data_final.year, 12, 31)
            data_contratacao = parse_datetime(contrato_obj.date_start).date()

            if provisao:
                ultimo_dia_ano = data_final
                inclui_mes = True

            if data_contratacao > data_inicial:
                data_inicial = data_contratacao
                comeco_mes, fim_mes = primeiro_ultimo_dia_mes(data_inicial.year, data_inicial.month)
                fim_mes = parse_datetime(fim_mes).date()
                dias_corridos_mes = fim_mes.toordinal() - data_inicial.toordinal() + 1

                #
                # Menos de 15 dias trabalhados no mês de contratação
                # o próprio mês de contratação não conta para 13º
                #
                if dias_corridos_mes < 15:
                    data_inicial = fim_mes + relativedelta(days=+1)

            if retorna_datas:
                if (not contrato_obj.date_end) or contrato_obj.date_end > str(ultimo_dia_ano):
                    data_final = ultimo_dia_ano

            elif data_final < ultimo_dia_ano:
                dias_corridos_mes = data_final.day
                comeco_mes, fim_mes = primeiro_ultimo_dia_mes(data_final.year, data_final.month)
                comeco_mes = parse_datetime(comeco_mes).date()
                #print('dias corridos', dias_corridos_mes, comeco_mes, fim_mes)

                #
                # Menos de 15 dias trabalhados no mês de rescisão/encerramento
                # não conta para 13º
                #
                if dias_corridos_mes < 15:
                    data_final = comeco_mes + relativedelta(days=-1)

            #print(data_inicial, data_final)
            meses = idade_meses(data_inicial, data_final, quinze_dias=True)
            #print(data_final, data_inicial, meses)

            #
            # Busca os meses afastados (que trabalhou menos de 15 dias)
            #
            filtro_afastamento = {
                'data_inicial': str(data_inicial),
                'data_final': str(data_final),
                'contract_id': str(contrato_obj.id),
            }

            if contrato_obj.contrato_transf_id:
                filtro_afastamento['contract_id'] += ', ' + str(contrato_obj.contrato_transf_id.id)

            sql = self._SQL_HOLERITE_AFASTADO.format(**filtro_afastamento)
            #print(sql)
            cr.execute(sql)
            dados_afastamento = cr.fetchall()
            meses_afastado = len(dados_afastamento)
            #print('meses afastado', meses_afastado)

            if meses > 0:
                meses -= meses_afastado

                if meses < 0:
                    meses = 0

            if meses > 0 and data_final > data_inicial:
                meses = data_final.month - data_inicial.month + 1
                meses -= meses_afastado

            #
            # Paga 1 avo no mês de contratação do funcionário, mesmo sem folha fechada
            #
            if meses == 0 and '-12-' in str(data_inicial) and str(data_inicial)[:8] == contrato_obj.date_start[:8]:
                meses = 1

            #print(data_final, data_inicial, meses)

            #
            # Paga 1 avo no mês de contratação do funcionário, mesmo sem folha fechada
            #
            if meses == 0 and '-12-' in str(data_inicial) and str(data_inicial)[:8] == contrato_obj.date_start[:8]:
                meses = 1

            #print(data_final, data_inicial, meses)
            #
            # Busca os meses com pelo menos 16 faltas, o que causa a perda de 1 avo
            #
            sql = self._SQL_FALTAS_PERDA_AVO_DECIMO.format(**filtro_afastamento)
            cr.execute(sql)
            dados_falta = cr.fetchall()
            meses_falta = len(dados_falta)

            if meses > 0:
                meses -= meses_falta

                if meses < 0:
                    meses = 0

            #print(data_final, data_inicial, meses)
            valor_proporcional = 0

            holerite_obj = None
            if (calcula or soh_busca_valor) and meses > 0:
                dados = {
                    'employee_id': contrato_obj.employee_id.id,
                    'contract_id': contrato_obj.id,
                    'struct_id': contrato_obj.struct_id.estrutura_decimo_terceiro_id.id,
                    'tipo': 'D',
                    'date_from': date_from,
                    'date_to': date_to,
                    'meses_decimo_terceiro': meses,
                    'data_inicio_periodo_aquisitivo': str(data_inicial),
                    'data_fim_periodo_aquisitivo': str(data_final),
                    'simulacao': True,
                    'media_inclui_mes': inclui_mes or False,
                    'ano': str(date_from)[:4],
                    'mes': str(date_from)[5:7],
                    'dias_aviso_previo': dias_aviso_previo,
                }

                if data_rescisao:
                    dados['data_fim_periodo_aquisitivo'] = data_rescisao
                #print(dados)

                if mantem_calculo:
                    busca = [
                        ('contract_id', '=', contrato_obj.id),
                        ('tipo', '=', 'D'),
                        ('simulacao', '=', True),
                        ('date_from', '=', date_from),
                        ('date_to', '=', date_to),
                    ]
                    hids = holerite_pool.search(cr, uid, busca)

                    #print(hids, 'encontrados')

                    if len(hids):
                        holerite_id = hids[0]
                    else:
                        holerite_id = holerite_pool.create(cr, uid, dados)
                else:
                    holerite_id = holerite_pool.create(cr, uid, dados)

                holerite_obj = holerite_pool.browse(cr, uid, holerite_id)
                if not soh_busca_valor:
                    holerite_obj.write({'simulacao': True, 'media_inclui_mes': inclui_mes})
                    holerite_obj.compute_sheet()
                #cr.commit()

                #
                # Depois do cálculo, pega o valor Bruto
                #
                for linha_holerite_obj in holerite_obj.line_ids:
                    if linha_holerite_obj.code == 'BRUTO':
                        valor_proporcional += linha_holerite_obj.total

                #print(valor_proporcional)
                if not mantem_calculo:
                    holerite_obj.unlink()

            if retorna_datas:
                res[contrato_obj.id] = [meses, data_inicial, data_final]
            else:
                res[contrato_obj.id] = [meses, valor_proporcional]

            if mantem_calculo:
                if holerite_obj:
                    res[contrato_obj.id].append(holerite_obj.id)
                else:
                    res[contrato_obj.id].append(None)

        if len(ids) == 1:
            res = res.values()[0]

        #print('calculou e vai retornar', res)

        return res

    def folha_complementar(self, cr, uid, ids, data_inicial, data_final, tipo='N', dias_ferias=30, context={}):
        res = {}
        holerite_pool = self.pool.get('hr.payslip')
        holerite_line_pool = self.pool.get('hr.payslip.line')

        for contrato_obj in self.browse(cr, uid, ids):
            #
            # Buscamos se houve reajuste marcado para gerar folha complementar
            # no período
            #
            sql = """
                select
                    rs.data,
                    rs.valor,
                    rs.arredondamento

                from
                    hr_reajuste_salarial rs
                    join hr_reajuste_salarial_contrato rsc on rsc.reajuste_salarial_id = rs.id

                where
                    cast(rs.data_confirmacao at time zone 'UTC' at time zone 'America/Sao_Paulo' as date) between '{data_inicial}' and '{data_final}'
                    and rs.confirmado = True
                    and rs.gerar_folha_complementar = True
                    and rsc.contrato_id = {contract_id}

                order by
                    rs.data_confirmacao desc

                limit 1;
            """

            sql = sql.format(data_inicial=str(data_inicial), data_final=str(data_final), contract_id=contrato_obj.id)
            cr.execute(sql)
            reajuste = cr.fetchall()

            if not len(reajuste):
                return False

            data_reajuste, valor_reajuste, arredondamento = reajuste[0]

            #
            # Busca agora a folha fechada do período da data do reajuste até
            # a data inicial
            #
            if tipo == 'N':
                holerite_ids = holerite_pool.search(cr, uid, [('simulacao', '=', False), ('state', '=', 'done'), ('tipo', '=', tipo), ('contract_id', '=', contrato_obj.id), ('date_from', '>=', data_reajuste), ('date_to', '<', str(data_inicial))])
            else:
                #holerite_ids = holerite_pool.search(cr, uid, [('simulacao', '=', False), ('state', '=', 'done'), ('tipo', '=', tipo), ('contract_id', '=', contrato_obj.id), ('date_from', '>=', data_reajuste), ('date_from', '<', str(data_inicial))])
                holerite_ids = holerite_pool.search(cr, uid, [('simulacao', '=', False), ('state', '=', 'done'), ('tipo', '=', tipo), ('contract_id', '=', contrato_obj.id), ('date_from', '<=', data_reajuste), ('date_to', '>=', data_reajuste)])

            print('periodo', holerite_ids)

            valor_complementar = D(0)

            for holerite_obj in holerite_pool.browse(cr, uid, holerite_ids):
                busca = [
                    ('contract_id', '=', contrato_obj.id),
                    ('tipo', '=', tipo),
                    ('simulacao', '=', True),
                    ('complementar', '=', True),
                    ('date_from', '=', str(holerite_obj.date_from)),
                    ('date_to', '=', str(holerite_obj.date_to)),
                ]
                hids = holerite_pool.search(cr, uid, busca)

                if len(hids):
                    complemento_id = hids[0]
                else:
                    dados = {
                        'company_id': holerite_obj.company_id.id,
                        'employee_id': contrato_obj.employee_id.id,
                        'contract_id': contrato_obj.id,
                        'struct_id': holerite_obj.struct_id.id,
                        'tipo': tipo,
                        'date_from': holerite_obj.date_from,
                        'date_to': holerite_obj.date_to,
                        'meses_decimo_terceiro': holerite_obj.meses_decimo_terceiro,
                        'data_inicio_periodo_aquisitivo': holerite_obj.data_inicio_periodo_aquisitivo,
                        'data_fim_periodo_aquisitivo': holerite_obj.data_fim_periodo_aquisitivo,
                        'simulacao': True,
                        'complementar': True,
                        'ano': holerite_obj.ano,
                        'mes': holerite_obj.mes,
                        'abono_pecuniario_ferias': holerite_obj.abono_pecuniario_ferias,
                        'dias_ferias': holerite_obj.dias_ferias,
                        'data_aviso_ferias': holerite_obj.data_aviso_ferias,
                    }
                    complemento_id = holerite_pool.create(cr, uid, dados)


                #
                # Quando for férias, tem que haver o proporcional do abono e das férias
                #
                if tipo == 'F':
                    proporcao = D(dias_ferias) / D(holerite_obj.dias_ferias)
                    proporcao_abono = D(0)

                    if holerite_obj.abono_pecuniario_ferias:
                        data_inicial_abono = parse_datetime(holerite_obj.date_to).date()
                        data_inicial_abono += relativedelta(days=1)
                        data_final_abono = parse_datetime(holerite_obj.date_to).date()
                        data_final_abono += relativedelta(days=10)

                        if str(data_inicial_abono) < data_inicial:
                            data_inicial_abono = parse_datetime(data_inicial_abono).date()

                        print('data_inicial_abono, data_final')
                        print(data_inicial_abono, data_final)

                        if str(data_inicial_abono) <= data_final:
                            if str(data_final_abono) > data_final:
                                data_final_abono = parse_datetime(data_final).date()

                            dias_abono = data_final_abono - data_inicial_abono

                            if dias_abono.days:
                                dias_abono = dias_abono.days + 1
                                proporcao_abono = D(dias_abono) / D(10)

                #
                # Exclui os cálculos do complemento
                #
                complemento_obj = holerite_pool.browse(cr, uid, complemento_id)
                for linha_obj in complemento_obj.line_ids:
                    linha_obj.unlink()

                for linha_obj in holerite_obj.line_ids:
                    if linha_obj.sinal != '+':
                        continue

                    if linha_obj.holerite_anterior_line_id:
                        continue

                    if linha_obj.code in ['SALFAM']:
                        continue

                    dados = {
                        'salary_rule_id': linha_obj.salary_rule_id.id,
                        'contract_id': linha_obj.contract_id.id,
                        'name': linha_obj.name,
                        'code': linha_obj.code,
                        'category_id': linha_obj.category_id.id,
                        'sequence': linha_obj.sequence,
                        'appears_on_payslip': linha_obj.appears_on_payslip,
                        'condition_select': linha_obj.condition_select,
                        'condition_python': linha_obj.condition_python,
                        'condition_range': linha_obj.condition_range,
                        'condition_range_min': linha_obj.condition_range_min,
                        'condition_range_max': linha_obj.condition_range_max,
                        'amount_select': linha_obj.amount_select,
                        'amount_fix': linha_obj.amount_fix,
                        'amount_python_compute': linha_obj.amount_python_compute,
                        'amount_percentage': linha_obj.amount_percentage,
                        'amount_percentage_base': linha_obj.amount_percentage_base,
                        'register_id': linha_obj.register_id.id,
                        'amount': linha_obj.amount,
                        'employee_id': linha_obj.employee_id.id,
                        'quantity': linha_obj.quantity,
                        'rate': linha_obj.rate,
                        'total': linha_obj.total,
                        'digitado': linha_obj.digitado,
                        'digitado_media': linha_obj.digitado_media,
                        'sinal': linha_obj.sinal,
                        'slip_id': complemento_obj.id,
                    }

                    valor = D(linha_obj.amount)
                    total = D(linha_obj.total)

                    #valor_novo = valor
                    #total_novo = total
                    valor_novo = valor * (D(1) + (D(valor_reajuste) /  D(100)))
                    valor_novo = valor_novo.quantize(D('0.01'), arredondamento or decimal.ROUND_HALF_EVEN)

                    if linha_obj.digitado:
                        total_novo = total * (D(1) + (D(valor_reajuste) /  D(100)))
                        total_novo = total_novo.quantize(D('0.01'), arredondamento or decimal.ROUND_HALF_EVEN)

                    else:
                        valor_novo = valor * (D(1) + (D(valor_reajuste) /  D(100)))
                        valor_novo = valor_novo.quantize(D('0.01'), arredondamento or decimal.ROUND_HALF_EVEN)

                        total_novo = valor_novo * D(linha_obj.quantity)
                        total_novo *= D(linha_obj.rate) / D(100)
                        total_novo = total_novo.quantize(D('0.01'))

                    if tipo == 'F':
                        #print('antes', linha_obj.code)
                        if 'ABONO' in linha_obj.code:
                            #print('abono', proporcao_abono, valor, total)
                            valor_novo *= proporcao_abono
                            total_novo *= proporcao_abono
                            valor *= proporcao_abono
                            total *= proporcao_abono
                            #print('depois', linha_obj.code)
                            #print('abono', proporcao_abono, valor, valor_novo, total, total_novo)

                        else:
                            #print('normal', proporcao, valor, total)
                            valor_novo *= proporcao
                            total_novo *= proporcao
                            valor *= proporcao
                            total *= proporcao
                            #print('depois', linha_obj.code)
                            #print('normal', proporcao, valor, valor_novo, total, total_novo)

                        dados['amount'] = valor
                        dados['total'] = total

                    diferenca = total_novo - total
                    valor_complementar += diferenca

                    dados['valor_novo'] = valor_novo
                    dados['total_novo'] = total_novo
                    dados['diferenca'] = diferenca

                    holerite_line_pool.create(cr, uid, dados)

            res[contrato_obj.id] = valor_complementar

        if len(ids) == 1:
            res = res.values()[0]

        return res

    def gerar_etiquetas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Lote Etiquetas', cr, uid)
        etiqueta_obj = self.browse(cr, uid, id)

        if not etiqueta_obj.mes:
            raise osv.except_osv(u'Inválido!', u'Campo mês Obrigatório!')


        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'etiqueta_empregado.jrxml')
        etiqueta = u'etiqueta_empregado.pdf'
        rel.parametros['DATA_ANO'] = str(etiqueta_obj.mes) +"/"+ str(etiqueta_obj.ano)
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        dados = {
                'nome': etiqueta,
                'arquivo': base64.encodestring(pdf)
        }
        etiqueta_obj.write(dados)
        return True

    def gerar_etiqueta_unica(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Lote Etiquetas', cr, uid)
        etiqueta_obj = self.browse(cr, uid, id)


        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'etiqueta_empregado_unico.jrxml')
        etiqueta = u'etiqueta_empregado.pdf'
        rel.parametros['DATA_ANO'] = str(etiqueta_obj.mes) +"/"+ str(etiqueta_obj.ano)
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'

        pdf, formato = rel.execute()

        dados = {
                'nome': etiqueta,
                'arquivo': base64.encodestring(pdf)
        }
        etiqueta_obj.write(dados)
        return True

    def create(self, cr, uid, dados, context={}):

        if 'company_id' in dados and dados['company_id']:
                company_id =  dados['company_id']

                company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

                cr.execute("""
                            select
                            coalesce(max(cast(co.name as integer)), 1) as id

                            from hr_contract co
                            join res_company c on c.id = co.company_id

                            where c.cnpj_cpf = '""" + str(company_obj.cnpj_cpf) + """'
                            and co.data_transf is null
                            ;""")


                for ret in cr.fetchall():
                    name_id = ret[0]

                name = str(name_id + 1).zfill(6)

                dados['name'] = name


        return super(hr_contract, self).create(cr, uid, dados, context)


    def copy(self, cr, uid, ids, dados, context={}):
        dados['falta_ids'] = False

        contrato_obj = self.browse(cr, uid, ids)
        dados['data_transf'] = contrato_obj.date_end
        dados['contrato_transf_id'] = contrato_obj.id

        dados['date_end'] = False
        dados['holerite_ids'] = False
        dados['mes'] = '01'

        #
        # Próxima matrícula
        #
        cr.execute('select max(id) + 1 from hr_contract;')
        matricula = cr.fetchall()

        dados['name'] = str(matricula[0][0])
        #dados['descricao'] = False
        #dados['salario'] = False

        return super(hr_contract, self).copy(cr, uid, ids, dados, context)
            #'holerite_ids': fields.one2many('hr.payslip', 'contract_id', string=u'Holerites'),
        #'holerite_ferias_ids': fields.one2many('hr.payslip', 'contract_id', string=u'Holerites de férias', domain=[('tipo', '=', 'F')]),
        #'ferias_ids': fields.one2many('hr.contract_ferias', 'contract_id', string=u'Controle de férias'),
        #'falta_ids': fields.one2many('hr.falta', 'contract_id', string=u'Faltas'),

    def calcula_data_aviso_previo(self, cr, uid, ids, data_aviso_previo, dispensa_empregador, context={}):

        for contrato_obj in self.browse(cr, uid, ids):
            data_admissao = parse_datetime(contrato_obj.date_start).date()
            data_aviso_previo = parse_datetime(data_aviso_previo).date()

            dias_aviso = 30
            idade_contrato = idade(data_admissao, data_aviso_previo)

            if dispensa_empregador:
                #
                # 30 dias corridos, incluindo o próprio dia do aviso
                # 3 dias a mais para cada ano trabalhado, com
                # limite até 90 dias
                #

                if len(contrato_obj.company_id.avisoprevioproporcional_ids) > 0:
                    avisoproporcional_obj = contrato_obj.company_id.avisoprevioproporcional_ids[0]
                    for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                        if item_aviso_proporcional_obj.anos == idade_contrato:
                            dias_aviso = item_aviso_proporcional_obj.dias - 1

                    data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
                    nova_idade_contrato = idade(data_admissao, data_final)

                    if nova_idade_contrato != idade_contrato:
                        for item_aviso_proporcional_obj in avisoproporcional_obj.avisoprevioproporcional_item_ids:
                            if item_aviso_proporcional_obj.anos == nova_idade_contrato:
                                dias_aviso = item_aviso_proporcional_obj.dias - 1

                else:
                    dias_aviso = 30 + (3 * idade_contrato)

                    if dias_aviso > 90:
                        dias_aviso = 90
                    #
                    # Tira 1 dia pq o dia do próprio aviso conta
                    #
                    dias_aviso -= 1

                    data_final = data_aviso_previo + relativedelta(days=+dias_aviso)

                    #
                    # Verifica se a data de afastamento vai dar mais 1 ano no contrato
                    #
                    nova_idade_contrato = idade(data_admissao, data_final)

                    if nova_idade_contrato != idade_contrato:
                        dias_aviso += 3

                        if dias_aviso > 90:
                            dias_aviso = 89

            #if cr.dbname.upper() == 'PATRIMONIAL':
                #data_final = data_aviso_previo + relativedelta(days=+dias_aviso)
            #else:
                #data_final = data_aviso_previo + relativedelta(days=+dias_aviso+1)
            data_final = data_aviso_previo + relativedelta(days=+dias_aviso+1)

            data_inicial = primeiro_ultimo_dia_mes(data_final.year, data_final.month)[0]
            dias_aviso += 1
            data_afastamento = data_final

            return data_inicial, data_final, dias_aviso, data_afastamento

    def calcula_aviso_previo(self, cr, uid, ids, data_inicio_aviso, data_termino_aviso, dias_aviso, context={}):
        holerite_pool = self.pool.get('hr.payslip')

        valor = D(0)
        for contrato_obj in self.browse(cr, uid, ids):
            dados = {
                'tipo': 'A',
                'simulacao': True,
                'provisao': False,
                'employee_id': contrato_obj.employee_id.id,
                'contract_id': contrato_obj.id,
                'struct_id': contrato_obj.struct_id.id,
                'date_from': str(parse_datetime(data_inicio_aviso).date() + relativedelta(days=+1)),
                'date_to': data_termino_aviso,
                'dias_saldo_salario': dias_aviso,
                'dias_aviso_previo': dias_aviso,
            }

            #
            # Verifica se já existe uma simulação anterior
            #
            busca = [
                ['simulacao', '=', True],
                ['employee_id', '=', contrato_obj.employee_id.id],
                ['contract_id', '=', contrato_obj.id],
                ['tipo', '=', 'A'],
            ]

            holerite_id = holerite_pool.search(cr, uid, busca)

            if holerite_id:
                holerite_obj = holerite_pool.browse(cr, uid, holerite_id[0])
            else:
                holerite_id = holerite_pool.create(cr, uid, dados)
                holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            holerite_obj.write(dados)
            holerite_obj.compute_sheet()

            #
            # Depois do cálculo, pega o valor Bruto
            #
            for linha_holerite_obj in holerite_obj.line_ids:
                if linha_holerite_obj.code == 'BRUTO':
                    valor = D(linha_holerite_obj.total or 0)

        return valor, holerite_obj.id

    def gera_ficha_registro(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        contract_id = rel_obj.id

        rel = Report('Ficha Registro Funcionário', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_ficha_registro_empregado.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(contract_id) + ')'
        recibo = 'hr_ficha_registro_empregado.pdf',

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.contract'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'hr_ficha_registro_empregado.pdf',
            'datas_fname': 'hr_ficha_registro_empregado.pdf',
            'res_model': 'hr.contract',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

hr_contract()


class hr_exame(osv.Model):
    _name = 'hr.exame'
    _description = 'Exames'
    _rec_name = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição do Exame', size=80, required=True),
        'validade': fields.integer('validade em meses', size=3, required=True),
    }


hr_exame()


class hr_contract_exame(osv.Model):
    _name = 'hr.contract_exame'
    _description = 'Exames'
    #_rec_name = 'exame_id'

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'data_exame': fields.date(u'Data do exame'),
        'exame_id': fields.many2one('hr.exame', u'Exame'),
        'data_validade': fields.date(u'Data de validade'),
    }

    def onchange_data_exame(self, cr, uid, ids, data_exame, exame_id, context={}):
        if not data_exame:
            return {}

        if not exame_id:
            return {}

        exame_pool = self.pool.get('hr.exame')
        exame_obj = exame_pool.browse(cr, uid, exame_id)

        retorno = {}
        valores = {}
        retorno['value'] = valores
        data_exame = parse_datetime(data_exame).date() + relativedelta(months=+exame_obj.validade)
        valores['data_validade'] = str(data_exame)
        return retorno


hr_contract_exame()

class hr_curso_treinamento(osv.Model):
    _name = 'hr.curso.treinamento'
    _description = 'Cursos e Treinamentos'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Nome', size=120),
    }

hr_curso_treinamento()


PERIODO_CURSO = [
    ('1',u'Cursando'),
    ('2', u'Suspenso'),
    ('3', u'Concluído'),
]

class hr_contract_curso_treinamento(osv.Model):
    _name = 'hr.contract.curso.treinamento'
    _description = 'Contrato Cursos e Treinamentos'
    _rec_name = 'curso_id'
    _order = 'data_inicial desc'

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'curso_id': fields.many2one('hr.curso.treinamento', u'Curso'),
        'carga_horaria': fields.float(u'Carga horária'),
        'data_inicial': fields.date(u'Périodo de'),
        'data_final': fields.date(u'Até'),
        'situacao': fields.selection(PERIODO_CURSO, u'Situação'),
    }

    _defaults = {

    }

hr_contract_curso_treinamento()


class hr_contract_regra(osv.Model):
    _name = 'hr.contract_regra'
    _description = u'Regras de salário por contrato'
    #_rec_name = 'descricao'

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'data_inicial': fields.date('Data de início'),
        'data_final': fields.date('Data de término'),
        'quantidade': fields.float(u'Quantidade específica'),
        'porcentagem': fields.float(u'Porcentagem específica'),
        'valor': fields.float(u'Valor específico'),
        #'descricao': fields.char(u'Descrição do exame', size=80),
    }

    _defaults = {
        'porcentagem': 100,
    }


hr_contract_regra()


class hr_contract_ferias(osv.Model):
    _name = 'hr.contract_ferias'
    _description = u'Controle de férias por contrato'
    _order = 'contract_id, employee_id, data_inicial_periodo_aquisitivo desc, data_final_periodo_aquisitivo desc, data_inicial_periodo_gozo desc, data_final_periodo_gozo desc'
    _rec_name = 'descricao'

    def _data_final_periodo_aquisitivo_cheio(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for ferias_obj in self.browse(cr, uid, ids):
            if nome_campo == 'data_final_periodo_aquisitivo_cheio':
                data_ini = parse_datetime(ferias_obj.data_inicial_periodo_aquisitivo).date()

            data_fim = data_ini + relativedelta(years=+1, days=-1)
            res[ferias_obj.id] = str(data_fim)

        return res

    def _meses_vencida(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for ferias_obj in self.browse(cr, uid, ids):
            res[ferias_obj.id] = 0

            if ferias_obj.data_inicial_periodo_concessivo < str(hoje_brasil()):
                res[ferias_obj.id] = idade_meses(parse_datetime(ferias_obj.data_inicial_periodo_concessivo), hoje_brasil(), quinze_dias=True)

            if res[ferias_obj.id] < 0:
                res[ferias_obj.id] = 0

        return res

    def _get_descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for ferias_obj in self.browse(cr, uid, ids):
            nome = ferias_obj.employee_id.nome or u''
            nome += ', aquis. de '
            nome += formata_data(parse_datetime(ferias_obj.data_inicial_periodo_aquisitivo))
            nome += u' a '
            nome += formata_data(parse_datetime(ferias_obj.data_final_periodo_aquisitivo))

            if ferias_obj.data_inicial_periodo_gozo:
                nome += u', gozada de '
                nome += formata_data(parse_datetime(ferias_obj.data_inicial_periodo_gozo))
                nome += u' a '
                nome += formata_data(parse_datetime(ferias_obj.data_final_periodo_gozo))

            elif ferias_obj.vencida:
                nome += u', vencida há '

                nome += str(ferias_obj.meses_vencida)

                if ferias_obj.meses_vencida == 1:
                    nome += u' mês'
                else:
                    nome += u' meses'

                if ferias_obj.pagamento_dobro:
                    nome += u', paga em dobro'

            elif ferias_obj.proporcional:
                nome += u', proporcional em '
                nome += str(ferias_obj.avos)
                nome += u'/12 avos'

            elif ferias_obj.perdido_afastamento:
                nome += u', perdida por afastamento de '
                nome += str(ferias_obj.afastamentos)
                nome += u' dias'

            res[ferias_obj.id] = nome

        return res

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True),
        'employee_id': fields.related('contract_id', 'employee_id', type='many2one', relation='hr.employee', string=u'Funcionário', store=True),
        'data_inicial_periodo_aquisitivo': fields.date(u'Início período aquisitivo'),
        'data_final_periodo_aquisitivo': fields.date(u'Fim período aquisitivo'),
        'data_final_periodo_aquisitivo_cheio': fields.function(_data_final_periodo_aquisitivo_cheio, type='date', string=u'Fim período aquisitivo', method=True, store=True),
        'data_inicial_periodo_concessivo': fields.date(u'Início período concessivo'),
        'data_final_periodo_concessivo': fields.date(u'Fim período concessivo'),
        'data_inicial_periodo_gozo': fields.date(u'Início período gozo'),
        'data_final_periodo_gozo': fields.date(u'Fim período gozo'),
        'data_aviso': fields.date(u'Data do aviso'),
        'data_limite_pagamento': fields.date(u'Limite para pagamento'),
        'data_limite_gozo': fields.date(u'Limite para gozo'),
        'data_limite_aviso': fields.date(u'Limite para aviso'),
        'pagamento_dobro': fields.boolean(u'Pagamento em dobro?'),
        'faltas': fields.integer(u'Faltas'),
        'afastamentos': fields.integer(u'Afastamentos'),
        'dias': fields.integer(u'Dias'),
        'saldo_dias': fields.float(u'Saldo'),
        'avos': fields.integer(u'Avos'),
        'proporcional': fields.boolean(u'Proporcional?'),
        'vencida': fields.boolean(u'Vencida?'),
        'perdido_afastamento': fields.boolean(u'Perdido por afastamento?'),
        'meses_vencida': fields.function(_meses_vencida, type='integer', string=u'Meses vencida', method=True),
        'descricao': fields.function(_get_descricao, type='char', size=250, string=u'Controle de férias', method=True),
        'abono': fields.boolean(u'Abono'),
        #'situacao': fields.selection('', )
    }

    _defaults = {
        'faltas': 0,
        'afastamentos': 0,
        'dias': 0,
        'saldo_dias': 0,
        'avos': 0,
        'proporcional': False,
        'pagamento_dobro': False,
        'vencida': False,
        'perdido_afastamento': False,
    }


hr_contract_ferias()
