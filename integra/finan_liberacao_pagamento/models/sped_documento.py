# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.models.trata_nfse import monta_nfse, grava_arquivo, grava_pdf_recibo_locacao
from pybrasil.valor.decimal import Decimal as D
from sped.constante_tributaria import *
from string import upper
from copy import copy


class sped_documento(osv.Model):
    _description = 'Documentos SPED'
    _name = 'sped.documento'
    _inherit = 'sped.documento'

    _columns = {
        'finan_documento_id': fields.many2one('finan.documento', u'Tipo do documento', ondelete='restrict', select=True),
        'finan_conta_id': fields.many2one('finan.conta', u'Conta financeira', ondelete='restrict', select=True),
        'finan_centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo/modelo de rateio', ondelete='restrict', select=True),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária para depósito', ondelete='restrict', select=True),
        'finan_carteira_id': fields.many2one('finan.carteira', u'Carteira de cobrança', ondelete='restrict', select=True),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária'),
        'rateio_ids': fields.one2many('finan.rateio', 'sped_documento_id', u'Itens do rateio'),        
    }

    def onchange_operacao(self, cr, uid, ids, operacao_id):
        retorno = super(sped_documento, self).onchange_operacao(cr, uid, ids, operacao_id)

        valores = retorno['value']
        
        if not operacao_id:
            return retorno


        pode_alterar = True
        try:
            documento_obj = self.browse(cr, uid, ids[0])

            for dup_obj in documento_obj.duplicata_ids:
                if dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.situacao in ['Quitado', 'Baixado', 'Conciliado']:
                    pode_alterar = False
        except:
            pass


        if pode_alterar:
            operacao = self.pool.get('sped.operacao').browse(cr, uid, operacao_id)

            if operacao.finan_documento_id:
                valores['finan_documento_id'] = operacao.finan_documento_id.id

            if operacao.finan_conta_id:
                valores['finan_conta_id'] = operacao.finan_conta_id.id

            if operacao.finan_centrocusto_id:
                valores['finan_centrocusto_id'] = operacao.finan_centrocusto_id.id

            if operacao.finan_carteira_id:
                valores['finan_carteira_id'] = operacao.finan_carteira_id.id

            if operacao.payment_term_id:
                valores['payment_term_id'] = operacao.payment_term_id.id

        return retorno

    def onchange_payment_term(self, cr, uid, ids, payment_term_id, vr_fatura, vr_nf, data_emissao, duplicata_ids):
        valores = {}
        retorno = {'value': valores}

        if not payment_term_id:
            return retorno

        payment_term_obj = self.pool.get('account.payment.term').browse(cr, uid, payment_term_id)

        if not vr_fatura:
            vr_fatura = vr_nf

        lista_vencimentos = payment_term_obj.compute(vr_fatura, date_ref=data_emissao)

        if len(duplicata_ids) == 0 and ids:
            doc_obj = self.browse(cr, uid, ids[0])
            duplicata_ids = []
            for dup_obj in doc_obj.duplicata_ids:
                duplicata_ids.append([4, dup_obj.id, {}])

        if lista_vencimentos:
            novas_duplicatas = []
            #
            # Marca os registros anteriores para exclusão
            #
            for i in range(len(duplicata_ids)):
                if duplicata_ids[i][0] in [4, 2]:
                    duplicata_ids[i][0] = 2
                    novas_duplicatas.append(duplicata_ids[i])

            duplicata_ids = novas_duplicatas

            parcela = 1
            for data, valor in lista_vencimentos:
                dados = {
                    'numero': str(parcela),
                    'data_vencimento': data,
                    'valor': valor
                }
                duplicata_ids.append( [0, False, dados] )
                parcela += 1

            valores['duplicata_ids'] = duplicata_ids

        return retorno

    def create(self, cr, uid, dados, context={}):
        res = super(sped_documento, self).create(cr, uid, dados, context=context)

        for doc_obj in self.browse(cr, uid, [res]):
            if doc_obj.emissao == TIPO_EMISSAO_PROPRIA and doc_obj.finan_conta_id and doc_obj.payment_term_id:
                if 'payment_term_id' in dados:
                    self.ajusta_vencimentos(cr, uid, [doc_obj.id], context={'forca_duplicatas': True})
                else:
                    self.ajusta_vencimentos(cr, uid, [doc_obj.id])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documento, self).write(cr, uid, ids, dados, context=context)

        if dados:
            for doc_obj in self.browse(cr, uid, ids):
                if doc_obj.emissao == TIPO_EMISSAO_PROPRIA and doc_obj.finan_conta_id and doc_obj.payment_term_id:
                    if 'payment_term_id' in dados:
                        self.ajusta_vencimentos(cr, uid, [doc_obj.id], context={'forca_duplicatas': True})
                    else:
                        self.ajusta_vencimentos(cr, uid, [doc_obj.id])

            if ('nao_calcula' not in context) and ('gera_do_contrato' not in context):
                if 'state' in dados and dados['state'] == 'autorizada':
                    for doc_obj in self.browse(cr, uid, ids):
                        if doc_obj.emissao == TIPO_EMISSAO_PROPRIA or doc_obj.finan_conta_id or ('finan_conta_id' in dados and dados['finan_conta_id']):
                            #self.ajusta_vencimentos(cr, uid, ids)
                            self.gera_financeiro(cr, uid, ids)

                elif ('state' in dados and dados['state'] in ['cancelada','denegada','inutilizada']) or \
                    ('situacao' in dados and dados['situacao'] in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO):
                    self.cancela_financeiro(cr, uid, ids)

                else:
                    #
                    # Documentos de terceiros ou recibos de locação
                    #
                    for doc_obj in self.browse(cr, uid, ids):
                        #if doc_obj.emissao == '1' or doc_obj.modelo == 'RL':
                        if doc_obj.emissao == TIPO_EMISSAO_TERCEIROS or (not doc_obj.finan_lancamento_id):
                            if doc_obj.situacao == '00':
                                if doc_obj.modelo == 'RL':
                                    self.ajusta_vencimentos(cr, uid, [doc_obj.id])

                                if doc_obj.finan_conta_id or ('finan_conta_id' in dados and dados['finan_conta_id']):
                                    self.gera_financeiro(cr, uid, [doc_obj.id])

                            elif doc_obj.situacao in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
                                self.cancela_financeiro(cr, uid, [doc_obj.id])
            #
            # Foi ajustado o valor da fatura
            #
            elif 'nao_calcula' in context:
                print('vai ajustar duplicatas')
                self.ajusta_vencimentos(cr, uid, [doc_obj.id], context=context)

        return res

    def ajusta_vencimentos(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            if (not doc_obj.finan_lancamento_id) and ((not doc_obj.duplicata_ids) or 'forca_duplicatas' in context) and doc_obj.finan_conta_id:
                for dup_obj in doc_obj.duplicata_ids:
                    dup_obj.unlink()

                res = doc_obj.onchange_payment_term(doc_obj.payment_term_id.id, doc_obj.vr_fatura, doc_obj.vr_nf, doc_obj.data_emissao, [])
                if 'value' in res and 'duplicata_ids' in res['value']:
                    duplicata_ids = res['value']['duplicata_ids']
                    print(duplicata_ids)

                    for comando, dup_id, dados in duplicata_ids:
                        if comando == 0:
                            dados['documento_id'] = doc_obj.id
                            self.pool.get('sped.documentoduplicata').create(cr, uid, dados)

                        elif comando == 2:
                            self.pool.get('sped.documentoduplicata').unlink(cr, uid, dup_id)

    def gera_financeiro(self, cr, uid, ids):
        if not ids:
            return

        lancamento_pool = self.pool.get('finan.lancamento')
        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        for doc_obj in self.browse(cr, uid, ids):
            if (not doc_obj.finan_lancamento_id) and (doc_obj.numero > 0):
                if doc_obj.emissao == '0':
                    dados = {
                        'company_id': doc_obj.company_id.id,
                        'tipo': 'R',  # Primeira letra do tipo P/R
                        'provisionado': False,
                        'conta_id': doc_obj.finan_conta_id.id,
                        'documento_id': doc_obj.finan_documento_id.id,
                        'partner_id': doc_obj.partner_id.id,
                        'data_documento': doc_obj.data_emissao[:10],
                        'sped_documento_id': doc_obj.id,
                    }

                else:
                    dados = {
                        'company_id': doc_obj.company_id.id,
                        'tipo': 'P',  # Primeira letra do tipo P/R
                        'provisionado': False,
                        'conta_id': doc_obj.finan_conta_id.id,
                        'documento_id': doc_obj.finan_documento_id.id,
                        'partner_id': doc_obj.partner_id.id,
                        'data_documento': doc_obj.data_emissao[:10],
                        'sped_documento_id': doc_obj.id,
                    }


                if doc_obj.res_partner_bank_id:
                    dados['res_partner_bank_id'] = doc_obj.res_partner_bank_id.id
                    if upper(doc_obj.res_partner_bank_id.state) in ['ADIANTAMENTO','DEVOLUCAO']:
                        if doc_obj.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                            dados['tipo'] = 'S'
                        else:
                            dados['tipo'] = 'E'

                if doc_obj.finan_centrocusto_id:
                    dados['centrocusto_id'] = doc_obj.finan_centrocusto_id.id

                if doc_obj.finan_carteira_id:
                    dados['carteira_id'] = doc_obj.finan_carteira_id.id

                for duplicata_obj in doc_obj.duplicata_ids:
                    numero_documento = doc_obj.serie or 'SS'
                    numero_documento += '-'
                    numero_documento += str(doc_obj.numero) + '-' + duplicata_obj.numero + '/' + str(len(doc_obj.duplicata_ids))
                    dados['numero_documento'] = numero_documento
                    dados['data_vencimento'] = duplicata_obj.data_vencimento
                    dados['valor_documento'] = duplicata_obj.valor
                    if dados['tipo'] in ('E','S'):
                        dados['data_quitacao'] = dados['data_vencimento']
                        dados['valor'] = dados['valor_documento']

                    lancamento_id = None
                    if not duplicata_obj.finan_lancamento_id:
                        lancamento_id = lancamento_pool.create(cr, uid, dados)
                        duplicata_obj.write({'finan_lancamento_id': lancamento_id})

                    elif duplicata_obj.finan_lancamento_id.situacao in ['Quitado', 'Conciliado', 'Baixado']:
                        raise osv.except_osv(u'Erro!', u'Não é permitido realizar a operação, pois a duplicata %s está vinculada a um título quitado/conciliado/baixado!!' % duplicata_obj.numero)

                    elif duplicata_obj.finan_lancamento_id.situacao in ['A vencer', 'Vencido', 'Vence hoje']:
                        lancamento_id = duplicata_obj.finan_lancamento_id.id
                        duplicata_obj.finan_lancamento_id.write(dados)

                    if lancamento_id:
                        lancamento_obj = lancamento_pool.browse(cr, uid, lancamento_id)
                        if 'carteira_id' in dados and doc_obj.modelo == 'RL':
                            lancamento_obj.gerar_boleto()

                        if 'centrocusto_id' in dados:
                            for rateio_obj in lancamento_obj.rateio_ids:
                                rateio_obj.unlink()
                                
                            if getattr(doc_obj.finan_centrocusto_id, 'rateio_rh', False):
                                dados_rateio = lancamento_obj.onchange_centrocusto_id(lancamento_obj.centrocusto_id.id, lancamento_obj.valor_documento, lancamento_obj.valor, lancamento_obj.company_id.id, doc_obj.finan_conta_id.id, partner_id=lancamento_obj.partner_id.id, data_vencimento=lancamento_obj.data_vencimento, data_documento=lancamento_obj.data_documento)
                                dados_rateio = dados_rateio['value']['rateio_ids']
                            else:
                                rateio_dic = doc_obj._dados_rateio()
                                print(rateio_dic)
                                dados_rateio = []
                                dados_rateio = cc_pool.monta_dados(rateio_dic, campos=campos, lista_dados=dados_rateio, valor=doc_obj.vr_produtos, forcar_valor=lancamento_obj.valor_documento)

                            salva_rateio = []
                            for dic_rateio in dados_rateio:
                                salva_rateio += [[0, lancamento_obj.id, dic_rateio]]

                            lancamento_obj.write({'rateio_ids': salva_rateio})

    def cancela_financeiro(self, cr, uid, ids):
        if not ids:
            return

        lancamento_pool = self.pool.get('finan.lancamento')

        for doc_obj in self.browse(cr, uid, ids):
            #
            # Tratativa das notas vinculadas a contratos
            #
            if doc_obj.finan_lancamento_id and doc_obj.finan_contrato_id:
                #
                # No cancelamento financeiro dos documentos vinculados a contratos,
                # desvincular o lançamento do respectivo contrato, e tornar ele
                # para provisionado (via update para não entrar em loop), mesmo
                # que o boleto tenha sido gerado, mas não se o lançamento tiver sido
                # quitado ou conciliado
                #
                if doc_obj.finan_lancamento_id.situacao in ['Quitado', 'Conciliado', 'Baixado']:
                    raise osv.except_osv(u'Erro!', u'Não é permitido cancelar um documento vinculado a um título quitado/conciliado/baixado!!')

                else:
                    dados = {
                        'nosso_numero': '',
                        'provisionado': True,
                        'sped_documento_id': False,
                        'numero_documento': doc_obj.finan_lancamento_id.numero_documento_original or doc_obj.finan_lancamento_id.numero_documento,
                    }
                    lancamento_pool.write(cr, uid, [doc_obj.finan_lancamento_id.id], dados)
                    cr.execute('update sped_documento set finan_contrato_id = null, finan_lancamento_id = null where id = {doc_id};'.format(doc_id=doc_obj.id))

            elif (doc_obj.emissao == '0' and doc_obj.modelo in ['SE', '55', 'RL', '2D'] and (not doc_obj.finan_lancamento_id)) or \
                doc_obj.emissao == '1':
                for duplicata_obj in doc_obj.duplicata_ids:
                    if not duplicata_obj.finan_lancamento_id:
                        continue

                    lanc_obj = duplicata_obj.finan_lancamento_id
                    if lanc_obj.situacao in ['Quitado', 'Conciliado', 'Baixado']:
                        raise osv.except_osv(u'Erro!', u'Não é permitido cancelar um documento vinculado a um título quitado/conciliado/baixado!!')

                    elif doc_obj.emissao == '0' and lanc_obj.nosso_numero:
                        #
                        # Lançamentos com boleto emitido não são excluídos automaticamente
                        #
                        #raise osv.except_osv(u'Erro!', u'Não é permitido cancelar um documento vinculado a um título para o qual foi emitido um boleto! Exclua o boleto antes de realizar o cancelamento!')
                        pass

                    else:
                        lanc_obj.unlink()

    def action_gerar_recibo_locacao(self, cr, uid, ids, context=None):
        #
        # Unifica o leiaute do recibo de locação com 1 boleto
        #
        res = {}
        for doc_obj in self.browse(cr, uid, ids):
            boleto = None
            if doc_obj.finan_lancamento_id and doc_obj.finan_carteira_id:
                boleto = doc_obj.finan_lancamento_id.gerar_boleto()

            grava_pdf_recibo_locacao(self, cr, uid, doc_obj, boleto)

        return res

    def _dados_rateio(self, cr, uid, ids, context={}):
        rateio = {}

        for doc_obj in self.browse(cr, uid, ids):
            conta_obj = doc_obj.finan_conta_id
            total = D(0)
            for item_obj in doc_obj.documentoitem_ids:
                item_obj.realiza_rateio(rateio=rateio)

                #proporcao = D(1)
                #if total > 0:
                    #proporcao = valor / total

                #rateio = self._ajusta_rateio_folha(rateio, proporcao)

        return rateio

    def unlink(self, cr, uid, ids, context={}):
        lanc_pool = self.pool.get('finan.lancamento')
        lancamento_ids = []

        for nota_obj in self.browse(cr, uid, ids):
            for dup_obj in nota_obj.duplicata_ids:
                if dup_obj.finan_lancamento_id and dup_obj.finan_lancamento_id.id not in lancamento_ids:
                    lancamento_ids.append(dup_obj.finan_lancamento_id.id)

        for lanc_obj in lanc_pool.browse(cr, uid, lancamento_ids):
            if (lanc_obj.situacao not in ['Quitado', 'Conciliado', 'Baixado']) and (lanc_obj.nosso_numero == False):
                pass
            elif (lanc_obj.situacao not in ['Quitado', 'Conciliado', 'Baixado']):
                raise osv.except_osv(u'Erro!', u'Não é permitido excluir uma nota/duplicata vinculada a um título quitado/conciliado/baixado %s!!' % lanc_obj.numero_documento)
            else:
                raise osv.except_osv(u'Erro!', u'Não é permitido excluir uma nota/duplicata vinculada a um boleto emitido %s!!' % lanc_obj.numero_documento)

        res = super(sped_documento, self).unlink(cr, uid, ids, context=context)

        for lanc_obj in lanc_pool.browse(cr, uid, lancamento_ids):
            lanc_obj.unlink()

        return res

    def onchange_centrocusto_id(self, cr, uid, ids, centrocusto_id, valor_documento, valor, company_id, conta_id, partner_id=False, data_vencimento=False, data_documento=False, context={}):
        valores = {}
        res = {'value': valores}

        if not context:
            context = {}

        context.update({
            'partner_id': partner_id,
            'data_vencimento': data_vencimento,
            'data_documento': data_documento,
        })

        valor_documento = valor_documento or 0
        valor = valor or 0
        company_id = company_id or False
        conta_id = conta_id or False
        centrocusto_id = centrocusto_id or False
        
        print('passou aqui', centrocusto_id, valor_documento, valor)

        if centrocusto_id:
            centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)

            #
            # Define os valores padrão para o rateio
            # outros valores podem vir do contexto
            #
            padrao = copy(context)
            padrao['company_id'] = company_id
            padrao['conta_id'] = conta_id
            padrao['centrocusto_id'] = centrocusto_id
            rateio = {}
            rateio = self.pool.get('finan.centrocusto').realiza_rateio(cr, uid, [centrocusto_id], context=context, rateio=rateio, padrao=padrao, valor=valor_documento)

            campos = self.pool.get('finan.centrocusto').campos_rateio(cr, uid)

            dados = []
            self.pool.get('finan.centrocusto').monta_dados(rateio, campos=campos, lista_dados=dados, valor=valor_documento)
            valores['rateio_ids'] = dados

            #print('rateio', dados)

            ###rateio_ids = []
            ###valores['rateio_ids'] = rateio_ids

            ###for rateio_obj in centrocusto_obj.rateio_ids:
                ###dados = {
                    ###'centrocusto_id': rateio_obj.centrocusto_id.id,
                    ###'porcentagem': rateio_obj.porcentagem,
                    ###'valor_documento': valor_documento * (rateio_obj.porcentagem / 100.00),
                    ###'valor': valor * (rateio_obj.porcentagem / 100.00),
                ###}

                ###if rateio_obj.company_id:
                    ###dados['company_id'] = rateio_obj.company_id.id
                ###else:
                    ###dados['company_id'] = company_id

                ###if rateio_obj.conta_id:
                    ###dados['conta_id'] = rateio_obj.conta_id.id
                ###else:
                    ###dados['conta_id'] = conta_id

                ###rateio_ids.append([0, False, dados])
        #
        # Força a geração de pelo menos 1 registro para a conta financeira
        #
        else:
            rateio_ids = []
            valores['rateio_ids'] = rateio_ids

            dados = {
                'centrocusto_id': False,
                'porcentagem': 100,
                'valor_documento': valor_documento,
                'valor': valor,
                'conta_id': conta_id,
                'company_id': company_id,
            }

            rateio_ids.append([0, False, dados])

        return res


sped_documento()
