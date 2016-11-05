# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from StringIO import StringIO
from pybrasil.febraban.banco import BANCO_CODIGO, Retorno, gera_retorno_pdf
from pybrasil.data import parse_datetime
from pybrasil.valor.decimal import Decimal as D


class finan_retorno(osv.Model):
    _name = 'finan.retorno'
    _description = 'Retornos de cobrança'
    _order = 'data desc, numero_arquivo desc'
    _rec_name = 'numero_arquivo'

    _columns = {
        'carteira_id': fields.many2one('finan.carteira', u'Carteira', required=True),
        'numero_arquivo': fields.integer(u'Número do arquivo'),
        'data': fields.datetime(u'Data e hora'),
        'retorno_item_ids': fields.one2many('finan.retorno_item', 'retorno_id', u'Boletos no retorno'),
        'arquivo_binario': fields.binary(u'Arquivo'),
    }

    _defaults = {
        'data': fields.datetime.now,
    }

    def processar_retorno(self, cr, uid, id, context=None):
        if isinstance(id, list):
            id = id[0]

        #if uid != 1:
            #return

        forma_pagamento_pool = self.pool.get('finan.formapagamento')
        retorno_obj = self.browse(cr, uid, id)

        if not retorno_obj.arquivo_binario:
            raise osv.except_osv(u'Erro!', u'Nenhum arquivo informado!')

        arquivo_texto = base64.decodestring(retorno_obj.arquivo_binario)
        arquivo = StringIO()
        arquivo.write(arquivo_texto)
        arquivo.seek(0)

        retorno = Retorno()
        if not retorno.arquivo_retorno(arquivo):
            raise osv.except_osv(u'Erro!', u'Formato do arquivo incorreto ou inválido!')

        if retorno.banco.codigo != retorno_obj.carteira_id.res_partner_bank_id.bank_bic:
            raise osv.except_osv(u'Erro!', u'O arquivo é de outro banco - {banco}!'.format(banco=retorno.banco.codigo))

        if retorno.beneficiario.cnpj_cpf != retorno_obj.carteira_id.res_partner_bank_id.partner_id.cnpj_cpf:
            raise osv.except_osv(u'Erro!', u'O arquivo é de outro beneficiário - {cnpj}!'.format(cnpj=retorno_obj.carteira_id.res_partner_bank_id.partner_id.cnpj_cpf))
            raise osv.except_osv(u'Erro!', u'O arquivo é de outro beneficiário - {cnpj}!'.format(cnpj=retorno.beneficiario.cnpj_cpf))

        if retorno.banco.codigo not in ('748', '104'):
            if retorno.beneficiario.agencia.numero != retorno_obj.carteira_id.res_partner_bank_id.agencia:
                raise osv.except_osv(u'Erro!', u'O arquivo é de outra agência - {agencia}!'.format(agencia=retorno.beneficiario.agencia.numero))

            if retorno.beneficiario.conta.numero != retorno_obj.carteira_id.res_partner_bank_id.acc_number:
                try:
                    if int(retorno.beneficiario.conta.numero) != int(retorno_obj.carteira_id.res_partner_bank_id.acc_number):
                        raise osv.except_osv(u'Erro!', u'O arquivo é de outra conta - {conta}!'.format(conta=retorno.beneficiario.conta.numero))
                except:
                    raise osv.except_osv(u'Erro!', u'O arquivo é de outra conta - {conta}!'.format(conta=retorno.beneficiario.conta.numero))

        if retorno.beneficiario.codigo_beneficiario.numero != retorno_obj.carteira_id.beneficiario:
            try:
                if int(retorno.beneficiario.codigo_beneficiario.numero) != int(retorno_obj.carteira_id.beneficiario):
                    raise osv.except_osv(u'Erro!', u'O arquivo é de outra código beneficiário - {bene}!'.format(bene=retorno.beneficiario.codigo_beneficiario.numero))
            except:
                raise osv.except_osv(u'Erro!', u'O arquivo é de outra código beneficiário - {bene}!'.format(bene=retorno.beneficiario.codigo_beneficiario.numero))

            retorno.beneficiario.conta.numero = retorno_obj.carteira_id.res_partner_bank_id.acc_number
            retorno.beneficiario.conta.digito = retorno_obj.carteira_id.res_partner_bank_id.conta_digito or ''

        retorno_obj.write({'numero_arquivo': retorno.sequencia, 'data': str(retorno.data_hora)})

        lancamento_pool = self.pool.get('finan.lancamento')

        #
        # Remove os boletos anteriores
        #
        for item_obj in retorno_obj.retorno_item_ids:
            item_obj.unlink()

        #
        # Exclui os retornos já existentes deste arquivo
        #
        cr.execute("update finan_lancamento set numero_documento = 'QUERO EXCLUIR' where tipo = 'PR' and retorno_id = " + str(retorno_obj.id) + ";")
        cr.execute("delete from finan_lancamento where tipo = 'PR' and retorno_id = " + str(retorno_obj.id) + ";")
        cr.commit()

        #
        # Adiciona os comandos separados para baixa/Liquidação de cliente negativado
        #
        for comando in retorno.banco.comandos_liquidacao:
            if comando + '-N' not in retorno.banco.descricao_comandos_retorno:
                retorno.banco.descricao_comandos_retorno[comando + '-N'] = retorno.banco.descricao_comandos_retorno[comando] + u' - cliente negativado'

        #
        # Processa os boletos do arquivo
        #
        for boleto in retorno.boletos:
            if boleto.identificacao.upper().startswith('ID_'):
                lancamento_id = int(boleto.identificacao.upper().replace('ID_', ''))
                lancamento_ids = lancamento_pool.search(cr, uid, [('carteira_id', '=', retorno_obj.carteira_id.id), ('id', '=', lancamento_id)])
            elif boleto.identificacao.upper().startswith('IX_'):
                lancamento_id = int(boleto.identificacao.upper().replace('IX_', ''), 36)
                lancamento_ids = lancamento_pool.search(cr, uid, [('carteira_id', '=', retorno_obj.carteira_id.id), ('id', '=', lancamento_id)])
            else:
                lancamento_ids = lancamento_pool.search(cr, uid, [('carteira_id', '=', retorno_obj.carteira_id.id), ('nosso_numero', '=', boleto.nosso_numero)])

            if lancamento_ids:
                lancamento_id = lancamento_ids[0]
            else:
                lancamento_id = False

            comando = ''
            if boleto.comando in retorno.banco.comandos_liquidacao:
                if retorno.banco.comandos_liquidacao[boleto.comando]:
                    comando = 'L'
                else:
                    comando = 'Q'
            elif boleto.comando in retorno.banco.comandos_baixa:
                comando = 'B'

            if lancamento_id:
                lancamento_obj = lancamento_pool.browse(cr, uid, lancamento_id)
                boleto.pagador.cnpj_cpf = lancamento_obj.partner_id.cnpj_cpf
                boleto.pagador.nome = lancamento_obj.partner_id.name
                boleto.documento.numero = lancamento_obj.numero_documento

                #
                # Cliente negativado não baixa automático o boleto
                #
                if comando != 'B' and lancamento_obj.formapagamento_id and lancamento_obj.formapagamento_id.cliente_negativado:
                    comando = 'N'
                    boleto.comando += '-N'

            if lancamento_id and comando:
                dados = {
                    'retorno_id': retorno_obj.id,
                    'comando': comando,
                    'lancamento_id': lancamento_id,
                }
                item_id = self.pool.get('finan.retorno_item').create(cr, uid, dados)

                dados['retorno_item_id'] = item_id

                #item_obj = self.pool.get('finan.retorno_item').browse(cr, uid, item_id)

                ##
                ## Não processa se já estiver quitado
                ##
                #if lancamento_obj.situacao not in ['A vencer', 'Vencido', 'Vence hoje']:
                    #if lancamento_obj.data_quitacao and parse_datetime(lancamento_obj.data_quitacao).date() != boleto.data_ocorrencia:
                        #item_obj.write({'quitacao_duplicada': True})
                        #boleto.pagamento_duplicado = True
                        #continue

                #
                # Deleta os pagamentos anteriores
                #
                pag_ids = lancamento_pool.search(cr, uid, [('tipo', '=', 'PR'), ('lancamento_id', '=', lancamento_obj.id), ('retorno_id', '=', retorno_obj.id), ('retorno_item_id', '=', item_id)])
                lancamento_pool.unlink(cr, uid, pag_ids)

                if comando in ('B', 'N'):
                    dados = {
                        #'data_baixa': boleto.data_
                    }
                else:
                    dados = {
                        'valor_desconto': boleto.valor_desconto,
                        'valor_juros': boleto.valor_juros,
                        'valor_multa': boleto.valor_multa,
                        'valor': boleto.valor_recebido,
                        'data_quitacao': str(boleto.data_ocorrencia)[:10],
                        'formapagamento_id': forma_pagamento_pool.id_credito_cobranca(cr, 1),
                    }

                    if comando == 'L':
                        dados['data'] = str(boleto.data_credito)[:10]
                        dados['conciliado'] = True

                    #print('lancamento id', lancamento_obj.id, 'data_quitacao', str(boleto.data_ocorrencia)[:10], 'data_credito', str(boleto.data_credito)[:10])

                lancamento_obj.write(dados, context={'baixa_boleto': True})

                if comando in ('B'):
                    pass
                else:
                    #
                    # Cria agora o pagamento em si
                    #
                    dados_pagamento = {
                        'tipo': 'PR',
                        'lancamento_id': lancamento_obj.id,
                        'company_id': lancamento_obj.company_id.id,
                        'valor_documento': lancamento_obj.valor_documento,
                        'data_quitacao': str(boleto.data_ocorrencia)[:10],
                        'data_juros': str(boleto.data_ocorrencia)[:10],
                        'data_multa': str(boleto.data_ocorrencia)[:10],
                        'data_desconto': str(boleto.data_ocorrencia)[:10],
                        'valor_desconto': boleto.valor_desconto,
                        'valor_juros': boleto.valor_juros,
                        'valor_multa': boleto.valor_multa,
                        'valor': boleto.valor_recebido,
                        'res_partner_bank_id': retorno_obj.carteira_id.res_partner_bank_id.id,
                        'carteira_id': retorno_obj.carteira_id.id,
                        'formapagamento_id': forma_pagamento_pool.id_credito_cobranca(cr, 1),
                        'retorno_id': retorno_obj.id,
                    }

                    if comando == 'L':
                        dados_pagamento['data'] = str(boleto.data_credito)[:10]
                        dados_pagamento['conciliado'] = True

                    pr_id = lancamento_pool.create(cr, uid, dados_pagamento, context={'baixa_boleto': True})
                    print('pagamento id', pr_id, 'data_quitacao', str(boleto.data_ocorrencia)[:10], 'data_credito', str(boleto.data_credito)[:10])

            cr.commit()

        pdf = gera_retorno_pdf(retorno)

        #
        # Anexa os boletos em PDF ao registro da remessa
        #
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.retorno'), ('res_id', '=', retorno_obj.id), ('name', '=', 'francesinha.pdf')])
        #
        # Apaga os boletos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': 'francesinha.pdf',
            'datas_fname': 'francesinha.pdf',
            'res_model': 'finan.retorno',
            'res_id': retorno_obj.id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

            #numero_arquivo = int(retorno_obj.carteira_id.ultimo_arquivo_retorno) + 1
            #self.write(cr, uid, [retorno_obj.id], {'numero_arquivo': str(numero_arquivo)})
            #self.pool.get('finan.carteira').write(cr, 1, [retorno_obj.carteira_id.id], {'ultimo_arquivo_retorno': str(numero_arquivo)})
        #else:
            #numero_arquivo = int(retorno_obj.numero_arquivo)

        ##
        ## Gera os boletos
        ##
        #lista_boletos = []
        #for lancamento_obj in retorno_obj.lancamento_ids:
            #boleto = lancamento_obj.gerar_boleto()
            #lista_boletos.append(boleto)

        #pdf = gera_boletos_pdf(lista_boletos)
        #nome_boleto = 'boletos_' + retorno_obj.carteira_id.res_partner_bank_id.bank_name + '_' + str(retorno_obj.data) + '.pdf'

        ##
        ## Anexa os boletos em PDF ao registro da remessa
        ##
        #attachment_pool = self.pool.get('ir.attachment')
        #attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.retorno'), ('res_id', '=', retorno_obj.id), ('name', '=', nome_boleto)])
        ##
        ## Apaga os boletos anteriores com o mesmo nome
        ##
        #attachment_pool.unlink(cr, uid, attachment_ids)

        #dados = {
            #'datas': base64.encodestring(pdf),
            #'name': nome_boleto,
            #'datas_fname': nome_boleto,
            #'res_model': 'finan.retorno',
            #'res_id': retorno_obj.id,
            #'file_type': 'application/pdf',
        #}
        #attachment_pool.create(cr, uid, dados)

        ##
        ## Gera a remessa propriamente dita
        ##
        #remessa = Remessa()
        #remessa.tipo = 'CNAB_400'
        #remessa.boletos = lista_boletos
        #remessa.sequencia = numero_arquivo
        #remessa.data_hora = datetime.strptime(retorno_obj.data, '%Y-%m-%d %H:%M:%S')

        ##
        ## Nomenclatura bradesco
        ##
        #if lista_boletos[0].banco.codigo == '237':
            #nome_retorno = 'CB' + remessa.data_hora.strftime('%d%m') + str(remessa.sequencia).zfill(2) + '.txt'
        #else:
            #nome_retorno = unicode(retorno_obj.carteira_id.nome).encode('utf-8') + '_retorno_' + str(numero_arquivo) + '.txt'

        ##
        ## Anexa a remessa ao registro da remessa
        ##
        #attachment_pool = self.pool.get('ir.attachment')
        #attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.retorno'), ('res_id', '=', retorno_obj.id), ('name', '=', nome_retorno)])
        ##
        ## Apaga os boletos anteriores com o mesmo nome
        ##
        #attachment_pool.unlink(cr, uid, attachment_ids)

        #dados = {
            #'datas': base64.encodestring(remessa.arquivo_retorno),
            #'name': nome_retorno,
            #'datas_fname': nome_retorno,
            #'res_model': 'finan.retorno',
            #'res_id': retorno_obj.id,
            #'file_type': 'text/plain',
        #}
        #attachment_pool.create(cr, uid, dados)

    #def gerar_retorno_anexo(self, cr, uid, ids, context=None):
        #for id in ids:
            #self.gerar_retorno(cr, uid, id)


