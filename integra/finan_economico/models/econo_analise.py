# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from sql_relatorio_economico import SQL_ANALISE_ECONOMICA, SQL_CONFERENCIA_ECONOMICA, SQL_NAO_ALOCADOS
from pybrasil.valor.decimal import Decimal as D
from datetime import datetime
import base64
from collections import OrderedDict


class econo_analise(orm.Model):
    _name = 'econo.analise'
    _description = u'Análise econômica'
    _order = 'data_inicial desc, data_final desc, data desc, descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=120, select=True),
        #'company_id': fields.many2one('res.company', u'Empresa/Unidade'),
        'company_ids': fields.many2many('res.company', 'econo_analise_company', 'analise_id', 'company_id', u'Empresas/Unidades'),

        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data': fields.datetime(u'Data de geração'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'arquivo_texto': fields.text(u'Arquivo'),
        'item_ids': fields.one2many('econo.analise.item', 'analise_id', u'Itens da análise'),
    }

    def gera_analise(self, cr, uid, ids, context={}):
        if not ids:
            return

        item_pool = self.pool.get('econo.analise.item')
        conta_pool = self.pool.get('econo.conta')

        for analise_obj in self.browse(cr, uid, ids):
            dados = {
                #'company_id': analise_obj.company_id.id,
                'data_inicial': analise_obj.data_inicial,
                'data_final': analise_obj.data_final,
            }

            company_ids = []
            for company_obj in analise_obj.company_ids:
                company_ids.append(company_obj.id)

            dados['company_ids'] = str(tuple(company_ids)).replace(',)', ')')

            #print('vai criar conferencia')
            sql = SQL_CONFERENCIA_ECONOMICA.format(**dados)
            cr.execute(sql)
            #print(sql)
            #print('criou conferencia')

            #print('vai criar nao alocados')
            sql = SQL_NAO_ALOCADOS.format(**dados)
            cr.execute(sql)
            #print(sql)
            #print('criou nao alocados')

            #print('vai ler analise')
            sql = SQL_ANALISE_ECONOMICA.format(**dados)
            cr.execute(sql)
            dados = cr.fetchall()
            #print('leu analise')

            #
            # Exclui os itens antigos
            #
            for item_obj in analise_obj.item_ids:
                item_obj.unlink()

            linhas_analise = {}
            resumidas = []

            for (conta_id, conta_codigo, conta_nome, valor_documento, valor,
                 valor_desconto, valor_juros, valor_multa, valor_juros_multa,
                 valor_desconto_recebido, valor_juros_recebido, valor_multa_recebido, valor_juros_multa_recebido,
                 valor_desconto_pago, valor_juros_pago, valor_multa_pago, valor_juros_multa_pago,
                 valor_usado, campo
                 ) in dados:
                dados_item = {
                    'analise_id': analise_obj.id,
                    'conta_id': conta_id,
                    'valor_documento': D(valor_documento),
                    'valor': D(valor),
                    'valor_desconto': D(valor_desconto),
                    'valor_juros': D(valor_juros),
                    'valor_multa': D(valor_multa),
                    'valor_juros_multa': D(valor_juros_multa),

                    'valor_desconto_recebido': D(valor_desconto_recebido),
                    'valor_juros_recebido': D(valor_juros_recebido),
                    'valor_multa_recebido': D(valor_multa_recebido),
                    'valor_juros_multa_recebido': D(valor_juros_multa_recebido),

                    'valor_desconto_pago': D(valor_desconto_pago),
                    'valor_juros_pago': D(valor_juros_pago),
                    'valor_multa_pago': D(valor_multa_pago),
                    'valor_juros_multa_pago': D(valor_juros_multa_pago),

                    'valor_usado': D(valor_usado),
                }
                linha = u'"' + conta_codigo + u'";'
                linha += u'"' + conta_nome + u'";'
                linha += u'{valor_usado};'
                
                if campo != 'valor_documento':
                    linha += u'{valor_usado};'
                else:
                    linha += u'{valor};'

                econo_conta_obj = conta_pool.browse(cr, uid, conta_id)

                item_pool.create(cr, uid, dados_item)

                if econo_conta_obj.resumida:
                    resumidas.append(econo_conta_obj)

                contas = u'"'
                for conta_obj in econo_conta_obj.conta_ids:
                    contas += conta_obj.codigo_completo or u''
                    contas += u' '
                    contas += conta_obj.nome or u''
                    contas += u', '

                if contas[-2:] == u', ':
                    contas = contas[:-2]

                linha += contas + u'";'

                centrocustos = u'"'
                for cc_obj in econo_conta_obj.centrocusto_ids:
                    centrocustos += cc_obj.nome or u''
                    centrocustos += u', '

                if centrocustos[-2:] == u', ':
                    centrocustos = centrocustos[:-2]

                linha += centrocustos + u'"'
                linha += u'\r\n'
                linhas_analise[conta_id] = [linha, D(valor_usado), D(valor)]

            #
            # Agora, vamos varrer a lista completa de contas, trazendo as contas
            # que faltam, definindo o valor para 0
            #
            linhas = OrderedDict()
            for conta_id in conta_pool.search(cr, uid, [], order='codigo_completo'):
                if conta_id in linhas_analise:
                    linhas[conta_id] = linhas_analise[conta_id]
                else:
                    econo_conta_obj = conta_pool.browse(cr, uid, conta_id)

                    #
                    # As conta não tem linha de análise, inserir zerada
                    #
                    dados_item = {
                        'analise_id': analise_obj.id,
                        'conta_id': conta_id,
                        'valor_documento': D(0),
                        'valor': D(0),
                        'valor_desconto': D(0),
                        'valor_juros': D(0),
                        'valor_multa': D(0),
                        'valor_juros_multa': D(0),

                        'valor_desconto_recebido': D(0),
                        'valor_juros_recebido': D(0),
                        'valor_multa_recebido': D(0),
                        'valor_juros_multa_recebido': D(0),

                        'valor_desconto_pago': D(0),
                        'valor_juros_pago': D(0),
                        'valor_multa_pago': D(0),
                        'valor_juros_multa_pago': D(0),

                        'valor_usado': D(0),
                    }
                    item_pool.create(cr, uid, dados_item)
                    linha = u'"' + econo_conta_obj.codigo_completo + u'";'
                    linha += u'"' + econo_conta_obj.nome + u'";'
                    linha += u'{valor_usado};'
                    linha += u'{valor};'
                    #linha += u'{valor_documento};'

                    if econo_conta_obj.resumida:
                        resumidas.append(econo_conta_obj)

                    contas = u'"'
                    for conta_obj in econo_conta_obj.conta_ids:
                        contas += conta_obj.codigo_completo or u''
                        contas += u' '
                        contas += conta_obj.nome or u''
                        contas += u', '

                    if contas[-2:] == u', ':
                        contas = contas[:-2]

                    linha += contas + u'";'

                    centrocustos = u'"'
                    for cc_obj in econo_conta_obj.centrocusto_ids:
                        centrocustos += cc_obj.nome or u''
                        centrocustos += u', '

                    if centrocustos[-2:] == u', ':
                        centrocustos = centrocustos[:-2]

                    linha += centrocustos + u'"'
                    linha += u'\r\n'
                    linhas[conta_id] = [linha, D(0), D(0)]

            #
            # Agora, vamos pegar as contas resumidas e fazer as somas e subtrações
            #
            for conta_resumida_obj in resumidas:
                valor_usado = D(0)
                valor = D(0)

                for soma_obj in conta_resumida_obj.resumida_soma:
                    if soma_obj.id in linhas:
                        valor_usado += linhas[soma_obj.id][1]
                        valor += linhas[soma_obj.id][2]

                for subtrai_obj in conta_resumida_obj.resumida_subtrai:
                    if subtrai_obj.id in linhas:
                        valor_usado += linhas[subtrai_obj.id][1]
                        valor += linhas[subtrai_obj.id][2]

                linhas[conta_resumida_obj.id][1] = valor_usado
                linhas[conta_resumida_obj.id][2] = valor

            #
            # Por fim, vamos montar o arquivo
            #
            arquivo = u'"CÓDIGO";"DESCRIÇÃO";"VALOR";"VALOR_LIQUIDO";"CONTAS";"CENTROS_CUSTO"\r\n'
            for conta_id in linhas:
                linha = linhas[conta_id]
                #print(linha)
                texto = linha[0]
                valor_usado = str(linha[1]).replace('.', ',')
                valor = str(linha[2]).replace('.', ',')
                arquivo += texto.format(valor_usado=valor_usado, valor=valor)

            #
            # Saldos bancários ao final do relatório
            #
            arquivo += u'"BANCO";"";"SALDO"\r\n'

            dados_analise = {
                'data': str(datetime.now())[:19],
                'arquivo_texto': arquivo.encode('utf-8'),
                'nome': 'analise_economica.csv',
                'arquivo': base64.encodestring(arquivo.encode('iso-8859-1')),
            }
            analise_obj.write(dados_analise)

            #
            # Agora, monta a conferência
            #
            cr.execute("""
                delete from finan_rateio_economico_bi;
                insert into finan_rateio_economico_bi
                (econo_conta_id, rateio_id, lancamento_id, tipo, data_quitacao, company_id, conta_id, centrocusto_id, hr_contract_id, porcentagem, valor_documento, valor,
                valor_desconto, valor_juros, valor_multa, valor_juros_multa,
                valor_desconto_recebido, valor_juros_recebido, valor_multa_recebido, valor_juros_multa_recebido,
                valor_desconto_pago, valor_juros_pago, valor_multa_pago, valor_juros_multa_pago,
                valor_usado, grupo_id, conta_individual_id, partner_bank_id)
                (
                select
                    ce.econo_conta_id,
                    ce.rateio_id,
                    ce.lancamento_id,
                    ce.tipo,
                    ce.data_compensacao as data_quitacao,
                    ce.company_id,
                    ce.conta_id,
                    ce.centrocusto_id,
                    ce.hr_contract_id,
                    ce.porcentagem,
                    ce.valor_documento,
                    ce.valor,
                    ce.valor_desconto,
                    ce.valor_juros,
                    ce.valor_multa,
                    ce.valor_juros_multa,
                    ce.valor_desconto_recebido,
                    ce.valor_juros_recebido,
                    ce.valor_multa_recebido,
                    ce.valor_juros_multa_recebido,
                    ce.valor_desconto_pago,
                    ce.valor_juros_pago,
                    ce.valor_multa_pago,
                    ce.valor_juros_multa_pago,
                    ce.valor_usado,
                    ce.grupo_id,
                    l.conta_id,
                    ce.partner_bank_id

                from
                    finan_conferencia_economica ce
                    left join finan_lancamento l on l.id = ce.lancamento_id

                where
                    ce.valor != 0
                );

update finan_rateio_economico_bi ecr set
    repetido = (
        select
            count(ecr2.*)
        from
            finan_rateio_economico_bi ecr2
        where
            ecr2.rateio_id = ecr.rateio_id
            --and ecr2.valor = ecr.valor
    )
where
    ecr.rateio_id is not null;

update finan_rateio_economico_bi ecr set
    repetido = (
        select
            count(ecr2.*)
        from
            finan_rateio_economico_bi ecr2
        where
            ecr2.lancamento_id = ecr.lancamento_id
    )
where
    ecr.rateio_id is null;

            """)


