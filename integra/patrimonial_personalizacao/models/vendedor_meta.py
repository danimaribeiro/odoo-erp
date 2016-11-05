# -*- encoding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
from finan_contrato_sale.models.sql_contratos_comercial import *
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia, formata_data
from dateutil.relativedelta import relativedelta

#
# Escala Atingimento metas  Variável
# De 0 a 39,99 (%)          0%
# De 40 a 49,99 (%)         25%
# De 50 a 59,99 (%)         40%
# De 60 a 100 (%)           proporcional
# De 100 para cima          100%
#

#
# Faixa de faturamento do posto e remuneração variável
# Gestor de negócio Junior e Gestor de negócio Pleno
#       0,00 -  24.999,99 =   750,00
#  25.000,00 -  49.999,99 = 1.000,00
#  50.000,00 -  74.999,99 = 1.500,00
#  75.000,00 -  99.999,99 = 2.000,00
# 100.000,00 - 124.999,99 = 2.500,00
# 125.000,00 - 149.999,99 = 3.000,00
# 150.000,00 - 199.999,99 = 3.500,00
#

#
# Faixa de faturamento do posto e remuneração variável
# Gestor de negócio Senior e Coordenador Comercial
#       0,00 -  49.999,99 =   750,00
#  50.000,00 -  99.999,99 = 1.000,00
# 100.000,00 - 149.999,99 = 1.500,00
# 150.000,00 - 199.999,99 = 2.000,00
# 200.000,00 - 249.999,99 = 2.500,00
# 250.000,00 - 299.999,99 = 3.000,00
# 300.000,00 - 349.999,99 = 3.500,00
# 350.000,00 - 399.999,99 = 4.000,00
# 400.000,00 - 499.999,99 = 4.500,00
#

#
# Faixa de faturamento do posto e remuneração variável
# Gerente de Unidade e Gerente de Mercado
#       0,00 -  74.999,99 = 2.500,00
#  75.000,00 - 149.999,99 = 3.000,00
# 150.000,00 - 224.999,99 = 3.500,00
# 225.000,00 - 299.999,99 = 4.000,00
# 300.000,00 - 399.999,99 = 4.500,00
#

#
# Faixa Atingimento das metas de retenção de carteira
# De  0,00% a  96,99%      =   0%
# De 97,00% a  97,49%      =  20%
# De 97,50% a  97,99%      =  40%
# De 98,00% a  98,49%      =  60%
# De 98,50% a  98,99%      =  80%
# De 99,00% a 100,00%      = 100%
#


