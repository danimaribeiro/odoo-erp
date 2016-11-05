# -*- coding: utf-8 -*-

from tools import config
from osv import fields, osv
import base64
from jasper_reports.JasperReports import *
from pybrasil.data import parse_datetime, MES_ABREVIADO, hoje, agora,data_hora_horario_brasilia, formata_data, tempo
from dateutil.relativedelta import relativedelta
from pybrasil.base import DicionarioBrasil
from relatorio import *
from pybrasil.valor.decimal import Decimal as D
from collections import OrderedDict

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


# Determines the port where the JasperServer process should listen with its XML-RPC server for incomming calls
config['jasperport'] = config.get('jasperport', 8090)

# Determines the file name where the process ID of the JasperServer process should be stored
config['jasperpid'] = config.get('jasperpid', 'openerp-jasper.pid')

# Determines if temporary files will be removed
config['jasperunlink'] = config.get('jasperunlink', False)

config['relatorio_integra'] = config.get('relatorio_integra', 'http://live.erpintegra.com.br:8237/')


class Report(object):
    def __init__(self, name, cr, uid):
        self.name = name
        self.cr = cr
        self.uid = uid
        self.caminho_arquivo_jasper = None
        self.relatorio = None
        self.temporaryFiles = []
        self.outputFormat = 'pdf'
        self.parametros = {}

    def execute(self):
        """
        If self.context contains "return_pages = True" it will return the number of pages
        of the generated report.
        """
        logger = logging.getLogger(__name__)
        logger.info("Requested report: '%s'" % self.caminho_arquivo_jasper)
        self.relatorio = JasperReport(self.caminho_arquivo_jasper)

        fd, outputFile = tempfile.mkstemp()
        os.close(fd)

        import time
        start = time.time()

        self.temporaryFiles.append(outputFile)
        numero_paginas = self.executeReport(outputFile)
        elapsed = (time.time() - start) / 60
        logger.info("ELAPSED: %f" % elapsed)

        # Read data from the generated file and return it
        f = open(outputFile, 'rb')
        try:
            data = f.read()
        finally:
            f.close()

        # Remove all temporary files created during the report
        if config['jasperunlink']:
            for arquivo in self.temporaryFiles:
                try:
                    os.unlink(arquivo)
                except:
                #except os.error, e:
                    pass
                    #logger.warning("Could not remove file '%s'." % file )
        self.temporaryFiles = []

        return (data, self.outputFormat)

    def path(self):
        return os.path.abspath(os.path.dirname(__file__))

    def systemUserName(self):
        if os.name == 'nt':
            import win32api
            return win32api.GetUserName()
        else:
            import pwd
            return pwd.getpwuid(os.getuid())[0]

    def dsn(self):
        host = config['db_host'] or 'localhost'
        port = config['db_port'] or '5432'
        dbname = self.cr.dbname

        if host.startswith('/'):
            return 'jdbc:postgresql:%s' % dbname
        else:
            return 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )

    def userName(self):
        return config['db_user'] or self.systemUserName()

    def password(self):
        return config['db_password'] or ''

    def executeReport(self, outputFile):
        parametros_conexao = {
            'output': self.outputFormat,
            #'xml': dataFile,
            #'csv': dataFile,
            'dsn': self.dsn(),
            'user': self.userName(),
            'password': self.password(),
            #'subreports': subreportDataFiles,
        }
        self.parametros.update({
            'STANDARD_DIR': self.relatorio.standardDirectory(),
            'REPORT_LOCALE': 'pt_BR',
            #'REPORT_TIME_ZONE': 'America/Sao_Paulo',
            #'IDS': self.ids,
            'UID': self.uid,
            'REPORT_NAME': self.name,
        })

        for chave in self.parametros:
            if chave.startswith('SQL_'):
                while '  ' in self.parametros[chave]:
                    self.parametros[chave] = self.parametros[chave].replace('  ', ' ')

        #print(self.parametros)

        server = JasperServer(int(config['jasperport']))
        server.setPidFile(config['jasperpid'])
        return server.execute(parametros_conexao, self.caminho_arquivo_jasper, outputFile, self.parametros)


SITUACAO = [
    ('1', 'Vencido'),
    ('2', 'Vencido + Hoje'),
    ('3', 'A Vencer'),
    ('4', 'Todos em aberto'),
    ('5', 'Liquidadas'),
    ('6', 'Registrados'),
]

PERIODO = [
     ('1',u'Mensal'),
     ('2', u'Diário'),
     ('3', u'Analítico'),
     #('4', u'Sintético por conta financeira'),
]

OPCOES_CAIXA = [
     ('1', 'Realizado'), #data quitação
     ('2', 'Comprometido(realizado + realizar)'),
     ('3', 'A realizar'), #data vencimento
]

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('xls', u'XLS'),
)

TIPO_NOTAS = [
     ('1', 'Analítico'),
     ('2', 'Sintetico'),
]

TIPO_REL = [
     ('0', 'Analítico'),
     ('1', 'Sintetico'),
]

TIPO_RAZAO = [
    ('1','Clientes'),
    ('2','Fornecedores'),
]

