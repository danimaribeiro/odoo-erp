# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from caged import *
from pybrasil.data import parse_datetime, hoje
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, MESES, MESES_DIC, mes_passado
import base64
import re
from pybrasil.data import primeiro_dia_mes, ultimo_dia_mes
from integra_rh.constantes_rh import TIPO_AFASTAMENTO_CAGED


TIPO_DECLARACAO = [
    ('1', u'1ª declaração'),
    ('2', u'Redeclaração'),
]

TIPO_ALTERACAO = [
    ('1', u'Nada'),
    ('2', u'Dados cadastrais'),
    ('3', u'Fechamento do estabelecimento'),
]


class hr_caged(orm.Model):
    _name = 'hr.caged'
    _description = 'Arquivo CAGED'
    _order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresas'),
        'somente_cnpj': fields.boolean(u'Somente este CNPJ?'),
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'declaracao': fields.selection(TIPO_DECLARACAO, u'Declaração'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'data': fields.date(u'Data do Arquivo'),
        'tipo_alteracao': fields.selection(TIPO_ALTERACAO, u'Alteração'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'seguro_desemprego': fields.boolean(u'Seguro Desemprego?'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
    }

    _defaults = {
        'data': fields.date.today,
        'declaracao' : '1',
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'tipo_alteracao': '1',
        'somente_cnpj': True,
        #'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        #'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
    }


    def _gera_empregados(self, cr, uid, estabelecimento, data_inicial, data_final, seguro_desemprego):
        employee_pool = self.pool.get('hr.employee')
        contract_pool = self.pool.get('hr.contract')
        caged_pool = self.pool.get('hr.caged')
        
        if seguro_desemprego:
            sql = """
                select distinct
                    hc.id, es.codigo_afastamento, e.nome, hc.date_start, hc.date_end

                from
                    hr_contract hc
                    join res_company rc on rc.id = hc.company_id
                    join res_partner p on p.id = rc.partner_id
                    join hr_employee e on e.id = hc.employee_id
                    join hr_job j on j.id = hc.job_id
                    join hr_cbo cbo on cbo.id = j.cbo_id
                    left join hr_payslip h on h.contract_id = hc.id and h.tipo = 'R'
                    left join hr_payroll_structure es on es.id = h.struct_id

                where
                    p.cnpj_cpf = '{cnpj}'
                    and hc.categoria_trabalhador not between '700' and '799'
                    and (
                        (hc.date_start >= '{data_inicial}' and hc.date_start <= '{data_final}')
                        and {seguro_desemprego}
                    )
                    and (h.simulacao is null or h.simulacao = False)

                order by
                    e.nome, hc.date_start, hc.date_end;
            """
            
        else:
            sql = """
                select distinct
                    hc.id, es.codigo_afastamento, e.nome, hc.date_start, hc.date_end

                from
                    hr_contract hc
                    join res_company rc on rc.id = hc.company_id
                    join res_partner p on p.id = rc.partner_id
                    join hr_employee e on e.id = hc.employee_id
                    join hr_job j on j.id = hc.job_id
                    join hr_cbo cbo on cbo.id = j.cbo_id
                    left join hr_payslip h on h.contract_id = hc.id and h.tipo = 'R'
                    left join hr_payroll_structure es on es.id = h.struct_id

                where
                    p.cnpj_cpf = '{cnpj}'
                    and hc.categoria_trabalhador not between '700' and '799'
                    and (
                        (
                            (hc.date_start >= '{data_inicial}' and hc.date_start <= '{data_final}')
                            and {seguro_desemprego}
                        )
                    or
                        (hc.date_end >= '{data_inicial}' and hc.date_end <= '{data_final}')
                    )
                    and (h.simulacao is null or h.simulacao = False)

                order by
                    e.nome, hc.date_start, hc.date_end;
            """

        sql = sql.format(cnpj=estabelecimento.cnpj, data_inicial=data_inicial, data_final=data_final, seguro_desemprego='(hc.seguro_desemprego = True)' if seguro_desemprego else '(hc.seguro_desemprego is null or hc.seguro_desemprego = False)')
        print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()
        contrato_ids = []
        rescisao_codigos = {}
        for lista_contrato in contrato_ids_listas:
            contrato_ids.append(lista_contrato[0])

            if lista_contrato[1]:
                rescisao_codigos[lista_contrato[0]] = lista_contrato[1]

        for contrato_obj in contract_pool.browse(cr, 1, contrato_ids):
            empregado_obj = contrato_obj.employee_id
            empregado = CAGEDEmpregado()
            empregado.estabelecimento = estabelecimento
            estabelecimento.empregados.append(empregado)

            empregado.pis = empregado_obj.nis
            empregado.sexo = empregado_obj.sexo
            empregado.data_nascimento = parse_datetime(empregado_obj.data_nascimento).date()
            empregado.grau_instrucao = empregado_obj.grau_instrucao
            empregado.salario_mensal = contrato_obj.wage
            empregado.horas_trabalhadas_semana = int(contrato_obj.horas_mensalista / 30.0 * 6)
            empregado.data_admissao = parse_datetime(contrato_obj.date_start).date()

            if contrato_obj.data_transf:
                empregado.tipo_movimento = '70'
            elif contrato_obj.primeiro_emprego:
                empregado.tipo_movimento = '10'
            elif contrato_obj.tipo_contrato == '2':
                empregado.tipo_movimento = '25'
            elif contrato_obj.tipo_admissao == '4':
                empregado.tipo_movimento = '35'
            elif contrato_obj.tipo_admissao == '2':
                empregado.tipo_movimento = '70'

            #
            # Atenção! Tratar aqui os tipos de rescisão
            #
            if contrato_obj.date_end and contrato_obj.date_end <= data_final:
                empregado.tipo_movimento_admissao = empregado.tipo_movimento

                if contrato_obj.id in rescisao_codigos and rescisao_codigos[contrato_obj.id] in TIPO_AFASTAMENTO_CAGED:
                    empregado.tipo_movimento = TIPO_AFASTAMENTO_CAGED[rescisao_codigos[contrato_obj.id]]
                else:
                    empregado.tipo_movimento = '31'

                empregado.dia_desligamento = int(contrato_obj.date_end[8:10])

                if contrato_obj.date_end[:7] == contrato_obj.date_start[:7]:
                    empregado.rescisao_mesmo_mes_admissao = True

            empregado.nome = empregado_obj.nome
            empregado.carteira_trabalho_numero = empregado_obj.carteira_trabalho_numero or ''
            empregado.carteira_trabalho_serie = empregado_obj.carteira_trabalho_numero or ''
            empregado.carteira_trabalho_estado = empregado_obj.carteira_trabalho_estado or estabelecimento.estado
            empregado.raca_cor = empregado_obj.raca_cor
            empregado.cbo = contrato_obj.job_id.cbo_id.codigo or ''
            #
            # 103 - aprendiz
            # 901 - estagiário
            #
            empregado.aprendiz = contrato_obj.categoria_trabalhador in ['103', '901']
            empregado.cpf = empregado_obj.cpf
            empregado.cep = empregado_obj.cep or ''

            if empregado_obj.deficiente_motor:
                empregado.deficiencia = True
                empregado.tipo_deficiencia = '1'
            elif empregado_obj.deficiente_auditivo:
                empregado.deficiencia = True
                empregado.tipo_deficiencia = '2'
            elif empregado_obj.deficiente_visual:
                empregado.deficiencia = True
                empregado.tipo_deficiencia = '3'
            elif empregado_obj.deficiente_mental:
                empregado.deficiencia = True
                empregado.tipo_deficiencia = '4'
            elif empregado_obj.deficiente_reabilitado:
                empregado.deficiencia = True
                empregado.tipo_deficiencia = '6'

    def _gera_estabelecimento(self, cr, uid, caged, cnpj, data_inicial, data_final):
        partner_pool = self.pool.get('res.partner')

        empresa_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj)], order='id')[0]
        print(empresa_id)
        empresa_obj = partner_pool.browse(cr, 1, empresa_id)

        estabelecimento = CAGEDEstabelecimento()
        caged.estabelecimentos.append(estabelecimento)

        estabelecimento.cnpj = empresa_obj.cnpj_cpf
        estabelecimento.razao_social = empresa_obj.razao_social or empresa_obj.name
        estabelecimento.endereco = empresa_obj.endereco or ''
        estabelecimento.endereco += ' '
        estabelecimento.endereco += empresa_obj.numero or ''
        estabelecimento.bairro = empresa_obj.bairro or ''
        estabelecimento.cep = empresa_obj.cep or ''
        try:
            estabelecimento.estado = empresa_obj.municipio_id.estado_id.uf
        except:
            estabelecimento.estado = '  '

        estabelecimento.telefone = empresa_obj.fone or ''
        estabelecimento.cnae = empresa_obj.cnae_id.codigo or ''
        #estabelecimento.email = empresa_obj.cnae_id.codigo

        cr.execute("""
            select count(*)

            from hr_contract hc
            join res_company rc on rc.id = hc.company_id
            join res_partner p on p.id = rc.partner_id

            where
            hc.categoria_trabalhador not between '700' and '999'
            and p.cnpj_cpf = '""" + empresa_obj.cnpj_cpf + """'
            and hc.date_start < '""" + data_inicial + """'
            and (hc.date_end is null or hc.date_end >= '""" + data_inicial + """');
        """)

        total_empregados_primeiro_dia = cr.fetchall()[0][0]
        print('total_empregados_primeiro_dia', total_empregados_primeiro_dia)

        estabelecimento.total_empregados_primeiro_dia = total_empregados_primeiro_dia
        return estabelecimento

    def _gera_caged(self, cr, uid, cnpj, ano, mes):
        partner_pool = self.pool.get('res.partner')
        empresa_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj)], order='id')[0]
        empresa_obj = partner_pool.browse(cr, 1, empresa_id)
        caged = CAGED()
        caged.ano = ano
        caged.mes = mes
        caged.cnpj = empresa_obj.cnpj_cpf
        caged.razao_social = empresa_obj.razao_social
        caged.endereco = empresa_obj.endereco + ', ' + empresa_obj.numero
        caged.cep = empresa_obj.cep or ''
        caged.estado = empresa_obj.municipio_id.estado_id.uf
        caged.telefone = empresa_obj.fone or ''
        return caged

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return True

        company_pool = self.pool.get('res.company')
        partner_pool = self.pool.get('res.partner')
        ano = context.get('ano', mes_passado()[0])
        mes = int(context.get('mes', mes_passado()[1]))
        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, mes)
        data_inicial = str(data_inicial)
        data_final = str(data_final)
        company_id = context.get('company_id', 1)
        company_obj = company_pool.browse(cr, 1, company_id)

        for caged_obj in self.browse(cr, uid, ids):
            cnpj = company_obj.partner_id.cnpj_cpf
            seguro_desemprego = caged_obj.seguro_desemprego
            raiz_cnpj = cnpj[:10]

            if caged_obj.somente_cnpj:
                cr.execute("""
                    select distinct
                    p.cnpj_cpf

                    from res_company c
                    join res_partner p on p.id = c.partner_id
                    join sped_municipio m on m.id = p.municipio_id
                    join sped_cnae cn on cn.id = p.cnae_id

                    where
                    p.fone != ''
                    and p.cnpj_cpf like '""" + raiz_cnpj +  """%'

                    order by
                    p.cnpj_cpf;
                """)

            else:
                cr.execute("""
                    select distinct
                    p.cnpj_cpf

                    from res_company c
                    join res_partner p on p.id = c.partner_id
                    join sped_municipio m on m.id = p.municipio_id
                    join sped_cnae cn on cn.id = p.cnae_id

                    where
                    p.cnpj_cpf != '' and p.fone != ''
                    --and p.cnpj_cpf like '""" + raiz_cnpj +  """%'

                    order by
                    p.cnpj_cpf;
                """)

            lista_cnpjs = cr.fetchall()
            cnpjs = []
            for lista_cnpj in lista_cnpjs:
                cnpjs.append(lista_cnpj[0])

            print('cnpjs', cnpjs, raiz_cnpj)

            caged = self._gera_caged(cr, uid, company_obj.partner_id.cnpj_cpf, ano, mes)
            
            if seguro_desemprego:
                data_inicial = caged_obj.data_inicial
                data_final = caged_obj.data_final

            for cnpj in cnpjs:
                estabelecimento = self._gera_estabelecimento(cr, uid, caged, cnpj, data_inicial, data_final)
                estabelecimento.tipo_alteracao = caged_obj.tipo_alteracao or '1'
                self._gera_empregados(cr, uid, estabelecimento, data_inicial, data_final, seguro_desemprego)

            arquivo_texto = caged.registro()
            sequencia = 2
            for estabelecimento in caged.estabelecimentos:
                if seguro_desemprego:
                    if len(estabelecimento.empregados) == 0:
                        continue

                elif estabelecimento.total_empregados_primeiro_dia == 0 and len(estabelecimento.empregados) == 0:
                    continue

                arquivo_texto += estabelecimento.registro(sequencia)
                sequencia += 1
                for empregado in estabelecimento.empregados:
                    arquivo_texto += empregado.registro(sequencia)
                    sequencia += 1

            dados = {
                'nome_arquivo': 'CGED' + str(ano).zfill(4) + '.M' + str(mes).zfill(2),
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }
            caged_obj.write(dados)

        return True