class comercial_meta(osv.Model):
    _name = 'comercial.meta'
    _order = 'data_inicial desc, name'
    _rec_name = 'descricao'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            txt = registro.vendedor_id.name or ''
            txt += ' - de '
            txt += formata_data(registro.data_inicial)
            txt += ' a '
            txt += formata_data(registro.data_final)

            retorno[registro.id] = txt

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [('vendedor_id.name', 'ilike', texto)]

        return procura


    def _get_saldo_meta(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for meta_obj in self.browse(cr, uid, ids):
            saldo = D(0)

            sql = """
            select
                sum(
                    case
                        when coalesce(cm.vr_novos_total, 0) - coalesce(cm.meta_vr_novos_real, 0) > 0 or cm.data_final = '{data_final}' then coalesce(cm.vr_novos_total, 0) - coalesce(cm.meta_vr_novos_real, 0)
                        else 0
                    end
                ) as saldo

            from
                comercial_meta cm

            where
                cm.data_final <= '{data_final}'
                and cm.vendedor_id = {vendedor_id}
                -- and exists(
                --    select cmd.meta_id from comercial_meta_department cmd
                --    where cmd.department_id in ({posto_ids})
                --    and cmd.meta_id = cm.id
                --)
                --and exists(
                --    select cmc.meta_id from comercial_meta_company cmc
                --    where cmc.company_id in ({company_ids})
                --    and cmc.meta_id = cm.id
                --)
                ;
            """

            company_ids = []
            for c_obj in meta_obj.company_ids:
                company_ids.append(c_obj.id)

            company_ids = str(company_ids)
            company_ids = company_ids.replace('[', '')
            company_ids = company_ids.replace(']', '')

            posto_ids = []
            for posto_obj in meta_obj.hr_department_ids:
                posto_ids.append(posto_obj.id)

            posto_ids = str(posto_ids)
            posto_ids = posto_ids.replace('[', '')
            posto_ids = posto_ids.replace(']', '')

            filtro = {
                'company_ids': company_ids,
                'posto_ids': posto_ids,
                'data_final': meta_obj.data_final,
                'vendedor_id': meta_obj.vendedor_id.id,
            }

            sql = sql.format(**filtro)
            #print(sql)
            cr.execute(sql)

            dados = cr.fetchall()

            if len(dados):
                saldo = D(dados[0][0])

            res[meta_obj.id] = saldo

        return res

    def get_campo_tela(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for meta_obj in self.browse(cr, uid, ids):
            nome_campo = nome_campo.replace('1', '')
            nome_campo = nome_campo.replace('2', '')
            nome_campo = nome_campo.replace('3', '')
            nome_campo = nome_campo.replace('4', '')
            nome_campo = nome_campo.replace('5', '')
            nome_campo = nome_campo.replace('6', '')

            res[meta_obj.id] = getattr(meta_obj, nome_campo)

        return res

    _columns = {
        'descricao': fields.function(_descricao, string='Documento', method=True, type='char', fnct_search=_procura_descricao),
        'vendedor_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
        'name': fields.related('vendedor_id', 'login', string=u'Vendedor', store=True, type='char', size=80),
        'company_ids': fields.many2many('res.company', 'comercial_meta_company', 'meta_id', 'company_id', u'Empresas'),
        'vendedor_ids': fields.many2many('res.users', 'comercial_meta_vendedor', 'meta_id', 'vendedor_id', u'Vendedores'),
        'hr_department_ids': fields.many2many('hr.department', 'comercial_meta_department', 'meta_id', 'department_id', u'Postos'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),

        'exclui_categoria_ids': fields.many2many('res.partner.category', 'comercial_meta_categoria', 'meta_id', 'categoria_id', u'Categorias a excluir'),
        #'categoria_ids': fields.one2many('comercia.meta.categoria.excluir', 'meta_id', u'Categorias a excluir'),

        'vr_novos_total': fields.float(u'Contratos novos'),
        'vr_novos_total2': fields.function(get_campo_tela, type='float', string=u'Contratos novos'),
        'vr_novos_total6': fields.function(get_campo_tela, type='float', string=u'Contratos novos'),
        'qtd_novos_total': fields.integer(u'Quant. de contratos novos'),
        'vr_novos_anterior_total': fields.float(u'Contratos novos anterior'),
        'qtd_novos_anterior_total': fields.integer(u'Quant. de contratos novos anterior'),

        'meta_vr_novos_total': fields.float(u'Meta original de contratos novos'),
        'meta_vr_novos_deficit': fields.float(u'Déficit perdas mês anterior'),
        'meta_vr_novos_superavit': fields.float(u'Crédito meta mês anterior'),
        'meta_vr_novos_superavit2': fields.function(get_campo_tela, type='float', string=u'Crédito meta mês anterior'),
        'meta_vr_novos_real': fields.float(u'Meta real de contratos novos'),
        'saldo_vr_novos_mes': fields.float(u'Saldo mês'),
        'saldo_vr_novos_mes2': fields.function(get_campo_tela, type='float', string=u'Saldo mês'),
        'saldo_vr_novos_total': fields.float(u'Saldo acumulado'),

        'vr_vendas_total': fields.float(u'Faturamento de vendas'),
        'meta_vr_vendas_total': fields.float(u'Meta de faturamento de vendas'),
        'vr_faturamento_total': fields.float(u'Faturamento de vendas'),

        'vr_rescindidos_total': fields.float(u'Valor dos rescindidos'),
        'vr_rescindidos_total2': fields.function(get_campo_tela, type='float', string=u'Valor dos rescindidos'),
        'vr_rescindidos_total6': fields.function(get_campo_tela, type='float', string=u'Valor dos rescindidos'),
        'qtd_rescindidos_total': fields.integer(u'Quant. de contratos rescindidos'),
        'vr_rescindidos_anterior_total': fields.float(u'Valor dos rescindidos anterior'),
        'qtd_rescindidos_anterior_total': fields.integer(u'Quant. de contratos rescindidos anterior'),

        'vr_reducao_total': fields.float(u'Diminuições de mensalidades'),
        'vr_anterior_total': fields.float(u'Valor período anterior'),
        'vr_anterior_total2': fields.function(get_campo_tela, type='float', string=u'Valor período anterior'),
        'vr_diferenca_total': fields.float(u'Diferença de mensalidades'),
        'vr_diferenca_total6': fields.function(get_campo_tela, type='float', string=u'Valor dos rescindidos'),
        'percentual_diminuicao_financeira': fields.float(u'Diminuição financeira da carteira'),
        'meta_percentual_diminuicao_financeira': fields.float(u'Meta de diminuição financeira'),
        'percentual_crescimento_financeiro': fields.float(u'Crescimento financeiro da carteira'),
        'meta_percentual_crescimento_financeiro': fields.float(u'Meta de crescimento financeiro'),
        'percentual_crescimento_quantitativo': fields.float(u'Crescimento quantitativo da carteira'),

        'vr_regulares_total': fields.float(u'Valor dos regulares'),
        'qtd_regulares_total': fields.float(u'Quant. de contratos regulares'),
        'vr_regulares_anterior_total': fields.float(u'Valor dos regulares anterior'),
        'qtd_regulares_anterior_total': fields.float(u'Quant. de contratos regulares anterior'),

        'vr_baixados_total': fields.float(u'Valor dos baixados'),
        'qtd_baixados_total': fields.integer(u'Quant. de contratos baixados'),
        'vr_baixados_anterior_total': fields.float(u'Valor dos baixados anterior'),
        'qtd_baixados_anterior_total': fields.integer(u'Quant. de contratos baixados anterior'),

        'vr_perdas_total': fields.float(u'Valor de perdas'),
        'media_perdas_total': fields.float(u'Média de perdas'),
        'qtd_anterior_total': fields.integer(u'Quant. anterior total'),

        'carteira': fields.float(u'Carteira final'),
        'carteira6': fields.function(get_campo_tela, type='float', string=u'Carteira final'),
        'carteira_inicial': fields.float(u'Carteira inicial'),
        'carteira_inicial2': fields.function(get_campo_tela, type='float', string=u'Carteira inicial'),
        'carteira_inicial3': fields.function(get_campo_tela, type='float', string=u'Carteira inicial'),
        'carteira_inicial6': fields.function(get_campo_tela, type='float', string=u'Carteira inicial'),

        'carteira_inicial_organica': fields.float(u'Carteira inicial orgânica'),
        'carteira_inicial_organica2': fields.function(get_campo_tela, type='float', string=u'Carteira inicial orgânica'),
        'carteira_organica': fields.float(u'Carteira final orgânica'),
        'carteira_organica2': fields.function(get_campo_tela, type='float', string=u'Carteira final orgânica'),

        'carteira_transferida': fields.float(u'Carteira transferida'),
        'carteira_transferida2': fields.function(get_campo_tela, type='float', string=u'Carteira transferida'),
        'carteira_transferida3': fields.function(get_campo_tela, type='float', string=u'Carteira transferida'),

        'teto_variavel': fields.float(u'Teto variável'),
        'percentual_aplicado': fields.float(u'Perc. variável'),
        'vr_variavel': fields.float(u'Valor variável'),

        'teto_variavel_organica': fields.float(u'Teto variável'),
        'percentual_aplicado_organica': fields.float(u'Perc. variável'),
        'vr_variavel_organica': fields.float(u'Valor variável'),

        'percentual_atingido_vr_novos_total': fields.float(u'Perc. atingido de contratos novos'),
        'percentual_repres_vr_novos_total': fields.float(u'Perc. repres. de contratos novos'),
        'vr_variavel_vr_novos_total': fields.float(u'Variável de contratos novos'),

        'percentual_atingido_vr_vendas_total': fields.float(u'Perc. atingido de faturamento de vendas'),
        'percentual_repres_vr_vendas_total': fields.float(u'Perc. repres. de faturamento de vendas'),
        'vr_variavel_vr_vendas_total': fields.float(u'Variável de faturamento de vendas'),

        'percentual_atingido_diminuicao_financeira': fields.float(u'Perc. atingido de diminuição financeira'),
        'percentual_repres_diminuicao_financeira': fields.float(u'Perc. repres. de diminuição financeira'),
        'vr_variavel_diminuicao_financeira': fields.float(u'Variável de diminuição financeira'),

        'percentual_atingido_crescimento_financeiro': fields.float(u'Perc. atingido de crescimento financeiro'),
        'percentual_repres_crescimento_financeiro': fields.float(u'Perc. repres. de crescimento financeiro'),
        'vr_variavel_crescimento_financeiro': fields.float(u'Variável de crescimento financeiro'),
        'saldo_crescimento_financeiro': fields.float(u'Saldo crescimento financeiro'),
        'saldo_acumulado_crescimento_financeiro': fields.float(u'Saldo acumulado crescimento financeiro'),

        'fechado': fields.boolean(u'Fechar cálculo?'),
        'data_fechamento': fields.datetime(u'Data de fechamento'),
        'user_id': fields.many2one('res.users', u'Responsável pelo fechamento'),

        'nf_venda_ids': fields.one2many('comercial.meta.nf.venda', 'meta_id', u'Notas de venda'),
        'nf_devolucao_ids': fields.one2many('comercial.meta.nf.devolucao', 'meta_id', u'Notas de devolução'),
        'contrato_novo_ids': fields.one2many('comercial.meta.contrato.novo', 'meta_id', u'Contratos novos'),
        'contrato_rescindido_ids': fields.one2many('comercial.meta.contrato.rescindido', 'meta_id', u'Contratos rescindidos'),
        'contrato_diferenca_ids': fields.one2many('comercial.meta.diferenca.meses', 'meta_id', u'Diferenças entre meses'),
        'contrato_transferido_ids': fields.one2many('comercial.meta.contrato.transferido', 'meta_id', u'Contratos transferidos'),

        'indicador_corporativo': fields.boolean(u'Indicadores corporativos?'),
        'incluir_vigilancia': fields.boolean(u'Incluir serviços de vigilância?'),
        'incluir_somente_vigilancia': fields.boolean(u'Incluir SOMENTE serviços de vigilância?'),


        'vr_retencao_carteira': fields.float(u'Retenção da carteira'),
        'percentual_retencao_carteira': fields.float(u'Perc. retenção da carteira'),
        'meta_percentual_retencao_carteira': fields.float(u'Meta de retenção da carteira'),
        'percentual_atingido_retencao_carteira': fields.float(u'Perc. atingido de retenção da carteira'),
        'percentual_repres_retencao_carteira': fields.float(u'Perc. respres. de retenção da carteira'),
        'vr_variavel_retencao_carteira': fields.float(u'Variável de retenção da carteira'),

        'vr_retencao_carteira_organica': fields.float(u'Retenção da carteira'),
        'percentual_retencao_carteira_organica': fields.float(u'Perc. retenção da carteira'),
        'meta_percentual_retencao_carteira_organica': fields.float(u'Meta de retenção da carteira'),
        'percentual_atingido_retencao_carteira_organica': fields.float(u'Perc. atingido de retenção da carteira'),
        'percentual_repres_retencao_carteira_organica': fields.float(u'Perc. respres. de retenção da carteira'),
        'vr_variavel_retencao_carteira_organica': fields.float(u'Variável de retenção da carteira'),
        
        'input_ids': fields.one2many('hr.payslip.input', 'meta_id', u'Entradas variáveis'),
    }

    def copy(self, cr, uid, id, default={}, context={}):
        default = {
            'nf_venda_ids': False,
            'nf_devolucao_ids': False,
            'contrato_novo_ids': False,
            'contrato_rescindido_ids': False,
            'contrato_diferenca_ids': False,
            'contrato_transferido_ids': False,
            'fechado': False,
            'data_fechamento': False,
            'user_id': False,
            'meta_vr_novos_deficit': False,
            'meta_vr_novos_superavit': False,
            'meta_vr_novos_real': False,
            'meta_vr_novos_total': False,
            'meta_vr_vendas_total': False,
            'meta_percentual_crescimento_financeiro': False,
            'meta_percentual_diminuicao_financeira': False,
            'carteira_inicial': False,
            'carteira_transferida': False,
            'carteira_inicial2': False,
            'carteira_inicial3': False,
            'carteira': False,
            'meta_percentual_retencao_carteira': False,
        }

        return super(comercial_meta, self).copy(cr, uid, id, default=default, context=context)

    def fechar_calculo(self, cr, uid, ids, context={}):
        meta_pool = self.pool.get('comercial.meta')
        contract_pool = self.pool.get('hr.contract')
        input_pool = self.pool.get('hr.payslip.input')

        for meta_obj in meta_pool.browse(cr, uid, ids):
            if meta_obj.fechado:
                continue

            dados = {
                'fechado': True,
                'data_fechamento': fields.datetime.now(),
                'user_id': uid,
            }

            meta_obj.write(dados)

            #
            # Acumular na meta de novos do mês seguinte a soma de
            # rescindidos e diminuições financeiras
            #
            deficit = D(meta_obj.vr_rescindidos_total or 0)
            deficit += D(meta_obj.vr_reducao_total or 0) * -1

            superavit = D(0)
            if meta_obj.saldo_vr_novos_total > 0:
                superavit = D(meta_obj.saldo_vr_novos_total)

            data_seguinte = parse_datetime(meta_obj.data_final).date() + relativedelta(days=1)
            proximo_periodo = meta_pool.search(cr, uid, [('vendedor_id', '=', meta_obj.vendedor_id.id), ('data_inicial', '=', str(data_seguinte))])

            if len(proximo_periodo):
                proxima_meta_obj = meta_pool.browse(cr, uid, proximo_periodo[0])
                meta_vr_novos_real = D(proxima_meta_obj.meta_vr_novos_total or 0)
                meta_vr_novos_real += deficit

                meta_pool.write(cr, uid, [proxima_meta_obj.id], {'meta_vr_novos_deficit': deficit * -1, 'meta_vr_novos_real': meta_vr_novos_real, 'meta_vr_novos_superavit': superavit, 'carteira_inicial': meta_obj.carteira, 'carteira_inicial_organica': meta_obj.carteira_organica})
            
            sql = """
                select distinct
                    co.id
                from res_users u
                    join resource_resource rr on rr.user_id = u.id
                    join hr_employee e on e.resource_id = rr.id
                    join hr_contract co on co.employee_id = e.id
                where 
                co.date_end is null
                and u.id = {id}                
                limit 1""".format(id=meta_obj.vendedor_id.id)
                
            cr.execute(sql)
            dados = cr.fetchall()
            
            linhas = []
            if not dados:
                continue
            else:
                contrato_obj = contract_pool.browse(cr, uid, dados[0][0])
                
                valor_comissao = D(meta_obj.vr_variavel) + D(meta_obj.vr_variavel_organica)
                dados = {                   
                    'meta_id': meta_obj.id,
                    'company_id': contrato_obj.company_id.id,
                    'contract_id': contrato_obj.id, 
                    'employee_id': contrato_obj.employee_id.id,
                    'rule_id': 11,                                                         
                    'data_inicial': meta_obj.data_inicial,
                    'data_final': meta_obj.data_final,                    
                    'amount': valor_comissao or 0                    
                }                    
                input_pool.create(cr,uid, dados)     
                
        return True          
            

    def monta_filtro(self, cr, uid, meta_obj, filtro_faturamento=False, filtro_transferencia=False):
        data_inicial = parse_datetime(meta_obj.data_inicial).date()
        data_final = parse_datetime(meta_obj.data_final).date()
        texto_filtro = ''

        #
        # Caso seja informado dia 1º e último dia do mês, as datas seguem o mês calendário,
        # caso contrário, são meses corridos
        #
        if data_inicial == primeiro_dia_mes(data_inicial) and data_final == ultimo_dia_mes(data_final):
            meses = idade_meses_sem_dia(data_inicial, data_final) + 1

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_inicial_anterior = primeiro_dia_mes(data_inicial_anterior)
            data_final_anterior = ultimo_dia_mes(data_inicial_anterior + relativedelta(months=+meses-1))

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(day=1)
            data_final_competencia += relativedelta(months=+1)
            data_final_competencia = ultimo_dia_mes(data_final_competencia)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(day=1)
            data_final_competencia_anterior += relativedelta(months=+1)
            data_final_competencia_anterior = ultimo_dia_mes(data_final_competencia_anterior)

        else:
            meses = idade_meses_sem_dia(data_inicial, data_final)

            data_inicial_anterior = data_inicial + relativedelta(months=-meses)
            data_final_anterior = data_final + relativedelta(months=-meses)

            data_inicial_competencia = data_inicial + relativedelta(months=+1)
            data_final_competencia = data_final + relativedelta(months=+1)

            data_inicial_competencia_anterior = data_inicial_anterior + relativedelta(months=+1)
            data_final_competencia_anterior = data_final_anterior + relativedelta(months=+1)

        filtro = {
            'campo_data_vencimento': 'data_vencimento_original',

            'data_inicial': data_inicial,
            'data_final': data_final,
            'data_inicial_competencia': data_inicial_competencia,
            'data_final_competencia': data_final_competencia,
            'filtro_adicional': '',
            'filtro_adicional_anterior': '',
            'data_inicial_anterior': data_inicial_anterior,
            'data_final_anterior': data_final_anterior,
            'data_inicial_competencia_anterior': data_inicial_competencia_anterior,
            'data_final_competencia_anterior': data_final_competencia_anterior,
        }

        ###
        ### Cancelando a filtragem por postos, e assumindo a filtragem por nome do vendedor
        ### 04/03/2016 - reunião com Simone e Liziane
        ###
        ##posto_ids = []
        ##for posto_obj in meta_obj.hr_department_ids:
            ##posto_ids.append(posto_obj.id)

        ##posto_ids = str(posto_ids)
        ##posto_ids = posto_ids.replace('[', '')
        ##posto_ids = posto_ids.replace(']', '')

        ##if len(posto_ids):
            ##if filtro_faturamento:
                ##filtro['filtro_adicional'] += ' and posto.id in ({posto_ids})'.format(posto_ids=posto_ids)
                ##filtro['filtro_adicional_anterior'] += ' and posto.id in ({posto_ids})'.format(posto_ids=posto_ids)

            ##else:
                ##filtro['filtro_adicional'] += ' and fc.hr_department_id in ({posto_ids})'.format(posto_ids=posto_ids)
                ##filtro['filtro_adicional_anterior'] += ' and fc.hr_department_id in ({posto_ids})'.format(posto_ids=posto_ids)

        ##elif meta_obj.indicador_corporativo:
            ##if len(meta_obj.vendedor_ids):
                ##vendedor_ids = []
                ##for vendedor_obj in meta_obj.vendedor_ids:
                    ##vendedor_ids.append(vendedor_obj.id)

                ##vendedor_ids = str(vendedor_ids)
                ##vendedor_ids = vendedor_ids.replace('[', '')
                ##vendedor_ids = vendedor_ids.replace(']', '')

                ##filtro['vendedor_ids'] = vendedor_ids

            ##else:
                ##filtro['vendedor_ids'] = meta_obj.vendedor_id.id

            ##if filtro_faturamento:
                ##filtro['filtro_adicional'] += ' and vendedor.id in ({vendedor_ids})'.format(**filtro)
                ##filtro['filtro_adicional_anterior'] += ' and vendedor.id in ({vendedor_ids})'.format(**filtro)

            ##else:
                ##filtro['filtro_adicional'] = """and exists(
                    ##select fcv.id
                    ##from finan_contrato_vendedor fcv
                    ##where fcv.contrato_id = fc.id
                    ##and fcv.vendedor_id in ({vendedor_ids})
                    ##and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
                ##)""".format(**filtro)
                ##filtro['filtro_adicional_anterior'] = """and exists(
                    ##select fcv.id
                    ##from finan_contrato_vendedor fcv
                    ##where fcv.contrato_id = fc.id
                    ##and fcv.vendedor_id in ({vendedor_ids})
                    ##and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
                ##)""".format(**filtro)

        if len(meta_obj.vendedor_ids):
            vendedor_ids = []
            for vendedor_obj in meta_obj.vendedor_ids:
                vendedor_ids.append(vendedor_obj.id)

            vendedor_ids = str(vendedor_ids)
            vendedor_ids = vendedor_ids.replace('[', '')
            vendedor_ids = vendedor_ids.replace(']', '')

            filtro['vendedor_ids'] = vendedor_ids

        else:
            filtro['vendedor_ids'] = meta_obj.vendedor_id.id

        if filtro_faturamento:
            filtro['filtro_adicional'] += ' and vendedor.id in ({vendedor_ids})'.format(**filtro)
            filtro['filtro_adicional_anterior'] += ' and vendedor.id in ({vendedor_ids})'.format(**filtro)

        elif filtro_transferencia:
            filtro['filtro_adicional'] += ' and v.vendedor_id in ({vendedor_ids})'.format(**filtro)
            filtro['filtro_adicional_anterior'] += ' and v.vendedor_id in ({vendedor_ids})'.format(**filtro)

        else:
            filtro['filtro_adicional'] += ' and fc.vendedor_id in ({vendedor_ids})'.format(**filtro)
            filtro['filtro_adicional_anterior'] += ' and fc.vendedor_id in ({vendedor_ids})'.format(**filtro)

            #filtro['filtro_adicional'] = """and exists(
                #select fcv.id
                #from finan_contrato_vendedor fcv
                #where fcv.contrato_id = fc.id
                #and fcv.vendedor_id in ({vendedor_ids})
                #and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
            #)""".format(**filtro)
            #filtro['filtro_adicional_anterior'] = """and exists(
                #select fcv.id
                #from finan_contrato_vendedor fcv
                #where fcv.contrato_id = fc.id
                #and fcv.vendedor_id in ({vendedor_ids})
                #and daterange(fcv.data_inicial, coalesce(fcv.data_final, cast(current_date + interval '10 years' as date))) && daterange('{data_inicial}', '{data_final}')
            #)""".format(**filtro)

        company_ids = []
        for c_obj in meta_obj.company_ids:
            company_ids.append(c_obj.id)

        company_ids = str(company_ids)
        company_ids = company_ids.replace('[', '')
        company_ids = company_ids.replace(']', '')
        filtro['company_ids'] = company_ids

        if len(meta_obj.exclui_categoria_ids):
            categoria_ids = []
            for cat_obj in meta_obj.exclui_categoria_ids:
                categoria_ids.append(cat_obj.id)

            if filtro_faturamento:
                filtro['filtro_adicional'] += ' and (ped.res_partner_category_id is null or ped.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and (ped.res_partner_category_id is null or ped.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')
            else:
                filtro['filtro_adicional'] += ' and (fc.res_partner_category_id is null or fc.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')
                filtro['filtro_adicional_anterior'] += ' and (fc.res_partner_category_id is null or fc.res_partner_category_id not in ({categorias}))'.format(categorias=categoria_ids).replace('[', '').replace(']', '')

        if filtro_faturamento:
            return filtro

        #if not rel_obj.zera_saldo:
        if meta_obj.incluir_somente_vigilancia:
            #texto_filtro += u'; incluídos SOMENTE serviços de vigilância'
            print('eh soh vigilancia organica')

            filtro['filtro_adicional'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) > 0)
            """
            filtro['filtro_adicional_anterior'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) > 0)
            """

        elif not meta_obj.incluir_vigilancia:
            #texto_filtro += u'; não incluídos serviços de vigilância'

            filtro['filtro_adicional'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) = 0)
            """
            filtro['filtro_adicional_anterior'] += """
                and (coalesce((
                    select
                        count(prod.*)
                    from
                        finan_contrato_produto prod
                    where
                        prod.contrato_id = fc.id
                        and prod.product_id in (3185, 3187)
                ),0) = 0)
            """

        return filtro

    def agrupa_indicadores(self, cr, uid, meta_obj):
        agrupa = {}

        #if numero_empresa == 0:
            #indice = 'total'
        #else:
            #indice = str(numero_empresa)
        indice = 'total'

        agrupa['vr_regulares_%s' % indice] = D(0)
        agrupa['qtd_regulares_%s' % indice] = D(0)
        agrupa['vr_regulares_anterior_%s' % indice] = D(0)
        agrupa['qtd_regulares_anterior_%s' % indice] = D(0)
        agrupa['vr_novos_%s' % indice] = D(0)
        agrupa['qtd_novos_%s' % indice] = D(0)
        agrupa['vr_novos_anterior_%s' % indice] = D(0)
        agrupa['qtd_novos_anterior_%s' % indice] = D(0)
        agrupa['vr_rescindidos_%s' % indice] = D(0)
        agrupa['qtd_rescindidos_%s' % indice] = D(0)
        agrupa['vr_rescindidos_anterior_%s' % indice] = D(0)
        agrupa['qtd_rescindidos_anterior_%s' % indice] = D(0)
        agrupa['vr_baixados_%s' % indice] = D(0)
        agrupa['qtd_baixados_%s' % indice] = D(0)
        agrupa['vr_baixados_anterior_%s' % indice] = D(0)
        agrupa['qtd_baixados_anterior_%s' % indice] = D(0)
        agrupa['vr_anterior_%s' % indice] = D(1)
        agrupa['qtd_anterior_%s' % indice] = D(1)
        agrupa['vr_reducao_%s' % indice] = D(0)
        agrupa['vr_diferenca_%s' % indice] = D(0)
        agrupa['vr_reajuste_%s' % indice] = D(0)
        agrupa['vr_faturamento_%s' % indice] = D(0)
        agrupa['vr_perdas_%s' % indice] = D(0)
        agrupa['media_perdas_%s' % indice] = D(0)
        agrupa['vr_vendas_%s' % indice] = D(0)

        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj, filtro_faturamento=True)
        #
        # Valor de vendas (vendas - devoluções)
        #
        sql = SQL_RESUMO_FATURAMENTO.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            for tipo, unidade, posto, vendedor, vr_faturado in dados:
                agrupa['vr_vendas_%s' % indice] += vr_faturado

        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj)
        #
        # Buscamos as reduções e diferenças do período
        #
        sql = SQL_CONTRATOS_DIFERENCA_MESES_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for numero_documento_original, numero_documento, data_vencimento_contrato, valor_contrato, valor_contrato_anterior, data_vencimento_anterior, contrato_id, contrato_ids, reajuste_ids, diferenca, cliente, numero_contrato in dados:
            if not reajuste_ids:
                agrupa['vr_diferenca_%s' % indice] += D(diferenca or 0)

                if diferenca < 0:
                    agrupa['vr_reducao_%s' % indice] += D(diferenca or 0)
            else:
                agrupa['vr_reajuste_%s' % indice] += D(diferenca or 0)

        #
        # Agrupamos os dados do período anterior
        #
        #
        # Valores agrupados para indicadores - REGULARES
        #
        sql = SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_regulares_anterior_%s' % indice], agrupa['qtd_regulares_anterior_%s' % indice] = dados[0]
            agrupa['vr_regulares_anterior_%s' % indice] = D(agrupa['vr_regulares_anterior_%s' % indice] or 0)
            agrupa['qtd_regulares_anterior_%s' % indice] = D(agrupa['qtd_regulares_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - NOVOS
        #
        sql = SQL_CONTRATOS_NOVOS_ANTERIOR_COMERCIAL.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_novos_anterior_%s' % indice], agrupa['qtd_novos_anterior_%s' % indice] = dados[0]
            agrupa['vr_novos_anterior_%s' % indice] = D(agrupa['vr_novos_anterior_%s' % indice] or 0)
            agrupa['qtd_novos_anterior_%s' % indice] = D(agrupa['qtd_novos_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - RESCINDIDOS
        #
        sql = SQL_CONTRATOS_RESCINDIDOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_rescindidos_anterior_%s' % indice], agrupa['qtd_rescindidos_anterior_%s' % indice] = dados[0]
            agrupa['vr_rescindidos_anterior_%s' % indice] = D(agrupa['vr_rescindidos_anterior_%s' % indice] or 0)
            agrupa['qtd_rescindidos_anterior_%s' % indice] = D(agrupa['qtd_rescindidos_anterior_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - BAIXADOS
        #
        sql = SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_baixados_anterior_%s' % indice], agrupa['qtd_baixados_anterior_%s' % indice] = dados[0]
            agrupa['vr_baixados_anterior_%s' % indice] = D(agrupa['vr_baixados_anterior_%s' % indice] or 0)
            agrupa['qtd_baixados_anterior_%s' % indice] = D(agrupa['qtd_baixados_anterior_%s' % indice] or 0)

        agrupa['vr_anterior_%s' % indice] = agrupa['vr_regulares_anterior_%s' % indice] + agrupa['vr_novos_anterior_%s' % indice]
        agrupa['vr_anterior_%s' % indice] = agrupa['vr_anterior_%s' % indice] or D(1)
        agrupa['qtd_anterior_%s' % indice] = agrupa['qtd_regulares_anterior_%s' % indice] + agrupa['qtd_novos_anterior_%s' % indice]
        agrupa['qtd_anterior_%s' % indice] = agrupa['qtd_anterior_%s' % indice] or D(1)

        #
        # Montamos o filtro do mês atual
        #
        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj)
        filtro['data_inicial_anterior'] = filtro['data_inicial']
        filtro['data_final_anterior'] = filtro['data_final']
        filtro['data_inicial_competencia_anterior'] = filtro['data_inicial_competencia']
        filtro['data_final_competencia_anterior'] = filtro['data_final_competencia']

        #
        # Valores agrupados para indicadores - REGULARES
        #
        sql = SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL.format(**filtro)
        #print('regulares')
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_regulares_%s' % indice], agrupa['qtd_regulares_%s' % indice] = dados[0]
            agrupa['vr_regulares_%s' % indice] = D(agrupa['vr_regulares_%s' % indice] or 0)
            agrupa['qtd_regulares_%s' % indice] = D(agrupa['qtd_regulares_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - NOVOS
        #
        sql = SQL_CONTRATOS_NOVOS_ANTERIOR_COMERCIAL.format(**filtro)
        #print('novos')
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()
        #print(dados)
        if len(dados):
            agrupa['vr_novos_%s' % indice], agrupa['qtd_novos_%s' % indice] = dados[0]
            agrupa['vr_novos_%s' % indice] = D(agrupa['vr_novos_%s' % indice] or 0)
            agrupa['qtd_novos_%s' % indice] = D(agrupa['qtd_novos_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - RESCINDIDOS
        #
        sql = SQL_CONTRATOS_RESCINDIDOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_rescindidos_%s' % indice], agrupa['qtd_rescindidos_%s' % indice] = dados[0]
            agrupa['vr_rescindidos_%s' % indice] = D(agrupa['vr_rescindidos_%s' % indice] or 0)
            agrupa['qtd_rescindidos_%s' % indice] = D(agrupa['qtd_rescindidos_%s' % indice] or 0)

        #
        # Valores agrupados para indicadores - BAIXADOS
        #
        sql = SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()
        if len(dados):
            agrupa['vr_baixados_%s' % indice], agrupa['qtd_baixados_%s' % indice] = dados[0]
            agrupa['vr_baixados_%s' % indice] = D(agrupa['vr_baixados_%s' % indice] or 0)
            agrupa['qtd_baixados_%s' % indice] = D(agrupa['qtd_baixados_%s' % indice] or 0)

        #
        # Calcula a média ponderada de perdas
        #
        agrupa['vr_faturamento_%s' % indice] = agrupa['vr_regulares_%s' % indice] + agrupa['vr_novos_%s' % indice]
        agrupa['vr_perdas_%s' % indice] = agrupa['vr_rescindidos_%s' % indice] + agrupa['vr_reducao_%s' % indice]
        agrupa['media_perdas_%s' % indice] = (agrupa['vr_perdas_%s' % indice] * 100)

        if agrupa['vr_faturamento_%s' % indice]:
            agrupa['media_perdas_%s' % indice] /= agrupa['vr_faturamento_%s' % indice]
        else:
            agrupa['media_perdas_%s' % indice] = D(0)

        agrupa['media_perdas_%s' % indice] /= 100
        agrupa['media_perdas_%s' % indice] = agrupa['media_perdas_%s' % indice].quantize(D('0.01'))

        return agrupa

    def guarda_dados_indicadores(self, cr, uid, meta_obj):
        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj, filtro_faturamento=True)
        #
        # Vendas - notas e cupons
        #
        sql = SQL_FATURAMENTO_PRODUTO.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for nf_obj in meta_obj.nf_venda_ids:
            nf_obj.unlink()

        if len(dados):
            for unidade, cliente, cnpj_cpf, modelo, data_emissao_brasilia, serie, numero, vr_nf, vendedor, pedido, data_pedido, posto in dados:
                item = {
                    'meta_id': meta_obj.id,
                    'unidade': unidade,
                    'cliente': cliente,
                    'cnpj_cpf': cnpj_cpf,
                    'modelo': modelo,
                    'data_emissao_brasilia': data_emissao_brasilia,
                    'serie': serie,
                    'numero': numero,
                    'vr_nf': vr_nf,
                    'pedido': pedido,
                    'data_pedido': data_pedido,
                    'posto': posto,
                }
                self.pool.get('comercial.meta.nf.venda').create(cr, uid, item)

        #
        # Devoluções - notas e cupons
        #
        sql = SQL_DEVOLUCAO_PRODUTO.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for nf_obj in meta_obj.nf_devolucao_ids:
            nf_obj.unlink()

        if len(dados):
            itens = {}
            for unidade, cliente, cnpj_cpf, emissao, modelo, data_entrada_saida_brasilia, serie, numero, vr_nf, data_nf_devolvida, serie_nf_devolvida, numero_nf_devolvida, vendedor, pedido, data_pedido, posto in dados:
                item = {
                    'meta_id': meta_obj.id,
                    'unidade': unidade,
                    'cliente': cliente,
                    'cnpj_cpf': cnpj_cpf,
                    'emissao': emissao,
                    'modelo': modelo,
                    'data_entrada_saida_brasilia': data_entrada_saida_brasilia,
                    'serie': serie,
                    'numero': numero,
                    'vr_nf': vr_nf,
                    'data_nf_devolvida': data_nf_devolvida,
                    'serie_nf_devolvida': serie_nf_devolvida,
                    'numero_nf_devolvida': numero_nf_devolvida,
                    'pedido': pedido,
                    'data_pedido': data_pedido,
                    'posto': posto,
                }
                self.pool.get('comercial.meta.nf.devolucao').create(cr, uid, item)

        #
        # Montamos o filtro do mês atual
        #
        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj)
        filtro['data_inicial_anterior'] = filtro['data_inicial']
        filtro['data_final_anterior'] = filtro['data_final']
        filtro['data_inicial_competencia_anterior'] = filtro['data_inicial_competencia']
        filtro['data_final_competencia_anterior'] = filtro['data_final_competencia']

        #
        # Buscamos as reduções e diferenças do período
        #
        sql = SQL_CONTRATOS_DIFERENCA_MESES_COMERCIAL.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        for nf_obj in meta_obj.contrato_diferenca_ids:
            nf_obj.unlink()

        if len(dados):
            for numero_documento_original, numero_documento, data_vencimento_contrato, valor_contrato, valor_contrato_anterior, data_vencimento_anterior, contrato_id, contrato_ids, reajuste_ids, diferenca, cliente, numero_contrato in dados:
                if not reajuste_ids:
                    item = {
                        'meta_id': meta_obj.id,
                        'cliente': cliente,
                        'numero_documento_original': numero_documento_original,
                        'numero_documento': numero_documento,
                        'data_vencimento': data_vencimento_contrato,
                        'vr_contrato': valor_contrato,
                        'vr_contrato_anterior': valor_contrato_anterior,
                        'data_vencimento_anterior': data_vencimento_anterior,
                        'contrato_id': contrato_id,
                        'contrato_ids': contrato_ids,
                        'numero_contrato': numero_contrato,
                        'vr_diferenca': diferenca,
                        'vr_reducao': diferenca if diferenca < 0 else 0,
                        'vr_aumento': diferenca if diferenca > 0 else 0,
                    }
                else:
                    item = {
                        'meta_id': meta_obj.id,
                        'cliente': cliente,
                        'numero_documento_original': numero_documento_original,
                        'numero_documento': numero_documento,
                        'data_vencimento': data_vencimento_contrato,
                        'vr_contrato': valor_contrato,
                        'vr_contrato_anterior': valor_contrato_anterior,
                        'data_vencimento_anterior': data_vencimento_anterior,
                        'contrato_id': contrato_id,
                        'contrato_ids': contrato_ids,
                        'numero_contrato': numero_contrato,
                        'vr_diferenca': diferenca,
                        'vr_reajuste': diferenca,
                    }

                self.pool.get('comercial.meta.diferenca.meses').create(cr, uid, item)
        ####
        #### Valores agrupados para indicadores - REGULARES
        ####
        ###sql = SQL_CONTRATOS_REGULARES_ANTERIOR_COMERCIAL.format(**filtro)
        ####print('regulares')
        ####print(sql)
        ###cr.execute(sql)
        ###dados = cr.fetchall()
        ###if len(dados):
            ###agrupa['vr_regulares_%s' % indice], agrupa['qtd_regulares_%s' % indice] = dados[0]
            ###agrupa['vr_regulares_%s' % indice] = D(agrupa['vr_regulares_%s' % indice] or 0)
            ###agrupa['qtd_regulares_%s' % indice] = D(agrupa['qtd_regulares_%s' % indice] or 0)

        #
        # Contratos - NOVOS
        #
        sql = SQL_CONTRATOS_NOVOS_COMERCIAL.format(**filtro)
        #print('novos')
        #print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        for contrato_obj in meta_obj.contrato_novo_ids:
            contrato_obj.unlink()

        if len(dados):
            for numero_contrato, data_inicio, cliente, cnpj_cpf, vr_contrato in dados:
                item = {
                    'meta_id': meta_obj.id,
                    'cliente': cliente,
                    'cnpj_cpf': cnpj_cpf,
                    'numero_contrato': numero_contrato,
                    'data_inicio': data_inicio,
                    'vr_contrato': vr_contrato,
                }
                self.pool.get('comercial.meta.contrato.novo').create(cr, uid, item)

        #
        # Valores agrupados para indicadores - RESCINDIDOS
        #
        sql = SQL_CONTRATOS_RESCINDIDOS_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for contrato_obj in meta_obj.contrato_rescindido_ids:
            contrato_obj.unlink()

        if len(dados):
            for numero_contrato, data_distrato, cliente, cnpj_cpf, vr_contrato in dados:
                item = {
                    'meta_id': meta_obj.id,
                    'cliente': cliente,
                    'cnpj_cpf': cnpj_cpf,
                    'numero_contrato': numero_contrato,
                    'data_distrato': data_distrato,
                    'vr_contrato': vr_contrato,
                }
                self.pool.get('comercial.meta.contrato.rescindido').create(cr, uid, item)

        #
        # Valores agrupados para indicadores - TRANSFERIDOS
        #
        filtro = self.pool.get('comercial.meta').monta_filtro(cr, uid, meta_obj, filtro_transferencia=True)
        sql = SQL_CONTRATOS_TRANSFERIDOS_COMERCIAL.format(**filtro)
        cr.execute(sql)
        dados = cr.fetchall()

        for contrato_obj in meta_obj.contrato_transferido_ids:
            contrato_obj.unlink()

        carteira_transferida = D(0)
        if len(dados):
            for numero_contrato, data_transferencia, cliente, cnpj_cpf, vr_contrato in dados:
                carteira_transferida += D(vr_contrato or 0)
                item = {
                    'meta_id': meta_obj.id,
                    'cliente': cliente,
                    'cnpj_cpf': cnpj_cpf,
                    'numero_contrato': numero_contrato,
                    'data_transferencia': data_transferencia,
                    'vr_contrato': vr_contrato,
                }
                self.pool.get('comercial.meta.contrato.transferido').create(cr, uid, item)

        #cr.execute('update comercial_meta set carteira_transferida = ' + str(carteira_transferida) + ' where id = ' + str(meta_obj.id) + ';')
        ####
        #### Valores agrupados para indicadores - BAIXADOS
        ####
        ###sql = SQL_CONTRATOS_BAIXADOS_ANTERIOR_COMERCIAL.format(**filtro)
        ###cr.execute(sql)
        ###dados = cr.fetchall()
        ###if len(dados):
            ###agrupa['vr_baixados_%s' % indice], agrupa['qtd_baixados_%s' % indice] = dados[0]
            ###agrupa['vr_baixados_%s' % indice] = D(agrupa['vr_baixados_%s' % indice] or 0)
            ###agrupa['qtd_baixados_%s' % indice] = D(agrupa['qtd_baixados_%s' % indice] or 0)

        ####
        #### Calcula a média ponderada de perdas
        ####
        ###agrupa['vr_faturamento_%s' % indice] = agrupa['vr_regulares_%s' % indice] + agrupa['vr_novos_%s' % indice]
        ###agrupa['vr_perdas_%s' % indice] = agrupa['vr_rescindidos_%s' % indice] + agrupa['vr_reducao_%s' % indice]
        ###agrupa['media_perdas_%s' % indice] = (agrupa['vr_perdas_%s' % indice] * 100)

        ###if agrupa['vr_faturamento_%s' % indice]:
            ###agrupa['media_perdas_%s' % indice] /= agrupa['vr_faturamento_%s' % indice]
        ###else:
            ###agrupa['media_perdas_%s' % indice] = D(0)

        ###agrupa['media_perdas_%s' % indice] /= 100
        ###agrupa['media_perdas_%s' % indice] = agrupa['media_perdas_%s' % indice].quantize(D('0.01'))
        return {'carteira_transferida': carteira_transferida}

    def acumula_indicadores(self, cr, uid, ids, context={}):
        self._acumula_indicadores_organica(cr, uid, ids, context=context)
        self._acumula_indicadores(cr, uid, ids, context=context)

    def _acumula_indicadores(self, cr, uid, ids, context={}):
        meta_pool = self.pool.get('comercial.meta')

        #
        # Usa o admin para acumular os indicadores
        #
        uid = 1
        for meta_obj in self.browse(cr, uid, ids):
            if meta_obj.fechado:
                continue
                #raise osv.except_osv(u'Email obrigatório!', u'Seu usuário precisa ter um endereço de email configurado nas preferências de usuário para poder enviar emails')

            indicadores = self.pool.get('comercial.meta').guarda_dados_indicadores(cr, uid, meta_obj)
            indicadores.update(self.pool.get('comercial.meta').agrupa_indicadores(cr, uid, meta_obj))

            #
            # Exceção inserida pelo chamado 1905
            # Liziane mandou zerar as perdas, ou seja, segundo ela, o sistema deve zerar os rescindidos
            # nas comissões do período 25/03 a 24/04, exceto para o Rafael, Carlinho e Gerce
            #
            if meta_obj.data_inicial == '2016-03-25' and meta_obj.vendedor_id.id not in (51, 13, 12):
                indicadores['vr_rescindidos_total'] = 0

            #if meta_obj.data_inicial == '2015-12-25':
                #meta_obj.carteira_inicial = D(meta_obj.vr_regulares_anterior_total or 0)
                #meta_obj.carteira_inicial += D(meta_obj.vr_novos_anterior_total or 0)
                #meta_obj.carteira_inicial -= D(meta_obj.vr_rescindidos_anterior_total or 0)
                #indicadores['carteira_inicial'] = meta_obj.carteira_inicial

            #sql_credito = """
                #select
                    #sum(coalesce(vr_novos_total, 0) - coalesce(meta_vr_novos_real, 0))

                #from comercial_meta

                #where
                    #vendedor_id = {vendedor_id}
                    #and data_final <= '{data_inicial}'
                    #and data_inicial >= '2015-12-25';
            #""".format(vendedor_id=meta_obj.vendedor_id.id, data_inicial=meta_obj.data_inicial)
            #cr.execute(sql_credito)
            #dados = cr.fetchall()
            #if len(dados):
                #indicadores['meta_vr_novos_superavit'] = dados[0][0]
                #indicadores['meta_vr_novos_superavit2'] = dados[0][0]
                #meta_obj.meta_vr_novos_superavit = dados[0][0]
            #else:
                #indicadores['meta_vr_novos_superavit'] = D(0)
                #indicadores['meta_vr_novos_superavit2'] = D(0)
                #meta_obj.meta_vr_novos_superavit = D(0)

            indicadores['carteira_inicial2'] = meta_obj.carteira_inicial
            indicadores['carteira_inicial3'] = meta_obj.carteira_inicial
            indicadores['carteira_transferida2'] = indicadores['carteira_transferida']
            indicadores['carteira_transferida3'] = indicadores['carteira_transferida']

            valor_carteira = D(meta_obj.carteira_inicial or 0) + D(indicadores['carteira_transferida'] or 0)

            if valor_carteira <= 0:
                valor_carteira = 1

            percentual_diminuicao_financeira = D(0)
            percentual_diminuicao_financeira += indicadores['vr_rescindidos_total']
            percentual_diminuicao_financeira += abs(indicadores['vr_reducao_total'])
            percentual_diminuicao_financeira /= valor_carteira
            percentual_diminuicao_financeira *= 100
            percentual_diminuicao_financeira = 100 - percentual_diminuicao_financeira
            percentual_diminuicao_financeira = percentual_diminuicao_financeira.quantize(D('0.01'))

            indicadores['percentual_diminuicao_financeira'] = percentual_diminuicao_financeira

            percentual_crescimento_quantitativo = D(0)
            percentual_crescimento_quantitativo = indicadores['qtd_novos_total']
            percentual_crescimento_quantitativo -= indicadores['qtd_rescindidos_total']
            percentual_crescimento_quantitativo /= indicadores['qtd_anterior_total']
            percentual_crescimento_quantitativo *= 100
            percentual_crescimento_quantitativo = percentual_crescimento_quantitativo.quantize(D('0.01'))

            indicadores['percentual_crescimento_quantitativo'] = percentual_crescimento_quantitativo

            indicadores['vr_novos_total2'] = indicadores['vr_novos_total']
            indicadores['vr_rescindidos_total2'] = indicadores['vr_rescindidos_total']
            indicadores['vr_anterior_total2'] = indicadores['vr_anterior_total']

            #
            # Carteira final é
            # carteira inicial + novos - rescindidos ± diferença de mensalidades
            #
            carteira = D(meta_obj.carteira_inicial or 0)
            carteira += D(indicadores['carteira_transferida'] or 0)
            carteira += D(indicadores['vr_novos_total'] or 0)
            carteira -= D(indicadores['vr_rescindidos_total'] or 0)
            carteira += D(indicadores['vr_diferenca_total'] or 0)
            carteira += D(indicadores['vr_reajuste_total'] or 0)
            indicadores['carteira'] = carteira

            #
            # Ajuste com crédito/débito de contratos novos
            #
            meta_vr_novos_real = D(meta_obj.meta_vr_novos_total or 0)
            meta_vr_novos_real += D(meta_obj.meta_vr_novos_deficit or 0) * -1
            indicadores['meta_vr_novos_real'] = meta_vr_novos_real

            vr_novos_total = indicadores['vr_novos_total']
            saldo_vr_novos_mes = vr_novos_total - meta_vr_novos_real
            indicadores['saldo_vr_novos_mes'] = saldo_vr_novos_mes

            indicadores['meta_vr_novos_superavit2'] = meta_obj.meta_vr_novos_superavit
            if saldo_vr_novos_mes > 0:
                indicadores['saldo_vr_novos_mes2'] = saldo_vr_novos_mes
            else:
                indicadores['saldo_vr_novos_mes2'] = 0

            superavit = D(meta_obj.meta_vr_novos_superavit or 0)
            saldo_vr_novos_total = saldo_vr_novos_mes + superavit
            #saldo_vr_novos_total -= D(meta_obj.meta_vr_novos_deficit or 0)
            indicadores['saldo_vr_novos_total'] = saldo_vr_novos_total

            vr_novos_total += superavit

            #
            # Caso o superávit do mês anterior cubra a meta, atingiu 100%
            #
            if vr_novos_total > meta_vr_novos_real:
                vr_novos_total = meta_vr_novos_real

            #
            # Agora, calculamos o crescimento financeiro, levando em conta o
            # crédito do mês anterior
            #
            valor_crescimento_financeiro = D(0)
            valor_crescimento_financeiro += indicadores['vr_novos_total']
            valor_crescimento_financeiro += superavit

            if saldo_vr_novos_mes > 0:
                valor_crescimento_financeiro += saldo_vr_novos_mes

            valor_crescimento_financeiro -= indicadores['vr_rescindidos_total']
            valor_crescimento_financeiro += indicadores['vr_diferenca_total']

            #print('valor crescimento', indicadores['vr_novos_total'], superavit, saldo_vr_novos_mes, indicadores['vr_rescindidos_total'], indicadores['vr_diferenca_total'], valor_crescimento_financeiro)

            valor_carteira = D(meta_obj.carteira_inicial or 0) + D(indicadores['carteira_transferida'] or 0)

            if valor_carteira <= 0:
                valor_carteira = 1

            percentual_crescimento_financeiro = valor_crescimento_financeiro / valor_carteira
            percentual_crescimento_financeiro *= 100
            percentual_crescimento_financeiro = percentual_crescimento_financeiro.quantize(D('0.01'))

            #
            # Passando a calcular automaticamente a meta de crescimento - 20/04/2016
            #
            meta_obj.meta_percentual_crescimento_financeiro = meta_vr_novos_real
            meta_obj.meta_percentual_crescimento_financeiro /= valor_carteira
            meta_obj.meta_percentual_crescimento_financeiro *= 100
            meta_obj.meta_percentual_crescimento_financeiro = meta_obj.meta_percentual_crescimento_financeiro.quantize(D('0.01'))
            indicadores['meta_percentual_crescimento_financeiro'] = meta_obj.meta_percentual_crescimento_financeiro

            #print('percentual_crescimento_financeiro', percentual_crescimento_financeiro)
            #print('meta_percentual_crescimento_financeiro', meta_obj.meta_percentual_crescimento_financeiro)

            if percentual_crescimento_financeiro >= meta_obj.meta_percentual_crescimento_financeiro:
                #valor_meta_crescimento_financeiro = D(meta_obj.carteira_inicial or 1) * meta_obj.meta_percentual_crescimento_financeiro / 100

                #
                # Removido devido ao chamado 1644
                #
                ###
                ### Caso tenha passado o crescimento financeiro, o saldo para levar para o mês seguinte é
                ### o que sobrar, somente quando no próprio mês houver sobre dos contratos novos
                ###
                ##if saldo_vr_novos_mes > 0:
                    ##saldo_vr_novos_total = valor_crescimento_financeiro - valor_meta_crescimento_financeiro
                    ##indicadores['saldo_vr_novos_total'] = saldo_vr_novos_total
                ##else:
                    ##indicadores['saldo_vr_novos_total'] = 0

                #percentual_crescimento_financeiro = meta_obj.meta_percentual_crescimento_financeiro
                indicadores['percentual_crescimento_financeiro'] = percentual_crescimento_financeiro

            else:
                #
                # Removido devido ao chamado 1644
                #
                ###
                ### Caso não tenha atingido a meta, zera o saldo para o mês seguinte
                ###
                ##saldo_vr_novos_total = 0
                ##indicadores['saldo_vr_novos_total'] = saldo_vr_novos_total
                indicadores['percentual_crescimento_financeiro'] = percentual_crescimento_financeiro

            saldo_crescimento_financeiro = percentual_crescimento_financeiro - meta_obj.meta_percentual_crescimento_financeiro
            indicadores['saldo_crescimento_financeiro'] = saldo_crescimento_financeiro

            sql_saldo_crescimento = """
                select
                    sum(coalesce(saldo_crescimento_financeiro, 0))

                from comercial_meta

                where
                    vendedor_id = {vendedor_id}
                    and data_final <= '{data_inicial}'
                    and data_inicial >= '2015-12-25';
            """.format(vendedor_id=meta_obj.vendedor_id.id, data_inicial=meta_obj.data_inicial)
            cr.execute(sql_saldo_crescimento)
            dados = cr.fetchall()

            if len(dados):
                saldo_acumulado_crescimento_financeiro = D(dados[0][0] or 0)
            else:
                saldo_acumulado_crescimento_financeiro = D(0)

            saldo_acumulado_crescimento_financeiro += saldo_crescimento_financeiro
            indicadores['saldo_acumulado_crescimento_financeiro'] = saldo_acumulado_crescimento_financeiro

            #
            # Com base no valor da carteira, vamos buscar a base de cálculo do variável
            #
            sql = """
            select
                coalesce(cmvf.base, 0)

            from
               comercial_meta_variavel_faixa cmvf
               join comercial_meta_variavel cmv on cmv.id = cmvf.variavel_id
               join comercial_meta_variavel_vendedor cmvv on cmvv.variavel_id = cmv.id

            where
               cmvv.vendedor_id = {vendedor_id}
               and {carteira} between coalesce(cmvf.valor_inicial, 0) and coalesce(cmvf.valor_final, 0)
               and cmvf.tipo = 'N';
            """

            sql = sql.format(vendedor_id=meta_obj.vendedor_id.id, carteira=carteira)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            try:
                teto_variavel = D(dados[0][0] or 0)
            except:
                teto_variavel = D(0)

            #
            # Calculamos agora, os percentuais atingidos e os valores de comissão
            #
            percentual_atingido_vr_novos_total = D(0)
            if meta_vr_novos_real:
                percentual_atingido_vr_novos_total = vr_novos_total / meta_vr_novos_real * 100
                percentual_atingido_vr_novos_total = percentual_atingido_vr_novos_total.quantize(D('0.01'))
            indicadores['percentual_atingido_vr_novos_total'] = percentual_atingido_vr_novos_total

            #print(saldo_vr_novos_mes)
            #print(saldo_vr_novos_total)

            percentual_atingido_vr_vendas_total = D(0)
            if meta_obj.meta_vr_vendas_total:
                percentual_atingido_vr_vendas_total = indicadores['vr_vendas_total'] / D(meta_obj.meta_vr_vendas_total) * 100
                percentual_atingido_vr_vendas_total = percentual_atingido_vr_vendas_total.quantize(D('0.01'))
            indicadores['percentual_atingido_vr_vendas_total'] = percentual_atingido_vr_vendas_total

            percentual_atingido_crescimento_financeiro = D(0)
            if meta_obj.meta_percentual_crescimento_financeiro:
                percentual_atingido_crescimento_financeiro = percentual_crescimento_financeiro / D(meta_obj.meta_percentual_crescimento_financeiro) * 100
                percentual_atingido_crescimento_financeiro = percentual_atingido_crescimento_financeiro.quantize(D('0.01'))
            indicadores['percentual_atingido_crescimento_financeiro'] = percentual_atingido_crescimento_financeiro

            percentual_atingido_diminuicao_financeira = D(0)
            if meta_obj.meta_percentual_diminuicao_financeira:
                percentual_atingido_diminuicao_financeira = percentual_diminuicao_financeira / D(meta_obj.meta_percentual_diminuicao_financeira) * 100
                percentual_atingido_diminuicao_financeira = percentual_atingido_diminuicao_financeira.quantize(D('0.01'))
            indicadores['percentual_atingido_diminuicao_financeira'] = percentual_atingido_diminuicao_financeira

            #
            # Agora, para cada percentual, vamos buscar a faixa de atingimento correspondente
            #
            sql = """
            select
                coalesce(cme.percentual_variavel, 0),
                coalesce(cme.percentual_total, 0)

            from
                comercial_meta_escala cme

            where
                cme.indicador = '{indicador}'
                and {percentual_atingido} between coalesce(cme.percentual_inicial, 0) and coalesce(cme.percentual_final, 0);
            """

            valor_variavel = D(0)
            percentual_aplicado = D(0)

            #
            # Indicador 1
            #
            sql_novos = sql.format(indicador='1', percentual_atingido=percentual_atingido_vr_novos_total)
            cr.execute(sql_novos)
            dados = cr.fetchall()

            #print(sql_novos)

            try:
                percentual_variavel, percentual_total = dados[0]

                if percentual_variavel > 100:
                    percentual_variavel = percentual_atingido_vr_novos_total

                percentual_aplicado += D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                indicadores['percentual_repres_vr_novos_total'] = percentual_total
                indicadores['vr_variavel_vr_novos_total'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

            except:
                indicadores['percentual_repres_vr_novos_total'] = 0
                indicadores['vr_variavel_vr_novos_total'] = 0

            #
            # Indicador 2
            #
            sql_vendas = sql.format(indicador='2', percentual_atingido=percentual_atingido_vr_vendas_total)
            cr.execute(sql_vendas)
            dados = cr.fetchall()

            try:
                percentual_variavel, percentual_total = dados[0]

                if percentual_variavel > 100:
                    percentual_variavel = percentual_atingido_vr_vendas_total

                percentual_aplicado += D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                indicadores['percentual_repres_vr_vendas_total'] = percentual_total
                indicadores['vr_variavel_vr_vendas_total'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

            except:
                indicadores['percentual_repres_vr_vendas_total'] = 0
                indicadores['vr_variavel_vr_vendas_total'] = 0

            #
            # Indicador 3
            #
            sql_crescimento = sql.format(indicador='3', percentual_atingido=percentual_atingido_crescimento_financeiro)
            cr.execute(sql_crescimento)
            dados = cr.fetchall()

            try:
                percentual_variavel, percentual_total = dados[0]

                if percentual_variavel > 100:
                    percentual_variavel = percentual_atingido_crescimento_financeiro

                percentual_aplicado += D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                indicadores['percentual_repres_crescimento_financeiro'] = percentual_total
                indicadores['vr_variavel_crescimento_financeiro'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

            except:
                indicadores['percentual_repres_crescimento_financeiro'] = 0
                indicadores['vr_variavel_crescimento_financeiro'] = 0

            #
            # Indicador 4
            #
            sql_diminuicao = sql.format(indicador='4', percentual_atingido=percentual_atingido_diminuicao_financeira)
            cr.execute(sql_diminuicao)
            dados = cr.fetchall()

            try:
                percentual_variavel, percentual_total = dados[0]

                if percentual_variavel > 100:
                    percentual_variavel = percentual_atingido_diminuicao_financeira

                percentual_aplicado += D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                indicadores['percentual_repres_diminuicao_financeira'] = percentual_total
                indicadores['vr_variavel_diminuicao_financeira'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

            except:
                indicadores['percentual_repres_diminuicao_financeira'] = 0
                indicadores['vr_variavel_diminuicao_financeira'] = 0


            #
            # Indicador 6
            #
            retencao = indicadores['carteira']
            indicadores['vr_retencao_carteira'] = retencao

            percentual_retencao = D(0)

            if meta_obj.carteira_inicial:
                percentual_retencao = retencao / D(meta_obj.carteira_inicial or 1) * D(100)

            indicadores['percentual_retencao_carteira'] = percentual_retencao

            percentual_atingido_retencao_carteira = D(0)
            if meta_obj.meta_percentual_retencao_carteira:
                percentual_atingido_retencao_carteira = indicadores['percentual_retencao_carteira'] / D(meta_obj.meta_percentual_retencao_carteira) * 100
                percentual_atingido_retencao_carteira = percentual_atingido_retencao_carteira.quantize(D('0.01'))
            indicadores['percentual_atingido_retencao_carteira'] = percentual_atingido_retencao_carteira

            sql_retencao = sql.format(indicador='6', percentual_atingido=percentual_atingido_retencao_carteira)
            cr.execute(sql_retencao)
            dados = cr.fetchall()

            try:
                percentual_variavel, percentual_total = dados[0]

                if percentual_variavel > 100:
                    percentual_variavel = 100

                if meta_obj.indicador_corporativo:
                    percentual_aplicado = D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                indicadores['percentual_repres_retencao_carteira'] = percentual_total
                indicadores['vr_variavel_retencao_carteira'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

            except:
                indicadores['percentual_repres_retencao_carteira'] = 0
                indicadores['vr_variavel_retencao_carteira'] = 0

            #
            # Por último, calcula o variável total
            #
            valor_variavel = teto_variavel * percentual_aplicado
            valor_variavel = valor_variavel.quantize(D('0.01'))

            indicadores['vr_variavel'] = valor_variavel
            indicadores['teto_variavel'] = teto_variavel
            indicadores['percentual_aplicado'] = percentual_aplicado * 100

            meta_obj.write(indicadores)
            cr.commit()

    def _acumula_indicadores_organica(self, cr, uid, ids, context={}):
        meta_pool = self.pool.get('comercial.meta')

        #
        # Usa o admin para acumular os indicadores
        #
        uid = 1
        for meta_obj in self.browse(cr, uid, ids):
            if meta_obj.fechado:
                continue
                #raise osv.except_osv(u'Email obrigatório!', u'Seu usuário precisa ter um endereço de email configurado nas preferências de usuário para poder enviar emails')

            meta_obj.incluir_somente_vigilancia = True

            dados_organica = {}

            indicadores = self.pool.get('comercial.meta').guarda_dados_indicadores(cr, uid, meta_obj)
            indicadores.update(self.pool.get('comercial.meta').agrupa_indicadores(cr, uid, meta_obj))

            dados_organica['carteira_inicial_organica2'] = meta_obj.carteira_inicial_organica

            #
            # Carteira final é
            # carteira inicial + novos - rescindidos ± diferença de mensalidades
            #
            carteira = D(meta_obj.carteira_inicial_organica or 0)
            carteira += D(indicadores['carteira_transferida'] or 0)
            carteira += D(indicadores['carteira_transferida'] or 0)
            carteira += D(indicadores['vr_novos_total'] or 0)
            carteira -= D(indicadores['vr_rescindidos_total'] or 0)
            carteira += D(indicadores['vr_diferenca_total'] or 0)
            carteira += D(indicadores['vr_reajuste_total'] or 0)

            indicadores['carteira_organica'] = carteira
            dados_organica['carteira_organica'] = carteira

            #
            # Indicador 7
            #
            retencao = indicadores['carteira_organica']
            indicadores['vr_retencao_carteira_organica'] = retencao
            dados_organica['vr_retencao_carteira_organica'] = retencao

            percentual_retencao = D(0)

            if meta_obj.carteira_inicial_organica:
                percentual_retencao = retencao / D(meta_obj.carteira_inicial_organica or 1) * D(100)

            indicadores['percentual_retencao_carteira_organica'] = percentual_retencao
            dados_organica['percentual_retencao_carteira_organica'] = percentual_retencao

            percentual_atingido_retencao_carteira = D(0)
            if meta_obj.meta_percentual_retencao_carteira_organica:
                percentual_atingido_retencao_carteira = indicadores['percentual_retencao_carteira_organica'] / D(meta_obj.meta_percentual_retencao_carteira_organica) * 100
                percentual_atingido_retencao_carteira = percentual_atingido_retencao_carteira.quantize(D('0.01'))

            indicadores['percentual_atingido_retencao_carteira_organica'] = percentual_atingido_retencao_carteira
            dados_organica['percentual_atingido_retencao_carteira_organica'] = percentual_atingido_retencao_carteira

            #
            # Com base no valor da carteira, vamos buscar a base de cálculo do variável
            #
            sql = """
            select
                coalesce(cmvf.base, 0)

            from
               comercial_meta_variavel_faixa cmvf
               join comercial_meta_variavel cmv on cmv.id = cmvf.variavel_id
               join comercial_meta_variavel_vendedor cmvv on cmvv.variavel_id = cmv.id

            where
               cmvv.vendedor_id = {vendedor_id}
               and {carteira} between coalesce(cmvf.valor_inicial, 0) and coalesce(cmvf.valor_final, 0)
               and cmvf.tipo = 'O';
            """

            sql = sql.format(vendedor_id=meta_obj.vendedor_id.id, carteira=carteira)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            try:
                teto_variavel = D(dados[0][0] or 0)
            except:
                teto_variavel = D(0)

            #
            # Agora, buscamos o percentual do variável
            #
            sql = """
            select
                coalesce(cme.percentual_variavel, 0),
                coalesce(cme.percentual_total, 0)

            from
                comercial_meta_escala cme

            where
                cme.indicador = '{indicador}'
                and {percentual_atingido} between coalesce(cme.percentual_inicial, 0) and coalesce(cme.percentual_final, 0);
            """

            sql_retencao = sql.format(indicador='7', percentual_atingido=percentual_atingido_retencao_carteira)
            cr.execute(sql_retencao)
            dados = cr.fetchall()

            if len(dados):
                #try:
                if True:
                    percentual_variavel, percentual_total = dados[0]

                    if percentual_variavel > 100:
                        percentual_variavel = 100

                    percentual_aplicado = D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                    dados_organica['percentual_repres_retencao_carteira_organica'] = percentual_total
                    dados_organica['vr_variavel_retencao_carteira_organica'] = teto_variavel * D(percentual_variavel or 0) * D(percentual_total or 0) / 100 / 100

                #except:
                    #dados_organica['percentual_repres_retencao_carteira_organica'] = 0
                    #dados_organica['vr_variavel_retencao_carteira_organica'] = 0

                #
                # Por último, calcula o variável total
                #
                valor_variavel = teto_variavel * percentual_aplicado
                valor_variavel = valor_variavel.quantize(D('0.01'))

                dados_organica['vr_variavel_organica'] = valor_variavel
                dados_organica['teto_variavel_organica'] = teto_variavel
                dados_organica['percentual_aplicado_organica'] = percentual_aplicado * 100

            print('dados_organica')
            print(dados_organica)

            meta_obj.write(dados_organica)
            cr.commit()

    def ajuste_antigo(self, cr, uid, ids, context={}):
        meta_pool = self.pool.get('comercial.meta')

        #
        # Usa o admin para acumular os indicadores
        #
        uid = 1
        for meta_obj in self.browse(cr, uid, ids):
            if meta_obj.fechado:
                continue

            #
            # Ajusta metas e carteiras anteriores a setembro/2015
            #
            #if meta_obj.data_final > '2015-09-25':
                #continue

            if D(meta_obj.carteira_inicial or 0) > 0:
                continue

            filtro_meta_posterior = (
                ('vendedor_id', '=', meta_obj.vendedor_id.id),
                ('data_inicial', '>', meta_obj.data_final),
            )

            meta_posterior_ids = meta_pool.search(cr, uid, filtro_meta_posterior, order='data_inicial', limit=1)
            if len(meta_posterior_ids) <= 0:
                continue


            meta_posterior_obj = meta_pool.browse(cr, uid, meta_posterior_ids[0])
            #print('carteira final posterior', meta_posterior_obj.carteira_inicial)

            dados = {
                'carteira_inicial': D(meta_posterior_obj.carteira_inicial or 0) - D(meta_obj.carteira),
                'carteira_inicial2': D(meta_posterior_obj.carteira_inicial or 0) - D(meta_obj.carteira),
                'carteira_inicial3': D(meta_posterior_obj.carteira_inicial or 0) - D(meta_obj.carteira),
            }
            #print('carteira inicial atual', dados['carteira_inicial'])
            meta_obj.write(dados)
            cr.commit()
            meta_pool.acumula_indicadores(cr, uid, [meta_obj.id])


comercial_meta()



class comercial_meta_variavel(osv.Model):
    _name = 'comercial.meta.variavel'
    _order = 'name'

    _columns = {
        'name': fields.char(u'Descrição', size=60, select=True),
        'vendedor_ids': fields.many2many('res.users', 'comercial_meta_variavel_vendedor', 'variavel_id', 'vendedor_id', u'Vendedores'),
        'faixa_ids': fields.one2many('comercial.meta.variavel.faixa', 'variavel_id', string=u'Faixas', domain=[('tipo', '=', 'N')]),
        'faixa_vigilancia_organica_ids': fields.one2many('comercial.meta.variavel.faixa', 'variavel_id', string=u'Faixas', domain=[('tipo', '=', 'O')]),
    }


comercial_meta_variavel()


class comercial_meta_variavel_faixa(osv.Model):
    _name = 'comercial.meta.variavel.faixa'
    _order = 'variavel_id, valor_final'

    _columns = {
        'variavel_id': fields.many2one('comercial.meta.variavel', u'Variável', ondelete='cascade'),
        'tipo': fields.selection((('N', u'Normal'), ('O', u'Orgânica')), string=u'Tipo', select=True),
        'valor_inicial': fields.float(u'Valor inicial'),
        'valor_final': fields.float(u'Valor final'),
        'base': fields.float(u'Teto'),
    }

    _defaults = {
        'tipo': 'N',
    }


comercial_meta_variavel_faixa()


INDICADOR = (
    ('1', u'1 - Novos contratos'),
    ('2', u'2 - Vendas'),
    ('3', u'3 - Crescimento da carteira'),
    ('4', u'4 - Diminuição da carteira'),
    ('6', u'6 - Retenção da carteira'),
    ('7', u'7 - Retenção da carteira orgânica'),
)


class comercial_meta_escala(osv.Model):
    _name = 'comercial.meta.escala'
    _order = 'indicador, percentual_final'

    _columns = {
        'indicador': fields.selection(INDICADOR, u'Indicador', select=True),
        'percentual_inicial': fields.float(u'Perc. inicial'),
        'percentual_final': fields.float(u'Perc. final', select=True),
        'percentual_variavel': fields.float(u'Perc. variável'),
        'percentual_total': fields.float(u'Perc. representatividade'),
    }

    _defaults = {
        'indicador': '1',
        'percentual_total': 25,
    }


comercial_meta_escala()



class comercial_meta_nf_venda(osv.Model):
    _name = 'comercial.meta.nf.venda'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),
        'unidade': fields.char(u'Unidade', size=120),
        'cliente': fields.char(u'Cliente', size=120),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'modelo': fields.char(u'Modelo', size=2),
        'data_emissao_brasilia': fields.date(u'Data emissão'),
        'serie': fields.char(u'Série', size=6),
        'numero': fields.integer(u'Número'),
        'vr_nf': fields.float(u'Valor'),
        'pedido': fields.char(u'Pedido', size=40),
        'data_pedido': fields.date(u'Data pedido'),
        'posto': fields.char(u'Posto', size=120),
    }


comercial_meta_nf_venda()


class comercial_meta_nf_devolucao(osv.Model):
    _name = 'comercial.meta.nf.devolucao'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),
        'unidade': fields.char(u'Unidade', size=120),
        'cliente': fields.char(u'Cliente', size=120),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'modelo': fields.char(u'Modelo', size=2),
        'data_entrada_saida_brasilia': fields.date(u'Data entrada'),
        'serie': fields.char(u'Série', size=6),
        'numero': fields.integer(u'Número'),
        'vr_nf': fields.float(u'Valor'),
        'pedido': fields.char(u'Pedido', size=40),
        'data_pedido': fields.date(u'Data pedido'),
        'posto': fields.char(u'Posto', size=120),
        'data_nf_devolvida': fields.date(u'Data NF devolvida'),
        'serie_nf_devolvida': fields.char(u'Série dev.', size=6),
        'numero_nf_devolvida': fields.integer(u'Número dev.'),
    }


comercial_meta_nf_devolucao()


class comercial_meta_contrato_novo(osv.Model):
    _name = 'comercial.meta.contrato.novo'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),
        #'unidade': fields.char(u'Unidade', size=120),
        'numero_contrato': fields.char(u'Contrato', size=120),
        'cliente': fields.char(u'Cliente', size=120),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'vr_contrato': fields.float(u'Valor'),
        'data_inicio': fields.date(u'Data início'),
    }