class finan_relatorio(osv.osv_memory):
    _name = 'finan.relatorio'
    _description = u'Relatórios Financeiros'

    _columns = {
        'situacao': fields.selection(SITUACAO, u'Situação'),
        'tipo_razao': fields.selection(TIPO_RAZAO, u'Tipo'),
        'tempo_vencimento': fields.integer(u'Intervalo de vencimento', size=3),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'nome': fields.char(u'Nome do arquivo', 254, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 254, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
        'periodo': fields.selection(PERIODO, u'Período'),
        'opcoes_caixa': fields.selection(OPCOES_CAIXA, u'Opções'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
        'provisionado': fields.boolean(u'Provisionado'),
        'ativo': fields.boolean(u'Ativos'),
        'zera_saldo': fields.boolean(u'Zerar Saldo Anterior?'),
        'saldo': fields.boolean(u'Saldo?'),
        'saldo_bancario': fields.boolean(u'Considerar Saldo Bancário?'),
        'tipo': fields.selection(TIPO_NOTAS, u'Tipo'),
        'tipo_rel': fields.selection(TIPO_REL, u'Tipo'),
        'conta_id': fields.many2one('finan.conta', u'Conta financeira'),
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro Custo'),
        'res_partner_bank_ids': fields.many2many('res.partner.bank','finan_partner_banks', 'finan_relatorio_id', 'res_partner_bank_id', string=u'Contas Bancárias'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária'),
        'categoria_id': fields.many2one('res.partner.category', u'Categoria'),
        'filtrar_rateio': fields.boolean(u'Usar rateios?'),
        'project_id': fields.many2one('project.project', u'Projeto'),
        'formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'total_empresa': fields.boolean(u'Totalizar Empresas'),
        'company_2_id': fields.many2one('res.company', u'Empresa 2'),
        'motivo_baixa_id': fields.many2one('finan.motivobaixa', u'Motivo para a baixa', select=True),
        'nao_provisionado': fields.boolean(u'Não provisionado'),
        'sem_nf': fields.boolean(u'Doc.Sem NF'),
        'data_entrada_nf': fields.boolean(u'Considerar Data Entr.NF'),
        'partner_ids': fields.many2many('res.partner', 'finan_relatorio_partners', 'finan_relatorio_id','partner_id', string=u'Clientes/Fornecedores'),
        'por_data': fields.boolean(u'Por Data'),
        'saldo_inicial': fields.float(u'Saldo inicial'),
        'company_ids': fields.many2many('res.company','finan_relatorio_company', 'finan_relatorio_id', 'company_id', string=u'Empresas'),
        'documento_ids': fields.many2many('finan.documento','finan_relatorio_documento', 'finan_relatorio_id', 'documento_id', string=u'Tipo Documento'),
        'somente_totais': fields.boolean(u'Imprimir Somente os Totais'),
        'imprime_cheque': fields.boolean(u'Imprimir Totais Cheque'),
        'dias_atraso': fields.integer(u'Dias de Atraso'),
        'agrupa_data_vencimento': fields.boolean(u'Agrupar por Data de Vencimento?'),
        'conf_contabilidade': fields.boolean(u'Para Conferência Contabilidade?'),
        'sem_projeto': fields.boolean(u'Somente Rateio Sem projeto?'),
        'sem_centrocusto': fields.boolean(u'Somente Rateio Sem Centro de Custo?'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
        'nome': '',
        'tempo_vencimento': 0,
        'formato': 'pdf',
        'provisionado': False,
        'nao_provisionado': True,
        'ativo': True,
        'tipo_rel': '0',
        'total_empresa': False,
        'sem_nf': False,
        'por_data': False,
        'conf_contabilidade': False,
    }


    ###def gera_relatorio_fluxo_caixa_analitico(self, cr, uid, ids, context={}):
        ###if not ids:
            ###return False

        ###company_id = context['company_id']
        ###data_inicial = context['data_inicial']
        ###data_final = context['data_final']
        ###provisionado = context.get('provisionado')


        ###id = ids[0]
        ###rel_obj = self.browse(cr, uid, id)
        ###data_inicial = parse_datetime(rel_obj.data_inicial).date()
        ###data_final = parse_datetime(rel_obj.data_final).date()

        ###filtro = {
            ###'company_id': company_id,
            ###'data_inicial': data_inicial,
            ###'data_final': data_final,
            ###'rateio': '',
        ###}

        ###rel = Report('Fluxo de Caixa', cr, uid)
        ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_mensal_diario.jrxml')
        ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        ###rel.outputFormat = rel_obj.formato

        ###if company_id:
            ###rel.parametros['COMPANY_ID'] = str(company_id)
        ###else:
            ###company_id_default = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')
            ###rel.parametros['COMPANY_ID'] = '%'

        ###if rel_obj.opcoes_caixa == '1':
            ###filtro['tipo'] = "('Q')"
            ###rel.parametros['TIPO'] = "('Q')"
        ###elif rel_obj.opcoes_caixa == '2':
            ###filtro['tipo'] = "('Q','V')"
            ###rel.parametros['TIPO'] = "('Q','V')"
        ###else:
            ###filtro['tipo'] = "('V')"
            ###rel.parametros['TIPO'] = "('V')"

        ####
        #### SALDO ANTERIOR
        ####

        ###sql_saldo = """
                ###select
                    ###sum(f.valor_entrada) - sum(f.valor_saida) as diferenca
                ###from
                    ###finan_fluxo_mensal_diario f
                ###where
                    ###f.data  < '{data_inicial}'
                    ###and f.tipo in {tipo} """
        ###if company_id:
                ###sql_saldo += """
                    ###and
                        ###f.company_id = {company_id} """

        ###if rel_obj.nao_provisionado != rel_obj.provisionado:
            ###sql_saldo += """
                    ###and f.provisionado = """ + str(provisionado)


        ###sql_saldo = sql_saldo.format(**filtro)
        ###print(sql_saldo)
        ###saldo_anterior = 0
        ###cr.execute(sql_saldo)
        ###dados = cr.fetchall()

        ###if len(dados) > 0:
            ###print(dados)
            ###if dados[0][0]:
                ###saldo_anterior += dados[0][0]

        ###rel.parametros['SALDO_ANTERIOR'] = saldo_anterior

        ####
        #### FLUXO CAIXA
        ####

        ###if rel_obj.periodo == '1':
            ###sql_relatorio = """
                ###select
                    ###f.mes,"""
        ###else:
            ###sql_relatorio = """
                ###select
                    ###f.data,"""

        ###sql_relatorio += """
                    ###sum(f.valor_entrada {rateio}) as valor_entrada,
                    ###sum(f.valor_saida {rateio}) as valor_saida,
                    ###sum(f.valor_entrada {rateio}) - sum(f.valor_saida {rateio}) as diferenca"""

        ###if rel_obj.periodo == '3':
            ###sql_relatorio += """,
                    ###fd.nome,
                    ###fl.tipo,
                    ###rp.name"""

        ###if rel_obj.filtrar_rateio:
            ###sql_relatorio += """,
                    ###a.name as projeto"""


        ###sql_relatorio += """
                ###from
                    ###finan_fluxo_mensal_diario f
                    ###join res_company c on c.id = f.company_id
                    ###left join res_company cc on cc.id = c.parent_id
                    ###left join res_company ccc on ccc.id = cc.parent_id
                    ###join finan_lancamento fl on fl.id = f.lancamento_id
                    ###left join res_partner rp on rp.id = fl.partner_id
                    ###left join finan_documento fd on fd.id = fl.documento_id"""

        ###if rel_obj.filtrar_rateio:
            ###sql_relatorio += """
                    ###join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = f.lancamento_id
                    ###left join project_project pp on pp.id = lr.project_id
                    ###left join account_analytic_account a on a.id = pp.analytic_account_id"""


            ###filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'


        ###sql_relatorio += """

                ###where
                    ###f.data between '{data_inicial}' and '{data_final}'
                    ###and f.tipo in {tipo} """

        ###if company_id:
            ###sql_relatorio += """
                     ###and (
                       ###c.id = {company_id}
                       ###or cc.id = {company_id}
                       ###or ccc.id = {company_id}
                    ###)"""

        ###if rel_obj.nao_provisionado != rel_obj.provisionado:
            ###sql_relatorio += """
                    ###and f.provisionado = """ + str(provisionado)

        ###if rel_obj.filtrar_rateio:

            ###if rel_obj.project_id:
                    ###sql_relatorio += """
                       ###and lr.project_id = """ + str(rel_obj.project_id.id)


        ###if rel_obj.periodo == '1':
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###f.mes"""

            ###if rel_obj.filtrar_rateio:
                ###sql_relatorio += """,
                    ###a.name"""
            ###sql_relatorio += """
                ###order by
                    ###f.mes"""

        ###elif rel_obj.periodo == '2':
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###f.data"""
            ###if rel_obj.filtrar_rateio:
                ###sql_relatorio += """,
                    ###a.name"""
            ###sql_relatorio += """

                ###order by
                    ###f.data;"""

        ###else:
            ###sql_relatorio += """
                ###group by
                    ###c.id,
                    ###f.data,
                    ###fd.nome,
                    ###fl.tipo,
                    ###rp.name"""

            ###if rel_obj.filtrar_rateio:
                ###sql_relatorio += """,
                    ###a.name"""
            ###sql_relatorio += """

                ###order by
                    ###f.data,
                     ###valor_entrada desc,
                     ###valor_saida desc;"""


        ###sql = sql_relatorio.format(**filtro)
        ####print(sql)

        ###if rel_obj.periodo == '1':
            ###if rel_obj.filtrar_rateio:
                ###rel.parametros['PERIODO'] = 'MENSAL RATEIO'
                ###rel.parametros['DETALHE'] = 'fluxo_mensal_lancamento_rateio.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_mensal__rateio_'
            ###else:
                ###rel.parametros['PERIODO'] = 'MENSAL'
                ###rel.parametros['DETALHE'] = 'fluxo_mensal_lancamento.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_mensal_'

        ###elif rel_obj.periodo == '2':
            ###if rel_obj.filtrar_rateio:
                ###rel.parametros['PERIODO'] = 'DIARIO RATEIO'
                ###rel.parametros['DETALHE'] = 'fluxo_diario_lancamento_rateio.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_diario_rateio_'
            ###else:
                ###rel.parametros['PERIODO'] = 'DIARIO'
                ###rel.parametros['DETALHE'] = 'fluxo_diario_lancamento.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_diario_'

        ###else:
            ###if rel_obj.filtrar_rateio:
                ###rel.parametros['PERIODO'] = 'ANALITICO RATEIO'
                ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico_rateio.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_analitico_rateio'
            ###else:
                ###rel.parametros['PERIODO'] = 'ANALITICO'
                ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico.jasper'
                ###rel.parametros['SQL_RELATORIO'] = sql
                ###relatorio = u'fluxo_caixa_analitico_'

        ###if rel_obj.saldo_bancario:
            ###rel.parametros['SALDO_BANCO'] = True
        ###else:
            ###rel.parametros['SALDO_BANCO'] = False

        ###if rel_obj.zera_saldo:
            ###rel.parametros['ZERA_SALDO'] = True
        ###else:
            ###rel.parametros['ZERA_SALDO'] = False

        ###pdf, formato = rel.execute()

        ###dados = {
            ###'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            ###'arquivo': base64.encodestring(pdf)
        ###}
        ###rel_obj.write(dados)

        ###return True

    ###def gera_relatorio_fluxo_caixa_sintetico(self, cr, uid, ids, context={}):

        ###if not ids:
            ###return False

        ###provisionado = context.get('provisionado')

        ###id = ids[0]
        ###rel_obj = self.browse(cr, uid, id)
        ####company_id = rel_obj.company_id.id
        ###data_inicial = parse_datetime(rel_obj.data_inicial).date()
        ###data_final = parse_datetime(rel_obj.data_final).date()

        ###meses = tempo(data_inicial,data_final)
        ###print(meses)

        ###if meses.years == 1 and meses.days > 0:
            ###raise osv.except_osv(u'Atenção', u'Limite entre datas é 12 meses!')

        ###if rel_obj.filtrar_rateio:
            ###rel = Report('Fluxo de Caixa', cr, uid)
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico_rateio.jrxml')
            ###rel.parametros['PERIODO'] = 'SINTETICO RATEIO'
            ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico_rateio.jasper'
            ####rel.parametros['COMPANY_ID'] = int(company_id)
            ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            ###relatorio = u'fluxo_caixa_sintetico_conta_rateio_'
            ###rel.outputFormat = rel_obj.formato
        ###else:
            ###rel = Report('Fluxo de Caixa', cr, uid)
            ###rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico.jrxml')
            ###rel.parametros['PERIODO'] = 'SINTETICO'
            ###rel.parametros['DETALHE'] = 'fluxo_caixa_analitico.jasper'

            ####rel.parametros['COMPANY_ID'] = int(company_id)
            ###rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            ###rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            ###rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            ###relatorio = u'fluxo_caixa_sintetico_conta_'
            ###rel.outputFormat = rel_obj.formato

        ###filtro = {
            ###'data_inicial': str(data_inicial)[:10],
            ###'data_final': str(data_final)[:10],
            ###'filtro_company': '',
            ####'company_id': int(company_id),
            ####'zera_saldo': str(rel_obj.zera_saldo or False),
            ###'filtro_adicional': """''""",
            ###'titulo_01': '',
            ###'titulo_02': '',
            ###'titulo_03': '',
            ###'titulo_04': '',
            ###'titulo_05': '',
            ###'titulo_06': '',
            ###'titulo_07': '',
            ###'titulo_08': '',
            ###'titulo_09': '',
            ###'titulo_10': '',
            ###'titulo_11': '',
            ###'titulo_12': '',
            ###'ordem_01': '01',
            ###'ordem_02': '02',
            ###'ordem_03': '03',
            ###'ordem_04': '04',
            ###'ordem_05': '05',
            ###'ordem_06': '06',
            ###'ordem_07': '07',
            ###'ordem_08': '08',
            ###'ordem_09': '09',
            ###'ordem_10': '10',
            ###'ordem_11': '11',
            ###'ordem_12': '12',
        ###}

        ###if rel_obj.opcoes_caixa == '1':
            ###rel.parametros['TIPO'] = 'Q'
            ###filtro['tipo'] = "and fcs.tipo = 'Q'"
        ###elif rel_obj.opcoes_caixa == '2':
            ###rel.parametros['TIPO'] = 'X'
            ###filtro['tipo'] = ""
        ###else:
            ###rel.parametros['TIPO'] = 'V'
            ###filtro['tipo'] = "and fcs.tipo = 'V'"

        ###if len(rel_obj.company_ids) == 1:
            ###rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            ###filtro['filtro_company'] = """
            ###(
                ###fcs.company_id = {company_id}
                ###or c.parent_id = {company_id}
            ###)
            ###""".format(company_id=rel_obj.company_ids[0].id)
            ###filtro['filtro_company_anterior'] = """
            ###and (
                ###pr.company_id = {company_id}
                ###or cc.parent_id = {company_id}
            ###)
            ###""".format(company_id=rel_obj.company_ids[0].id)


        ###elif len(rel_obj.company_ids) > 1:
            ###rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            ###company_ids = []
            ###for company_obj in rel_obj.company_ids:
                ###company_ids.append(company_obj.id)

            ###filtro['filtro_company'] = """
            ###(
                ###fcs.company_id in {company_ids}
                ###or c.parent_id in {company_ids}
            ###)
            ###""".format(company_ids=str(tuple(company_ids)).replace(',)', ')'))
            ###filtro['filtro_company_anterior'] = """
            ###and (
                ###pr.company_id in {company_ids}
                ###or cc.parent_id in {company_ids}
            ###)
            ###""".format(company_ids=str(tuple(company_ids)).replace(',)', ')'))

        ###else:
            ###raise osv.except_osv(u'Atenção', u'É preciso selecionar pelo menos uma empresa!')

        ####if rel_obj.filtrar_rateio:

            ####sql = """
                ####select
                    ####*
                ####from
                    ####finan_analitico_rateio('{data_inicial}', '{data_final}', {company_id}, {zera_saldo}, {filtro_adicional})
            ####"""
            ####if rel_obj.project_id:
                ####filtro['filtro_adicional'] = """' and lr.project_id = """ + str(rel_obj.project_id.id) + """'"""
                ####rel.parametros['PROJETO'] = rel_obj.project_id.name

        ####else:
            ####sql = """
                ####select
                    ####*
                ####from
                    ####finan_analitico('{data_inicial}', '{data_final}', {company_id}, {zera_saldo})
            ####"""


        ####if rel_obj.ativo:
            ####if rel_obj.opcoes_caixa == '1':
                ####sql += """
                    ####where
                        ####(id < 0 or quitado_total > 0)
                ####"""
            ####elif rel_obj.opcoes_caixa == '2':
                ####sql += """
                    ####where
                        ####(id < 0 or ((quitado_total > 0)
                        ####or (vencido_total > 0)))
                ####"""
            ####else:
                ####sql += """
                    ####where
                        ####(id < 0 or vencido_total > 0)
                ####"""

        ####
        #### Monta os títulos das colunas
        ####
        ###dif = tempo(data_final, data_inicial)
        ###data = data_inicial
        ###i = 1
        ###lista_meses = []
        ###while i <= 12:
            #####
            ##### Relatório por dia
            #####
            ####if (dif.years == 0 and dif.months == 0) and dif.days <= 7:
                ####filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%a %d/%m/%Y')
                ####data += relativedelta(days=+1)
            ####else:
            ###filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%B de %Y')
            ###filtro['ordem_' + formata_data(data, '%m')] = str(i).zfill(2)
            ###data += relativedelta(months=+1)

            ###i += 1

        ###sql = u"""
###drop table if exists finan_relatorio_fluxo_sintetico;
###create table finan_relatorio_fluxo_sintetico as
###select
    ###row_number() over() as id,
    ###fc.codigo_completo as codigo_ordem,
    ###fc.codigo_completo as codigo,
    ###fc.nome as descricao,
    ###cast(case
        ###when fc.tipo = 'R' then 1
        ###when fc.tipo = 'D' then -1
        ###when fc.tipo = 'C' then -1
        ###when fc.tipo = 'A' then -1
        ###when fc.tipo = 'P' then -1
        ###else -1
    ###end as integer) as tipo,
    ###coalesce(fcs.sintetica, False) as sintetica,
###"""
        ####if rel_obj.zera_saldo:
        ###if True:
            ###sql += """
    ###cast(0 as numeric) as quitado_anterior,
    ###cast(0 as numeric) as vencido_anterior,
###"""
        ###else:
            ###sql += """
    ###cast((
        ###select
            ###coalesce(sum(pr.valor), 0.00) as quitado
        ###from finan_pagamento_rateio pr
            ###join finan_conta_arvore ca on ca.conta_id = pr.conta_id
            ###join res_company cc on cc.id = pr.company_id

        ###where
            ###pr.tipo in ('R', 'P', 'E', 'S')
            ###and ca.conta_pai_id = fc.id
            ###and pr.data_quitacao < '{data_inicial}'
            ###{filtro_company_anterior}
    ###) as numeric) as quitado_anterior,
    ###cast(0 as numeric) as vencido_anterior,
###"""

        ###sql += """
    ###cast('{titulo_01}' as varchar) as titulo_01,
    ###cast('{titulo_02}' as varchar) as titulo_02,
    ###cast('{titulo_03}' as varchar) as titulo_03,
    ###cast('{titulo_04}' as varchar) as titulo_04,
    ###cast('{titulo_05}' as varchar) as titulo_05,
    ###cast('{titulo_06}' as varchar) as titulo_06,
    ###cast('{titulo_07}' as varchar) as titulo_07,
    ###cast('{titulo_08}' as varchar) as titulo_08,
    ###cast('{titulo_09}' as varchar) as titulo_09,
    ###cast('{titulo_10}' as varchar) as titulo_10,
    ###cast('{titulo_11}' as varchar) as titulo_11,
    ###cast('{titulo_12}' as varchar) as titulo_12,
    ###cast(sum(coalesce(fcs.quitado_01, 0)) as numeric) as quitado_{ordem_01},
    ###cast(sum(coalesce(fcs.quitado_02, 0)) as numeric) as quitado_{ordem_02},
    ###cast(sum(coalesce(fcs.quitado_03, 0)) as numeric) as quitado_{ordem_03},
    ###cast(sum(coalesce(fcs.quitado_04, 0)) as numeric) as quitado_{ordem_04},
    ###cast(sum(coalesce(fcs.quitado_05, 0)) as numeric) as quitado_{ordem_05},
    ###cast(sum(coalesce(fcs.quitado_06, 0)) as numeric) as quitado_{ordem_06},
    ###cast(sum(coalesce(fcs.quitado_07, 0)) as numeric) as quitado_{ordem_07},
    ###cast(sum(coalesce(fcs.quitado_08, 0)) as numeric) as quitado_{ordem_08},
    ###cast(sum(coalesce(fcs.quitado_09, 0)) as numeric) as quitado_{ordem_09},
    ###cast(sum(coalesce(fcs.quitado_10, 0)) as numeric) as quitado_{ordem_10},
    ###cast(sum(coalesce(fcs.quitado_11, 0)) as numeric) as quitado_{ordem_11},
    ###cast(sum(coalesce(fcs.quitado_12, 0)) as numeric) as quitado_{ordem_12},

    ###cast(sum(
        ###coalesce(fcs.quitado_01, 0)
        ###+ coalesce(fcs.quitado_02, 0)
        ###+ coalesce(fcs.quitado_03, 0)
        ###+ coalesce(fcs.quitado_04, 0)
        ###+ coalesce(fcs.quitado_05, 0)
        ###+ coalesce(fcs.quitado_06, 0)
        ###+ coalesce(fcs.quitado_07, 0)
        ###+ coalesce(fcs.quitado_08, 0)
        ###+ coalesce(fcs.quitado_09, 0)
        ###+ coalesce(fcs.quitado_10, 0)
        ###+ coalesce(fcs.quitado_11, 0)
        ###+ coalesce(fcs.quitado_12, 0)
    ###) as numeric) as quitado_total,
    ###cast(0 as numeric) as percentual_quitado,

    ###cast(sum(coalesce(fcs.vencido_01, 0)) as numeric) as vencido_{ordem_01},
    ###cast(sum(coalesce(fcs.vencido_02, 0)) as numeric) as vencido_{ordem_02},
    ###cast(sum(coalesce(fcs.vencido_03, 0)) as numeric) as vencido_{ordem_03},
    ###cast(sum(coalesce(fcs.vencido_04, 0)) as numeric) as vencido_{ordem_04},
    ###cast(sum(coalesce(fcs.vencido_05, 0)) as numeric) as vencido_{ordem_05},
    ###cast(sum(coalesce(fcs.vencido_06, 0)) as numeric) as vencido_{ordem_06},
    ###cast(sum(coalesce(fcs.vencido_07, 0)) as numeric) as vencido_{ordem_07},
    ###cast(sum(coalesce(fcs.vencido_08, 0)) as numeric) as vencido_{ordem_08},
    ###cast(sum(coalesce(fcs.vencido_09, 0)) as numeric) as vencido_{ordem_09},
    ###cast(sum(coalesce(fcs.vencido_10, 0)) as numeric) as vencido_{ordem_10},
    ###cast(sum(coalesce(fcs.vencido_11, 0)) as numeric) as vencido_{ordem_11},
    ###cast(sum(coalesce(fcs.vencido_12, 0)) as numeric) as vencido_{ordem_12},

    ###cast(sum(
        ###coalesce(fcs.vencido_01, 0)
        ###+ coalesce(fcs.vencido_02, 0)
        ###+ coalesce(fcs.vencido_03, 0)
        ###+ coalesce(fcs.vencido_04, 0)
        ###+ coalesce(fcs.vencido_05, 0)
        ###+ coalesce(fcs.vencido_06, 0)
        ###+ coalesce(fcs.vencido_07, 0)
        ###+ coalesce(fcs.vencido_08, 0)
        ###+ coalesce(fcs.vencido_09, 0)
        ###+ coalesce(fcs.vencido_10, 0)
        ###+ coalesce(fcs.vencido_11, 0)
        ###+ coalesce(fcs.vencido_12, 0)
    ###) as numeric) as vencido_total,
    ###cast(0 as numeric) as percentual_vencido

###from
    ###finan_conta fc
    ###left outer join finan_fluxo_caixa_sintetico fcs on fcs.id = fc.id
    ###left outer join res_company c on c.id = fcs.company_id

###where
    ###{filtro_company}
    ###and fcs.data between '{data_inicial}' and '{data_final}'
    ###-- and fc.tipo in ('R', 'D', 'C')
    ###{tipo}
    ###{provisionado}

###group by
    ###fc.id,
    ###fc.codigo_completo,
    ###fc.nome,
    ###fcs.sintetica

###order by
    ###fc.codigo_completo,
    ###fc.nome;
        ###"""

        ###if rel_obj.nao_provisionado != rel_obj.provisionado:
            ###if rel_obj.nao_provisionado:
                ###filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = False)'
            ###else:
                ###filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = True)'
        ###else:
            ###filtro['provisionado'] = ''

        ####if rel_obj.nao_provisionado != rel_obj.provisionado:
            ####rel.parametros['PROV'] = True
        ####else:
            ####rel.parametros['PROV'] = False

        ####if rel_obj.saldo_bancario:
            ####rel.parametros['SALDO_BANCO'] = True
        ####else:
            ####rel.parametros['SALDO_BANCO'] = False

        ####if rel_obj.zera_saldo:
            ####rel.parametros['ZERA_SALDO'] = True
        ####else:
            ####rel.parametros['ZERA_SALDO'] = False

        ###sql = sql.format(**filtro)
        ###print(sql)
        ###cr.execute(sql)
        ###cr.commit()

        ###sql_receitas = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###1000000 as id,
    ###'9999999901' as codigo_ordem,
    ###'' as codigo,
    ###'RECEITAS' as descricao,
    ###fc.tipo,
    ###True as sintetica,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.tipo = 1
    ###and fc.sintetica = False

###group by
    ###fc.tipo,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12;
        ###"""
        ###cr.execute(sql_receitas)
        ###cr.commit()

        ###sql_despesas = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###2000000 as id,
    ###'9999999902' as codigo_ordem,
    ###'' as codigo,
    ###'DESPESAS E CUSTOS' as descricao,
    ###fc.tipo,
    ###True as sintetica,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.tipo = -1
    ###and fc.sintetica = False

###group by
    ###fc.tipo,
    ###fc.titulo_01,
    ###fc.titulo_02,
    ###fc.titulo_03,
    ###fc.titulo_04,
    ###fc.titulo_05,
    ###fc.titulo_06,
    ###fc.titulo_07,
    ###fc.titulo_08,
    ###fc.titulo_09,
    ###fc.titulo_10,
    ###fc.titulo_11,
    ###fc.titulo_12;
        ###"""
        ###cr.execute(sql_despesas)
        ###cr.commit()

        ###sql_saldo = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###3000000 as id,
    ###'9999999903' as codigo_ordem,
    ###'' as codigo,
    ###'SALDO FINAL' as descricao,
    ###0,
    ###True as sintetica,
    ###'' as titulo_01,
    ###'' as titulo_02,
    ###'' as titulo_03,
    ###'' as titulo_04,
    ###'' as titulo_05,
    ###'' as titulo_06,
    ###'' as titulo_07,
    ###'' as titulo_08,
    ###'' as titulo_09,
    ###'' as titulo_10,
    ###'' as titulo_11,
    ###'' as titulo_12,
    ###sum(fc.quitado_anterior) as quitado_anterior,
    ###sum(fc.vencido_anterior) as vencido_anterior,
    ###sum(fc.quitado_01) as quitado_01,
    ###sum(fc.quitado_02) as quitado_02,
    ###sum(fc.quitado_03) as quitado_03,
    ###sum(fc.quitado_04) as quitado_04,
    ###sum(fc.quitado_05) as quitado_05,
    ###sum(fc.quitado_06) as quitado_06,
    ###sum(fc.quitado_07) as quitado_07,
    ###sum(fc.quitado_08) as quitado_08,
    ###sum(fc.quitado_09) as quitado_09,
    ###sum(fc.quitado_10) as quitado_10,
    ###sum(fc.quitado_11) as quitado_11,
    ###sum(fc.quitado_12) as quitado_12,
    ###sum(fc.quitado_total) as quitado_total,
    ###100 as percentual_quitado,
    ###sum(fc.vencido_01) as vencido_01,
    ###sum(fc.vencido_02) as vencido_02,
    ###sum(fc.vencido_03) as vencido_03,
    ###sum(fc.vencido_04) as vencido_04,
    ###sum(fc.vencido_05) as vencido_05,
    ###sum(fc.vencido_06) as vencido_06,
    ###sum(fc.vencido_07) as vencido_07,
    ###sum(fc.vencido_08) as vencido_08,
    ###sum(fc.vencido_09) as vencido_09,
    ###sum(fc.vencido_10) as vencido_10,
    ###sum(fc.vencido_11) as vencido_11,
    ###sum(fc.vencido_12) as vencido_12,
    ###sum(fc.vencido_total) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.id >= 1000000;
        ###"""
        ###cr.execute(sql_saldo)
        ###cr.commit()

        ###sql_acumulado = """
###insert into finan_relatorio_fluxo_sintetico
    ###(
        ###id,
        ###codigo_ordem,
        ###codigo,
        ###descricao,
        ###tipo,
        ###sintetica,
        ###titulo_01,
        ###titulo_02,
        ###titulo_03,
        ###titulo_04,
        ###titulo_05,
        ###titulo_06,
        ###titulo_07,
        ###titulo_08,
        ###titulo_09,
        ###titulo_10,
        ###titulo_11,
        ###titulo_12,
        ###quitado_anterior,
        ###vencido_anterior,
        ###quitado_01,
        ###quitado_02,
        ###quitado_03,
        ###quitado_04,
        ###quitado_05,
        ###quitado_06,
        ###quitado_07,
        ###quitado_08,
        ###quitado_09,
        ###quitado_10,
        ###quitado_11,
        ###quitado_12,
        ###quitado_total,
        ###percentual_quitado,
        ###vencido_01,
        ###vencido_02,
        ###vencido_03,
        ###vencido_04,
        ###vencido_05,
        ###vencido_06,
        ###vencido_07,
        ###vencido_08,
        ###vencido_09,
        ###vencido_10,
        ###vencido_11,
        ###vencido_12,
        ###vencido_total,
        ###percentual_vencido
    ###)
###select
    ###4000000 as id,
    ###'9999999904' as codigo_ordem,
    ###'' as codigo,
    ###'ACUMULADO' as descricao,
    ###0,
    ###True as sintetica,
    ###'' as titulo_01,
    ###'' as titulo_02,
    ###'' as titulo_03,
    ###'' as titulo_04,
    ###'' as titulo_05,
    ###'' as titulo_06,
    ###'' as titulo_07,
    ###'' as titulo_08,
    ###'' as titulo_09,
    ###'' as titulo_10,
    ###'' as titulo_11,
    ###'' as titulo_12,
    ###{saldo_inicial} as quitado_anterior,
    ###fc.vencido_anterior as vencido_anterior,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
    ###) as quitado_01,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
    ###) as quitado_02,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
    ###) as quitado_03,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
    ###) as quitado_04,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
    ###) as quitado_05,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
    ###) as quitado_06,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
    ###) as quitado_07,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
    ###) as quitado_08,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
    ###) as quitado_09,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
    ###) as quitado_10,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
    ###) as quitado_11,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
        ###+ fc.quitado_12
    ###) as quitado_12,
    ###(   {saldo_inicial}
        ###+ fc.quitado_01
        ###+ fc.quitado_02
        ###+ fc.quitado_03
        ###+ fc.quitado_04
        ###+ fc.quitado_05
        ###+ fc.quitado_06
        ###+ fc.quitado_07
        ###+ fc.quitado_08
        ###+ fc.quitado_09
        ###+ fc.quitado_10
        ###+ fc.quitado_11
        ###+ fc.quitado_12
    ###) as quitado_total,
    ###100 as percentual_quitado,

    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
    ###) as vencido_01,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
    ###) as vencido_02,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
    ###) as vencido_03,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
    ###) as vencido_04,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
    ###) as vencido_05,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
    ###) as vencido_06,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
    ###) as vencido_07,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
    ###) as vencido_08,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
    ###) as vencido_09,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
    ###) as vencido_10,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
    ###) as vencido_11,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
        ###+ fc.vencido_12
    ###) as vencido_12,
    ###(   fc.vencido_anterior + {saldo_inicial}
        ###+ fc.vencido_01
        ###+ fc.vencido_02
        ###+ fc.vencido_03
        ###+ fc.vencido_04
        ###+ fc.vencido_05
        ###+ fc.vencido_06
        ###+ fc.vencido_07
        ###+ fc.vencido_08
        ###+ fc.vencido_09
        ###+ fc.vencido_10
        ###+ fc.vencido_11
        ###+ fc.vencido_12
    ###) as vencido_total,
    ###100 as percentual_vencido

###from
    ###finan_relatorio_fluxo_sintetico fc

###where
    ###fc.id = 3000000;
        ###"""

        ###if getattr(rel_obj, 'saldo_inicial', False):
            ###cr.execute(sql_acumulado.format(saldo_inicial=D(rel_obj.saldo_inicial or 0)))

        ###else:
            ###cr.execute(sql_acumulado.format(saldo_inicial='fc.quitado_anterior'))

        ###cr.commit()

        ###if rel_obj.opcoes_caixa != '2':
            ###sql_percentual = """
                ###update finan_relatorio_fluxo_sintetico fc set
                ###percentual_quitado =
                    ###case
                        ###when (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else quitado_total / (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end,

                ###percentual_vencido =
                    ###case
                        ###when (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else vencido_total / (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end

                ###where
                ###fc.id < 1000000;
            ###"""
        ###else:
            ###sql_percentual = """
                ###update finan_relatorio_fluxo_sintetico fc set
                ###percentual_quitado =
                    ###case
                        ###when (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else (quitado_total + vencido_total) / (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end,

                ###percentual_vencido =
                    ###case
                        ###when (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        ###else (vencido_total + vencido_total) / (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    ###end

                ###where
                ###fc.id < 1000000;
            ###"""

        ###cr.execute(sql_percentual)
        ###cr.commit()

        ###sql = """
        ###select
            ###*
        ###from
            ###finan_relatorio_fluxo_sintetico fc

        ###order by
            ###fc.codigo_ordem
        ###"""
        ####print(filtro)
        ###rel.parametros['SQL'] = sql.replace('\n', ' ')

        ###pdf, formato = rel.execute()

        ###dados = {
            ###'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            ###'arquivo': base64.encodestring(pdf)
        ###}
        ###rel_obj.write(dados)

        ###return True

    def gera_relatorio_resumo_resultado(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        cr.execute("""
                    select
                    c.id
                    from
                    res_company c
                    join res_partner rp on rp.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id

                    where
                    (c.id = """ + str(rel_obj.company_id.id) + """
                    or c.parent_id = """ + str(rel_obj.company_id.id) + """
                    or cc.parent_id = """ + str(rel_obj.company_id.id) + """
                     )""")

        company_ids = []
        for ret in cr.fetchall():
            company_ids.append(ret[0])
        #print(company_ids)

        rel = Report('Resumo de Resultado', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_resultado.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        rel.parametros['COMPANY_IDS'] =  str(tuple(company_ids)).replace(',)', ')')
        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = "('Q')"
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = "('Q','V')"
        else:
            rel.parametros['TIPO'] = "('V')"

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Resumo_Resultado.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_aging_formapagamento(self, cr, uid, ids, context={}):
        rel_pool = self.pool.get('finan.relatorio')
        return rel_pool.gera_relatorio_aging(cr, uid, ids, context=context, formapagamento=True, tipo='R')


    def gera_relatorio_aging_receber(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_aging(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_aging_pagar(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_aging(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_aging(self, cr, uid, ids, context={}, formapagamento=False, tipo='R'):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if tipo == 'R':
            tipo2 = 'PR'
        else:
            tipo2 = 'PP'

        rel = FinanRelatorioAutomaticoRetrato()
        rel.cpc_minimo_detalhe = 4

        if tipo == 'R':
            rel.title = u'Posição de Contas a Receber - Aging'
        else:
            rel.title = u'Posição de Contas a Pagar - Aging'

        rel.colunas = [
            ['periodo', 'C', 10, u'Período', False],
            ['valor', 'F', 15, u'Valor', True],
            ['percentual', 'F', 12, u'Percentual', True],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        if formapagamento:
            rel.grupos = [
                ['formapagamento', u'Forma de pagamento', True],
                ['tipo', u'Tipo', False],
            ]
        else:
            rel.grupos = [
                ['tipo', u'Tipo', False],
            ]
        rel.monta_grupos(rel.grupos)

        if formapagamento:
            sql = """
        select
            resumo.formapagamento,
            resumo.tipo,
            case
                when resumo.dias <= 15 then '000 - 015'
                when resumo.dias > 15 and resumo.dias <= 30 then '016 - 030'
                when resumo.dias > 30 and resumo.dias <= 60 then '031 - 060'
                when resumo.dias > 60 and resumo.dias <= 90 then '061 - 090'
                when resumo.dias > 90 and resumo.dias <= 120 then '091 - 120'
                when resumo.dias > 120 and resumo.dias <= 150 then '121 - 150'
                when resumo.dias > 150 and resumo.dias <= 180 then '151 - 180'
                else '181 - '
            end as periodo, """

        else:
            sql = """
        select
            '' as formapagamento,
            resumo.tipo,
            case
                when resumo.dias <= 15 then '000 - 015'
                when resumo.dias > 15 and resumo.dias <= 30 then '016 - 030'
                when resumo.dias > 30 and resumo.dias <= 60 then '031 - 060'
                when resumo.dias > 60 and resumo.dias <= 90 then '061 - 090'
                when resumo.dias > 90 and resumo.dias <= 120 then '091 - 120'
                when resumo.dias > 120 and resumo.dias <= 150 then '121 - 150'
                when resumo.dias > 150 and resumo.dias <= 180 then '151 - 180'
                else '181 - '
            end as periodo, """


        if rel_obj.saldo:
            sql +="""
                sum(resumo.valor_documento - resumo.valor_pago) as saldo """

        else:
            sql +="""
                sum(resumo.valor_documento) as saldo """

        sql +="""

        from

        (select
            case
                when l.data <= '{data_final}' then 'Conciliado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) = 0 then 'Baixado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) != 0 then 'Baixado parcial'
                when l.data_quitacao <= '{data_final}' then 'Quitado'
                when l.data_vencimento <= '{data_final}' then 'Vencido'
                else 'A vencer'
            end as tipo,
            case
                when l.data <= '{data_final}' then 0
                when l.data_baixa <= '{data_final}' then 0
                when l.data_quitacao <= '{data_final}' then 0
                when l.data_vencimento > '{data_final}' then l.data_vencimento - cast('{data_final}' as date)
                when l.data_quitacao is null or l.data_quitacao > '{data_final}' then cast('{data_final}' as date) - l.data_vencimento
                else 0
            end as dias,
            l.valor_documento,
            case
                when l.lancamento_id is not null then l.valor_documento
                else coalesce((select sum(p.valor_documento) from finan_lancamento p where p.tipo = '{tipo2}' and p.lancamento_id = l.id and p.data_quitacao <= '{data_final}'), 0)
            end as valor_pago,
            (select c.id from res_partner_category c join res_partner_category_rel pc on pc.category_id = c.id and pc.partner_id = l.partner_id limit 1) as categoria_id,
            l.formapagamento_id,
            coalesce(fp.nome, '') as formapagamento

        from
            finan_lancamento l
            join res_company u on u.id = l.company_id
            left join finan_formapagamento fp on fp.id = l.formapagamento_id

        where
            l.tipo = '{tipo}'
            and (l.provisionado = False or l.provisionado is null)
            and (u.id in ({company_ids}) or u.parent_id in ({company_ids}))
            and l.data_documento <= '{data_final}'
        ) as resumo

        where
            (resumo.tipo = 'Vencido' or resumo.tipo = 'A vencer')
            {filtro_adicional}

        group by
            1,
            resumo.tipo,
            periodo

        order by
            1,
            resumo.tipo desc,
            periodo;
                """

        filtro = {
            'company_ids': str(rel_obj.company_id.id),
            'data_final': rel_obj.data_final,
            'tipo': tipo,
            'tipo2': tipo2,
            'filtro_adicional': '',
        }

        rel.band_page_header.elements[-1].text = u'Empresa/unidade ' + rel_obj.company_id.name

        if rel_obj.company_2_id:
            filtro['company_ids'] += u', ' + str(rel_obj.company_2_id.id)
            rel.band_page_header.elements[-1].text += u' e ' + rel_obj.company_2_id.name

        rel.band_page_header.height += 18
        rel.band_page_header.elements[-1].text += u'<br/>Data ' + formata_data(rel_obj.data_final)

        if rel_obj.categoria_id:
            filtro['filtro_adicional'] += "and (resumo.categoria_id = '{categoria}')".format(categoria=rel_obj.categoria_id.id)
            rel.band_page_header.height += 7
            rel.band_page_header.elements[-1].text += u'<br/>Categoria: ' + rel_obj.categoria_id.complete_name

        if rel_obj.formapagamento_id:
            filtro['filtro_adicional'] += "and (resumo.formapagamento_id = '{formapagamento}')".format(formapagamento=rel_obj.formapagamento_id.id)
            rel.band_page_header.height += 7
            rel.band_page_header.elements[-1].text += u'<br/>Forma de pagamento: ' + rel_obj.formapagamento_id.nome
        #else:
        #    filtro['filtro_adicional'] += "and (resumo.formapagamento_id is null)"

        sql = sql.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        PERIODOS = OrderedDict((
            (u'000 - 015', u'\u2003\u20030 -  15'),
            (u'016 - 030', u'\u200316 -  30'),
            (u'031 - 060', u'\u200331 -  60'),
            (u'061 - 090', u'\u200361 -  90'),
            (u'091 - 120', u'\u200391 - 120'),
            (u'121 - 150', u'121 - 150'),
            (u'151 - 180', u'151 - 180'),
            (u'181 - '   , u'181 - '   ),
        ))

        valores = {}
        formaspagamento = []
        total_vencido = D(0)
        total_vencer = D(0)

        for fp, tipo, periodo, valor in dados:
            linha = DicionarioBrasil()
            linha['formapagamento'] = fp
            linha['tipo'] = tipo
            linha['periodo'] = periodo
            valor = D(valor or 0)
            linha['valor'] = valor
            linha['percentual'] = D(0)

            if tipo == 'Vencido':
                total_vencido += valor
            else:
                total_vencer += valor

            if fp not in valores:
                valores[fp] = {
                    u'Vencido': {},
                    u'A vencer': {},
                }

            valores[fp][tipo][periodo] = linha
            if fp not in formaspagamento:
                formaspagamento.append(fp)

        total_geral = total_vencido + total_vencer

        total_percentual_vencido = D(0)
        total_percentual_vencer = D(0)

        linhas = []
        for fp in formaspagamento:
            for tipo in (u'Vencido', u'A vencer'):
                for periodo in PERIODOS:
                    if periodo in valores[fp][tipo]:
                        linha = valores[fp][tipo][periodo]
                        linha.periodo = PERIODOS[periodo]
                        percentual = linha.valor / total_geral * 100
                        percentual = percentual.quantize(D('0.01'))
                        linha.percentual = percentual

                        if tipo == 'Vencido':
                            total_percentual_vencido += percentual
                        else:
                            total_percentual_vencer += percentual

                    else:
                        linha = DicionarioBrasil()
                        linha['formapagamento'] = fp
                        linha['tipo'] = tipo
                        linha['periodo'] = PERIODOS[periodo]
                        linha['valor'] = D(0)
                        linha['percentual'] = D(0)
                        valores[fp][tipo][periodo] = linha

                    linhas.append(linha)

        total_percentual_geral = total_percentual_vencido + total_percentual_vencer

        pdf = gera_relatorio(rel, linhas)

        #
        # Monta os subtotais
        #
        linhas_csv = []
        for fp in formaspagamento:
            total_vencido = D(0)
            total_vencer = D(0)
            total_percentual_vencido = D(0)
            total_percentual_vencer = D(0)

            for tipo in (u'Vencido', u'A vencer'):
                for periodo in PERIODOS:
                    linhas_csv.append(valores[fp][tipo][periodo])
                    if tipo == 'Vencido':
                        total_vencido += valores[fp][tipo][periodo].valor
                        total_percentual_vencido += valores[fp][tipo][periodo].percentual
                    else:
                        total_vencer += valores[fp][tipo][periodo].valor
                        total_percentual_vencer += valores[fp][tipo][periodo].percentual

                if tipo == 'Vencido':
                    linha = DicionarioBrasil()
                    linha['formapagamento'] = fp
                    linha['tipo'] = u'Total - Tipo Vencido'
                    linha['periodo'] = ''
                    linha['valor'] = total_vencido
                    linha['percentual'] = total_percentual_vencido

                else:
                    linha = DicionarioBrasil()
                    linha['formapagamento'] = fp
                    linha['tipo'] = u'Total - Tipo A vencer'
                    linha['periodo'] = ''
                    linha['valor'] = total_vencer
                    linha['percentual'] = total_percentual_vencer

                linhas_csv.append(linha)

        linha = DicionarioBrasil()
        linha['formapagamento'] = u''
        linha['tipo'] = u'Total'
        linha['periodo'] = ''
        linha['valor'] = total_geral
        linha['percentual'] = total_percentual_geral
        linhas_csv.append(linha)

        rel.colunas = [
            ['formapagamento', 'C', 40, u'Forma de pagamento', False],
            ['tipo', 'C', 10, u'Tipo', False],
            ['periodo', 'C', 10, u'Período', False],
            ['valor', 'F', 15, u'Valor', True],
            ['percentual', 'F', 12, u'Percentual', True],
        ]
        rel.monta_detalhe_automatico(rel.colunas)

        csv = gera_relatorio_csv(rel, linhas_csv)

        dados = {
            'nome': 'finan_ageing.pdf',
            'arquivo': base64.encodestring(pdf),
            'nome_csv': 'finan_ageing.csv',
            'arquivo_csv': base64.encodestring(csv),
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_aging_receber_grafico(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_aging_grafico(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_aging_pagar_grafico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_aging_grafico(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_aging_grafico(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if tipo == 'R':
            tipo2 = 'PR'
        else:
            tipo2 = 'PP'

        sql = """
        select
            count(resumo.dias) as quantidade_dias,
            resumo.tipo,
            case
                when resumo.dias <= 15 then '000 - 015'
                when resumo.dias > 15 and resumo.dias <= 30 then '016 - 030'
                when resumo.dias > 30 and resumo.dias <= 60 then '031 - 060'
                when resumo.dias > 60 and resumo.dias <= 90 then '061 - 090'
                when resumo.dias > 90 and resumo.dias <= 120 then '091 - 120'
                when resumo.dias > 120 and resumo.dias <= 150 then '121 - 150'
                when resumo.dias > 150 and resumo.dias <= 180 then '151 - 180'
                else '181 - '
            end as periodo, """

        if rel_obj.saldo:
            sql +="""
                sum(resumo.valor_documento - resumo.valor_pago) as saldo,
                formata_valor(sum(resumo.valor_documento- resumo.valor_pago)) as saldo_string"""
        else:
            sql +="""
                sum(resumo.valor_documento) as saldo,
                formata_valor(sum(resumo.valor_documento)) as saldo_string """

        sql +="""
        from

        (select
            case
                when l.data <= '{data_final}' then 'Conciliado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) = 0 then 'Baixado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) != 0 then 'Baixado parcial'
                when l.data_quitacao <= '{data_final}' then 'Quitado'
                when l.data_vencimento <= '{data_final}' then 'Vencido'
                else 'A vencer'
            end as tipo,
            case
                when l.data <= '{data_final}' then 0
                when l.data_baixa <= '{data_final}' then 0
                when l.data_quitacao <= '{data_final}' then 0
                when l.data_vencimento > '{data_final}' then l.data_vencimento - cast('{data_final}' as date)
                when l.data_quitacao is null or l.data_quitacao > '{data_final}' then cast('{data_final}' as date) - l.data_vencimento
                else 0
            end as dias,
            coalesce(l.valor_documento, 0) as valor_documento,

            case
            when l.lancamento_id is not null then l.valor_documento
            else coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.tipo = '{tipo2}' and p.lancamento_id = l.id and p.data_quitacao <= '{data_final}'), 0)
            end as valor_pago,

            (select c.id from res_partner_category c join res_partner_category_rel pc on pc.category_id = c.id and pc.partner_id = l.partner_id limit 1) as categoria_id,
            l.formapagamento_id

        from
            finan_lancamento l
            join res_company u on u.id = l.company_id

        where
            l.tipo = '{tipo}'
            and (l.provisionado = False or l.provisionado is null)
            and (u.id in ({company_ids}) or u.parent_id in ({company_ids}))
            and l.data_documento <= '{data_final}'
        ) as resumo

        where
            (resumo.tipo = 'Vencido' or resumo.tipo = 'A vencer')
            {filtro_adicional}

        group by
            resumo.tipo,
            periodo

        order by
            resumo.tipo desc,
            periodo;
                """

        filtro = {
            'company_ids': str(rel_obj.company_id.id),
            'data_final': rel_obj.data_final,
            'tipo': tipo,
            'tipo2': tipo2,
            'filtro_adicional': '',
        }

        nome_empresa = rel_obj.company_id.name

        if rel_obj.company_2_id:
            filtro['company_ids'] += u', ' + str(rel_obj.company_2_id.id)
            nome_empresa += u' e ' + rel_obj.company_2_id.name

        if rel_obj.categoria_id:
            filtro['filtro_adicional'] += "and (resumo.categoria_id = '{categoria}')".format(categoria=rel_obj.categoria_id.id)

        if rel_obj.formapagamento_id:
            filtro['filtro_adicional'] += "and (resumo.formapagamento_id = '{formapagamento}')".format(formapagamento=rel_obj.formapagamento_id.id)
        else:
            filtro['filtro_adicional'] += "and (resumo.formapagamento_id is null)"

        sql = sql.format(**filtro)
        data_final = parse_datetime(rel_obj.data_final).date()

        if tipo == 'R':
            rel = Report(u'Ageing Contas a Receber', cr, uid)
            nome = u'finan_ageing_receber_'
        else:
            rel = Report(u'Ageing Contas a Pagar', cr, uid)
            nome = u'finan_ageing_pagar_'

        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_aging.jrxml')
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['NOME_EMPRESAS'] = nome_empresa

        if rel_obj.categoria_id:
            rel.parametros['CATEGORIA_NOME'] = rel_obj.categoria_id.complete_name

        if rel_obj.formapagamento_id:
            rel.parametros['FORMA_NOME'] = rel_obj.formapagamento_id.nome

        if tipo == 'R':
            rel.parametros['TIPO'] = 'R'
        else:
            rel.parametros['TIPO'] = 'P'


        pdf, formato = rel.execute()

        dados = {
            'nome': nome + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_aging_receber_analitico(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_aging_analitico(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_aging_pagar_analitico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_aging_analitico(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_aging_analitico(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if tipo == 'R':
            tipo2 = 'PR'
        else:
            tipo2 = 'PP'

        sql = """
        select
            resumo.dias as quantidade_dias,
            coalesce(resumo.tipo,'') as tipo,
            coalesce(case
                when resumo.dias <= 15 then '000 - 015'
                when resumo.dias > 15 and resumo.dias <= 30 then '016 - 030'
                when resumo.dias > 30 and resumo.dias <= 60 then '031 - 060'
                when resumo.dias > 60 and resumo.dias <= 90 then '061 - 090'
                when resumo.dias > 90 and resumo.dias <= 120 then '091 - 120'
                when resumo.dias > 120 and resumo.dias <= 150 then '121 - 150'
                when resumo.dias > 150 and resumo.dias <= 180 then '151 - 180'
                else '181 - '
            end,'') as periodo,
            resumo.numero_documento as numero_documento,
            resumo.parceiro_nome as parceiro_nome,
            resumo.data_documento as data_documento,
            resumo.valor_documento as valor_documento,
            resumo.valor_desconto as valor_desconto,
            resumo.valor_juros as valor_juros,
            resumo.valor_multa as valor_multa,
            resumo.valor as valor,
            resumo.valor_pago as valor_pago,
            resumo.categoria_id as categoria_id,
            resumo.formapagamento_id as formapagamento_id,
            resumo.valor_documento - resumo.valor_pago as saldo

        from

        (select
            case
                when l.data <= '{data_final}' then 'Conciliado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) = 0 then 'Baixado'
                when l.data_baixa <= '{data_final}' and coalesce(l.valor, 0) != 0 then 'Baixado parcial'
                when l.data_quitacao <= '{data_final}' then 'Quitado'
                when l.data_vencimento <= '{data_final}' then 'Vencido'
                else 'A vencer'
            end as tipo,
            case
                when l.data <= '{data_final}' then 0
                when l.data_baixa <= '{data_final}' then 0
                when l.data_quitacao <= '{data_final}' then 0
                when l.data_vencimento > '{data_final}' then l.data_vencimento - cast('{data_final}' as date)
                when l.data_quitacao is null or l.data_quitacao > '{data_final}' then cast('{data_final}' as date) - l.data_vencimento
                else 0
            end as dias,

            l.id as lancamento,
            l.data_documento as data_documento,
            coalesce(l.numero_documento, '') as numero_documento,
            coalesce(p.name, '') as parceiro_nome,
            coalesce(l.valor_documento, 0.00)  as valor_documento,
            coalesce((
            select
                sum(coalesce(p.valor_desconto, 0) * coalesce(ldp.porcentagem, 1))
            from
                finan_lancamento p
                left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = p.id and ldp.divida_id = l.id
            where
                p.tipo = '{tipo2}'
                and (p.lancamento_id = l.id or p.lancamento_id = ldp.lote_id)
                and p.data_quitacao <= '{data_final}'
            ), 0) as valor_desconto,
            coalesce(
            case
                when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then l.valor_juros_previsto
            else
                (
                select
                    sum(coalesce(p.valor_juros, 0) * coalesce(ldp.porcentagem, 1))
                from
                    finan_lancamento p
                    left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = p.id and ldp.divida_id = l.id
                where
                    p.tipo = '{tipo2}'
                    and (p.lancamento_id = l.id or p.lancamento_id = ldp.lote_id)
                    and p.data_quitacao <= '{data_final}'
                )
            end, 0.00) as valor_juros,

            coalesce(
            case
                when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then l.valor_multa_prevista
            else
                (
                select
                    sum(coalesce(p.valor_multa, 0) * coalesce(ldp.porcentagem, 1))
                from
                    finan_lancamento p
                    left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = p.id and ldp.divida_id = l.id
                where
                    p.tipo = '{tipo2}'
                    and (p.lancamento_id = l.id or p.lancamento_id = ldp.lote_id)
                    and p.data_quitacao <= '{data_final}'
                )
            end, 0.00)  as valor_multa,

            coalesce((
            select
                sum(coalesce(p.valor, 0) * coalesce(ldp.porcentagem, 1))
            from
                finan_lancamento p
                left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = p.id and ldp.divida_id = l.id
            where
                p.tipo = '{tipo2}'
                and (p.lancamento_id = l.id or p.lancamento_id = ldp.lote_id)
                and p.data_quitacao <= '{data_final}'
            ), 0) as valor,

            coalesce(case
                    when l.lancamento_id is not null then l.valor_documento
                else
                    (
                    select
                        sum(coalesce(p.valor_documento, 0) * coalesce(ldp.porcentagem, 1))
                    from
                        finan_lancamento p
                        left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = p.id and ldp.divida_id = l.id
                    where
                        p.tipo = '{tipo2}'
                        and (p.lancamento_id = l.id or p.lancamento_id = ldp.lote_id)
                        and p.data_quitacao <= '{data_final}'
                    )
            end, 0) as valor_pago,

            (select c.id from res_partner_category c join res_partner_category_rel pc on pc.category_id = c.id and pc.partner_id = l.partner_id limit 1) as categoria_id,
            l.formapagamento_id,

            case
                when l.data <= '{data_final}' then  l.res_partner_bank_id
                when l.data_baixa <= '{data_final}' then l.sugestao_bank_id
                when l.data_quitacao <= '{data_final}' then  l.res_partner_bank_id
                when l.data_vencimento <= '{data_final}' then  l.res_partner_bank_id
                else l.sugestao_bank_id
            end as banco


        from
            finan_lancamento l
            join res_company u on u.id = l.company_id
            left join res_partner p on p.id = l.partner_id

        where
            l.tipo = '{tipo}'
            and (l.provisionado = False or l.provisionado is null)
            and (u.id in ({company_ids}) or u.parent_id in ({company_ids}))
            and l.data_documento <= '{data_final}'
        ) as resumo

        where
            (resumo.tipo = 'Vencido' or resumo.tipo = 'A vencer')
            {filtro_adicional}

        order by
            resumo.tipo desc,
            periodo,
            data_documento;
                """

        filtro = {
            'company_ids': str(rel_obj.company_id.id),
            'data_final': rel_obj.data_final,
            'tipo': tipo,
            'tipo2': tipo2,
            'filtro_adicional': '',
        }

        nome_empresa = rel_obj.company_id.name

        if rel_obj.company_2_id:
            filtro['company_ids'] += u', ' + str(rel_obj.company_2_id.id)
            nome_empresa += u' e ' + rel_obj.company_2_id.name

        if rel_obj.categoria_id:
            filtro['filtro_adicional'] += "and (resumo.categoria_id = '{categoria}')".format(categoria=rel_obj.categoria_id.id)

        if rel_obj.formapagamento_id:
            filtro['filtro_adicional'] += "and (resumo.formapagamento_id = '{formapagamento}')".format(formapagamento=rel_obj.formapagamento_id.id)
        else:
            filtro['filtro_adicional'] += "and (resumo.formapagamento_id is null)"

        if rel_obj.res_partner_bank_id:
            filtro['filtro_adicional'] += " and resumo.banco = {res_partner_bank_id}".format(res_partner_bank_id=rel_obj.res_partner_bank_id.id)



        sql = sql.format(**filtro)
        data_final = parse_datetime(rel_obj.data_final).date()

        if tipo == 'R':
            rel = Report(u'Ageing Contas a Receber Analitico', cr, uid)
            nome = u'finan_ageing_receber_analitico_'
        else:
            rel = Report(u'Ageing Contas a Pagar Analitico', cr, uid)
            nome = u'finan_ageing_pagar_analitico_'

        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_aging_analitico.jrxml')
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql
        rel.parametros['NOME_EMPRESAS'] = nome_empresa

        if rel_obj.categoria_id:
            rel.parametros['CATEGORIA_NOME'] = rel_obj.categoria_id.complete_name

        if rel_obj.formapagamento_id:
            rel.parametros['FORMA_NOME'] = rel_obj.formapagamento_id.nome

        if rel_obj.res_partner_bank_id:
            rel.parametros['BANCO'] = rel_obj.res_partner_bank_id.nome

        if tipo == 'R':
            rel.parametros['TIPO'] = 'R'
        else:
            rel.parametros['TIPO'] = 'P'

        pdf, formato = rel.execute()

        dados = {
            'nome': nome + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_analise_contratos(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Analise de Contratos', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_analise_contratos.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['IS_SINTETICO'] = rel_obj.tipo_rel


        pdf, formato = rel.execute()

        dados = {
            'nome': u'Analise_Contratos_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_resultado_analitico_centrocusto(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Lançamentos - Analítico por Conta e Centro de Custo', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analise_resultado_analitico_centrocusto.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa

        if rel_obj.conta_id:
            rel.parametros['CONTA_ID'] = str(rel_obj.conta_id.id)
        else:
            rel.parametros['CONTA_ID'] = '%'

        if rel_obj.centrocusto_id:
            rel.parametros['CENTROCUSTO_ID'] = str(rel_obj.centrocusto_id.id)
        else:
            rel.parametros['CENTROCUSTO_ID'] = '%'

        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = 'Q'
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = 'X'
        else:
            rel.parametros['TIPO'] = 'V'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Resultado_Analitico_CentroCusto_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_resultado_analitico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Analise de Resultado_Analítico', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analise_resultado_analitico.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = 'Q'
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = 'X'
        else:
            rel.parametros['TIPO'] = 'V'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Análise_Resultado_Analitico.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_resultado_analitico_data(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Analise de Resultado_Analítico por Data', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'analise_resultado_analitico_data.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = 'Q'
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = 'X'
        else:
            rel.parametros['TIPO'] = 'V'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Análise_Resultado_Analitico_data.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_notas_canceladas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Notas Canceladas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_notas_canceladas.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato
        relatorio = u'notas_canceladas_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_retencao_inss(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        cnpj_cpf = rel_obj.company_id.cnpj_cpf
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório Retenção de INSS', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'retencao_inss.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['CNPJ_CPF'] = cnpj_cpf
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato

        relatorio = u'retenção_inss_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_notas_emitidas(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Notas Emitidas', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_notas_emitidas.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato

        if rel_obj.tipo == '1':
            rel.parametros['TIPO'] = '1'
            rel.parametros['TIPO_ANALISE'] = 'finan_notas_emitidas_analitico.jasper'
            relatorio = u'notas_emitidas_analitico_'
        else:
            rel.parametros['TIPO'] = '2'
            rel.parametros['TIPO_ANALISE'] = 'finan_notas_emitidas_sintetico.jasper'
            relatorio = u'notas_emitidas_sintetico_'

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_fluxo_sintetico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Fluxo de Caixa Sintetico ', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
        rel.parametros['ZERA_SALDO'] = 'S' if rel_obj.zera_saldo else 'N'
        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = 'Q'
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = 'X'
        else:
            rel.parametros['TIPO'] = 'V'

        pdf, formato = rel.execute()

        dados = {
            'nome': u'fluxo_caixa_sintetico.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_contas_receber_inadiplencia(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)

        rel = Report('Relatório de Contas a Receber', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_contas_receber.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]

        if situacao == '1':
            rel.parametros['SITUACAO'] = u"('Vencido')"
            rel.parametros['TEXTO_FILTRO'] = u'Somente vencidos'
        elif situacao == '2':
            rel.parametros['SITUACAO'] = u"('Vencido', 'Vence hoje')"
            rel.parametros['TEXTO_FILTRO'] = u'Somente vencidos ou que vencem hoje'
        elif situacao == '3':
            rel.parametros['SITUACAO'] = u"('A vencer')"
            rel.parametros['TEXTO_FILTRO'] = u'Somente a vencer'
        elif situacao == '4':
            rel.parametros['SITUACAO'] = u"('A vencer', 'Vencido', 'Vence hoje')"
            rel.parametros['TEXTO_FILTRO'] = u'Qualquer situação (a vencer, vencido etc.)'
        else:
            rel.parametros['SITUACAO'] = u"('Quitado', 'Conciliado')"
            rel.parametros['TEXTO_FILTRO'] = u'Somente liquidados'

        if partner_id:
            rel.parametros['PARTNER_ID'] = str(partner_id)

        if rel_obj.formapagamento_id:
            rel.parametros['FILTRO_ADICIONAL'] = 'and l.formapagamento_id = ' + str(rel_obj.formapagamento_id.id)
            rel.parametros['TEXTO_FILTRO'] += u'; somente forma de pagamento '
            rel.parametros['TEXTO_FILTRO'] += rel_obj.formapagamento_id.nome

        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'finan_conta_receber.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_contas(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo[0],
            'rateio': '',
        }

        if situacao == '1':
            sql_situacao = u"('Vencido')"
        elif situacao == '2':
            sql_situacao = u"('Vencido', 'Vence hoje')"
        elif situacao == '3':
            sql_situacao = u"('A vencer')"
        elif situacao == '4':
            sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
        else:
            sql_situacao = u"('Quitado', 'Conciliado')"


        for rel_obj in self.browse(cr, uid, ids):
            rel = FinanRelatorioAutomaticoPaisagem()

            if tipo == 'R':
                rel.title = u'Contas a Receber por Cliente'
            else:
                rel.title = u'Contas a Pagar por Fornecedor'

            rel.colunas = [
                ['conta_codigo', 'C', 10, u'Cod.Conta', False],
                ['conta_nome', 'C', 38, u'Conta', False],
            ]

            if tipo == 'P-R':
                rel.colunas += [
                    ['projeto', 'C', 30, u'Projeto', False],
                    ['centro_custo', 'C', 30, u'Centro Custo', False],
                    ['banco', 'C', 30, u'Conta Bancária', False],
            ]

            rel.colunas += [
                ['numero_documento', 'C', 25, u'Nº doc.', False],
                ['data_documento', 'D', 10, u'Data doc.', False],
                ['data_vencimento', 'D', 10, u'Data venc.', False],
                #['carteira_id.res_partner_bank_id.name', 'C', 10, u'Banco', False],
            ]

            if tipo == 'R':
                rel.colunas += [['nosso_numero', 'C', 10, u'Nosso nº', False]]


            rel.colunas += [
                ['provisionado', 'B', 5, u'Prov.', False],
                ['valor_documento', 'F', 10, u'Valor orig.', True],
                ['valor_desconto', 'F', 10, u'Desc.', True],
                ['valor_multa', 'F', 10, u'Multa', True],
                ['valor_juros', 'F', 10, u'Juros', True],
                ['valor', 'F', 10, u'Total', True],
                ['valor_saldo', 'F', 10, u'Parc.', True],
                ['dias_atraso', 'I', 6, u'Atraso', True],
                #['situacao', 'C', 10, u'Situação', False],
            ]

            if situacao == '5':
                rel.colunas += ['data_quitacao', 'D', 10, u'Data quit.', False],

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['unidade', u'Unidade', True],
                ['situacao', u'Situação', False],
                ['cliente', u'Cliente' if tipo == 'R' else u'Fornecedor', False],
            ]
            rel.monta_grupos(rel.grupos)

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(l.valor_documento, 0.00) {rateio} as valor_documento,
                   coalesce(l.valor_desconto, 0.00) {rateio} as valor_desconto,
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) {rateio} as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) {rateio} as valor_multa,

                   coalesce(l.valor, 0.00) {rateio} as valor,
                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.name, '') || ' - ' || coalesce(p.cnpj_cpf, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   coalesce(cf.nome, '') as conta_nome,
                   l.provisionado"""

            if tipo == 'P-R':
                sql_relatorio += """,
                   fcc.nome as centro_custo,
                   a.name as projeto,
                   ba.nome as banco
                """

            sql_relatorio += """
                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id
                   left join finan_conta cf on cf.id = l.conta_id """

            if rel_obj.filtrar_rateio or tipo == 'P-R':
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            if tipo == 'P-R':
                sql_relatorio += """
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""

            if situacao != '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if rel_obj.res_partner_bank_id:
                    sql_relatorio += 'and l.sugestao_bank_id = ' + str(rel_obj.res_partner_bank_id.id)

            else:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_quitacao between '{data_inicial}' and '{data_final}'"""

                if rel_obj.res_partner_bank_id:
                    sql_relatorio += 'and l.res_partner_bank_id = ' + str(rel_obj.res_partner_bank_id.id)

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """

            if partner_id:
                sql_relatorio += """
                   and l.partner_id = """ + str(partner_id)

            if provisionado == True and ativo == False:
                sql_relatorio += """
                   and l.provisionado = """ + str(provisionado)

            if ativo == True and provisionado == False:
                sql_relatorio += """
                   and l.provisionado = False """

            if rel_obj.formapagamento_id:
                sql_relatorio += """
                   and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    sql_relatorio += """
                       and lr.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

                if rel_obj.project_id:
                    sql_relatorio += """
                       and lr.project_id = """ + str(rel_obj.project_id.id)

            sql_relatorio += """
                    order by c.name, l.situacao, p.name, p.cnpj_cpf, l.data_vencimento;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            #print(sql_relatorio)
            cr.execute(sql_relatorio)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            if tipo == 'P-R':
                for id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, valor_saldo, nosso_numero, cliente, contato, unidade, situacao, conta_codigo, conta_nome, provisionado, centro_custo, projeto, banco  in dados:
                    linha = DicionarioBrasil()
                    linha['id'] = id
                    linha['numero_documento'] = numero_documento
                    linha['data_documento'] = parse_datetime(data_documento)
                    linha['data_vencimento'] = parse_datetime(data_vencimento)
                    linha['data_quitacao'] = parse_datetime(data_quitacao)
                    linha['valor_documento'] = valor_documento
                    linha['valor_desconto'] = valor_desconto
                    linha['valor_juros'] = valor_juros
                    linha['valor_multa'] = valor_multa

                    if data_quitacao:
                        linha['valor'] = valor
                    else:
                        linha['valor'] = valor_documento - valor_desconto + valor_juros + valor_multa

                    if tipo == 'P-R':
                        linha['projeto'] = projeto
                        linha['centro_custo'] = centro_custo
                        linha['banco'] = banco

                    linha['valor_saldo'] = valor_saldo
                    linha['nosso_numero'] = nosso_numero
                    linha['cliente'] = cliente + ' | ' + contato
                    linha['unidade'] = unidade
                    linha['situacao'] = situacao
                    linha['conta_codigo'] = conta_codigo
                    linha['conta_nome'] = conta_nome
                    linha['provisionado'] = provisionado

                    if situacao == 'Vencido':
                        atraso = hoje() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    elif situacao in ('Quitado', 'Conciliado') and data_quitacao > data_vencimento:
                        atraso = parse_datetime(data_quitacao).date() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    else:
                        linha['dias_atraso'] = 0

                    linhas.append(linha)

            else:
                for id, numero_documento, data_documento, data_vencimento, data_quitacao, valor_documento, valor_desconto, valor_juros, valor_multa, valor, valor_saldo, nosso_numero, cliente, contato, unidade, situacao, conta_codigo, conta_nome, provisionado  in dados:
                    linha = DicionarioBrasil()
                    linha['id'] = id
                    linha['numero_documento'] = numero_documento
                    linha['data_documento'] = parse_datetime(data_documento)
                    linha['data_vencimento'] = parse_datetime(data_vencimento)
                    linha['data_quitacao'] = parse_datetime(data_quitacao)
                    linha['valor_documento'] = valor_documento
                    linha['valor_desconto'] = valor_desconto
                    linha['valor_juros'] = valor_juros
                    linha['valor_multa'] = valor_multa

                    if data_quitacao:
                        linha['valor'] = valor
                    else:
                        linha['valor'] = valor_documento - valor_desconto + valor_juros + valor_multa

                    linha['valor_saldo'] = valor_saldo
                    linha['nosso_numero'] = nosso_numero
                    linha['cliente'] = cliente + ' | ' + contato
                    linha['unidade'] = unidade
                    linha['situacao'] = situacao
                    linha['conta_codigo'] = conta_codigo
                    linha['conta_nome'] = conta_nome
                    linha['provisionado'] = provisionado

                    if situacao == 'Vencido':
                        atraso = hoje() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    elif situacao in ('Quitado', 'Conciliado') and data_quitacao > data_vencimento:
                        atraso = parse_datetime(data_quitacao).date() - parse_datetime(data_vencimento).date()
                        linha['dias_atraso'] = atraso.days
                    else:
                        linha['dias_atraso'] = 0

                    linhas.append(linha)

            rel.band_page_header.elements[-1].text = u'Período ' + parse_datetime(data_inicial).strftime('%d/%m/%Y') + u' a ' + parse_datetime(data_final).strftime('%d/%m/%Y')

            if rel_obj.company_id:
                rel.band_page_header.elements[-1].text += u', empresa/unidade '
                rel.band_page_header.elements[-1].text += rel_obj.company_id.name

            if situacao != '5':
                rel.band_page_header.elements[-1].text += u', situação é ' + sql_situacao

                if rel_obj.res_partner_bank_id:
                    rel.band_page_header.elements[-1].text += u', com previsão para a conta '
                    rel.band_page_header.elements[-1].text += rel_obj.res_partner_bank_id.descricao
                    rel.band_page_header.height += 14
                    rel.band_page_header.elements[-1].text += '<br/>'

            else:
                rel.band_page_header.elements[-1].text += u', situação Liquidados/Quitados'

                if rel_obj.res_partner_bank_id:
                    rel.band_page_header.elements[-1].text += u', na conta '
                    rel.band_page_header.elements[-1].text += rel_obj.res_partner_bank_id.descricao
                    rel.band_page_header.height += 14
                    rel.band_page_header.elements[-1].text += '<br/>'

            if rel_obj.partner_id:
                if tipo == 'R':
                    rel.band_page_header.elements[-1].text += u', do cliente '
                else:
                    rel.band_page_header.elements[-1].text += u', do fornecedor '

                rel.band_page_header.elements[-1].text += rel_obj.partner_id.name

            if rel_obj.formapagamento_id:
                rel.band_page_header.elements[-1].text += u', forma de pagamento '
                rel.band_page_header.elements[-1].text += rel_obj.formapagamento_id.nome

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    rel.band_page_header.elements[-1].text += u', centro de custo '
                    rel.band_page_header.elements[-1].text += rel_obj.centrocusto_id.nome_completo

                if rel_obj.project_id:
                    rel.band_page_header.elements[-1].text += u', projeto '
                    rel.band_page_header.elements[-1].text += rel_obj.project_id.name

            #pdf = gera_relatorio(rel, lancamento_objs)
            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'contas_receber.pdf' if tipo == 'R' else 'contas_pagar.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'contas_receber.csv' if tipo == 'R' else 'contas_pagar.csv',
                'arquivo_csv': base64.encodestring(csv),
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_contas_jasper(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo[0],
            'rateio': '',
        }


        if situacao == '1':
            sql_situacao = u"('Vencido')"
            SITUACAO = u'Vencido'

        elif situacao == '2':
            sql_situacao = u"('Vencido', 'Vence hoje')"
            SITUACAO = u'Vencido + Hoje'

        elif situacao == '3':
            sql_situacao = u"('A vencer')"
            SITUACAO = u'A Vencer'

        elif situacao == '4':
            sql_situacao = u"('A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Todos em aberto'

        elif situacao == '5':
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Liquidadas'

        else:
            sql_situacao = u"('Quitado', 'Conciliado', 'A vencer', 'Vencido', 'Vence hoje')"
            SITUACAO = u'Registrados'


        for rel_obj in self.browse(cr, uid, ids):

            if len(rel_obj.res_partner_bank_ids):
                texto_filtro = u''
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    #banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += u', ' + banco_obj.nome or ''

            sql_relatorio = """
                select
                   l.id as lancamento,
                   coalesce(l.numero_documento, '') as numero_documento,
                   l.data_documento as data_documento,
                   l.data_vencimento as data_vencimento,
                   l.data_quitacao as data_quitacao,
                   coalesce(l.valor_documento, 0.00) {rateio} as valor_documento,
                   coalesce(l.valor_desconto, 0.00) {rateio} as valor_desconto,
                   coalesce(
                   case
                   when l.valor_juros = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_juros_previsto
                   else
                   l.valor_juros
                   end, 0.00) {rateio} as valor_juros,

                   coalesce(
                   case
                   when l.valor_multa = 0 and l.situacao not in ('Quitado', 'Conciliado', 'Baixado', 'Baixado parcial') then
                   l.valor_multa_prevista
                   else
                   l.valor_multa
                   end, 0.00) {rateio} as valor_multa,

                   coalesce(l.valor, 0.00) {rateio} as valor,
                   coalesce(l.valor_saldo, 0.00) {rateio} as valor_saldo,
                   coalesce(l.nosso_numero, '') as nosso_numero,
                   coalesce(p.razao_social, '') || ' | ' || coalesce(p.name, '') || ' | ' || coalesce(p.cnpj_cpf, '') as cliente,
                   coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                   coalesce(p.email_nfe, '') as email_nfe,
                   c.name as unidade,
                   coalesce(l.situacao, '') as situacao,
                   coalesce(cf.codigo_completo, '') as conta_codigo,
                   pfc.nome || '/' || cf.nome as conta_nome,
                   l.provisionado,
                   case
                   when l.data_vencimento < current_date then
                   current_date - l.data_vencimento
                   else
                   0 end as data_atraso"""
            if tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """,
                   fcc.nome as centro_custo,
                   a.name as projeto,
                   ba.nome as banco
                """

            sql_relatorio += """
                   from finan_lancamento l
                   join res_partner p on p.id = l.partner_id
                   join res_company c on c.id = l.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id"""

            if rel_obj.filtrar_rateio or tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = l.id """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            if rel_obj.filtrar_rateio or tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   left join finan_conta cf on cf.id = lr.conta_id
                   left join finan_conta pfc on pfc.id = cf.parent_id"""
            else:
                sql_relatorio += """
                   left join finan_conta cf on cf.id = l.conta_id
                   left join finan_conta pfc on pfc.id = cf.parent_id"""

            if tipo == 'P-R' or tipo == 'R-R':
                sql_relatorio += """
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.sugestao_bank_id"""

            if situacao < '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_vencimento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.sugestao_bank_id in '  +  str(tuple(bancos_ids)).replace(',)', ')')
            elif situacao == '5':
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and exists(select lp.id from finan_lancamento lp where lp.lancamento_id = l.id and lp.tipo in ('PP', 'PR') and lp.data_quitacao between '{data_inicial}' and '{data_final}')"""

                if len(rel_obj.res_partner_bank_ids):
                    sql_relatorio += 'and l.res_partner_bank_id in'   +  str(tuple(bancos_ids)).replace(',)', ')')
            else:
                sql_relatorio += """
                   where l.tipo = '{tipo}'
                   and l.data_documento between '{data_inicial}' and '{data_final}'
                   and l.situacao in """ + sql_situacao



            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """
            if rel_obj.dias_atraso:
                sql_relatorio +="""
                    and current_date - l.data_vencimento = """ + str(rel_obj.dias_atraso)


            if rel_obj.sem_nf:
                sql_relatorio +="""
                    and sped_documento_id is null"""

            if partner_id:
                sql_relatorio += """
                   and l.partner_id = """ + str(partner_id)

            if ativo != provisionado:
                sql_relatorio += """
                   and l.provisionado = """ + str(provisionado)

            if rel_obj.formapagamento_id:
                sql_relatorio += """
                   and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    sql_relatorio += """
                       and lr.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

                if rel_obj.project_id:
                    sql_relatorio += """
                       and lr.project_id = """ + str(rel_obj.project_id.id)

                if rel_obj.conta_id:
                    sql_relatorio += """
                       and cf.codigo_completo like '""" + rel_obj.conta_id.codigo_completo + """%'"""

            if rel_obj.agrupa_data_vencimento:
                sql_relatorio += """
                        order by c.name, l.situacao,l.data_vencimento, p.razao_social, p.name, p.cnpj_cpf, cf.codigo_completo desc;"""
            else:
                sql_relatorio += """
                        order by c.name, l.situacao, p.razao_social, p.name, p.cnpj_cpf, l.data_vencimento, cf.codigo_completo desc;"""

            sql_relatorio = sql_relatorio.format(**filtro)
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            if tipo == 'R':
                rel = Report('Relatório de Contas a Receber', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_receber.jrxml')
                nome_rel = u'contas_receber.'

                if rel_obj.agrupa_data_vencimento:
                    rel.parametros['AGRUPA_DATA_VENC'] = True

                if rel_obj.formapagamento_id:
                    rel.parametros['FORMA_PAGAMENTO'] = rel_obj.formapagamento_id.nome

            if tipo == 'P':
                rel = Report('Relatório de Contas a Pagar', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_pagar.jrxml')
                nome_rel = u'contas_pagar.'

                if len(rel_obj.res_partner_bank_ids):
                        rel.parametros['BANCO'] = texto_filtro

            if tipo == 'R-R':
                rel = Report('Relatório de Contas a Receber Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_receber_rateio.jrxml')
                nome_rel = u'contas_receber_rateio.'

                if rel_obj.filtrar_rateio:
                    if rel_obj.centrocusto_id:
                        rel.parametros['CENTRO_CUSTO'] = rel_obj.centrocusto_id.nome_completo

                    if rel_obj.project_id:
                        rel.parametros['PROJETO'] = rel_obj.project_id.name

            if tipo == 'P-R':
                rel = Report('Relatório de Contas a Pagar Rateio', cr, uid)
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_conta_pagar_rateio.jrxml')
                nome_rel = u'contas_pagar_rateio.'

                if len(rel_obj.res_partner_bank_ids):
                        rel.parametros['BANCO'] = texto_filtro

                if rel_obj.filtrar_rateio:
                    if rel_obj.centrocusto_id:
                        rel.parametros['CENTRO_CUSTO'] = rel_obj.centrocusto_id.nome_completo

                    if rel_obj.project_id:
                        rel.parametros['PROJETO'] = rel_obj.project_id.name

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['SQL_RELATORIO'] = sql_relatorio
            rel.parametros['SITUACAO'] = SITUACAO

            if rel_obj.total_empresa:
                rel.parametros['TOTAIS'] = True

            rel.outputFormat = rel_obj.formato

            if rel_obj.partner_id:
                rel.parametros['PARTNER'] = rel_obj.partner_id.name

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_rel + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contas_receber(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_contas_jasper(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_contas_pagar(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_jasper(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_contas_receber_rateio(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_jasper(cr, uid, ids, context=context, tipo='R-R')

    def gera_relatorio_contas_pagar_rateio(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_jasper(cr, uid, ids, context=context, tipo='P-R')

    def gera_relatorio_contas_pagamentos(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        data_inicial = context['data_inicial']
        data_final = context['data_final']
        situacao = context['situacao']
        partner_id = context.get('partner_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': 'P' + tipo[0],
            'rateio': '',
        }

        situacao = '5'
        sql_situacao = u"('Quitado', 'Conciliado')"

        for rel_obj in self.browse(cr, uid, ids):

            sql_relatorio = """
                select
                    l.id  as lancamento,
                    coalesce(fl.numero_documento, '') as numero_documento,
                    fl.data_documento,
                    fl.data_vencimento,
                    l.data_quitacao,
                    coalesce(l.valor_documento, 0.00) * coalesce(ldp.porcentagem, 1) {rateio}  as valor_documento,
                    coalesce(l.valor_desconto, 0.00) * coalesce(ldp.porcentagem, 1) {rateio}  as valor_desconto,
                    coalesce(l.valor_documento, 0.00) * coalesce(ldp.porcentagem, 1) as valor_documento,
                    coalesce(l.valor_desconto, 0.00) * coalesce(ldp.porcentagem, 1) as valor_desconto,
                    coalesce(l.valor_juros, 0) * coalesce(ldp.porcentagem, 1) as valor_juros,
                    coalesce(l.valor_multa, 0) * coalesce(ldp.porcentagem, 1) as valor_multa,
                    coalesce(l.valor, 0.00) * coalesce(ldp.porcentagem, 1) as valor,
                    coalesce(p.name, '') || ' - ' || coalesce(p.cnpj_cpf, '') as cliente,
                    coalesce(p.fone, '') || ' - ' || coalesce(p.celular, '') as contato,
                    c.name as unidade,
                    coalesce(lp.situacao, '') as situacao,
                    coalesce(cf.codigo_completo, '') as conta_codigo,
                    coalesce(cf.nome, '') as conta_nome,
                    lp.provisionado"""

            if rel_obj.filtrar_rateio:
                sql_relatorio += """,
                   fcc.nome as centro_custo,
                   a.name as projeto,
                   ba.nome as banco,
                   ba.agencia as agencia,
                   ba.acc_number as conta
                """

            sql_relatorio += """
                from finan_lancamento l
                   left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = l.id
                   join finan_lancamento fl on (ldp.divida_id is not null and fl.id = ldp.divida_id) or (ldp.divida_id is null and fl.id = l.lancamento_id)
                   left join res_partner p on p.id = fl.partner_id
                   join finan_lancamento lp on lp.id = l.lancamento_id
                   join res_company c on c.id = fl.company_id
                   left join res_company cc on cc.id = c.parent_id
                   left join res_company ccc on ccc.id = cc.parent_id"""

            if rel_obj.filtrar_rateio:
                sql_relatorio += """
                   join finan_lancamento_rateio_geral_folha lr on lr.lancamento_id = fl.id
                   left join finan_conta cf on cf.id = lr.conta_id
                   left join finan_centrocusto fcc on fcc.id = lr.centrocusto_id
                   left join project_project pp on pp.id = lr.project_id
                   left join account_analytic_account a on a.id = pp.analytic_account_id
                   left join res_partner_bank ba on ba.id = l.res_partner_bank_id
                """

                filtro['rateio'] = '* (coalesce(lr.porcentagem, 0) / 100.00)'

            else:
                sql_relatorio += """
                   join finan_conta cf on (fl.tipo != 'T' and cf.id = fl.conta_id) or (fl.tipo = 'T' and cf.id = l.id)
                """


            sql_relatorio += """
               where l.tipo = '{tipo}'
               and l.data_quitacao between '{data_inicial}' and '{data_final}'"""

            if rel_obj.res_partner_bank_id:
                sql_relatorio += 'and l.res_partner_bank_id = ' + str(rel_obj.res_partner_bank_id.id)
            elif rel_obj.res_partner_bank_ids:
                #texto_filtro = u''
                bancos_ids = []

                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    #banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    #texto_filtro += u', ' + banco_obj.nome or ''

                sql_relatorio += 'and l.res_partner_bank_id in ' + str(tuple(bancos_ids)).replace(',)', ')')

            if rel_obj.company_id:
                sql_relatorio += """
                   and (
                       c.id = {company_id}
                       or cc.id = {company_id}
                       or ccc.id = {company_id}
                   )
                """

            if partner_id:
                sql_relatorio += """
                   and fl.partner_id = """ + str(partner_id)


            if rel_obj.formapagamento_id:
                sql_relatorio += """
                   and l.formapagamento_id = """ + str(rel_obj.formapagamento_id.id)

            if rel_obj.filtrar_rateio:
                if rel_obj.centrocusto_id:
                    sql_relatorio += """
                       and lr.centrocusto_id = """ + str(rel_obj.centrocusto_id.id)

                if rel_obj.project_id:
                    sql_relatorio += """
                       and lr.project_id = """ + str(rel_obj.project_id.id)

                if rel_obj.conta_id:
                    sql_relatorio += """
                       and cf.codigo_completo like '""" + rel_obj.conta_id.codigo_completo + """%'"""

                #
                # Campo booleano usado na tela como sendo Rateio sem projeto ou sem centro de custo?
                #
                if rel_obj.sem_projeto:
                    sql_relatorio += """
                        and lr.project_id is null 
                    """
                if rel_obj.sem_centrocusto:
                    sql_relatorio += """
                        and lr.centrocusto_id is null
                    """

            sql_relatorio += """
                    order by c.name, fl.situacao, p.name, p.cnpj_cpf, fl.data_vencimento;"""

            sql_relatorio = sql_relatorio.format(**filtro)


            if not rel_obj.filtrar_rateio:

                if tipo == 'R':
                    rel = Report('Relatório de Recebimento de Contas por Cliente', cr, uid)
                    rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_contas_pagamento.jrxml')
                    titulo = u'RECEBIMENTO DE CONTAS POR CLIENTE'
                    nome_rel = u'recebimento_contas_cliente.'

                    if rel_obj.formapagamento_id:
                        rel.parametros['FORMA_PAGAMENTO'] = rel_obj.formapagamento_id.nome

                else:
                    rel = Report('Relatório de Pagamento de Contas por Fornecedor', cr, uid)
                    rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_contas_pagamento.jrxml')
                    titulo = u'PAGAMENTO DE CONTAS POR FORNECEDOR'
                    nome_rel = u'pagamento_contas_fornecedor.'

            else:

                if tipo == 'R':
                    rel = Report('Relatório de Pagamento de Contas por Cliente Rateio', cr, uid)
                    rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_contas_pagamento_rateio.jrxml')
                    nome_rel = u'pagamento_contas_cliente_rateio.'
                    titulo = u'PAGAMENTO DE CONTAS POR CLIENTE RATEIO'
                else:
                    rel = Report('Relatório de Pagamento de Contas por Fornecedor Rateio', cr, uid)
                    rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_contas_pagamento_rateio.jrxml')
                    nome_rel = u'pagamento_contas_fornecedor_rateio.'
                    titulo = u'PAGAMENTO DE CONTAS POR FORNECEDOR RATEIO'

                if rel_obj.centrocusto_id:
                    rel.parametros['CENTRO_CUSTO'] = rel_obj.centrocusto_id.nome_completo

                if rel_obj.project_id:
                    rel.parametros['PROJETO'] = rel_obj.project_id.name

            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['SQL_RELATORIO'] = sql_relatorio
            rel.parametros['TITULO'] = titulo
            if rel_obj.total_empresa:
                rel.parametros['TOTAIS'] = True

            rel.outputFormat = rel_obj.formato

            if rel_obj.partner_id:
                rel.parametros['PARTNER'] = rel_obj.partner_id.name

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_rel + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True


    def gera_relatorio_contas_receber_pagamentos(self, cr, uid, ids, context={}):
       if not ids:
          return {}

       return self.gera_relatorio_contas_pagamentos(cr, uid, ids, context=context, tipo='R')


    def gera_relatorio_contas_pagar_pagamentos(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_contas_pagamentos(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_extrato_cliente(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_extrato(cr, uid, ids, context=context, tipo='R')

    def gera_relatorio_extrato_fornecedor(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        return self.gera_relatorio_extrato(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_extrato(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        data_inicial = context.get('data_inicial', False)
        data_final = context.get('data_final', False)
        partner_id = context.get('partner_id', False)
        company_id = context.get('company_id', False)
        provisionado = context.get('provisionado')
        ativo = context.get('ativo')

        filtro = {
            'company_id': company_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'partner_id': partner_id,
        }

        if not data_inicial or not data_final:
            raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

        if tipo == 'R':
            rel = Report('Extrato de Cliente', cr, uid)
            nome_r = 'Cliente'
            #filtro['tipos'] = "('R', 'PR')"
            filtro['tipos'] = "('R')"
        else:
            rel = Report('Extrato de Fornecedores', cr, uid)
            nome_r = 'Fornecedor'
            #filtro['tipos'] = "('P', 'PP')"
            filtro['tipos'] = "('P')"

        sql_relatorio = """
            select
                rp.razao_social as empresa_razao_social,
                rp.cnpj_cpf as empresa_cnpj_cpf,
                rp.ie as empresa_ie,
                rp.endereco as empresa_endereco,
                rp.numero as empresa_numero,
                rp.complemento as empresa_complemento,
                rp.bairro as empresa_bairro,
                rp.cidade as empresa_cidade,
                rp.estado as empresa_estado,
                rp.cep as empresa_cep,
                rp.fone,

                coalesce(cli.razao_social, cli.name) as cli_razao_social,
                cli.cnpj_cpf as cli_cnpj_cpf,

                l.id as lancamento_id,
                l.data_documento as data_documento,
                l.numero_documento  as numero_documento,
                l.data_vencimento as data_vencimento,
                l.valor_documento as valor_documento,
                l.situacao,
                l.data_baixa,
                lp.data_quitacao,
                case
                    when l.situacao = 'Baixado' or l.situacao = 'Baixado parcial' then 0
                    else l.valor_saldo
                end as valor_saldo,
                case
                  when l.situacao = 'Vencido' then (current_date - l.data_vencimento)
                  when l.situacao in ('Quitado', 'Conciliado') then (l.data_quitacao - l.data_vencimento)
                  else 0
                end as dias_atraso,

                coalesce(lp.valor_documento, 0) * coalesce(ldp.porcentagem, 1) as valor_documento_liquidado,
                coalesce(lp.valor_multa, 0) * coalesce(ldp.porcentagem, 1) as valor_multa,
                coalesce(lp.valor_juros, 0) * coalesce(ldp.porcentagem, 1) as valor_juros,
                coalesce(lp.valor_desconto, 0) * coalesce(ldp.porcentagem, 1) as valor_desconto,
                coalesce(lp.valor, 0) * coalesce(ldp.porcentagem, 1) as valor_liquidado,
                mb.nome as motivo_baixa,
                cast(c.photo as varchar) as photo,
                coalesce(nf.vr_nf, l.valor_documento) as valor_bruto

            from
                finan_lancamento as l
                join res_company c on c.id = l.company_id
                join res_partner rp on rp.id = c.partner_id
                join res_partner cli on cli.id = l.partner_id
                left join finan_lancamento_lote_divida_pagamento ldp on ldp.divida_id = l.id
                left join finan_lancamento lp on (ldp.divida_id is not null and lp.id = ldp.pagamento_id) or (ldp.divida_id is null and lp.lancamento_id = l.id)
                left join finan_motivobaixa mb on mb.id = l.motivo_baixa_id
                left join res_company cc on cc.id = c.parent_id
                left join sped_documento nf on nf.id = l.sped_documento_id

            where
                cli.id = {partner_id}
                and l.tipo in {tipos}
                and (
                    l.data_vencimento between '{data_inicial}' and '{data_final}'
                    or l.data_quitacao between '{data_inicial}' and '{data_final}'
                    or l.data_baixa between '{data_inicial}' and '{data_final}'
                )"""
        if company_id:
            sql_relatorio += """
                and (c.id = {company_id}
                        or c.parent_id = {company_id}
                        or cc.parent_id = {company_id}
                )"""
        if ativo != provisionado:
                sql_relatorio += """
                and l.provisionado = """ + str(provisionado)

        sql_relatorio += """
            order by
                cli.razao_social,
                cli.cnpj_cpf,
                l.data_vencimento,
                l.numero_documento;"""

        sql_relatorio = sql_relatorio.format(**filtro)
        #print(sql_relatorio)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'extrato_financeiro.jrxml')
        rel.parametros['DATA_INICIAL'] = data_inicial
        rel.parametros['DATA_FINAL'] =  data_final
        rel.parametros['CLIENTE_ID'] = '(' + str(partner_id) + ')'
        rel.parametros['TIPO'] = tipo
        #rel.parametros['COMPANY_ID'] = company_id
        rel.parametros['SQL_RELATORIO'] = sql_relatorio

        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        banco_de_dados_extratos = cr.dbname
        nome = 'Extrato_'+ nome_r + '_' + banco_de_dados_extratos + '_' + data_final + '.' + rel_obj.formato
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


    ##def gera_relatorio_movimentacao_financeira(self, cr, uid, ids, context=None):
        ##data_inicial = context.get('data_inicial', False)
        ##data_final = context.get('data_final', False)
        ###res_partner_bank_id = context.get('res_partner_bank_id', '%')
        ##company_id = context.get('company_id', False)

        ##if not ids:
            ##return {}

        ##if isinstance(ids, (list, tuple)):
            ##id = ids[0]
        ##else:
            ##id = ids

        ##rel_obj = self.browse(cr, uid, id)

        ##if not data_inicial or not data_final:
            ##raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

        ##rel = Report('Movimentação Financeira', cr, uid)
        ##rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'movimentacao_financeira_diaria.jrxml')
        ##rel.parametros['DATA_QUITACAO_INICIAL'] = data_inicial
        ##rel.parametros['DATA_QUITACAO_FINAL'] = data_final
        ##rel.parametros['DATA_INICIAL_FILTRO'] = parse_datetime(data_inicial).date().strftime('%d/%m/%Y')
        ##rel.parametros['DATA_FINAL_FILTRO'] = parse_datetime(data_final).date().strftime('%d/%m/%Y')
        ##rel.parametros['IMPRIME_SALDO'] = rel_obj.saldo_bancario
        ##rel.outputFormat = rel_obj.formato

        ##if len(rel_obj.res_partner_bank_ids):
           ##texto_filtro = u''
           ##bancos_ids = []

           ##for banco_obj in rel_obj.res_partner_bank_ids:
               ##bancos_ids.append(banco_obj.id)
               ###banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
               ##texto_filtro += u', ' + banco_obj.nome or ''

           ##rel.parametros['RES_PARTNER_BANK_ID'] = 'and e.res_partner_bank_id in ' +  str(tuple(bancos_ids)).replace(',)', ')')
           ##rel.parametros['RES_PARTNER_BANK_ID_SUB'] = 'and b.id in ' +  str(tuple(bancos_ids)).replace(',)', ')')
           ##rel.parametros['BANCO_FILTRO'] = texto_filtro or ''

        ##else:
            ##rel.parametros['RES_PARTNER_BANK_ID'] = ''
            ##rel.parametros['RES_PARTNER_BANK_ID_SUB'] = ''
            ##rel.parametros['BANCO_FILTRO'] = 'Todos'

        ##rel.parametros['INTEGRA_REPORT_TITLE'] = 'Movimentação Financeira'
        ##if company_id:
            ##rel.parametros['COMPANY_ID'] =  company_id
        ##else:
            ##company_id_default = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')
            ##print(company_id_default)
            ##rel.parametros['COMPANY_ID'] = company_id_default

        ##pdf, formato = rel.execute()

        ##banco_de_dados = cr.dbname
        ##nome = 'mov_banco_' + banco_de_dados + '_' + data_final + '.pdf'
        ##self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})

    def gera_relatorio_movimentacao_financeira(self, cr, uid, ids, context=None):
        data_inicial = context.get('data_inicial', False)
        data_final = context.get('data_final', False)
        #res_partner_bank_id = context.get('res_partner_bank_id', '%')
        company_id = context.get('company_id', False)

        if not ids:
            return {}

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)

        if not data_inicial or not data_final:
            raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

        rel = Report('Movimentação Financeira', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'movimentacao_financeira_diaria_exata.jrxml')
        rel.parametros['DATA_QUITACAO_INICIAL'] = data_inicial
        rel.parametros['DATA_QUITACAO_FINAL'] = data_final
        rel.parametros['DATA_INICIAL_FILTRO'] = parse_datetime(data_inicial).date().strftime('%d/%m/%Y')
        rel.parametros['DATA_FINAL_FILTRO'] = parse_datetime(data_final).date().strftime('%d/%m/%Y')
        rel.parametros['IMPRIME_SALDO'] = rel_obj.saldo_bancario
        rel.outputFormat = rel_obj.formato

        if len(rel_obj.res_partner_bank_ids) or rel_obj.res_partner_bank_id:
            texto_filtro = u''
            bancos_ids = []

            if len(rel_obj.res_partner_bank_ids) > 0:
                for banco_obj in rel_obj.res_partner_bank_ids:
                    bancos_ids.append(banco_obj.id)
                    banco_obj = self.pool.get('res.partner.bank').browse(cr, uid, banco_obj.id)
                    texto_filtro += banco_obj.nome or '' + u', '
            else:
                bancos_ids.append(rel_obj.res_partner_bank_id.id)
                texto_filtro += rel_obj.res_partner_bank_id.nome or ''

            rel.parametros['RES_PARTNER_BANK_ID'] = 'and e.res_partner_bank_id in ' +  str(tuple(bancos_ids)).replace(',)', ')')
            rel.parametros['RES_PARTNER_BANK_ID_SUB'] = 'and b.id in ' +  str(tuple(bancos_ids)).replace(',)', ')')
            rel.parametros['BANCO_FILTRO'] = texto_filtro or ''

        else:
            rel.parametros['RES_PARTNER_BANK_ID'] = ''
            rel.parametros['RES_PARTNER_BANK_ID_SUB'] = ''
            rel.parametros['BANCO_FILTRO'] = 'Todos'

        rel.parametros['INTEGRA_REPORT_TITLE'] = 'Movimentação Financeira'

        if rel_obj.imprime_cheque:
            rel.parametros['IMPRIME_CHEQUE'] = True

        if company_id:
            rel.parametros['COMPANY_ID'] = company_id
            rel.parametros['FILTRO_COMPANY'] = ' and e.company_id = {company_id}'.format(company_id=company_id)
            rel.parametros['BANCO_FILTRO'] += '; empresa/unidade ' + rel_obj.company_id.name
        else:
            company_id_default = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')
            #print(company_id_default)
            rel.parametros['COMPANY_ID'] = company_id_default
            rel.parametros['FILTRO_COMPANY'] = ''

        pdf, formato = rel.execute()

        banco_de_dados = cr.dbname
        nome = 'mov_banco_' + banco_de_dados + '_' + data_final +  '.' + rel_obj.formato
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})

    def gera_relatorio_financeiro(self, cr, uid, ids, context=None):
        data_inicial = context.get('data_inicial', False)
        data_final = context.get('data_final', False)
        res_partner_bank_id = context.get('res_partner_bank_id', False)
        company_id = context.get('company_id', False)
        partner_id = context.get('partner_id', False)
        situacao = context.get('situacao', False)
        tempo_vencimento = context.get('tempo_vencimento', False)
        nome_relatorio = context['nome_relatorio']

        filtro_dinamico = []

        if company_id:
            filtro_dinamico.append('company__pk=%d' % company_id)

        if partner_id:
            filtro_dinamico.append('partner__pk=%d' % company_id)

        if res_partner_bank_id:
            filtro_dinamico.append('res_partner_bank__pk=' + str(res_partner_bank_id))

        if not situacao:
            filtro_dinamico.append("data_quitacao__range=['%s', '%s']" % (data_inicial, data_final))

        else:
            #
            # Vencidos
            #
            if situacao == '1':
                filtro_dinamico.append("situacao__exact='Vencido'")

                if tempo_vencimento and tempo_vencimento != 0:
                    data_prazo = parse_datetime(data_inicial).date() - relativedelta(days=-tempo_vencimento)
                    filtro_dinamico.append("data_vencimento__gte='%s'" % str(data_prazo))

            #
            # Vencidos e vence hoje
            #
            elif situacao == "2":
                if tempo_vencimento and tempo_vencimento != 0:
                    filtro_dinamico.append("(situacao__exact='Vencido'")
                    data_prazo = parse_datetime(data_inicial).date() - relativedelta(days=-tempo_vencimento)
                    filtro_dinamico.append(")data_vencimento__gte='%s'" % str(data_prazo))
                    filtro_dinamico.append("|situacao__exact='Vence hoje'")
                else:
                    filtro_dinamico.append("situacao__in=['Vencido', 'Vence hoje']")

            #
            # A vencer
            #
            elif situacao == "3":
                filtro_dinamico.append("situacao__exact='A vencer'")

                if tempo_vencimento and tempo_vencimento != 0:
                    data_prazo = parse_datetime(data_inicial).date() - relativedelta(days=+tempo_vencimento)
                    filtro_dinamico.append("data_vencimento__gte='%s'" % str(data_prazo))

            #
            # Liquidados
            #
            elif situacao == "4":
                if not data_inicial or not data_final:
                    raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

                filtro_dinamico.append("data_quitacao__range=['%s', '%s']" % (data_inicial, data_final))

            elif situacao == '5':
                filtro_dinamico.append("situacao__in=['A vencer', 'Vencido', 'Vence hoje']")

                if tempo_vencimento and tempo_vencimento != 0:
                    data_prazo = parse_datetime(data_inicial).date() - relativedelta(days=+tempo_vencimento)
                    filtro_dinamico.append("data_vencimento__gte='%s'" % str(data_prazo))

        banco_de_dados = config['db_name']
        nome = nome_relatorio + '_' + banco_de_dados + '_' + data_inicial + '_a_' + data_final + '.pdf'

        if nome_relatorio == 'Contas_Pagar':
            relatorio_id = 5
        elif nome_relatorio == 'Contas_Receber':
            relatorio_id = 3
        elif nome_relatorio == 'Diario_Analitico':
            relatorio_id = 7
        elif nome_relatorio == 'Diario_Sintetico':
            relatorio_id = 11

        pdf = gera_relatorio_integra(relatorio_id, filtro_dinamico)
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})

    def gera_relatorio_saldo_bancario_movimento(self, cr, uid, ids, context=None):
        data_inicial = context.get('data_inicial', fields.date.today())
        data_final = context.get('data_final', fields.date.today())
        res_partner_bank_id = context.get('res_partner_bank_id', False)
        company_id = context.get('company_id', False)

        if not data_inicial or not data_final:
            raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

        filtro_dinamico = [
            "company__pk=%d" % company_id,
            "data_quitacao__range=['%s', '%s']" % (data_inicial, data_final),
        ]

        if res_partner_bank_id:
            filtro_dinamico.append('res_partner_bank__pk=' + str(res_partner_bank_id))

        relatorio_id = 9
        banco_de_dados = config['db_name']
        nome = 'Saldo_Bancario_Movimento' + banco_de_dados + '_' + data_inicial + '_a_' + data_final + '.pdf'
        pdf = gera_relatorio_integra(relatorio_id, filtro_dinamico)
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})

    def gera_relatorio_saldo_bancario(self, cr, uid, ids, context=None):
        data_inicial = context.get('data_inicial', False)
        data_final = context.get('data_final', False)
        res_partner_bank_id = context.get('res_partner_bank_id', False)

        if not data_inicial or not data_final:
            raise osv.except_osv(u'Atenção', u'É preciso escolher um período para o relatório!')

        filtro_dinamico = [
            "data_compensacao__range=['%s', '%s']" % (data_inicial, data_final)
        ]

        if res_partner_bank_id:
            filtro_dinamico.append('res_partner_bank__pk=' + str(res_partner_bank_id))

        relatorio_id = 2
        banco_de_dados = config['db_name']
        nome = 'Relatorio_Saldo_Bancario_' + banco_de_dados + '_' + data_inicial + '_a_' + data_final + '.pdf'
        pdf = gera_relatorio_integra(relatorio_id, filtro_dinamico)
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})

    def gera_relatorio_diario(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            company_id = rel_obj.company_id.id
            partner_id = rel_obj.partner_id.id


            filtro = {
                'data_inicial': data_inicial,
                'data_final': data_final,
                'tipos': '',
            }

            if tipo == 'R':
                periodo = u'Diário de Clientes de ' + data_inicial.strftime('%d/%m/%Y') + ' a ' + data_final.strftime('%d/%m/%Y')
                rel = Report('Diário de Clientes', cr, uid)
                nome = periodo.lower().replace(' ', '_') + u'.' + rel_obj.formato
                rel.parametros['TIPOS'] = "('R', 'PR', 'E')"

            else:
                periodo = u'Diário de Fornecedores de ' + data_inicial.strftime('%d/%m/%Y') + ' a ' + data_final.strftime('%d/%m/%Y')
                rel = Report('Diário de Fornecedores', cr, uid)
                nome = periodo.lower().replace(' ', '_') + u'.' + rel_obj.formato
                rel.parametros['TIPOS'] = "('P', 'PP', 'S')"

            sql_relatorio ="""
                select
                    coalesce(e.name, '') as empresa,
                    coalesce(p.cnpj_cpf, '') as cliente_cnpj_cpf,
                    coalesce(p.name, '') as cliente_nome,
                    lp.tipo,
                    coalesce(d.nome, '') as documento,
                    coalesce(lp.numero_documento, '') as numero_documento,
                    lp.data_documento,
                    cc.data,
                    coalesce((
                        select
                            coalesce(sum(coalesce(cca.saldo_documento, 0.00)), 0.00)
                        from
                            finan_contacorrente cca
                        where
                            cca.data < '{data_inicial}'
                            and cca.partner_id = cc.partner_id
                            and cca.tipo in {tipos}
                            and cca.company_id = cc.company_id), 0.00) as saldo_anterior,
                    cc.debito_documento as debito,
                    cc.credito_documento as credito,
                    cc.saldo_documento as saldo,
                    lp.provisionado as provisionado,
                    coalesce(lp.complemento,'') as complemento

                from
                    finan_contacorrente cc
                    join res_partner p on p.id = cc.partner_id
                    join finan_lancamento lp on lp.id = abs(cc.id)
                    left join finan_documento d on d.id = lp.documento_id
                    join res_company e on e.id = cc.company_id

                where
                    cc.data between '{data_inicial}' and '{data_final}'
                    and cc.tipo != 'T'
                    and lp.situacao != 'Baixado'
                    and cc.tipo in {tipos}
                    and coalesce(lp.provisionado, False) = False
            """


            if rel_obj.company_id:
                company_ids = self.pool.get('res.company').search(cr, 1, ['|', ('id', '=', company_id), ('parent_id', '=', company_id)])

                if len(company_ids) == 1:
                    sql_relatorio += """
                        and e.id = """ + str(company_ids[0])

                elif len(company_ids) > 1:
                    sql_relatorio += """
                        and e.id in """ + str(tuple(company_ids)).replace(',)', ')')

            if partner_id:
                sql_relatorio += """ and cc.partner_id = """ +  str(partner_id)

            #if rel_obj.ativo != rel_obj.provisionado:
                #sql_relatorio += """
                    #and lp.provisionado = True """

            if tipo == 'R':
                filtro['tipos'] = "('R', 'PR')"
                sql_relatorio += """
                    order by
                        e.name, p.name, p.cnpj_cpf, cc.data, cc.debito desc, cc.credito desc, cc.id;
                """

            else:
                filtro['tipos'] = "('P', 'PP')"
                sql_relatorio += """
                    order by
                        e.name, p.name, p.cnpj_cpf, cc.data, cc.credito desc, cc.debito desc, cc.id;
                """

            sql_relatorio = sql_relatorio.format(**filtro)

            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'diario_analitico.jrxml')
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['PERIODO'] = periodo
            rel.parametros['SQL_RELATORIO'] = sql_relatorio
            rel.outputFormat = rel_obj.formato

            pdf, formato = rel.execute()

            dados = {
                'nome': nome,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_diario_cliente(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario(cr, uid, ids, context=context, tipo='R')

    def gera_relatorio_diario_fornecedor(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario(cr, uid, ids, context=context, tipo='P')

    def gera_relatorio_analitico(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()
            company_id = rel_obj.company_id.id

            meses_primeiro_ano = 12 - data_inicial.month + 1

            meses_segundo_ano = 0
            if data_final.year != data_inicial.year:
                meses_segundo_ano = data_final.month

            mes_inicial = rel_obj.data_inicial[:7]

            if meses_primeiro_ano + meses_segundo_ano > 12:
                raise osv.except_osv(u'Atenção', u'Período informado tem mais de 12 meses!')

            cr.execute("""
                select * from finan_analitico('%s', '%s', %d)
                """ % (rel_obj.data_inicial, rel_obj.data_final, company_id))

            dados = cr.fetchall()

            linhas = []
            for id, codigo, descricao, quitado_anterior, quitado_mes_01, quitado_mes_02, quitado_mes_03, quitado_mes_04, quitado_mes_05, quitado_mes_06, quitado_mes_07, quitado_mes_08, quitado_mes_09, quitado_mes_10, quitado_mes_11, quitado_mes_12, quitado_total, percentual_quitado, vencido_anterior, vencido_mes_01, vencido_mes_02, vencido_mes_03, vencido_mes_04, vencido_mes_05, vencido_mes_06, vencido_mes_07, vencido_mes_08, vencido_mes_09, vencido_mes_10, vencido_mes_11, vencido_mes_12, vencido_total, percentual_vencido in dados:
                linha = DicionarioBrasil()
                linha['id'] = id
                linha['codigo'] = codigo
                linha['descricao'] = descricao
                linha['quitado_anterior'] = quitado_anterior
                linha['quitado_mes_01'] = quitado_mes_01
                linha['quitado_mes_02'] = quitado_mes_02
                linha['quitado_mes_03'] = quitado_mes_03
                linha['quitado_mes_04'] = quitado_mes_04
                linha['quitado_mes_05'] = quitado_mes_05
                linha['quitado_mes_06'] = quitado_mes_06
                linha['quitado_mes_07'] = quitado_mes_07
                linha['quitado_mes_08'] = quitado_mes_08
                linha['quitado_mes_09'] = quitado_mes_09
                linha['quitado_mes_10'] = quitado_mes_10
                linha['quitado_mes_11'] = quitado_mes_11
                linha['quitado_mes_12'] = quitado_mes_12
                linha['quitado_total'] = quitado_total
                linha['percentual_quitado'] = percentual_quitado
                linha['vencido_anterior'] = vencido_anterior
                linha['vencido_mes_01'] = vencido_mes_01
                linha['vencido_mes_02'] = vencido_mes_02
                linha['vencido_mes_03'] = vencido_mes_03
                linha['vencido_mes_04'] = vencido_mes_04
                linha['vencido_mes_05'] = vencido_mes_05
                linha['vencido_mes_06'] = vencido_mes_06
                linha['vencido_mes_07'] = vencido_mes_07
                linha['vencido_mes_08'] = vencido_mes_08
                linha['vencido_mes_09'] = vencido_mes_09
                linha['vencido_mes_10'] = vencido_mes_10
                linha['vencido_mes_11'] = vencido_mes_11
                linha['vencido_mes_12'] = vencido_mes_12
                linha['vencido_total'] = vencido_total
                linha['percentual_vencido'] = percentual_vencido
                linhas.append(linha)

            rel = FinanRelatorioAutomaticoPaisagem()
            rel.title = u'Analítico de ' + data_inicial.strftime('%d/%m/%Y') + ' a ' + data_final.strftime('%d/%m/%Y')
            rel.colunas = [
                ['codigo', 'C', 10, u'Conta', False],
                ['descricao', 'C', 25, u'Conta', False],
                ['quitado_anterior', 'F', 10, u'Anterior', False],
            ]

            mes_atual = data_inicial.month
            ano_atual = data_inicial.year
            i = 0

            while i < 12:
                matual = str(mes_atual).zfill(2)
                rel.colunas.append(['quitado_mes_' + matual, 'F', 10, MES_ABREVIADO[mes_atual] + u'/' + str(ano_atual), False])
                i += 1
                mes_atual += 1
                if mes_atual > 12:
                    mes_atual = 1
                    ano_atual += 1

                ano_mes_atual = str(ano_atual)+ '-' + str(mes_atual).zfill(2)
                if ano_mes_atual > rel_obj.data_final[:7]:
                    break

            rel.colunas.append(['quitado_total', 'F', 10, u'Total', False])
            rel.colunas.append(['percentual_quitado', 'F', 10, u'%', False])

            rel.monta_detalhe_automatico(rel.colunas)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = u'Empresa/Unidade ' + company_obj.name

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'finan_analitico.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'finan_analitico.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            rel_obj.write(dados)

        return True

    _SQL_RAZAO_ANTIGO = """
select
    razao.data_documento,
    rp.name,
    razao.numero_documento,
    razao.debito,
    razao.credito,
    razao.historico

from
    (
        select
            c.partner_id as empresa_id,
            debito.partner_id,
            {data_documento},
            cast(debito.numero as varchar) as numero_documento,
            debito.vr_fatura as debito,
            0 as credito,
            case
                when debito.emissao = '0' then 'Nossa emissão'
                else 'Dup. emitida'
            end as historico

        from
            sped_documento as debito
            left join finan_lancamento fc on fc.sped_documento_id = debito.id
            left join sped_documentoduplicata sdd on sdd.finan_lancamento_id = debito.id
            join res_company c on c.id = debito.company_id

        where
                debito.emissao = '{emissao}'
            and (
                    (debito.state = 'autorizada' and debito.modelo in ('55','SE'))
                or
                    (debito.modelo not in ('55','SE'))
            )
            and (fc.id is not null or sdd.id is not null)

        union all

        select
            b.partner_id as empresa_id,
            l.partner_id,
            case
                when credito.data_baixa is not null and mb.id is not null then credito.data_baixa
                when credito.data is not null then credito.data
                else credito.data_quitacao
            end as data_documento,
            l.numero_documento as numero_documento,
            0 as debito,
            credito.valor as credito,
            case
                when credito.tipo = 'PR' then
                    case
                        when l.valor_documento = credito.valor_documento then 'Recebimento Total'
                        else 'Recebimento Parcial'
                    end
                else
                    case
                        when l.valor_documento = credito.valor_documento then 'Pagamento Total'
                        else 'Pagamento Parcial'
                    end
            end as historico

        from
            finan_lancamento as credito
            join finan_lancamento l on l.id = credito.lancamento_id
            join res_partner_bank b on b.id = credito.res_partner_bank_id
            left join finan_motivobaixa mb on mb.id = credito.motivo_baixa_id and upper(mb.nome) like '%PERDA%'

        where
            credito.tipo = '{tipo_lancamento}'

    ) as razao
    join res_partner rpd on rpd.id = razao.empresa_id
    left join res_partner rp on rp.id = razao.partner_id

where
    rpd.cnpj_cpf = '{cnpj}'
    and razao.data_documento between '{data_inicial}' and '{data_final}'

order by
    data_documento;
"""

    _SQL_RAZAO = """
select
    rpd.name as empresa,
    razao.empresa_id,
    razao.data_documento,
    cli.id as partner_id,
    cli.name as cliente,
    razao.numero_documento,
    razao.debito,
    razao.credito,
    razao.historico

from
    (
        select distinct
            c.partner_id as empresa_id,
            fc.partner_id,
            {data_documento},
            case
            when debito.numero is not null then
            cast(debito.numero as varchar)
            else
            fc.numero_documento end  as numero_documento,
            case
                when debito.id is null then fc.valor_documento
                else debito.vr_nf
            end as debito,
            0 as credito,
            case
            when debito.id is not null then 'Nota Fiscal'
            else 'Dup. emitida'
            end as historico

        from
            finan_lancamento as fc
            {nota_fical}
            join res_company c on c.id = fc.company_id

        where
            fc.tipo = '{tipo}'
            and coalesce(fc.provisionado, False) = False
            {documento_ids_entrada}


        union all
        
        select
            b.partner_id as empresa_id,
            l.partner_id,
            case                
                when credito.data is not null then credito.data
                else credito.data_quitacao
            end as data_documento,
            l.numero_documento as numero_documento,
            coalesce(credito.valor_juros, 0) * coalesce(ldp.porcentagem, 1) as debito,
            0 as credito,
            'Juros'as historico
        from
            finan_lancamento as credito
            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = credito.id
            left join finan_lancamento l on (ldp.divida_id is not null and l.id = ldp.divida_id) or (ldp.divida_id is null and l.id = credito.lancamento_id)
            {pagamento_nota}
            join res_partner_bank b on b.id = credito.res_partner_bank_id             

        where
            credito.tipo = '{tipo_lancamento}'
            and l.situacao not in ('Baixado','Baixado parcial')
            and credito.provisionado = False
            {documento_ids_saida}
            
        union all
        
        select
            b.partner_id as empresa_id,
            l.partner_id,
            case                
                when credito.data is not null then credito.data
                else credito.data_quitacao
            end as data_documento,
            l.numero_documento as numero_documento,
            coalesce(credito.valor_multa, 0) * coalesce(ldp.porcentagem, 1) as debito,
            0 as credito,
            'Multa'as historico
        from
            finan_lancamento as credito
            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = credito.id
            left join finan_lancamento l on (ldp.divida_id is not null and l.id = ldp.divida_id) or (ldp.divida_id is null and l.id = credito.lancamento_id)
            {pagamento_nota}
            join res_partner_bank b on b.id = credito.res_partner_bank_id             

        where
            credito.tipo = '{tipo_lancamento}'
            and l.situacao not in ('Baixado','Baixado parcial')
            and credito.provisionado = False
            {documento_ids_saida}
            
        union all
        
        select
            b.partner_id as empresa_id,
            l.partner_id,
            case                
                when credito.data is not null then credito.data
                else credito.data_quitacao
            end as data_documento,
            l.numero_documento as numero_documento,
            0 as debito,
            coalesce(credito.valor_desconto, 0) * coalesce(ldp.porcentagem, 1) as credito,
            'Desconto'as historico
        from
            finan_lancamento as credito
            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = credito.id
            left join finan_lancamento l on (ldp.divida_id is not null and l.id = ldp.divida_id) or (ldp.divida_id is null and l.id = credito.lancamento_id)
            {pagamento_nota}
            join res_partner_bank b on b.id = credito.res_partner_bank_id             

        where
            credito.tipo = '{tipo_lancamento}'
            and l.situacao not in ('Baixado','Baixado parcial')
            and credito.provisionado = False
            {documento_ids_saida}
        
        union all
        
        select
            b.partner_id as empresa_id,
            l.partner_id,
            case                
                when credito.data is not null then credito.data
                else credito.data_quitacao
            end as data_documento,
            l.numero_documento as numero_documento,
            0 as debito,
            coalesce(credito.valor, 0) * coalesce(ldp.porcentagem, 1) as credito,
            case
                when credito.tipo = 'PR' then
                    case
                        when coalesce(l.valor_documento, 0) = credito.valor_documento * coalesce(ldp.porcentagem, 1) then 'Recebimento Total'
                        else 'Recebimento Parcial'
                    end
                else
                    case
                        when coalesce(l.valor_documento, 0) = credito.valor_documento * coalesce(ldp.porcentagem, 1) then 'Pagamento Total'
                        else 'Pagamento Parcial'
                    end
            end as historico

        from
            finan_lancamento as credito
            left join finan_lancamento_lote_divida_pagamento ldp on ldp.pagamento_id = credito.id
            left join finan_lancamento l on (ldp.divida_id is not null and l.id = ldp.divida_id) or (ldp.divida_id is null and l.id = credito.lancamento_id)
            {pagamento_nota}
            join res_partner_bank b on b.id = credito.res_partner_bank_id             

        where
            credito.tipo = '{tipo_lancamento}'
            and l.situacao not in ('Baixado','Baixado parcial')
            and credito.provisionado = False
            {documento_ids_saida}
        
        union all
            
        select distinct
            c.partner_id as empresa_id,
            fc.partner_id,
            fc.data_documento as data_documento,
            case
            when fc.numero_documento is not null then
            cast(fc.numero_documento as varchar)
            else
            fc.numero_documento end as numero_documento,
            0 as debito,
            fc.valor_documento as credito,
            case
            when mb.nome is not null then mb.nome
            else 'Dup.Baixada'
            end as historico

        from
            finan_lancamento as fc
            join res_company c on c.id = fc.company_id
            {pagamento_nota_baixa}
            left join finan_motivobaixa mb on mb.id = fc.motivo_baixa_id 
 
        where
            fc.situacao in ('Baixado','Baixado parcial')
            and coalesce(fc.provisionado, False) = False
            {documento_ids_entrada}

) as razao
    join res_partner rpd on rpd.id = razao.empresa_id
    left join res_partner cli on cli.id = razao.partner_id

where
    rpd.cnpj_cpf = '{cnpj}'
    and razao.data_documento between '{data_inicial}' and '{data_final}'
    and (razao.debito > 0 or razao.credito > 0)
    {partner_ids}

order by
    rpd.name,
    razao.data_documento,
    cli.name,
    razao.historico,
    razao.numero_documento        
    
"""


    def gera_relatorio_diario_razao_cliente(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario_razao(cr, uid, ids, context=context, tipo='R')

    def gera_relatorio_diario_razao_fornecedor(self, cr, uid, ids, context={}):
        return self.gera_relatorio_diario_razao(cr, uid, ids, context=context, tipo='P')


    def gera_relatorio_diario_razao(self, cr, uid, ids, context={}, tipo='R'):
        if not ids:
            return {}

        company_id = context['company_id']
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        cnpj = company_obj.partner_id.cnpj_cpf
        data_inicial = context['data_inicial']
        data_final = context['data_final']


        for rel_obj in self.browse(cr, uid, ids):

            partner_ids = []
            if len(rel_obj.partner_ids) > 0:

                for partner_id in rel_obj.partner_ids:
                    partner_ids.append(partner_id.id)
                    
            documento_ids = []
            if len(rel_obj.documento_ids) > 0:

                for documento_id in rel_obj.documento_ids:
                    documento_ids.append(documento_id.id)

            filtro = {
                'cnpj': cnpj,
                'data_inicial': data_inicial,
                'data_final': data_final,
                'partner_ids': '',
                'documento_ids_entrada': '',
                'documento_ids_saida': '',
                'pagamento_nota': '',
                'pagamento_nota_baixa': '',
            }

            if len(partner_ids) > 0 :
                filtro['partner_ids'] = """and razao.partner_id in """ +  str(tuple(partner_ids)).replace(',)', ')')
                
            if len(documento_ids) > 0 :
                filtro['documento_ids_entrada'] = """and fc.documento_id in """ +  str(tuple(documento_ids)).replace(',)', ')')
                filtro['documento_ids_saida'] = """and l.documento_id in """ +  str(tuple(documento_ids)).replace(',)', ')')


            if tipo == 'P':
                filtro['tipo_lancamento'] = 'PP'
                filtro['tipo'] = 'P'
                filtro['emissao'] = '1'
                nome_relatorio = u'Razao_diario_Fornecedores_'

                if rel_obj.data_entrada_nf:
                   filtro['data_documento'] = """case
                                                 when debito.data_entrada_saida is not null then
                                                 cast(debito.data_entrada_saida as date)
                                                 else
                                                 fc.data_documento end as data_documento"""
                else:
                   filtro['data_documento'] = 'fc.data_documento as data_documento'
            else:
                filtro['emissao'] = '0'
                filtro['tipo_lancamento'] = 'PR'
                filtro['tipo'] = 'R'
                filtro['data_documento'] = 'fc.data_documento as data_documento'
                
                nome_relatorio = u'Razao_diario_Clientes_'
            
            if rel_obj.conf_contabilidade:
                filtro['nota_fical'] = """join sped_documento debito on debito.id = fc.sped_documento_id
                                          left join sped_documentoduplicata sdd on sdd.finan_lancamento_id = debito.id"""
                                           
                filtro['pagamento_nota'] = """join sped_documento sd on sd.id = l.sped_documento_id"""                                           
                filtro['pagamento_nota_baixa'] = """join sped_documento sd on sd.id = fc.sped_documento_id"""                                           
                                           
                                           
            else:
                filtro['nota_fical'] = """left join sped_documento debito on debito.id = fc.sped_documento_id
                                          left join sped_documentoduplicata sdd on sdd.finan_lancamento_id = debito.id"""
                

            sql_relatorio = self._SQL_RAZAO.format(**filtro)

            rel = Report('Relatório de Razão Diário', cr, uid)

            if rel_obj.por_data:
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_razao_diario_data.jrxml')
            else:
                rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_relatorio_razao_diario.jrxml')
            rel.parametros['DATA_INICIAL'] = data_inicial
            rel.parametros['DATA_FINAL'] = data_final
            rel.parametros['SQL_RELATORIO'] = sql_relatorio
            rel.parametros['TIPO'] = tipo
            rel.outputFormat = rel_obj.formato

            pdf, formato = rel.execute()

            dados = {
                'nome': nome_relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_curva_abc(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Analise de Contratos', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_curva_abc.jrxml')
        rel.parametros['COMPANY_ID'] = int(company_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato


        pdf, formato = rel.execute()

        dados = {
            'nome': u'Curva_abc_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_saldo_banco(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        if rel_obj.res_partner_bank_id:
            banco_id = str(rel_obj.res_partner_bank_id.id)
        else:
            banco_id = '%'

        if rel_obj.company_id:
            partner_id = str(rel_obj.company_id.partner_id.id)
        else:
            partner_id = '%'

        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report('Relatório de Saldos Bancários', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_saldo_banco.jrxml')
        rel.parametros['BANK_ID'] = str(banco_id)
        rel.parametros['PARTNER_ID'] = str(partner_id)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.outputFormat = rel_obj.formato

        pdf, formato = rel.execute()

        dados = {
            'nome': u'Saldo_Bancario_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def movimentacao_diaria_financeira(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            filtro = {
                'data_inicial': rel_obj.data_inicial,
                'data_final': rel_obj.data_final,
            }

            #sql = """
            #select
                #cast(fs.saldo_final as numeric(18,2)) as saldo_inicial,
                #fs.data as data_inicial

            #from
                #finan_saldo as fs
                #left join res_partner_bank rb on rb.id = fs.res_partner_bank_id

            #where
                #fs.data < '{data_inicial}'
                #and fs.res_partner_bank_id = {res_partner_bank_id}

            #order by
                #fs.data desc

            #limit 1
            #"""
            #sql = sql.format(res_partner_bank_id=res_partner_bank_id, data_inicial=data_inicial)
            #print(sql)
            #cr.execute(sql)
            #contrato_ids_listas = cr.fetchall()

            #saldo_anterior = D(0)
            #data_anterior = None
            #if len(contrato_ids_listas) > 0:
                #saldo_anterior = contrato_ids_listas[0][0]
                #data_anterior = contrato_ids_listas[0][1]

            #
            # Acumulamos o saldo entre o último fechamento de caixa e o início do período
            #
            sql = """
            select
                coalesce(sum(coalesce(e.valor_compensado_credito, 0) - coalesce(e.valor_compensado_debito, 0)), 0) as saldo_inicial

            from
                finan_extrato e
            where
                e.data_quitacao < '{data_inicial}'
            """

            if rel_obj.res_partner_bank_id:
                filtro['bank_id'] = rel_obj.res_partner_bank_id.id

                sql += """
                and e.res_partner_bank_id = {bank_id}
                """

            if rel_obj.partner_id:
                filtro['partner_id'] = rel_obj.partner_id.id

                sql += """
                and e.partner_id = {partner_id}
                """

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            saldo_anterior = D(0)
            saldo_anterior_titulo = D(0)
            if len(dados):
                saldo_anterior = D(dados[0][0])
                saldo_anterior_titulo = D(dados[0][0])

            sql =  """
                select
                    e.tipo as tipo,
                    e.id as numero,
                    e.data_quitacao,
                    e.data_documento,
                    b.nome as banco,
                    coalesce(c.codigo_completo, '') as codigo_conta_financeira,
                    coalesce(c.nome, '') as nome_conta_financeira,
                    coalesce(e.numero_documento, '') as numero_documento,
                    coalesce(p.name, '') as portador,
                    coalesce(p.cnpj_cpf, '') as portador_cnpj_cpf,
                    coalesce(e.valor_compensado_credito, 0) as entrada,
                    coalesce(e.valor_compensado_debito, 0) as saida,
                    coalesce(f.nome, '') as formapagamento,
                    case
                    when e.tipo in ('E', 'S', 'T') then coalesce(l.complemento, '')
                    else coalesce(le.complemento, '')
                    end as complemento,
                    case
                    when e.tipo in ('E', 'S', 'T') then coalesce(l.numero_documento, '')
                    else coalesce(le.numero_documento, '')
                    end as numero_cheque,
                    coalesce(d.nome, '') as documento

                from
                    finan_extrato e
                    left join res_partner p on p.id = e.partner_id
                    left join res_partner_bank b on b.id = e.res_partner_bank_id
                    left join finan_conta c on c.id = e.conta_id
                    left join finan_lancamento l on l.id = e.lancamento_id
                    left join finan_formapagamento f on f.id = l.formapagamento_id
                    left join finan_lancamento le on le.id = e.id
                    left join finan_documento d on d.id = l.documento_id

            where
                e.data_quitacao between '{data_inicial}' and '{data_final}'
            """

            if rel_obj.res_partner_bank_id:
                sql += """
                and e.res_partner_bank_id = {bank_id}
                """

            if rel_obj.partner_id:
                sql += """
                and e.partner_id = {partner_id}
                """

            sql += """
                order by
                e.data_quitacao,
                e.valor_compensado_credito desc,
                e.valor_compensado_debito desc;
            """

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []

            if not dados:
            #    raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')
                rel = FinanRelatorioAutomaticoPaisagem()
                linha = DicionarioBrasil()
                rel.title = u'Movimentação Financeira Diária'
                linha['vazio'] = u'SEM MOVIMENTO'
                rel.colunas = [
                    ['vazio', 'C', 20 , u'', False],
                ]
                linhas.append(linha)
                rel.monta_detalhe_automatico(rel.colunas)
            else:

                saldo_atual = saldo_anterior
                for tipo, numero, data_quitacao, data_documento, banco, codigo_conta_financeira, nome_conta_financeira, numero_documento, portador, portador_cnpj_cpf, entrada, saida, formapagamento, complemento, numero_cheque, documento  in dados:
                    linha = DicionarioBrasil()
                    linha['tipo'] = tipo
                    linha['numero'] = str(numero)
                    linha['data_quitacao'] = data_quitacao
                    linha['data_documento'] = data_documento
                    linha['banco'] = banco
                    linha['codigo_conta_financeira'] = codigo_conta_financeira
                    linha['nome_conta_financeira'] = nome_conta_financeira
                    linha['numero_documento'] = numero_documento
                    linha['portador'] = portador
                    linha['portador_cnpj_cpf'] = portador_cnpj_cpf
                    linha['debito'] = saida
                    linha['credito'] = entrada
                    linha['formapagamento'] = formapagamento
                    linha['complemento'] = complemento
                    linha['numero_cheque'] = numero_cheque
                    linha['documento'] = documento
                    saldo_atual += entrada
                    saldo_atual -= saida
                    linha['saldo'] = float(saldo_atual)

                    linhas.append(linha)

                rel = FinanRelatorioAutomaticoPaisagem()
                rel.title = u'Movimentação Financeira Diária'

                rel.colunas = [
                    #['numero', 'C', 8,  u'Nº Doc.',False],
                    ['data_quitacao', 'D', 10, u'Data quit.', False],
                    ['numero_documento', 'C', 15, u'Nº doc.', False],
                    ['data_documento', 'D', 10, u'Data doc.', False],
                ]
                if not rel_obj.res_partner_bank_id:
                    rel.colunas += [
                        ['banco', 'C', 40, u'Bancos', False],
                    ]
                rel.colunas += [
                    #['codigo_conta_financeira', 'C', 10, u'Cod. Fin.', False],
                    #['nome_conta_financeira', 'C', 25, u'Conta Financeira.', False],
                    ['formapagamento', 'C', 15, u'Forma Pagto', False],
                    ['tipo', 'C', 2, u'T', False],
                    ['portador', 'C', 40, u'Portador', False],
                    ['documento', 'C', 25, u'Tipo doc.', False],
                    ['complemento', 'C', 25, u'Histórico', False],
                    #['portador_cnpj_cpf', 'C', 10, u'CNPJ', False],
                    ['numero_cheque', 'C', 7, u'CHQ.', False],
                    ['debito', 'F', 15, u'Débito', True],
                    ['credito', 'F', 15, u'Crédito', True],
                    ['saldo', 'F', 15, u'Saldo', lambda objeto, valor: unicode(formata_valor(saldo_atual))],
                ]

                rel.monta_detalhe_automatico(rel.colunas)

                rel.grupos = [
                   # ['data_documento', u'Data', False],
                ]
                rel.monta_grupos(rel.grupos)

            banco_nome = u''
            if rel_obj.res_partner_bank_id:
                banco_nome = rel_obj.res_partner_bank_id.nome

            rel.band_page_header.elements[-1].text = banco_nome + u' ' + formata_data(rel_obj.data_inicial) + u' a ' + formata_data(rel_obj.data_final) + u'          »»»          Saldo inicial: ' + formata_valor(saldo_anterior_titulo)
            rel.band_page_header.elements[-1].style = ESTILO['CABECALHO_FILTRO_ESQUERDA']

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'mov_financeira_periodo_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

            return True

    def gera_relatorio_lancamentos_baixados(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            company_id = rel_obj.company_id.id
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            sql = """
                select
                    co.name,
                    mb.nome as motivo_baixa,
                    fl.data_baixa as data_baixa,
                    coalesce(fc.numero, '') as numero_contrato,
                    fl.numero_documento,
                    rp.name as cliente,
                    rp.cnpj_cpf,
                    coalesce(fl.valor_original_contrato, 0) as valor_contrato,
                    fl.valor_documento as valor_baixado,
                    fl.data_vencimento

                from
                    finan_lancamento fl
                    left join finan_contrato fc on fc.id = fl.contrato_id
                    join finan_motivobaixa mb on mb.id = fl.motivo_baixa_id
                    join res_partner rp on rp.id = fl.partner_id

                    join res_company c on c.id = fl.company_id
                    join res_partner co on co.id = c.partner_id
                    left join res_company cc on cc.id = c.parent_id
                    left join res_company ccc on ccc.id = cc.parent_id


                where
                    fl.data_baixa between '{data_inicial}' and '{data_final}'
                    and (
                        c.id = {company_id}
                        or cc.id = {company_id}
                        or ccc.id = {company_id}
                    )
                    and fl.tipo = 'R' """


            if rel_obj.partner_id:
                sql += """
                        and rp.id = """  + str(rel_obj.partner_id.id)

            if rel_obj.motivo_baixa_id:
                sql += """
                        and mb.id = """  + str(rel_obj.motivo_baixa_id.id)

            sql += """
                    order by
                        co.name,
                        mb.nome,
                        rp.name;
                    """

            sql = sql.format(company_id=company_id, data_inicial=formata_data(data_inicial), data_final=formata_data(data_final))
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

            linhas = []
            for empresa, motivo_baixa, data_baixa, numero_contrato, numero_documento, cliente, cnpj_cpf, valor_contrato, valor_baixado, data_vencimento in dados:
                linha = DicionarioBrasil()
                linha['empresa'] = empresa
                linha['motivo_baixa'] = motivo_baixa

                linha['data_baixa'] = formata_data(data_baixa)
                linha['numero_contrato'] = numero_contrato
                linha['numero_documento'] = numero_documento
                linha['cliente'] = cliente
                linha['cnpj_cpf'] = cnpj_cpf
                linha['valor_contrato'] = valor_contrato
                linha['valor_baixado'] = valor_baixado
                linha['data_vencimento'] = formata_data(data_vencimento)
                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Relatório de Lançamentos Baixados'

            rel.colunas = [
                ['data_baixa', 'D', 10, u'Dt. Baixa', False],
                ['cliente', 'C', 40, u'Cliente', False],
                ['cnpj_cpf', 'C', 40, u'CNPJ/CPF', False],
                ['valor_baixado', 'F', 10, u'Vlr. Baixado', True],
                ['data_vencimento', 'D', 10, u'Dt. Venc.', False],
                #['numero_contrato', 'C', 15, u'Nº Contrato', False],
                ['numero_documento', 'C', 15, u'Nº Documento', False],
                ['valor_contrato', 'F', 10, u'Vlr. Contrato', True],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['empresa', u'Empresa', False],
                ['motivo_baixa', u'Motivo Baixa', False],
            ]
            rel.monta_grupos(rel.grupos)

            company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
            rel.band_page_header.elements[-1].text = company_obj.name + u' DATA ' + parse_datetime(data_inicial).strftime('%d/%m/%Y') + u' - ' + parse_datetime(data_final).strftime('%d/%m/%Y')

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'lancamentos_baixados_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

        return True

    def gera_relatorio_plano_contas(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):

            sql = """
            select
                fc.codigo_completo,
                fc.codigo,
                fc.nome,
                pai.nome,
                case
                when fc.tipo = 'A' then
                'ATIVO'
                when fc.tipo = 'P' then
                'PASSIVO'
                when fc.tipo = 'R' then
                'RECEITA'
                when fc.tipo = 'D' then
                'DESPESA'
                when fc.tipo = 'C' then
                'CUSTO'
                when fc.tipo = 'T' then
                'TRANSFERÊNCIA'
                when fc.tipo = 'O' then
                'OUTRAS'end  as tipo
            from finan_conta fc
                left join finan_conta pai on pai.id = fc.parent_id
                order by
                fc.codigo_completo """

            #sql = sql.format(res_partner_bank_id=res_partner_bank_id, data_inicial=str(data_inicial), data_final=str(data_final), partner_id=partner_id)
            print(sql)
            cr.execute(sql)

            dados = cr.fetchall()
            linhas = []
            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existe dados nos parâmetros informados!')

            for codigo_completo, codigo, nome, conta_pai, tipo in dados:
                linha = DicionarioBrasil()
                linha['codigo_completo'] = codigo_completo
                linha['codigo'] = codigo
                linha['nome'] = nome
                linha['conta_pai'] = conta_pai
                linha['tipo'] = tipo

                linhas.append(linha)

            rel = FinanRelatorioAutomaticoRetrato()
            rel.title = u'Plano de Contas Financeiro'

            rel.colunas = [
                ['codigo_completo', 'C', 15, u'Código Completo.', False],
                ['codigo', 'C', 10, u'C.Reduz..', False],
                ['nome', 'C', 50, u'Descrição', False],
                ['conta_pai', 'C', 50, u'Conta Superior', False],
            ]

            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['tipo', u'', False],
            ]
            rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'plano_contas_financeiro.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)

            return True

    def gera_relatorio_fluxo_caixa_analitico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        data_inicial = context['data_inicial']
        data_final = context['data_final']
        provisionado = context.get('provisionado')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        filtro = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'join_departamento': '',
        }

        rel = Report('Fluxo de Caixa', cr, uid)
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa

        #if rel_obj.saldo_inicial:
        rel.parametros['SALDO_INICIAL'] = float(rel_obj.saldo_inicial or 0)

        rel.outputFormat = rel_obj.formato

        if rel_obj.opcoes_caixa == '1':
            filtro['tipo'] = "('Q')"
            rel.parametros['TIPO'] = "('Q')"
        elif rel_obj.opcoes_caixa == '2':
            filtro['tipo'] = "('Q','V')"
            rel.parametros['TIPO'] = "('Q','V')"
        else:
            filtro['tipo'] = "('V')"
            rel.parametros['TIPO'] = "('V')"

        if rel_obj.periodo == '1':
            sql_relatorio = """
                select
                    c.id,
                    c.cnpj_cpf,
                    c.raiz_cnpj,
                    rpc.name as empresa,
                    f.mes,
            """

            sql_relatorio_SUB = """
                select
                    f.mes,
            """
        else:
            sql_relatorio = """
                select
                    c.id,
                    c.cnpj_cpf,
                    c.raiz_cnpj,
                    rpc.name as empresa,
                    f.data,
            """

            sql_relatorio_SUB = """
                select
                    f.data,
            """

        sql_relatorio += """
                    sum(coalesce(f.valor_entrada, 0))  as valor_entrada,
                    sum(coalesce(f.valor_saida, 0))  as valor_saida,
                    sum(coalesce(f.valor_entrada, 0)) - sum(coalesce(f.valor_saida, 0)) as diferenca"""

        sql_relatorio_SUB += """
                    sum(coalesce(f.valor_entrada, 0))  as valor_entrada,
                    sum(coalesce(f.valor_saida, 0))  as valor_saida,
                    sum(coalesce(f.valor_entrada, 0)) - sum(coalesce(f.valor_saida, 0)) as diferenca"""

        if rel_obj.periodo == '3':
            sql_relatorio += """,
                    fl.numero_documento,
                    fd.nome,
                    fl.tipo,
                    rp.name"""

        if not rel_obj.filtrar_rateio:
            sql_relatorio += """
                    from
                        finan_fluxo_mensal_diario f

                        join finan_lancamento fl on fl.id = f.lancamento_id
                        left join res_partner rp on rp.id = fl.partner_id
                        left join finan_documento fd on fd.id = fl.documento_id
                        join finan_conta fc on (fl.tipo != 'T' and fc.id = fl.conta_id) or (fl.tipo = 'T' and fc.id = f.id)
                        {join_departamento}

                        join res_company c on c.id = fl.company_id
                        join res_partner rpc on rpc.id = c.partner_id
            """

            sql_relatorio_SUB += """
                    from
                        finan_fluxo_mensal_diario f

                        join finan_lancamento fl on fl.id = f.lancamento_id
                        left join res_partner rp on rp.id = fl.partner_id
                        left join finan_documento fd on fd.id = fl.documento_id
                        join finan_conta fc on (fl.tipo != 'T' and fc.id = fl.conta_id) or (fl.tipo = 'T' and fc.id = f.id)
                        {join_departamento}

                        join res_company c on c.id = fl.company_id
                        join res_partner rpc on rpc.id = c.partner_id
            """

        else:
            sql_relatorio += """
                    from
                        finan_fluxo_mensal_diario_rateio f

                        join finan_lancamento fl on fl.id = f.lancamento_id
                        left join res_partner rp on rp.id = fl.partner_id
                        left join finan_documento fd on fd.id = fl.documento_id
                        join finan_conta fc on fc.id = f.conta_id
                        {join_departamento}

                        join res_company c on c.id = f.company_id
                        join res_partner rpc on rpc.id = c.partner_id
            """

            sql_relatorio_SUB += """
                    from
                        finan_fluxo_mensal_diario_rateio f

                        join finan_lancamento fl on fl.id = f.lancamento_id
                        left join res_partner rp on rp.id = fl.partner_id
                        left join finan_documento fd on fd.id = fl.documento_id
                        join finan_conta fc on fc.id = f.conta_id
                        {join_departamento}

                        join res_company c on c.id = f.company_id
                        join res_partner rpc on rpc.id = c.partner_id
            """

        #if rel_obj.periodo == '3' and rel_obj.conta_id:
            #sql_relatorio += """
            #"""
            #sql_relatorio_SUB += """
                    #left join finan_lancamento_lote_divida_pagamento ldp on ldp.lote_id = fl.id
                    #left join finan_lancamento divida on divida.id = ldp.divida_id
                    #left join finan_conta fc on (fc.id = fl.conta_id or fc.id = divida.conta_id)
            #"""

        sql_relatorio += """
                where
                    f.data between '{data_inicial}' and '{data_final}'
                    and f.tipo in {tipo}
        """

        sql_relatorio_SUB += """
                where
                    f.data between '{data_inicial}' and '{data_final}'
                    and f.tipo in {tipo}
        """

        if len(rel_obj.company_ids) == 1:
            filtro['company_id'] = rel_obj.company_ids[0].id
            sql_relatorio += """
                     and (
                       c.id = {company_id}
                       or c.parent_id = {company_id}
                    )"""
            sql_relatorio_SUB += """
                     and (
                       c.id = {company_id}
                       or c.parent_id = {company_id}
                    )"""

        elif len(rel_obj.company_ids) > 1:
            company_ids = []
            for company_obj in rel_obj.company_ids:
                company_ids.append(company_obj.id)

            filtro['company_ids'] = str(tuple(company_ids)).replace(',)', ')')
            sql_relatorio += """
                     and (
                       c.id in {company_ids}
                       or c.parent_id in {company_ids}
                    )"""
            sql_relatorio_SUB += """
                     and (
                       c.id in {company_ids}
                       or c.parent_id in {company_ids}
                    )"""
        else:
            raise osv.except_osv(u'Atenção', u'É preciso selecionar pelo menos uma empresa!')

        if len(rel_obj.res_partner_bank_ids) == 1:
            filtro['bank_id'] = rel_obj.res_partner_bank_ids[0].id
            sql_relatorio += """
                     and f.res_partner_bank_id = {bank_id}
            """
            sql_relatorio_SUB += """
                     and f.res_partner_bank_id = {bank_id}
            """

        elif len(rel_obj.res_partner_bank_ids) > 1:
            bancos_ids = []
            for banco_obj in rel_obj.res_partner_bank_ids:
                bancos_ids.append(banco_obj.id)

            filtro['bank_ids'] = str(tuple(bancos_ids)).replace(',)', ')')
            sql_relatorio += """
                     and f.res_partner_bank_id in {bank_ids}
            """
            sql_relatorio_SUB += """
                     and f.res_partner_bank_id in {bank_ids}
            """

        if rel_obj.nao_provisionado != rel_obj.provisionado:
            sql_relatorio += """
                    and f.provisionado = """ + str(provisionado)

            sql_relatorio_SUB += """
                    and f.provisionado = """ + str(provisionado)

        if rel_obj.conta_id:
            sql_relatorio += """
                    and fc.id = {conta_id}
            """
            sql_relatorio_SUB += """
                    and fc.id = {conta_id}
            """
            filtro['conta_id'] = rel_obj.conta_id.id

        if cr.dbname.upper() == 'PATRIMONIAL' or cr.dbname.upper()[:5] == 'TESTE':
            grupo_ids = self.pool.get('res.groups').search(cr, 1, [('name', '=', 'Patrimonial / Contas financeiras bloqueadas por departamento')])
            bloqueia_departamento = False

            if grupo_ids:
                grupo_obj = self.pool.get('res.groups').browse(cr, 1, grupo_ids[0])

                for usuario_obj in grupo_obj.users:
                    if usuario_obj.id == uid:
                        bloqueia_departamento = True

            if bloqueia_departamento:
                filtro['join_departamento'] = """
                    left join hr_department hd on hd.id = fc.hr_department_id
                    left join hr_employee he on he.id = hd.manager_id
                    left join resource_resource rr on rr.id = he.resource_id
                """
                filtro['usuario_id'] = uid

                sql_relatorio += """
                    and (fc.sintetica = True
                        or (
                            fc.hr_department_id is not null
                            and rr.user_id = {usuario_id}
                        )
                    )
                """
                sql_relatorio_SUB += """
                    and (fc.sintetica = True
                        or (
                            fc.hr_department_id is not null
                            and rr.user_id = {usuario_id}
                        )
                    )
                """

            elif rel_obj.hr_department_id:
                filtro['hr_department_id'] = rel_obj.hr_department_id.id

                if not rel_obj.filtrar_rateio:
                    sql_relatorio += """
                            and fc.hr_department_id = {hr_department_id}
                    """
                    sql_relatorio_SUB += """
                            and fc.hr_department_id = {hr_department_id}
                    """
                else:
                    sql_relatorio += """
                            and f.hr_department_id = {hr_department_id}
                    """
                    sql_relatorio_SUB += """
                            and f.hr_department_id = {hr_department_id}
                    """

        if rel_obj.project_id:
            filtro['project_id'] = rel_obj.project_id.id
            sql_relatorio += """
                    and f.project_id = {project_id}
            """
            sql_relatorio_SUB += """
                    and f.project_id = {project_id}
            """

        if rel_obj.periodo == '1':
            sql_relatorio += """
                group by
                    c.id,
                    rpc.name,
                    f.mes

                order by
                    c.id,
                    f.mes;"""

            sql_relatorio_SUB += """
                group by
                    f.mes

                order by
                    f.mes;"""

        elif rel_obj.periodo == '2':
            sql_relatorio += """
                group by
                    c.id,
                    rpc.name,
                    f.data

                order by
                    c.id,
                    f.data;"""

            sql_relatorio_SUB += """
                group by
                    f.data

                order by
                    f.data;"""

        else:
            sql_relatorio += """
                group by
                    c.id,
                    rpc.name,
                    f.data,
                    fl.numero_documento,
                    fd.nome,
                    fl.tipo,
                    rp.name

                order by
                    c.id,
                    f.data,
                    valor_entrada desc,
                    valor_saida desc;"""

            sql_relatorio_SUB += """
                group by
                    f.data

                order by
                    f.data,
                    valor_entrada desc,
                    valor_saida desc;"""


        sql = sql_relatorio.format(**filtro)
        print(sql)
        sql_relatorio_SUB = sql_relatorio_SUB.format(**filtro)

        if rel_obj.periodo == '1':
            rel.parametros['PERIODO'] = 'MENSAL'
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_mensal_patrimonial.jrxml')
            rel.parametros['SQL_RELATORIO'] = sql
            rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            relatorio = u'fluxo_caixa_mensal_'

        elif rel_obj.periodo == '2':
            rel.parametros['PERIODO'] = 'DIARIO'
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_diario_patrimonial.jrxml')
            rel.parametros['SQL_RELATORIO'] = sql
            rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            relatorio = u'fluxo_caixa_diario_'

        else:
            rel.parametros['PERIODO'] = 'ANALITICO'
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_analitico_patrimonial.jrxml')
            rel.parametros['SQL_RELATORIO'] = sql
            rel.parametros['SQL_RELATORIO_SUB'] = sql_relatorio_SUB
            relatorio = u'fluxo_caixa_analitico_'

        if rel_obj.saldo_bancario:
            rel.parametros['SALDO_BANCO'] = True
        else:
            rel.parametros['SALDO_BANCO'] = False

        if rel_obj.zera_saldo:
            rel.parametros['ZERA_SALDO'] = True
        else:
            rel.parametros['ZERA_SALDO'] = False

        if rel_obj.somente_totais:
            rel.parametros['SOMENTE_TOTAIS'] = True
        else:
            rel.parametros['SOMENTE_TOTAIS'] = False

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True

    def gera_relatorio_fluxo_caixa_sintetico(self, cr, uid, ids, context={}):
        if not ids:
            return False

        provisionado = context.get('provisionado')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)
        #company_id = rel_obj.company_id.id
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        meses = tempo(data_inicial,data_final)
        print(meses)

        if meses.years == 1 and meses.days > 0:
            raise osv.except_osv(u'Atenção', u'Limite entre datas é 12 meses!')

        if rel_obj.filtrar_rateio:
            rel = Report('Fluxo de Caixa', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico_rateio.jrxml')
            rel.parametros['PERIODO'] = 'SINTETICO RATEIO'
            rel.parametros['DETALHE'] = 'fluxo_caixa_analitico_rateio.jasper'
            #rel.parametros['COMPANY_ID'] = int(company_id)
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            relatorio = u'fluxo_caixa_sintetico_conta_rateio_'
            rel.outputFormat = rel_obj.formato
        else:
            rel = Report('Fluxo de Caixa', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fluxo_caixa_sintetico.jrxml')
            rel.parametros['PERIODO'] = 'SINTETICO'
            rel.parametros['DETALHE'] = 'fluxo_caixa_analitico.jasper'

            #rel.parametros['COMPANY_ID'] = int(company_id)
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]
            rel.parametros['TIPO_ANALISE'] = rel_obj.opcoes_caixa
            relatorio = u'fluxo_caixa_sintetico_conta_'
            rel.outputFormat = rel_obj.formato

        filtro = {
            'data_inicial': str(data_inicial)[:10],
            'data_final': str(data_final)[:10],
            'filtro_company': '',
            'filtro_res_partner_bank': '',
            #'company_id': int(company_id),
            #'zera_saldo': str(rel_obj.zera_saldo or False),
            'filtro_adicional': """''""",
            'titulo_01': '',
            'titulo_02': '',
            'titulo_03': '',
            'titulo_04': '',
            'titulo_05': '',
            'titulo_06': '',
            'titulo_07': '',
            'titulo_08': '',
            'titulo_09': '',
            'titulo_10': '',
            'titulo_11': '',
            'titulo_12': '',
            'ordem_01': '01',
            'ordem_02': '02',
            'ordem_03': '03',
            'ordem_04': '04',
            'ordem_05': '05',
            'ordem_06': '06',
            'ordem_07': '07',
            'ordem_08': '08',
            'ordem_09': '09',
            'ordem_10': '10',
            'ordem_11': '11',
            'ordem_12': '12',
            'setor': '',
            'join_departamento': '',
        }

        if rel_obj.opcoes_caixa == '1':
            rel.parametros['TIPO'] = 'Q'
            filtro['tipo'] = "and fcs.tipo = 'Q'"
        elif rel_obj.opcoes_caixa == '2':
            rel.parametros['TIPO'] = 'X'
            filtro['tipo'] = ""
        else:
            rel.parametros['TIPO'] = 'V'
            filtro['tipo'] = "and fcs.tipo = 'V'"

        if not rel_obj.filtrar_rateio:
            if cr.dbname.upper() == 'PATRIMONIAL' or cr.dbname.upper()[:5] == 'TESTE':
                filtro['view_fluxo_sintetico'] = 'finan_fluxo_caixa_sintetico_departamento'
            else:
                filtro['view_fluxo_sintetico'] = 'finan_fluxo_caixa_sintetico'
        else:
            filtro['view_fluxo_sintetico'] = 'finan_fluxo_caixa_sintetico_rateio'

        if len(rel_obj.company_ids) == 1:
            rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            filtro['filtro_company'] = """
            (
                fcs.company_id = {company_id}
                or c.parent_id = {company_id}
            )
            """.format(company_id=rel_obj.company_ids[0].id)
            filtro['filtro_company_anterior'] = """
            and (
                pr.company_id = {company_id}
                or cc.parent_id = {company_id}
            )
            """.format(company_id=rel_obj.company_ids[0].id)


        elif len(rel_obj.company_ids) > 1:
            rel.parametros['COMPANY_ID'] = rel_obj.company_ids[0].id

            company_ids = []
            for company_obj in rel_obj.company_ids:
                company_ids.append(company_obj.id)

            filtro['filtro_company'] = """
            (
                fcs.company_id in {company_ids}
                or c.parent_id in {company_ids}
            )
            """.format(company_ids=str(tuple(company_ids)).replace(',)', ')'))
            filtro['filtro_company_anterior'] = """
            and (
                pr.company_id in {company_ids}
                or cc.parent_id in {company_ids}
            )
            """.format(company_ids=str(tuple(company_ids)).replace(',)', ')'))

        else:
            raise osv.except_osv(u'Atenção', u'É preciso selecionar pelo menos uma empresa!')

        if len(rel_obj.res_partner_bank_ids) == 1:
            filtro['filtro_res_partner_bank'] = """
                and fcs.res_partner_bank_id = {res_partner_bank_id}
            """.format(res_partner_bank_id=rel_obj.res_partner_bank_ids[0].id)
            filtro['filtro_res_partner_bank_anterior'] = """
                and pr.res_partner_bank_id = {res_partner_bank_id}
            """.format(res_partner_bank_id=rel_obj.res_partner_bank_ids[0].id)


        elif len(rel_obj.res_partner_bank_ids) > 1:
            res_partner_bank_ids = []
            for res_partner_bank_obj in rel_obj.res_partner_bank_ids:
                res_partner_bank_ids.append(res_partner_bank_obj.id)

            filtro['filtro_res_partner_bank'] = """
                and fcs.res_partner_bank_id in {res_partner_bank_ids}
            """.format(res_partner_bank_ids=str(tuple(res_partner_bank_ids)).replace(',)', ')'))
            filtro['filtro_res_partner_bank_anterior'] = """
                and pr.res_partner_bank_id in {res_partner_bank_ids}
            """.format(res_partner_bank_ids=str(tuple(res_partner_bank_ids)).replace(',)', ')'))

        #if rel_obj.filtrar_rateio:

            #sql = """
                #select
                    #*
                #from
                    #finan_analitico_rateio('{data_inicial}', '{data_final}', {company_id}, {zera_saldo}, {filtro_adicional})
            #"""
            #if rel_obj.project_id:
                #filtro['filtro_adicional'] = """' and lr.project_id = """ + str(rel_obj.project_id.id) + """'"""
                #rel.parametros['PROJETO'] = rel_obj.project_id.name

        #else:
            #sql = """
                #select
                    #*
                #from
                    #finan_analitico('{data_inicial}', '{data_final}', {company_id}, {zera_saldo})
            #"""


        #if rel_obj.ativo:
            #if rel_obj.opcoes_caixa == '1':
                #sql += """
                    #where
                        #(id < 0 or quitado_total > 0)
                #"""
            #elif rel_obj.opcoes_caixa == '2':
                #sql += """
                    #where
                        #(id < 0 or ((quitado_total > 0)
                        #or (vencido_total > 0)))
                #"""
            #else:
                #sql += """
                    #where
                        #(id < 0 or vencido_total > 0)
                #"""

        if cr.dbname.upper() == 'PATRIMONIAL' or cr.dbname.upper()[:5] == 'TESTE':
            grupo_ids = self.pool.get('res.groups').search(cr, 1, [('name', '=', 'Patrimonial / Contas financeiras bloqueadas por departamento')])
            bloqueia_departamento = False

            if grupo_ids:
                grupo_obj = self.pool.get('res.groups').browse(cr, 1, grupo_ids[0])

                for usuario_obj in grupo_obj.users:
                    if usuario_obj.id == uid:
                        bloqueia_departamento = True

            if bloqueia_departamento:
                filtro['join_departamento'] = """
                    left join hr_department hd on hd.id = fcs.hr_department_id
                    left join hr_employee he on he.id = hd.manager_id
                    left join resource_resource rr on rr.id = he.resource_id
                """

                #filtro['setor'] ="""
                    #and (fcs.sintetica = True or rr.user_id = {usuario_id})
                #""".format(usuario_id=uid)
                filtro['setor'] ="""
                    and (rr.user_id = {usuario_id})
                """.format(usuario_id=uid)

            elif rel_obj.hr_department_id:
                #filtro['setor'] = """
                #and (fcs.sintetica = True or fc.hr_department_id = {hr_department_id})
                #""".format(hr_department_id=rel_obj.hr_department_id.id)
                filtro['setor'] = """
                and (fc.hr_department_id = {hr_department_id})
                """.format(hr_department_id=rel_obj.hr_department_id.id)

        #
        # Monta os títulos das colunas
        #
        dif = tempo(data_final, data_inicial)
        data = data_inicial
        i = 1
        lista_meses = []
        while i <= 12:
            ##
            ## Relatório por dia
            ##
            #if (dif.years == 0 and dif.months == 0) and dif.days <= 7:
                #filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%a %d/%m/%Y')
                #data += relativedelta(days=+1)
            #else:
            filtro['titulo_' + str(i).zfill(2)] = formata_data(data, '%B de %Y')
            filtro['ordem_' + formata_data(data, '%m')] = str(i).zfill(2)
            data += relativedelta(months=+1)

            i += 1

        sql = u"""
drop table if exists finan_relatorio_fluxo_sintetico;
create table finan_relatorio_fluxo_sintetico as
select
    row_number() over() as id,
    fc.codigo_completo as codigo_ordem,
    fc.codigo_completo as codigo,
    fc.nome as descricao,
    cast(case
        when fc.tipo = 'R' then 1
        when fc.tipo = 'D' then -1
        when fc.tipo = 'C' then -1
        when fc.tipo = 'A' then -1
        when fc.tipo = 'P' then -1
        else -1
    end as integer) as tipo,
    coalesce(fcs.sintetica, False) as sintetica,
"""
        #if rel_obj.zera_saldo:
        if True:
            sql += """
    cast(0 as numeric) as quitado_anterior,
    cast(0 as numeric) as vencido_anterior,
"""
        else:
            sql += """
    cast((
        select
            coalesce(sum(pr.valor), 0.00) as quitado
        from finan_pagamento_rateio pr
            join finan_conta_arvore ca on ca.conta_id = pr.conta_id
            join res_company cc on cc.id = pr.company_id

        where
            pr.tipo in ('R', 'P', 'E', 'S')
            and ca.conta_pai_id = fc.id
            and pr.data_quitacao < '{data_inicial}'
            {filtro_company_anterior}
            {filtro_res_partner_bank_anterior}
    ) as numeric) as quitado_anterior,
    cast(0 as numeric) as vencido_anterior,
"""

        sql += """
    cast('{titulo_01}' as varchar) as titulo_01,
    cast('{titulo_02}' as varchar) as titulo_02,
    cast('{titulo_03}' as varchar) as titulo_03,
    cast('{titulo_04}' as varchar) as titulo_04,
    cast('{titulo_05}' as varchar) as titulo_05,
    cast('{titulo_06}' as varchar) as titulo_06,
    cast('{titulo_07}' as varchar) as titulo_07,
    cast('{titulo_08}' as varchar) as titulo_08,
    cast('{titulo_09}' as varchar) as titulo_09,
    cast('{titulo_10}' as varchar) as titulo_10,
    cast('{titulo_11}' as varchar) as titulo_11,
    cast('{titulo_12}' as varchar) as titulo_12,
    cast(sum(coalesce(fcs.quitado_01, 0)) as numeric) as quitado_{ordem_01},
    cast(sum(coalesce(fcs.quitado_02, 0)) as numeric) as quitado_{ordem_02},
    cast(sum(coalesce(fcs.quitado_03, 0)) as numeric) as quitado_{ordem_03},
    cast(sum(coalesce(fcs.quitado_04, 0)) as numeric) as quitado_{ordem_04},
    cast(sum(coalesce(fcs.quitado_05, 0)) as numeric) as quitado_{ordem_05},
    cast(sum(coalesce(fcs.quitado_06, 0)) as numeric) as quitado_{ordem_06},
    cast(sum(coalesce(fcs.quitado_07, 0)) as numeric) as quitado_{ordem_07},
    cast(sum(coalesce(fcs.quitado_08, 0)) as numeric) as quitado_{ordem_08},
    cast(sum(coalesce(fcs.quitado_09, 0)) as numeric) as quitado_{ordem_09},
    cast(sum(coalesce(fcs.quitado_10, 0)) as numeric) as quitado_{ordem_10},
    cast(sum(coalesce(fcs.quitado_11, 0)) as numeric) as quitado_{ordem_11},
    cast(sum(coalesce(fcs.quitado_12, 0)) as numeric) as quitado_{ordem_12},

    cast(sum(
        coalesce(fcs.quitado_01, 0)
        + coalesce(fcs.quitado_02, 0)
        + coalesce(fcs.quitado_03, 0)
        + coalesce(fcs.quitado_04, 0)
        + coalesce(fcs.quitado_05, 0)
        + coalesce(fcs.quitado_06, 0)
        + coalesce(fcs.quitado_07, 0)
        + coalesce(fcs.quitado_08, 0)
        + coalesce(fcs.quitado_09, 0)
        + coalesce(fcs.quitado_10, 0)
        + coalesce(fcs.quitado_11, 0)
        + coalesce(fcs.quitado_12, 0)
    ) as numeric) as quitado_total,
    cast(0 as numeric) as percentual_quitado,

    cast(sum(coalesce(fcs.vencido_01, 0)) as numeric) as vencido_{ordem_01},
    cast(sum(coalesce(fcs.vencido_02, 0)) as numeric) as vencido_{ordem_02},
    cast(sum(coalesce(fcs.vencido_03, 0)) as numeric) as vencido_{ordem_03},
    cast(sum(coalesce(fcs.vencido_04, 0)) as numeric) as vencido_{ordem_04},
    cast(sum(coalesce(fcs.vencido_05, 0)) as numeric) as vencido_{ordem_05},
    cast(sum(coalesce(fcs.vencido_06, 0)) as numeric) as vencido_{ordem_06},
    cast(sum(coalesce(fcs.vencido_07, 0)) as numeric) as vencido_{ordem_07},
    cast(sum(coalesce(fcs.vencido_08, 0)) as numeric) as vencido_{ordem_08},
    cast(sum(coalesce(fcs.vencido_09, 0)) as numeric) as vencido_{ordem_09},
    cast(sum(coalesce(fcs.vencido_10, 0)) as numeric) as vencido_{ordem_10},
    cast(sum(coalesce(fcs.vencido_11, 0)) as numeric) as vencido_{ordem_11},
    cast(sum(coalesce(fcs.vencido_12, 0)) as numeric) as vencido_{ordem_12},

    cast(sum(
        coalesce(fcs.vencido_01, 0)
        + coalesce(fcs.vencido_02, 0)
        + coalesce(fcs.vencido_03, 0)
        + coalesce(fcs.vencido_04, 0)
        + coalesce(fcs.vencido_05, 0)
        + coalesce(fcs.vencido_06, 0)
        + coalesce(fcs.vencido_07, 0)
        + coalesce(fcs.vencido_08, 0)
        + coalesce(fcs.vencido_09, 0)
        + coalesce(fcs.vencido_10, 0)
        + coalesce(fcs.vencido_11, 0)
        + coalesce(fcs.vencido_12, 0)
    ) as numeric) as vencido_total,
    cast(0 as numeric) as percentual_vencido

from
    finan_conta fc
    left outer join {view_fluxo_sintetico} fcs on fcs.id = fc.id
    left outer join res_company c on c.id = fcs.company_id
    {join_departamento}

where
    {filtro_company}
    {filtro_res_partner_bank}
    and fcs.data between '{data_inicial}' and '{data_final}'
    -- and fc.tipo in ('R', 'D', 'C')
    {tipo}
    {provisionado}
    {setor}
    {projeto}

group by
    fc.id,
    fc.codigo_completo,
    fc.nome,
    fcs.sintetica

order by
    fc.codigo_completo,
    fc.nome;
        """

        if rel_obj.nao_provisionado != rel_obj.provisionado:
            if rel_obj.nao_provisionado:
                filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = False)'
            else:
                filtro['provisionado'] = 'and (fcs.provisionado is null or fcs.provisionado = True)'
        else:
            filtro['provisionado'] = ''

        if rel_obj.project_id:
            filtro['projeto'] = ' and fcs.project_id = {project_id}'.format(project_id=rel_obj.project_id.id)
        else:
            filtro['projeto'] = ''

        #if rel_obj.nao_provisionado != rel_obj.provisionado:
            #rel.parametros['PROV'] = True
        #else:
            #rel.parametros['PROV'] = False

        #if rel_obj.saldo_bancario:
            #rel.parametros['SALDO_BANCO'] = True
        #else:
            #rel.parametros['SALDO_BANCO'] = False

        #if rel_obj.zera_saldo:
            #rel.parametros['ZERA_SALDO'] = True
        #else:
            #rel.parametros['ZERA_SALDO'] = False

        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)
        cr.commit()

        sql_receitas = """
insert into finan_relatorio_fluxo_sintetico
    (
        id,
        codigo_ordem,
        codigo,
        descricao,
        tipo,
        sintetica,
        titulo_01,
        titulo_02,
        titulo_03,
        titulo_04,
        titulo_05,
        titulo_06,
        titulo_07,
        titulo_08,
        titulo_09,
        titulo_10,
        titulo_11,
        titulo_12,
        quitado_anterior,
        vencido_anterior,
        quitado_01,
        quitado_02,
        quitado_03,
        quitado_04,
        quitado_05,
        quitado_06,
        quitado_07,
        quitado_08,
        quitado_09,
        quitado_10,
        quitado_11,
        quitado_12,
        quitado_total,
        percentual_quitado,
        vencido_01,
        vencido_02,
        vencido_03,
        vencido_04,
        vencido_05,
        vencido_06,
        vencido_07,
        vencido_08,
        vencido_09,
        vencido_10,
        vencido_11,
        vencido_12,
        vencido_total,
        percentual_vencido
    )
select
    1000000 as id,
    '9999999901' as codigo_ordem,
    '' as codigo,
    'RECEITAS' as descricao,
    fc.tipo,
    True as sintetica,
    fc.titulo_01,
    fc.titulo_02,
    fc.titulo_03,
    fc.titulo_04,
    fc.titulo_05,
    fc.titulo_06,
    fc.titulo_07,
    fc.titulo_08,
    fc.titulo_09,
    fc.titulo_10,
    fc.titulo_11,
    fc.titulo_12,
    sum(fc.quitado_anterior) as quitado_anterior,
    sum(fc.vencido_anterior) as vencido_anterior,
    sum(fc.quitado_01) as quitado_01,
    sum(fc.quitado_02) as quitado_02,
    sum(fc.quitado_03) as quitado_03,
    sum(fc.quitado_04) as quitado_04,
    sum(fc.quitado_05) as quitado_05,
    sum(fc.quitado_06) as quitado_06,
    sum(fc.quitado_07) as quitado_07,
    sum(fc.quitado_08) as quitado_08,
    sum(fc.quitado_09) as quitado_09,
    sum(fc.quitado_10) as quitado_10,
    sum(fc.quitado_11) as quitado_11,
    sum(fc.quitado_12) as quitado_12,
    sum(fc.quitado_total) as quitado_total,
    100 as percentual_quitado,
    sum(fc.vencido_01) as vencido_01,
    sum(fc.vencido_02) as vencido_02,
    sum(fc.vencido_03) as vencido_03,
    sum(fc.vencido_04) as vencido_04,
    sum(fc.vencido_05) as vencido_05,
    sum(fc.vencido_06) as vencido_06,
    sum(fc.vencido_07) as vencido_07,
    sum(fc.vencido_08) as vencido_08,
    sum(fc.vencido_09) as vencido_09,
    sum(fc.vencido_10) as vencido_10,
    sum(fc.vencido_11) as vencido_11,
    sum(fc.vencido_12) as vencido_12,
    sum(fc.vencido_total) as vencido_total,
    100 as percentual_vencido

from
    finan_relatorio_fluxo_sintetico fc

where
    fc.tipo = 1
    and fc.sintetica = False

group by
    fc.tipo,
    fc.titulo_01,
    fc.titulo_02,
    fc.titulo_03,
    fc.titulo_04,
    fc.titulo_05,
    fc.titulo_06,
    fc.titulo_07,
    fc.titulo_08,
    fc.titulo_09,
    fc.titulo_10,
    fc.titulo_11,
    fc.titulo_12;
        """
        cr.execute(sql_receitas)
        cr.commit()

        sql_despesas = """
insert into finan_relatorio_fluxo_sintetico
    (
        id,
        codigo_ordem,
        codigo,
        descricao,
        tipo,
        sintetica,
        titulo_01,
        titulo_02,
        titulo_03,
        titulo_04,
        titulo_05,
        titulo_06,
        titulo_07,
        titulo_08,
        titulo_09,
        titulo_10,
        titulo_11,
        titulo_12,
        quitado_anterior,
        vencido_anterior,
        quitado_01,
        quitado_02,
        quitado_03,
        quitado_04,
        quitado_05,
        quitado_06,
        quitado_07,
        quitado_08,
        quitado_09,
        quitado_10,
        quitado_11,
        quitado_12,
        quitado_total,
        percentual_quitado,
        vencido_01,
        vencido_02,
        vencido_03,
        vencido_04,
        vencido_05,
        vencido_06,
        vencido_07,
        vencido_08,
        vencido_09,
        vencido_10,
        vencido_11,
        vencido_12,
        vencido_total,
        percentual_vencido
    )
select
    2000000 as id,
    '9999999902' as codigo_ordem,
    '' as codigo,
    'DESPESAS E CUSTOS' as descricao,
    fc.tipo,
    True as sintetica,
    fc.titulo_01,
    fc.titulo_02,
    fc.titulo_03,
    fc.titulo_04,
    fc.titulo_05,
    fc.titulo_06,
    fc.titulo_07,
    fc.titulo_08,
    fc.titulo_09,
    fc.titulo_10,
    fc.titulo_11,
    fc.titulo_12,
    sum(fc.quitado_anterior) as quitado_anterior,
    sum(fc.vencido_anterior) as vencido_anterior,
    sum(fc.quitado_01) as quitado_01,
    sum(fc.quitado_02) as quitado_02,
    sum(fc.quitado_03) as quitado_03,
    sum(fc.quitado_04) as quitado_04,
    sum(fc.quitado_05) as quitado_05,
    sum(fc.quitado_06) as quitado_06,
    sum(fc.quitado_07) as quitado_07,
    sum(fc.quitado_08) as quitado_08,
    sum(fc.quitado_09) as quitado_09,
    sum(fc.quitado_10) as quitado_10,
    sum(fc.quitado_11) as quitado_11,
    sum(fc.quitado_12) as quitado_12,
    sum(fc.quitado_total) as quitado_total,
    100 as percentual_quitado,
    sum(fc.vencido_01) as vencido_01,
    sum(fc.vencido_02) as vencido_02,
    sum(fc.vencido_03) as vencido_03,
    sum(fc.vencido_04) as vencido_04,
    sum(fc.vencido_05) as vencido_05,
    sum(fc.vencido_06) as vencido_06,
    sum(fc.vencido_07) as vencido_07,
    sum(fc.vencido_08) as vencido_08,
    sum(fc.vencido_09) as vencido_09,
    sum(fc.vencido_10) as vencido_10,
    sum(fc.vencido_11) as vencido_11,
    sum(fc.vencido_12) as vencido_12,
    sum(fc.vencido_total) as vencido_total,
    100 as percentual_vencido

from
    finan_relatorio_fluxo_sintetico fc

where
    fc.tipo = -1
    and fc.sintetica = False

group by
    fc.tipo,
    fc.titulo_01,
    fc.titulo_02,
    fc.titulo_03,
    fc.titulo_04,
    fc.titulo_05,
    fc.titulo_06,
    fc.titulo_07,
    fc.titulo_08,
    fc.titulo_09,
    fc.titulo_10,
    fc.titulo_11,
    fc.titulo_12;
        """
        cr.execute(sql_despesas)
        cr.commit()

        sql_saldo = """
insert into finan_relatorio_fluxo_sintetico
    (
        id,
        codigo_ordem,
        codigo,
        descricao,
        tipo,
        sintetica,
        titulo_01,
        titulo_02,
        titulo_03,
        titulo_04,
        titulo_05,
        titulo_06,
        titulo_07,
        titulo_08,
        titulo_09,
        titulo_10,
        titulo_11,
        titulo_12,
        quitado_anterior,
        vencido_anterior,
        quitado_01,
        quitado_02,
        quitado_03,
        quitado_04,
        quitado_05,
        quitado_06,
        quitado_07,
        quitado_08,
        quitado_09,
        quitado_10,
        quitado_11,
        quitado_12,
        quitado_total,
        percentual_quitado,
        vencido_01,
        vencido_02,
        vencido_03,
        vencido_04,
        vencido_05,
        vencido_06,
        vencido_07,
        vencido_08,
        vencido_09,
        vencido_10,
        vencido_11,
        vencido_12,
        vencido_total,
        percentual_vencido
    )
select
    3000000 as id,
    '9999999903' as codigo_ordem,
    '' as codigo,
    'SALDO FINAL' as descricao,
    0,
    True as sintetica,
    '' as titulo_01,
    '' as titulo_02,
    '' as titulo_03,
    '' as titulo_04,
    '' as titulo_05,
    '' as titulo_06,
    '' as titulo_07,
    '' as titulo_08,
    '' as titulo_09,
    '' as titulo_10,
    '' as titulo_11,
    '' as titulo_12,
    sum(fc.quitado_anterior) as quitado_anterior,
    sum(fc.vencido_anterior) as vencido_anterior,
    sum(fc.quitado_01) as quitado_01,
    sum(fc.quitado_02) as quitado_02,
    sum(fc.quitado_03) as quitado_03,
    sum(fc.quitado_04) as quitado_04,
    sum(fc.quitado_05) as quitado_05,
    sum(fc.quitado_06) as quitado_06,
    sum(fc.quitado_07) as quitado_07,
    sum(fc.quitado_08) as quitado_08,
    sum(fc.quitado_09) as quitado_09,
    sum(fc.quitado_10) as quitado_10,
    sum(fc.quitado_11) as quitado_11,
    sum(fc.quitado_12) as quitado_12,
    sum(fc.quitado_total) as quitado_total,
    100 as percentual_quitado,
    sum(fc.vencido_01) as vencido_01,
    sum(fc.vencido_02) as vencido_02,
    sum(fc.vencido_03) as vencido_03,
    sum(fc.vencido_04) as vencido_04,
    sum(fc.vencido_05) as vencido_05,
    sum(fc.vencido_06) as vencido_06,
    sum(fc.vencido_07) as vencido_07,
    sum(fc.vencido_08) as vencido_08,
    sum(fc.vencido_09) as vencido_09,
    sum(fc.vencido_10) as vencido_10,
    sum(fc.vencido_11) as vencido_11,
    sum(fc.vencido_12) as vencido_12,
    sum(fc.vencido_total) as vencido_total,
    100 as percentual_vencido

from
    finan_relatorio_fluxo_sintetico fc

where
    fc.id >= 1000000;
        """
        cr.execute(sql_saldo)
        cr.commit()

        sql_acumulado = """
insert into finan_relatorio_fluxo_sintetico
    (
        id,
        codigo_ordem,
        codigo,
        descricao,
        tipo,
        sintetica,
        titulo_01,
        titulo_02,
        titulo_03,
        titulo_04,
        titulo_05,
        titulo_06,
        titulo_07,
        titulo_08,
        titulo_09,
        titulo_10,
        titulo_11,
        titulo_12,
        quitado_anterior,
        vencido_anterior,
        quitado_01,
        quitado_02,
        quitado_03,
        quitado_04,
        quitado_05,
        quitado_06,
        quitado_07,
        quitado_08,
        quitado_09,
        quitado_10,
        quitado_11,
        quitado_12,
        quitado_total,
        percentual_quitado,
        vencido_01,
        vencido_02,
        vencido_03,
        vencido_04,
        vencido_05,
        vencido_06,
        vencido_07,
        vencido_08,
        vencido_09,
        vencido_10,
        vencido_11,
        vencido_12,
        vencido_total,
        percentual_vencido
    )
select
    4000000 as id,
    '9999999904' as codigo_ordem,
    '' as codigo,
    'ACUMULADO' as descricao,
    0,
    True as sintetica,
    '' as titulo_01,
    '' as titulo_02,
    '' as titulo_03,
    '' as titulo_04,
    '' as titulo_05,
    '' as titulo_06,
    '' as titulo_07,
    '' as titulo_08,
    '' as titulo_09,
    '' as titulo_10,
    '' as titulo_11,
    '' as titulo_12,
    {saldo_inicial} as quitado_anterior,
    fc.vencido_anterior as vencido_anterior,
    (   {saldo_inicial}
        + fc.quitado_01
    ) as quitado_01,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
    ) as quitado_02,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
    ) as quitado_03,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
    ) as quitado_04,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
    ) as quitado_05,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
    ) as quitado_06,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
    ) as quitado_07,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
    ) as quitado_08,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
        + fc.quitado_09
    ) as quitado_09,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
        + fc.quitado_09
        + fc.quitado_10
    ) as quitado_10,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
        + fc.quitado_09
        + fc.quitado_10
        + fc.quitado_11
    ) as quitado_11,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
        + fc.quitado_09
        + fc.quitado_10
        + fc.quitado_11
        + fc.quitado_12
    ) as quitado_12,
    (   {saldo_inicial}
        + fc.quitado_01
        + fc.quitado_02
        + fc.quitado_03
        + fc.quitado_04
        + fc.quitado_05
        + fc.quitado_06
        + fc.quitado_07
        + fc.quitado_08
        + fc.quitado_09
        + fc.quitado_10
        + fc.quitado_11
        + fc.quitado_12
    ) as quitado_total,
    100 as percentual_quitado,

    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
    ) as vencido_01,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
    ) as vencido_02,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
    ) as vencido_03,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
    ) as vencido_04,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
    ) as vencido_05,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
    ) as vencido_06,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
    ) as vencido_07,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
    ) as vencido_08,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
        + fc.vencido_09
    ) as vencido_09,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
        + fc.vencido_09
        + fc.vencido_10
    ) as vencido_10,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
        + fc.vencido_09
        + fc.vencido_10
        + fc.vencido_11
    ) as vencido_11,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
        + fc.vencido_09
        + fc.vencido_10
        + fc.vencido_11
        + fc.vencido_12
    ) as vencido_12,
    (   fc.vencido_anterior + {saldo_inicial}
        + fc.vencido_01
        + fc.vencido_02
        + fc.vencido_03
        + fc.vencido_04
        + fc.vencido_05
        + fc.vencido_06
        + fc.vencido_07
        + fc.vencido_08
        + fc.vencido_09
        + fc.vencido_10
        + fc.vencido_11
        + fc.vencido_12
    ) as vencido_total,
    100 as percentual_vencido

from
    finan_relatorio_fluxo_sintetico fc

where
    fc.id = 3000000;
        """

        if getattr(rel_obj, 'saldo_inicial', False):
            cr.execute(sql_acumulado.format(saldo_inicial=D(rel_obj.saldo_inicial or 0)))

        else:
            cr.execute(sql_acumulado.format(saldo_inicial='fc.quitado_anterior'))

        cr.commit()

        if rel_obj.opcoes_caixa != '2':
            sql_percentual = """
                update finan_relatorio_fluxo_sintetico fc set
                percentual_quitado =
                    case
                        when (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        else quitado_total / (select fct.quitado_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    end,

                percentual_vencido =
                    case
                        when (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        else vencido_total / (select fct.vencido_total from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    end

                where
                fc.id < 1000000;
            """
        else:
            sql_percentual = """
                update finan_relatorio_fluxo_sintetico fc set
                percentual_quitado =
                    case
                        when (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        else (quitado_total + vencido_total) / (select (fct.quitado_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    end,

                percentual_vencido =
                    case
                        when (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) = 0 then 0
                        else (vencido_total + vencido_total) / (select (fct.vencido_total + fct.vencido_total) from finan_relatorio_fluxo_sintetico fct where fct.id >= 1000000 and fct.tipo = fc.tipo) * 100
                    end

                where
                fc.id < 1000000;
            """

        cr.execute(sql_percentual)
        cr.commit()

        sql = """
        select
            *
        from
            finan_relatorio_fluxo_sintetico fc

        order by
            fc.codigo_ordem
        """
        #print(filtro)
        rel.parametros['SQL'] = sql.replace('\n', ' ')

        pdf, formato = rel.execute()

        dados = {
            'nome': relatorio + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato,
            'arquivo': base64.encodestring(pdf)
        }
        rel_obj.write(dados)

        return True


finan_relatorio()