econo_analise()


class econo_analise_item(orm.Model):
    _name = 'econo.analise.item'
    _description = u'Item de análise econômica'

    _columns = {
        'analise_id': fields.many2one('econo.analise', u'Análise econômica'),
        'conta_id': fields.many2one('econo.conta', u'Conta'),
        'codigo_completo': fields.related('conta_id', 'codigo_completo', string=u'Código', type='char'),
        'nome': fields.related('conta_id', 'nome', string=u'Descrição', type='char'),
        'valor_documento': fields.float(u'Valor do documento'),
        'valor': fields.float(u'Valor líquido'),
        'valor_desconto': fields.float(u'Desconto'),
        'valor_juros': fields.float(u'Juros'),
        'valor_multa': fields.float(u'Multa'),
        'valor_juros_multa': fields.float(u'Juros/Multa'),

        'valor_desconto_recebido': fields.float(u'Desconto recebido'),
        'valor_juros_recebido': fields.float(u'Juros recebido'),
        'valor_multa_recebido': fields.float(u'Multa recebido'),
        'valor_juros_multa_recebido': fields.float(u'Juros/Multa recebido'),

        'valor_desconto_pago': fields.float(u'Desconto pago'),
        'valor_juros_pago': fields.float(u'Juros pago'),
        'valor_multa_pago': fields.float(u'Multa pago'),
        'valor_juros_multa_pago': fields.float(u'Juros/Multa pago'),

        'valor_usado': fields.float(u'Valor usado'),
    }


econo_analise_item()