comercial_meta_contrato_novo()


class comercial_meta_contrato_rescindido(osv.Model):
    _name = 'comercial.meta.contrato.rescindido'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),
        #'unidade': fields.char(u'Unidade', size=120),
        'numero_contrato': fields.char(u'Contrato', size=120),
        'cliente': fields.char(u'Cliente', size=120),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'vr_contrato': fields.float(u'Valor'),
        'data_distrato': fields.date(u'Data rescisão'),
    }


comercial_meta_contrato_rescindido()


class comercial_meta_diferenca_meses(osv.Model):
    _name = 'comercial.meta.diferenca.meses'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),

        'numero_documento_original': fields.char(u'Parcela', size=120),
        'numero_documento': fields.char(u'Nº doc.', size=120),
        'vr_contrato': fields.float(u'Valor'),
        'vr_contrato_anterior': fields.float(u'Valor anterior'),

        'data_vencimento': fields.date(u'Data vencimento'),
        'data_vencimento_anterior': fields.date(u'Data vencimento anterior'),

        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),
        'contrato_ids': fields.char(u'Contratos anteriores', size=255),
        'cliente': fields.char(u'Cliente', size=120),
        'numero_contrato': fields.char(u'Número contrato', size=120),
        'vr_diferenca': fields.float(u'Diferença'),
        'vr_reducao': fields.float(u'Redução'),
        'vr_aumento': fields.float(u'Aumento'),
        'vr_reajuste': fields.float(u'Reajuste'),
    }


comercial_meta_diferenca_meses()


class comercial_meta_contrato_transferido(osv.Model):
    _name = 'comercial.meta.contrato.transferido'

    _columns = {
        'meta_id': fields.many2one('comercial.meta', u'Meta', ondelete='cascade'),

        'numero_contrato': fields.char(u'Contrato', size=120),
        'cliente': fields.char(u'Cliente', size=120),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18),
        'vr_contrato': fields.float(u'Valor'),
        'data_transferencia': fields.date(u'Data transferência'),
    }


comercial_meta_contrato_transferido()
