#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
from pybrasil.base import DicionarioBrasil
from finan.wizard.relatorio import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import formata_data, agora
import base64


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


class hr_holerite_variavel_media(osv.osv_memory):
    _name = 'hr.holerite_variavel_media'
    _description = u'Variáveis de Media'
    _order = 'contract_id'
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
            line_pool = self.pool.get('hr.payslip.line')
            rubrica_pool = self.pool.get('hr.salary.rule')

            for operacao, line_id, valores in valor_campo:
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

                line_obj = None
                if line_id:
                    line_obj = line_pool.browse(cr, uid, line_id)

                if isinstance(valores, dict) and 'salary_rule_id' in valores and operacao == 0:
                    rubrica_id = valores['salary_rule_id']
                    rubrica_obj = rubrica_pool.browse(cr, uid, rubrica_id)
                    valores['code'] = rubrica_obj.code
                    valores['name'] = rubrica_obj.name
                    valores['sequence'] = rubrica_obj.sequence
                    valores['category_id'] = rubrica_obj.category_id.id

                    #if rubrica_obj.tipo_media == 'valor':
                        #valores['total'] = valores['amount']

                #
                # ALTERAR
                #
                if operacao == 1:
                    if not line_obj.digitado_media:
                        continue

                    line_pool.write(cr, uid, [line_id], valores)

                #
                # CRIAR
                #
                elif operacao == 0:
                    ano = valores['ano']
                    mes = valores['mes']
                    contract_id = valores['contract_id']
                    date_from, date_to = primeiro_ultimo_dia_mes(ano, int(mes))

                    busca = [('mes', '=', mes), ('ano', '=', ano), ('contract_id', '=', contract_id), ('simulacao', '=', False), ('tipo', '=', 'N')]

                    holerite_ids = self.pool.get('hr.payslip').search(cr, uid, busca)

                    if not holerite_ids:
                        contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)
                        dados = {
                            'tipo': 'N',
                            'simulacao': False,
                            'contract_id': contract_id,
                            'employee_id': contract_obj.employee_id.id,
                            'date_from': date_from,
                            'date_to': date_to,
                            'struct_id': contract_obj.struct_id.id,
                            'ano': ano,
                            'mes': mes,
                        }
                        print(dados)
                        holerite_ids = [self.pool.get('hr.payslip').create(cr, uid, dados)]

                    valores['slip_id'] = holerite_ids[0]
                    valores['digitado'] = True
                    valores['digitado_media'] = True

                    line_pool.create(cr, uid, valores)

                #
                # EXCLUIR
                #
                elif operacao == 2:
                    if line_obj:
                        if not line_obj.digitado_media:
                            continue

                    line_pool.unlink(cr, uid, [line_id])


    def _get_input_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        variavel_obj = self.browse(cr, uid, ids[0])

        if variavel_obj.contract_id:
            contract_id = variavel_obj.contract_id.id
        else:
            contract_id = False

        data_inicial = str(variavel_obj.ano).zfill(4) + '-' + variavel_obj.mes + '-01'
        data_final = parse_datetime(data_inicial).date()
        data_final += relativedelta(years=+1, days=-1)
        data_final = str(data_final)

        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
        }

        sql = """
            select
                pl.id

            from hr_payslip_line pl
            join hr_payslip p on p.id = pl.slip_id
            join hr_salary_rule sr on sr.id = pl.salary_rule_id

            where
                p.contract_id  = {contract_id}
                and (
                    sr.tipo_media in ('quantidade','valor')
                    or pl.digitado_media = True
                )
                and (p.simulacao = null or p.simulacao = False)
                and p.tipo = 'N'
                and p.date_from >= '{data_inicial}'
                and p.date_to <= '{data_final}'

            order by
                p.ano desc,
                p.mes desc,
                sr.name
        """

        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)

        input_ids = []
        for ret in cr.fetchall():
            input_ids.append(ret[0])

        res = {}
        if ids:
            for id in ids:
                res[id] = input_ids
        else:
            res = input_ids

        return res

    _columns = {
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'ano': fields.integer(u'Ano inicial'),
        'mes': fields.selection(MESES, u'Mês inicial'),
        'input_ids': fields.function(_get_input_ids, method=True, type='one2many', string=u'Rubrica para Médias', relation='hr.payslip.line', fnct_inv=_set_input_ids),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
    }

    def busca_entradas(self, cr, uid, ids, context={}):
        valores = {}
        retorno = {'value': valores}

        valores['input_ids'] = self._get_input_ids(cr, uid, ids, 'input_ids', context=context)

        return retorno

    def gera_relatorio_media(self, cr, uid, ids, context={}):
        if not ids:
            return

        holerite_pool = self.pool.get('hr.payslip')

        for variavel_obj in self.browse(cr, uid, ids):
            data_inicial = str(variavel_obj.ano).zfill(4) + '-' + variavel_obj.mes + '-01'
            data_final = str(variavel_obj.ano).zfill(4) + '-' + variavel_obj.mes + '-01'
            data_inicial = parse_datetime(data_inicial)
            data_final = parse_datetime(data_final)
            data_final += relativedelta(years=+1, days=-1)

            dados = {
                'tipo': 'F',
                'simulacao': True,
                'contract_id': variavel_obj.contract_id.id,
                'employee_id': variavel_obj.contract_id.employee_id.id,
                'company_id': variavel_obj.contract_id.company_id.id,
                'date_from': str(data_final + relativedelta(days=+1))[:10],
                'date_to': str(data_final + relativedelta(days=+31))[:10],
                'data_inicio_periodo_aquisitivo': str(data_inicial)[:10],
                'data_fim_periodo_aquisitivo': str(data_final)[:10],
                'dias_ferias': 30,
            }

            holerite_id = holerite_pool.create(cr, uid, dados)
            holerite_pool.calcula_medias(cr, uid, [holerite_id])
            holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            linhas = []
            for media_obj in holerite_obj.media_ids:
                linha = DicionarioBrasil()
                linha['rubrica'] = media_obj.nome
                linha['tipo_media'] = media_obj.tipo_media
                linha['digitado'] = media_obj.digitado
                linha['mes_01'] = media_obj.mes_01
                linha['mes_02'] = media_obj.mes_02
                linha['mes_03'] = media_obj.mes_03
                linha['mes_04'] = media_obj.mes_04
                linha['mes_05'] = media_obj.mes_05
                linha['mes_06'] = media_obj.mes_06
                linha['mes_07'] = media_obj.mes_07
                linha['mes_08'] = media_obj.mes_08
                linha['mes_09'] = media_obj.mes_09
                linha['mes_10'] = media_obj.mes_10
                linha['mes_11'] = media_obj.mes_11
                linha['mes_12'] = media_obj.mes_12
                linha['total'] = D(media_obj.total or 0)
                linha['meses'] = D(media_obj.meses or 0)
                linha['proporcao'] = D(media_obj.proporcao or 0)
                linha['media'] = D(media_obj.media or 0)

                linhas.append(linha)

            rel = FinanRelatorioAutomaticoPaisagem()
            rel.title = u'Médias de '
            rel.title += variavel_obj.contract_id.employee_id.nome
            filtro = rel.band_page_header.elements[-1]
            filtro.text = u'Período de '
            filtro.text += formata_data(data_inicial)
            filtro.text += ' a '
            filtro.text += formata_data(data_final)

            rel.colunas = [
                ['rubrica', 'C', 30, u'Rubrica', False, None],
                ['tipo_media', 'C', 5, u'Tipo', False, None],
                ['digitado', 'B', 4, u'Digitado', False, None],
                ['mes_01', 'C', 14, u'1º mês', False, 'D'],
                ['mes_02', 'C', 14, u'2º mês', False, 'D'],
                ['mes_03', 'C', 14, u'3º mês', False, 'D'],
                ['mes_04', 'C', 14, u'4º mês', False, 'D'],
                ['mes_05', 'C', 14, u'5º mês', False, 'D'],
                ['mes_06', 'C', 14, u'6º mês', False, 'D'],
                ['mes_07', 'C', 14, u'7º mês', False, 'D'],
                ['mes_08', 'C', 14, u'8º mês', False, 'D'],
                ['mes_09', 'C', 14, u'9º mês', False, 'D'],
                ['mes_10', 'C', 14, u'10º mês', False, 'D'],
                ['mes_11', 'C', 14, u'11º mês', False, 'D'],
                ['mes_12', 'C', 14, u'12º mês', False, 'D'],
                ['total', 'F', 10, u'Total', False, None],
                ['meses', 'F', 5, u'Meses', False, None],
                ['proporcao', 'F', 5, u'Proporção', False, None],
                ['media', 'F', 10, u'Média', False, None],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            #rel.grupos = [
                #['servico', u'Serviço', False],
                #['tipo', u'Tipo', False],
            #]
            #rel.monta_grupos(rel.grupos)

            pdf = gera_relatorio(rel, linhas)
            csv = gera_relatorio_csv(rel, linhas)

            dados = {
                'nome': 'relatorio_medias_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.pdf',
                'arquivo': base64.encodestring(pdf),
                'nome_csv': 'relatorio_medias_' + str(agora())[:16].replace(' ','_' ).replace('-','_') + '.csv',
                'arquivo_csv': base64.encodestring(csv)
            }
            variavel_obj.write(dados)

            #holerite_obj.unlink()


hr_holerite_variavel_media()
