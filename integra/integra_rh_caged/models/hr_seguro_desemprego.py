# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from seguro_desemprego import *
from pybrasil.data import parse_datetime, hoje, formata_data
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, MESES, MESES_DIC, mes_passado
import base64
import re
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes


class hr_seguro_desemprego(orm.Model):
    _name = 'hr.seguro.desemprego'
    _description = 'Arquivo Seguro Desemprego'
    _order = 'data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresas'),
        'ano': fields.integer(u'Ano'),
        'mes': fields.selection(MESES, u'Mês'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'data': fields.date(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
    }

    _defaults = {
        'data': fields.date.today,
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,


    }


    def _gera_empregados(self, cr, uid, arquivo_seguro, data_inicial, data_final):

        contract_pool = self.pool.get('hr.contract')

        sql = """
            select
                hc.id, es.codigo_afastamento

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
                and hc.date_end is not null
                and (
                    (hc.date_start >= '{data_inicial}' and hc.date_start <= '{data_final}')
                or
                    (hc.date_end >= '{data_inicial}' and hc.date_end <= '{data_final}')
                )

            order by
                e.nome, hc.date_start, hc.date_end;
        """

        sql = sql.format(cnpj=arquivo_seguro.cnpj_empresa, data_inicial=data_inicial, data_final=data_final)
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
            empregado = REGISTRO_REQUERIMENTO()
            arquivo_seguro.empregados.append(empregado)

            empregado.cpf = empregado_obj.cpf
            empregado.nome = empregado_obj.nome
            empregado.endereco = empregado_obj.endereco or ''
            empregado.complemento = empregado_obj.complemento or ''
            empregado.cep = empregado_obj.cep or ''
            empregado.uf = empregado_obj.municipio_id.estado_id.uf or ''
            empregado.nome_mae = empregado_obj.nome_mae or ''
            empregado.pis = empregado_obj.nis
            empregado.carteira_trabalho_numero = empregado_obj.carteira_trabalho_numero or ''
            empregado.carteira_trabalho_serie = empregado_obj.carteira_trabalho_serie or ''
            empregado.carteira_trabalho_estado = empregado_obj.carteira_trabalho_estado or 'SC'
            empregado.cbo = contrato_obj.job_id.cbo_id.codigo or ''
            empregado.data_admissao = parse_datetime(contrato_obj.date_start).date()
            empregado.data_demissao = parse_datetime(contrato_obj.date_end).date()
            empregado.sexo = empregado_obj.sexo
            empregado.grau_instrucao = empregado_obj.grau_instrucao
            empregado.data_nascimento = parse_datetime(empregado_obj.data_nascimento).date()
            empregado.horas_trabalhadas_semana = int(contrato_obj.horas_mensalista / 30.0 * 6)


    def _gera_seguro(self, cr, uid, cnpj, data_inicial, data_final):
        partner_pool = self.pool.get('res.partner')
        empresa_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj)], order='id')[0]
        empresa_obj = partner_pool.browse(cr, 1, empresa_id)

        seguro = REGISTRO_HEADER()
        seguro.cnpj_empresa = empresa_obj.cnpj_cpf
        return seguro

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return True

        company_pool = self.pool.get('res.company')
        data_inicial = context.get('data_inicial')
        data_final = context.get('data_final')
        data = context.get('data')

        company_id = context.get('company_id', 1)

        company_obj = company_pool.browse(cr, 1, company_id)


        for seguro_obj in self.browse(cr, uid, ids):
            cnpj = company_obj.partner_id.cnpj_cpf
            raiz_cnpj = cnpj[:10]


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



            lista_cnpjs = cr.fetchall()
            cnpjs = []
            for lista_cnpj in lista_cnpjs:
                cnpjs.append(lista_cnpj[0])

            print('cnpjs', cnpjs, raiz_cnpj)

            arquivo_seguro = self._gera_seguro(cr, uid, company_obj.partner_id.cnpj_cpf, data_inicial, data_inicial)

            arquivo_texto = arquivo_seguro.registro()

            for cnpj in cnpjs:
                self._gera_empregados(cr, uid, arquivo_seguro, data_inicial, data_final)

            sequencia = 0
            for empregado in arquivo_seguro.empregados:
                arquivo_texto += empregado.registro()
                sequencia += 1

            trailler = REGISTRO_TRAILLER()

            arquivo_texto += trailler.registro(sequencia)

            dados = {
                'nome_arquivo': 'DESLIGAMENTOS_' + formata_data(data) + '.SD',
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }
            seguro_obj.write(dados)

        return True

hr_seguro_desemprego()