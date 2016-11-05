# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from pybrasil.valor import formata_valor
from pybrasil.valor.decimal import Decimal as D
from sped_modelo_partida_dobrada import PartidaDobrada


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'contabilizacao_entrada_ids': fields.one2many('sped.documento.contabilidade', 'lancamento_id', u'Lançamentos contábeis', domain=[('tipo','in', ('R','P'))]),
        'contabilizacao_pagamento_ids': fields.one2many('sped.documento.contabilidade', 'lancamento_id', u'Lançamentos contábeis', domain=[('tipo','in', ('PR','PP'))]),
    }

    def get_partidas_dobradas_lote(self, cr, uid, ids, context={}):
        res = []

        partida_pool = self.pool.get('sped.modelo_partida_dobrada')

        partida_obj = False

        for lote_obj in self.browse(cr, uid, ids):
            print('lote', lote_obj.id, lote_obj.tipo)
            #if not lote_obj.tipo not in ['LP', 'LR']:
                #continue

            #
            # Gera as partidas a partir dos lançamento a receber ou a pagar
            # incluídos no lote, e acumula os valores das dívidas, descontando possíveis
            # pagamentos ocorridos fora do lote
            #
            total_divida = D(0)
            valor_dividas = {}
            for divida_obj in lote_obj.lote_pago_ids:
                valor_documento = D(divida_obj.valor_documento or 0)

                if divida_obj.pagamento_ids:
                    for pagamento_obj in divida_obj.pagamento_ids:
                        valor_documento -= D(pagamento_obj.valor_documento or 0)

                valor_dividas[divida_obj.id] = valor_documento
                total_divida += valor_documento

            print('total_divida', total_divida, valor_dividas)

            total_pagamento = {
                'valor': D(0),
                'valor_documento': D(0),
                'valor_juros': D(0),
                'valor_multa': D(0),
                'valor_multa': D(0),
                'valor_desconto': D(0),
                'outros_acrescimos': D(0),
            }

            for pagamento_obj in lote_obj.pagamento_ids:
                for campo in total_pagamento:
                    total_pagamento[campo] += D(getattr(pagamento_obj, campo, False) or 0)

            total_pagamento_diferenca = {
                'valor': D(0),
                'valor_documento': D(0),
                'valor_juros': D(0),
                'valor_multa': D(0),
                'valor_multa': D(0),
                'valor_desconto': D(0),
                'outros_acrescimos': D(0),
            }

            print('pago_ids', lote_obj.lote_pago_ids)
            print('pagamento_ids', lote_obj.pagamento_ids)
            i = 0
            total_divida_diferenca = D(0)
            for divida_obj in lote_obj.lote_pago_ids:
                partida = PartidaDobrada()

                partida_ids = False
                if divida_obj.tipo == 'R':
                    if divida_obj.documento_id and divida_obj.documento_id.modelo_partida_dobrada_rebimento_id:
                        partida_ids = [divida_obj.documento_id.modelo_partida_dobrada_rebimento_id.id]

                else:
                    if divida_obj.documento_id and divida_obj.documento_id.modelo_partida_dobrada_pagamento_id:
                        partida_ids = [divida_obj.documento_id.modelo_partida_dobrada_pagamento_id.id]

                print('partidas do lote', partida_ids)

                if partida_ids:
                    partida_obj = partida_pool.browse(cr, uid, partida_ids[0])
                    i += 1

                    #
                    # Busca o valor proporcional de cada dívida, descontado de possíveis pagamentos anteriores
                    #
                    valor_documento = valor_dividas[divida_obj.id]

                    porcentagem =  valor_documento / total_divida

                    #
                    # Acumula os valores proporcionais dos pagamentos
                    #
                    for pagamento_obj in lote_obj.pagamento_ids:
                        for campo in total_pagamento:
                            valor = D(getattr(pagamento_obj, campo, False) or 0)
                            valor *= porcentagem
                            valor = valor.quantize(D('0.01'))
                            total_pagamento_diferenca[campo] +=  valor

                    for item_partida_obj in partida_obj.item_ids:
                        j = 0

                        #pagamento_obj = lanc_obj
                        #if True:
                        for pagamento_obj in lote_obj.pagamento_ids:
                            partida = PartidaDobrada()

                            if item_partida_obj.conta_credito_id:
                                partida.conta_credito_id = item_partida_obj.conta_credito_id
                            elif pagamento_obj.res_partner_bank_id.conta_id:
                                partida.conta_credito_id = pagamento_obj.res_partner_bank_id.conta_id

                            if item_partida_obj.conta_debito_id:
                                partida.conta_debito_id = item_partida_obj.conta_debito_id
                            elif pagamento_obj.res_partner_bank_id.conta_id:
                                partida.conta_debito_id = pagamento_obj.res_partner_bank_id.conta_id

                            if item_partida_obj.historico_id:
                                partida.codigo_historico = item_partida_obj.historico_id.codigo
                                partida.historico = item_partida_obj.historico_id.nome or u'Lote '      
                            
                            partida.numero_documento = divida_obj.numero_documento                                                                                  

                            #
                            # Busca o valor do campo correspondente
                            #
                            partida.valor = D(getattr(pagamento_obj, item_partida_obj.campo_financeiro, 0))

                            #
                            # Agora, aplicamos a proporção do pagamento correta
                            #
                            partida.valor *= porcentagem
                            partida.valor = partida.valor.quantize(D('0.01'))

                            j += 1

                            if (partida.valor > 0) and \
                                (partida.conta_debito_id and partida.conta_credito_id) and \
                                partida.conta_credito_id.id != partida.conta_debito_id.id:

                                if i == len(lote_obj.lote_pago_ids) and j == len(lote_obj.pagamento_ids):
                                    if total_pagamento[item_partida_obj.campo_financeiro] != total_pagamento_diferenca[item_partida_obj.campo_financeiro]:
                                        partida.valor += total_pagamento[item_partida_obj.campo_financeiro] - total_pagamento_diferenca[item_partida_obj.campo_financeiro]

                                res.append(partida)

        return res

    def get_partidas_dobradas(self, cr, uid, ids, rateio=False, context={}):
        res = []

        partida_pool = self.pool.get('sped.modelo_partida_dobrada')

        partida_obj = False

        for lanc_obj in self.browse(cr, uid, ids):
            partida = PartidaDobrada()

            if lanc_obj.tipo in ['LP', 'LR']:
                res += lanc_obj.get_partidas_dobradas_lote()

            elif lanc_obj.tipo in ['E', 'S', 'T']:
                partida.valor = D(lanc_obj.valor)

                partida_obj = None

                if lanc_obj.documento_id:
                    if lanc_obj.tipo == 'E' and lanc_obj.documento_id.modelo_partida_dobrada_receber_id:
                        partida_obj = lanc_obj.documento_id.modelo_partida_dobrada_receber_id
                    elif lanc_obj.tipo == 'S' and lanc_obj.documento_id.modelo_partida_dobrada_pagar_id:
                        partida_obj = lanc_obj.documento_id.modelo_partida_dobrada_pagar_id

                if partida_obj:
                    for item_partida_obj in partida_obj.item_ids:
                        partida = PartidaDobrada()

                        if item_partida_obj.conta_credito_id:
                            partida.conta_credito_id = item_partida_obj.conta_credito_id
                        elif lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_credito_id = lanc_obj.res_partner_bank_id.conta_id

                        if item_partida_obj.conta_debito_id:
                            partida.conta_debito_id = item_partida_obj.conta_debito_id
                        elif lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_debito_id = lanc_obj.res_partner_bank_id.conta_id

                        if item_partida_obj.historico_id:
                            partida.codigo_historico = item_partida_obj.historico_id.codigo
                            partida.historico = item_partida_obj.historico_id.nome or u'' 

                        #
                        # Busca o valor do campo correspondente
                        #
                        partida.valor = D(getattr(lanc_obj, item_partida_obj.campo_financeiro, 0))

                        if (partida.valor > 0) and \
                            (partida.conta_debito_id and partida.conta_credito_id) and \
                            partida.conta_credito_id.id != partida.conta_debito_id.id:
                            res.append(partida)

                else:
                    if lanc_obj.tipo in ['S', 'T']:
                        if lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_credito_id = lanc_obj.res_partner_bank_id.conta_id
                            
                        if lanc_obj.tipo == 'S':
                            partida.conta_debito_id = lanc_obj.conta_id                             

                        elif lanc_obj.res_partner_bank_creditar_id.conta_id:
                            partida.conta_debito_id = lanc_obj.res_partner_bank_creditar_id.conta_id

                    elif lanc_obj.tipo == 'E':
                        partida.conta_credito_id = lanc_obj.conta_id

                        if lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_debito_id = lanc_obj.res_partner_bank_id.conta_id                    

                    if (partida.valor > 0) and \
                        (partida.conta_debito_id and partida.conta_credito_id) and \
                        partida.conta_credito_id.id != partida.conta_debito_id.id:
                        res.append(partida)

            #elif lanc_obj.tipo in ['PR', 'PP'] and lanc_obj.lancamento_id and lanc_obj.lancamento_id.tipo in ['LP', 'LR']:
                #res += lanc_obj.get_partidas_dobradas_lote()

            elif lanc_obj.tipo in ['PR', 'PP'] and lanc_obj.lancamento_id:
                #if lanc_obj.tipo == 'PR':
                    #if lanc_obj.lancamento_id.documento_id and lanc_obj.lancamento_id.documento_id.modelo_partida_dobrada_receber_id:
                        #partida_ids = [lanc_obj.lancamento_id.documento_id.modelo_partida_dobrada_receber_id.id]
                    #else:
                        #partida_ids = partida_pool.search(cr, uid, [('tabela', '=', lanc_obj.tipo)])
                #else:
                    #if lanc_obj.lancamento_id.documento_id and lanc_obj.lancamento_id.documento_id.modelo_partida_dobrada_pagar_id:
                        #partida_ids = [lanc_obj.lancamento_id.documento_id.modelo_partida_dobrada_pagar_id.id]
                    #else:
                        #partida_ids = partida_pool.search(cr, uid, [('tabela', '=', lanc_obj.tipo)])
                divida_obj = lanc_obj.lancamento_id

                partida_ids = []

                if lanc_obj.tipo == 'PR':
                    if divida_obj.documento_id and divida_obj.documento_id.modelo_partida_dobrada_rebimento_id:
                        partida_ids = [divida_obj.documento_id.modelo_partida_dobrada_rebimento_id.id]

                    #if lanc_obj.documento_id and lanc_obj.documento_id.modelo_partida_dobrada_receber_id:
                        #partida_ids = [lanc_obj.documento_id.modelo_partida_dobrada_receber_id.id]
                    #else:
                        #partida_ids = partida_pool.search(cr, uid, [('tabela', '=', lanc_obj.tipo)])
                else:
                    if divida_obj.documento_id and divida_obj.documento_id.modelo_partida_dobrada_pagamento_id:
                        partida_ids = [divida_obj.documento_id.modelo_partida_dobrada_pagamento_id.id]
                    #if lanc_obj.documento_id and lanc_obj.documento_id.modelo_partida_dobrada_pagar_id:
                        #partida_ids = [lanc_obj.documento_id.modelo_partida_dobrada_pagar_id.id]
                    #else:
                        #partida_ids = partida_pool.search(cr, uid, [('tabela', '=', lanc_obj.tipo)])

                if partida_ids:
                    partida_obj = partida_pool.browse(cr, uid, partida_ids[0])

                    for item_partida_obj in partida_obj.item_ids:
                        partida = PartidaDobrada()

                        if item_partida_obj.conta_credito_id:
                            partida.conta_credito_id = item_partida_obj.conta_credito_id
                        elif lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_credito_id = lanc_obj.res_partner_bank_id.conta_id

                        if item_partida_obj.conta_debito_id:
                            partida.conta_debito_id = item_partida_obj.conta_debito_id
                        elif lanc_obj.res_partner_bank_id.conta_id:
                            partida.conta_debito_id = lanc_obj.res_partner_bank_id.conta_id

                        if item_partida_obj.historico_id:
                            partida.codigo_historico = item_partida_obj.historico_id.codigo
                            partida.historico = item_partida_obj.historico_id.nome or u''

                        #
                        # Busca o valor do campo correspondente
                        #
                        partida.valor = D(getattr(lanc_obj, item_partida_obj.campo_financeiro, 0))

                        if (partida.valor > 0) and \
                            (partida.conta_debito_id and partida.conta_credito_id) and \
                            partida.conta_credito_id.id != partida.conta_debito_id.id:
                            res.append(partida)

            else:
                partida_obj = None
                itens = []

                if lanc_obj.data_baixa and lanc_obj.motivo_baixa_id and \
                    ((lanc_obj.tipo == 'R' and lanc_obj.motivo_baixa_id.modelo_partida_dobrada_receber_id)
                    or (lanc_obj.tipo == 'P' and lanc_obj.motivo_baixa_id.modelo_partida_dobrada_pagar_id)):
                    
                    if lanc_obj.tipo == 'R':
                        partida_obj = lanc_obj.motivo_baixa_id.modelo_partida_dobrada_receber_id
                    else:
                        partida_obj = lanc_obj.motivo_baixa_id.modelo_partida_dobrada_pagar_id
                    itens = partida_obj.item_ids                                                        

                elif lanc_obj.contrato_id.modelo_partida_dobrada_id:
                    partida_obj = lanc_obj.contrato_id.modelo_partida_dobrada_id
                    itens = partida_obj.item_ids

                elif lanc_obj.tipo == 'R' and lanc_obj.documento_id.modelo_partida_dobrada_receber_id:
                    partida_obj = lanc_obj.documento_id.modelo_partida_dobrada_receber_id
                    itens = partida_obj.item_ids

                elif lanc_obj.tipo == 'P' and lanc_obj.documento_id.modelo_partida_dobrada_pagar_id:
                    partida_obj = lanc_obj.documento_id.modelo_partida_dobrada_pagar_id
                    itens = partida_obj.item_ids

                for item_partida_obj in itens:
                    if rateio and ((not item_partida_obj.conta_credito_id) or (not item_partida_obj.conta_debito_id)):
                        partidas_rateio = lanc_obj.get_partidas_dobradas_rateio(item_partida_obj, D(getattr(lanc_obj, item_partida_obj.campo_financeiro, 0)))
                        res += partidas_rateio
                        continue

                    partida = PartidaDobrada()

                    if item_partida_obj.conta_credito_id:
                        partida.conta_credito_id = item_partida_obj.conta_credito_id
                    elif lanc_obj.tipo in ['PP', 'PR'] and lanc_obj.res_partner_bank_id.conta_id:
                        partida.conta_credito_id = lanc_obj.res_partner_bank_id.conta_id
                    else:
                        partida.conta_credito_id = lanc_obj.conta_id

                    if item_partida_obj.conta_debito_id:
                        partida.conta_debito_id = item_partida_obj.conta_debito_id
                    elif lanc_obj.tipo in ['PP', 'PR'] and lanc_obj.res_partner_bank_id.conta_id:
                        partida.conta_debito_id = lanc_obj.res_partner_bank_id.conta_id
                    else:
                        partida.conta_debito_id = lanc_obj.conta_id

                    if item_partida_obj.historico_id:
                        partida.codigo_historico = item_partida_obj.historico_id.codigo
                        partida.historico = item_partida_obj.historico_id.nome or u''

                    #
                    # Busca o valor do campo correspondente
                    #
                    partida.valor = D(getattr(lanc_obj, item_partida_obj.campo_financeiro, 0))

                    if (partida.valor > 0) and \
                        (partida.conta_debito_id and partida.conta_credito_id) and \
                        partida.conta_credito_id.id != partida.conta_debito_id.id:
                        res.append(partida)

        return res

    def get_partidas_dobradas_rateio(self, cr, uid, ids, item_partida_obj, valor, context={}):
        res = []

        valor = D(valor)

        for lanc_obj in self.browse(cr, uid, ids):
            contas = {}

            if lanc_obj.rateio_ids:
                for rat_obj in lanc_obj.rateio_ids:
                    partida = PartidaDobrada()

                    chave = ''
                    if item_partida_obj.conta_credito_id:
                        partida.conta_credito_id = item_partida_obj.conta_credito_id
                        chave += str(item_partida_obj.conta_credito_id.id) + '_'
                    elif rat_obj.conta_id:
                        partida.conta_credito_id = rat_obj.conta_id
                        chave += str(rat_obj.conta_id.id) + '_'

                    if item_partida_obj.conta_debito_id:
                        partida.conta_debito_id = item_partida_obj.conta_debito_id
                        chave += str(item_partida_obj.conta_debito_id.id) + '_'
                    elif rat_obj.conta_id:
                        partida.conta_debito_id = rat_obj.conta_id
                        chave += str(rat_obj.conta_id.id) + '_'

                    if rat_obj.centrocusto_id:
                        centrocusto_id = rat_obj.centrocusto_id.id
                        partida.centrocusto_id = rat_obj.centrocusto_id
                        chave += str(rat_obj.centrocusto_id.id) + '_'

                    if item_partida_obj.historico_id:
                        partida.codigo_historico = item_partida_obj.historico_id.codigo
                        partida.historico = item_partida_obj.historico_id.nome or u''

                    if not chave in contas:
                        contas[chave] = partida
                        partida.valor = valor * D(rat_obj.porcentagem) / D(100)
                    else:
                        partida = contas[chave]
                        partida.valor += valor * D(rat_obj.porcentagem) / D(100)

            else:
                partida = PartidaDobrada()

                contas[str(lanc_obj.conta_id.id)] = partida

                if item_partida_obj.conta_credito_id:
                    partida.conta_credito_id = item_partida_obj.conta_credito_id

                elif lanc_obj.conta_id:
                    partida.conta_credito_id = lanc_obj.conta_id

                if item_partida_obj.conta_debito_id:
                    partida.conta_debito_id = item_partida_obj.conta_debito_id

                elif lanc_obj.conta_id:
                    partida.conta_debito_id = lanc_obj.conta_id

                if lanc_obj.centrocusto_id and lanc_obj.centrocusto_id.tipo == 'C':
                    partida.centrocusto_id = lanc_obj.centrocusto_id

                if item_partida_obj.historico_id:
                    partida.codigo_historico = item_partida_obj.historico_id.codigo
                    partida.historico = item_partida_obj.historico_id.nome or u''

                partida.valor = valor

            for chave in contas:
                partida = contas[chave]
                if (partida.valor > 0) and \
                    (partida.conta_debito_id and partida.conta_credito_id) and \
                    partida.conta_credito_id.id != partida.conta_debito_id.id:
                    res.append(partida)

        return res

    def get_rateio_contabil_gerencial(self, cr, uid, ids, context={}):
        res = []

        cc_pool = self.pool.get('finan.centrocusto')
        campos_rateio = cc_pool.campos_rateio(cr, uid)
        campos_rateio.remove('conta_id')
        campos_rateio = sorted(campos_rateio)

        sql = """
            select
                {campos_rateio},
                sum(coalesce(porcentagem, 0)) as porcentagem
            from
                finan_lancamento_rateio_geral_folha
            where
                lancamento_id = {lancamento_id}
            group by
               {campos_rateio};
        """
        filtro = {
            'campos_rateio': str(campos_rateio).replace('[', '').replace(']', '').replace("'", ''),
            'lancamento_id': 'null',
        }

        for lanc_obj in self.browse(cr, uid, ids):
            if lanc_obj.tipo in ('R', 'P', 'E', 'S', 'T'):
                filtro['lancamento_id'] = lanc_obj.id

                sql_rateio = sql.format(**filtro)
                cr.execute(sql_rateio)
                rateios = cr.fetchall()

                for valores in rateios:
                    dados = {
                        'porcentagem': valores[-1],
                    }

                    i = 0
                    for campo in campos_rateio:
                        dados[campo] = valores[i]
                        i += 1

                    res.append(dados)

            elif lanc_obj.tipo in ('PP', 'PR'):
                #
                # O pagamento foi direto, ou foi em lote?
                #
                if lanc_obj.lancamento_id.tipo in ('R', 'P'):
                    res += lanc_obj.lancamento_id.get_rateio_contabil_gerencial()
                else:
                    #
                    # Foi em lote, e agora?
                    #
                    pass

        return res

    def gera_contabilizacao(self, cr, uid, ids, context={}):

        tipo = context.get('tipo')

        for finan_obj in self.browse(cr, uid, ids):

            partidas = []

            if tipo in ['P','R']:
                lanc_id =  finan_obj.id
                for cont_obj in finan_obj.contabilizacao_entrada_ids:
                    cont_obj.unlink()

                res = self.pool.get('finan.lancamento').get_partidas_dobradas(cr, uid, [lanc_id], rateio=False, context={})

                for partida in res:
                    
                    partidas.append(partida)

            elif tipo in ['PR','PP']:

                for pag_obj in finan_obj.pagamento_ids:

                    for cont_obj in finan_obj.contabilizacao_pagamento_ids:
                        cont_obj.unlink()

                    lanc_id = pag_obj.id

                    res = self.pool.get('finan.lancamento').get_partidas_dobradas(cr, uid, [lanc_id], rateio=False, context={})

                    if partida in res:

                        partidas.append(partida)

            if partidas > 0:

                for partida in partidas:
                    dados = {
                        'lancamento_id': finan_obj.id,
                        'tipo': tipo,
                        'data': fields.related('lancamento_id', 'data_documento', type='date', string=u'Data'),
                        'conta_credito_id': partida.conta_credito_id.id,
                        'conta_debito_id': partida.conta_debito_id.id,
                        'valor': partida.valor,
                        'codigo_historico': partida.codigo_historico,
                        'historico': partida.historico,
                    }
                    self.pool.get('sped.documento.contabilidade').create(cr, uid, dados)

        return {}

finan_lancamento()