finan_retorno()


class finan_retorno_item(osv.Model):
    _name = 'finan.retorno_item'
    _description = 'Item de retorno de cobrança'
    _order = 'retorno_id, lancamento_id'
    _rec_name = 'lancamento_id'

    def _valor(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if item_obj.comando in ['L', 'Q']:
                if nome_campo in ['valor', 'valor_multa', 'valor_juros', 'valor_desconto'] and item_obj.comando == 'L':
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))
                elif nome_campo not in ['valor', 'valor_multa', 'valor_juros', 'valor_desconto']:
                    valor = getattr(item_obj.lancamento_id, nome_campo, D(0))

            res[item_obj.id] = valor

        return res

    _columns = {
        'retorno_id': fields.many2one(u'finan.retorno', u'Arquivo de remessa', ondelete='cascade'),
        'comando': fields.selection(((u'L', u'Liquidação conciliada'), (u'Q', u'Liquidação a conciliar'), (u'B', u'Baixa'), (u'N', u'Liquidação a conciliar - cliente negativado')), u'Comando'),
        'lancamento_id': fields.many2one(u'finan.lancamento', u'Boleto'),
        'quitacao_duplicada': fields.boolean(u'Quitação duplicada?'),
        'data_vencimento': fields.related('lancamento_id', 'data_vencimento', type='date', relation='finan.lancamento', string=u'Data de vencimento', store=False),
        'nosso_numero': fields.related('lancamento_id', 'nosso_numero', type='char', relation='finan.lancamento', string=u'Nosso número', store=False),
        'partner_id': fields.related('lancamento_id', 'partner_id', type='many2one', relation='res.partner', string=u'Cliente', store=False),
        'data_quitacao': fields.related('lancamento_id', 'data_quitacao', type='date', relation='finan.lancamento', string=u'Data quitação', store=False),
        'data': fields.related('lancamento_id', 'data', type='date', relation='finan.lancamento', string=u'Data conciliação', store=False),
        'valor_documento': fields.related('lancamento_id', 'valor_documento', type='float', relation='finan.lancamento', string=u'Valor documento', store=False),
        #'valor_multa': fields.related('lancamento_id', 'valor_multa', type='float', relation='finan.lancamento', string=u'Multa', store=False),
        #'valor_juros': fields.related('lancamento_id', 'valor_juros', type='float', relation='finan.lancamento', string=u'Juros', store=False),
        #'valor_desconto': fields.related('lancamento_id', 'valor_desconto', type='float', relation='finan.lancamento', string=u'Desconto', store=False),
        #'valor': fields.related('lancamento_id', 'valor', type='float', relation='finan.lancamento', string=u'Valor recebido', store=False),

        'valor_multa': fields.function(_valor, type='float', string=u'Multa', store=False),
        'valor_juros': fields.function(_valor, type='float', string=u'Juros', store=False),
        'valor_desconto': fields.function(_valor, type='float', string=u'Desconto', store=False),
        'valor': fields.function(_valor, type='float', string=u'Valor', store=False),
    }

    _defaults = {
        'comando': 'L',
        'quitacao_duplicada': False,
    }


finan_retorno_item()
