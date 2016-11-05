# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje, formata_data
import base64
from pybrasil.valor.decimal import Decimal as D
from seguro_desemprego import *
from pybrasil.base import tira_acentos


class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    #_order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'nome_arquivo_seguro': fields.char(u'Nome arquivo', size=30),
        'arquivo_seguro': fields.binary(u'Arquivo'),
        'arquivo_texto_seguro': fields.text(u'Arquivo'),
    }

    _defaults = {
        #'data': fields.date.today,
        #'declaracao' : '1',
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
    }

    def gera_seguro_desemprego(self, cr, uid, ids, context={}):

        if not ids:
            return True
        for holerite_obj in self.browse(cr, uid, ids):
            holerite_item_pool = self.pool.get('hr.payslip.line')
            empregado_obj = holerite_obj.employee_id
            contract_obj = holerite_obj.contract_id
            empresa_obj =  contract_obj.company_id

            seguro = REGISTRO_HEADER()
            seguro.cnpj_empresa = empresa_obj.partner_id.cnpj_cpf

            empregado = REGISTRO_REQUERIMENTO()
            seguro.empregados.append(empregado)

            empregado.cpf = empregado_obj.cpf
            empregado.nome = empregado_obj.nome
            empregado.endereco = empregado_obj.endereco or ''
            empregado.complemento = empregado_obj.numero or ''
            empregado.complemento += ' '
            empregado.complemento += empregado_obj.complemento or ''
            empregado.complemento = empregado_obj.complemento.strip()
            empregado.cep = empregado_obj.cep or ''
            empregado.uf = empregado_obj.municipio_id.estado_id.uf or ''
            empregado.nome_mae = empregado_obj.nome_mae or ''
            empregado.pis = empregado_obj.nis
            empregado.carteira_trabalho_numero = empregado_obj.carteira_trabalho_numero or ''
            empregado.carteira_trabalho_serie = empregado_obj.carteira_trabalho_serie or ''
            empregado.carteira_trabalho_estado = empregado_obj.carteira_trabalho_estado or 'SC'
            empregado.cbo = contract_obj.job_id.cbo_id.codigo or ''
            empregado.data_admissao = parse_datetime(contract_obj.date_start).date()
            empregado.data_demissao = parse_datetime(contract_obj.date_end).date()
            empregado.sexo = empregado_obj.sexo
            empregado.grau_instrucao = empregado_obj.grau_instrucao
            empregado.data_nascimento = parse_datetime(empregado_obj.data_nascimento).date()
            empregado.horas_trabalhadas_semana = int(contract_obj.horas_mensalista / 30.0 * 6)

            valor_aviso_previo = D(0)

            if holerite_obj.aviso_previo_indenizado:
                empregado.aviso_previo_indenizado = '1'              
            else:
                empregado.aviso_previo_indenizado = '2'

            sql_ultimos_salarios = """
                select
                    (select aps.valor from (select h.date_from, sum(coalesce(hl.total, 0.00)) as valor
                    from hr_payslip_line hl
                    join hr_payslip h on h.id = hl.slip_id
                    where
                    h.contract_id = co.id
                    and hl.code in ('BASE_INSS') and h.tipo = 'N'
                    group by
                    h.date_from
                    order by
                    h.date_from desc limit 1 offset 2) as aps) as antepenultimo_salario,

                    (select ps.valor from (select h.date_from, sum(coalesce(hl.total, 0.00)) as valor
                    from hr_payslip_line hl
                    join hr_payslip h on h.id = hl.slip_id
                    where
                    h.contract_id = co.id
                    and hl.code in ('BASE_INSS')  and h.tipo = 'N'
                    group by
                    h.date_from
                    order by
                    h.date_from desc limit 1 offset 1) as ps) as penultimo_salario,

                    (select us.valor from (select h.date_from, sum(coalesce(hl.total, 0.00)) as valor
                    from hr_payslip_line hl
                    join hr_payslip h on h.id = hl.slip_id
                    where
                    h.contract_id = co.id
                    and hl.code in ('BASE_INSS')  and h.tipo = 'N'
                    group by
                    h.date_from
                    order by
                    h.date_from desc limit 1) as us) as ultimo_salario

                from
                    hr_contract co

                where
                    co.id = {contract_id};
            """

            sql_ultimos_salarios = sql_ultimos_salarios.format(contract_id=holerite_obj.contract_id.id)
            cr.execute(sql_ultimos_salarios)
            salarios = cr.fetchall()
            if len(salarios):
                print(salarios)
                
                empregado.remuneracao_antepenultimo_salario, empregado.remuneracao_penultimo_salario, empregado.ultimo_salario = salarios[0]
                empregado.remuneracao_antepenultimo_salario = D(empregado.remuneracao_antepenultimo_salario)
                empregado.remuneracao_penultimo_salario = D(empregado.remuneracao_penultimo_salario)
                empregado.ultimo_salario = D(empregado.ultimo_salario)           
                
                empregado.remuneracao_antepenultimo_salario = empregado.remuneracao_antepenultimo_salario.quantize(D('0.01'))
                empregado.remuneracao_penultimo_salario = empregado.remuneracao_penultimo_salario.quantize(D('0.01'))
                empregado.ultimo_salario = empregado.ultimo_salario.quantize(D('0.01'))

            arquivo_texto = seguro.registro()

            sequencia = 0
            for empregado in seguro.empregados:
                arquivo_texto += empregado.registro()
                sequencia += 1

            trailler = REGISTRO_TRAILLER()

            arquivo_texto += trailler.registro(sequencia)

            dados = {
                'nome_arquivo_seguro': 'SD_' + str(holerite_obj.number) + '.SD',
                'arquivo_texto_seguro': arquivo_texto[:-2],
                'arquivo_seguro': base64.encodestring(arquivo_texto[:-2]),
            }
            holerite_obj.write(dados)
        return True
