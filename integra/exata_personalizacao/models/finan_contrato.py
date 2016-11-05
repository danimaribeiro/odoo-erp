# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import os
import base64
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

COMISSAO = [
    [0,False, {'partner_id': 6822, 'papel': 'E','porcentagem': 44.80 }],
    [0,False, {'partner_id': 7089, 'papel': 'G','porcentagem': 5 }],
    [0,False, {'papel': 'A','porcentagem': 40 }],
    [0,False, {'papel': 'C','porcentagem': 10 }],
    [0,False, {'papel': 'O','porcentagem': 0.20 }],
]


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
        'comissao_ids': fields.one2many('finan.contrato.comissao', 'contrato_id', u'Comissões'),
        'data_comissao': fields.date(u'Data Comissão'),
        'vezes': fields.integer(u'Vezes'),
        'reserva_ids': fields.related('imovel_id','reserva_ids',  type='one2many', string=u'Reservas do Imóvel', relation='const.reserva.imovel', store=False),
        'imovel_conta_id': fields.related('imovel_id','conta_id',  type='many2one', string=u'Conta Financeira', relation='finan.conta', store=False),
        'imovel_centrocusto_id': fields.related('imovel_id','centrocusto_id',  type='many2one', string=u'Centro Custo', relation='finan.centrocusto', store=False),
    }

    def _default_get_comissao_ids(self, cr, uid, context={}):
        #
        # Define quem é o corretor
        #
        sql = """
        select
            p.id

        from
            res_partner p
            join hr_employee e on e.cpf = p.cnpj_cpf
            join resource_resource rr on rr.id = e.resource_id
            join res_users u on u.id = rr.user_id

        where
            u.id = {id}

        order by
            p.id

        limit 1;
        """
        sql = sql.format(id=uid)
        cr.execute(sql)
        dados = cr.fetchall()

        corretor_id = False

        if len(dados):
            corretor_id = dados[0][0]

        comissao = [
            [0,False, {'partner_id': 6822, 'papel': 'E','porcentagem': 44.80 }],
            [0,False, {'partner_id': 7089, 'papel': 'G','porcentagem': 5 }],
            [0,False, {'papel': 'A','porcentagem': 10 }],
            [0,False, {'partner_id': corretor_id, 'papel': 'C','porcentagem': 40 }],
            [0,False, {'papel': 'O','porcentagem': 0.20 }],
        ]

        return comissao

    _defaults = {
        #'comissao_ids': _default_get_comissao_ids,
        'data_comissao': fields.datetime.now,
    }

    def ajusta_agenciadores(self, cr, uid, ids):
        condicao_pool = self.pool.get('finan.contrato.condicao')
        comissao_pool = self.pool.get('finan.contrato.comissao')

        for contrato_obj in self.browse(cr, uid, ids):

            if contrato_obj.natureza != 'RI':
                continue

            agencidor_ids = []
            for contrato_imovel_obj in contrato_obj.imovel_ids:

                imovel_obj = contrato_imovel_obj.imovel_id

                for condicao_obj in imovel_obj.condicao_ids:
                    condicao_id = condicao_pool.copy(cr, uid, condicao_obj.id, {'contrato_id': contrato_obj.id, 'imovel_id': False})

                for agenciador_obj in imovel_obj.agenciador_ids:
                    agencidor_ids.append(agenciador_obj.id)

            if len(agencidor_ids):

                percentual_agenciador = D('0')
                for comissao_obj in contrato_obj.comissao_ids:

                    if comissao_obj.papel != 'A':
                        continue
                    percentual_agenciador += D(comissao_obj.porcentagem or 0)
                    comissao_obj.unlink()

                for agencidor_id in agencidor_ids:

                    dados = {'papel': 'A',
                             'porcentagem': percentual_agenciador / len(agencidor_ids),
                             'partner_id': agencidor_id,
                             'contrato_id': contrato_obj.id,
                    }
                    comissao_pool.create(cr, uid, dados)


    def create(self, cr, uid, dados, context={}):
        res = super(finan_contrato, self).create(cr, uid, dados, context=context)

        if 'imovel_ids' in dados and dados['imovel_ids']:
            self.pool.get('finan.contrato').ajusta_agenciadores(cr, uid, [res])

        if 'data_comissao' in dados or 'vezes' in dados:
            for contrato_obj in self.browse(cr, uid, [res]):
                for comissao_obj in contrato_obj.comissao_ids:
                    self.pool.get('finan.contrato.comissao').gera_parcelas(cr, uid, [comissao_obj.id], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_contrato, self).write(cr, uid, ids, dados, context=context)

        if 'imovel_ids' in dados and dados['imovel_ids']:
            self.pool.get('finan.contrato').ajusta_agenciadores(cr, uid, ids)

        if 'data_comissao' in dados or 'vezes' in dados:

            for contrato_obj in self.browse(cr, uid, ids):
                for comissao_obj in contrato_obj.comissao_ids:
                    self.pool.get('finan.contrato.comissao').gera_parcelas(cr, uid, [comissao_obj.id], context=context)

        return res


    def gera_lancamento_comissao(self, cr, uid, ids, context={}):
        lancamento_pool = self.pool.get('finan.lancamento')
        comissao_pool = self.pool.get('finan.contrato.comissao')
        parcela_pool = self.pool.get('finan.contrato.comisao.parcela')
        company_pool = self.pool.get('res.company')

        SQL_ATUALIZA_RATEIO = """
        update finan_lancamento_rateio flr set
            company_id = coalesce(flr.company_id, {company_id}),
            contrato_id = coalesce(flr.contrato_id, {contrato_id}),
            project_id = coalesce(flr.project_id, {project_id}),
            imovel_id = coalesce(flr.imovel_id, {imovel_id})
        where
            flr.lancamento_id = {lancamento_id};
        """

        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.imovel_project_id.modelo_comissao_total_receber_id:
                modelo_total_receber = contrato_obj.imovel_project_id.modelo_comissao_total_receber_id.id
            else:
                raise osv.except_osv(u'Inválido !', u'Não existe no projeto modelo financeiro Total a Receber')

            if contrato_obj.imovel_project_id.modelo_comissao_total_pagar_id:
                modelo_total_pagar = contrato_obj.imovel_project_id.modelo_comissao_total_pagar_id.id
            else:
                raise osv.except_osv(u'Inválido !', u'Não existe no projeto modelo financeiro Total a Pagar')

            #if not contrato_obj.imovel_project_id.modelo_comissao_pagar_empresa_id:
                #raise osv.except_osv(u'Inválido !', u'Não existe no projeto modelo financeiro de Comissao papel Empresa, para corretor {b}'.format(b=contrato_obj.imovel_project_id.name))

            if not contrato_obj.imovel_project_id.modelo_comissao_pagar_gerente_id:
                raise osv.except_osv(u'Inválido !', u'Não existe, no projeto {projeto}, modelo financeiro de Comissao papel Gerente'.format(projeto=contrato_obj.imovel_project_id.name))

            if not contrato_obj.imovel_project_id.modelo_comissao_pagar_agenciador_id:
                raise osv.except_osv(u'Inválido !', u'Não existe, no projeto {projeto}, modelo financeiro de Comissao papel Agenciador'.format(projeto=contrato_obj.imovel_project_id.name))

            if not contrato_obj.imovel_project_id.modelo_comissao_pagar_corretor_id:
                raise osv.except_osv(u'Inválido !', u'Não existe, no projeto {projeto}, modelo financeiro de Comissao papel Corretor'.format(projeto=contrato_obj.imovel_project_id.name))

            if not contrato_obj.imovel_project_id.modelo_comissao_pagar_outros_id:
                raise osv.except_osv(u'Inválido !', u'Não existe, no projeto {projeto}, modelo financeiro de Comissao papel Outros'.format(projeto=contrato_obj.imovel_project_id.name))

            comissao_empresa_obj = None
            for comissao_obj in contrato_obj.comissao_ids:
                if comissao_obj.papel == 'E':
                    comissao_empresa_obj = comissao_obj
                    break

            if comissao_empresa_obj is None:
                raise osv.except_osv(u'Inválido !', u'Não existe no projeto modelo financeiro Total a Pagar')

            company_empresa_ids = company_pool.search(cr, uid, [('partner_id', '=', comissao_empresa_obj.partner_id.id)])

            if len(company_empresa_ids) == 0:
                raise osv.except_osv(u'Inválido !', u'No papel de Empresa foi selecionado um parceiro que não é uma das empresas no sistema')

            company_empresa_id = company_empresa_ids[0]

            #
            # Apaga as comissões anteriores
            #
            for lanc_obj in contrato_obj.lancamento_imovel_ids:
                if lanc_obj.lancamento_recebimento_imovel_id:
                    continue

                lanc_obj.unlink()

            historico = contrato_obj.imovel_id.descricao_lista or ''
            historico += '\n'
            historico += contrato_obj.partner_id.name or ''

            filtro = {
                'company_id': company_empresa_id,
                'contrato_id': contrato_obj.id,
                'project_id': contrato_obj.imovel_id.project_id.id,
                'imovel_id': contrato_obj.imovel_id.id,
                'lancamento_id': False,
            }

            comissao_pool.gera_parcelas(cr, uid, [comissao_empresa_obj.id], valor_total=contrato_obj.valor_comissao, context=context)

            parcelas_receber = {}
            i = 1
            total_parcelas = len(comissao_empresa_obj.parcela_ids)
            for parcela_obj in comissao_empresa_obj.parcela_ids:
                #
                # Imóvel de terceiros não gera a comissão a pagar
                #
                if contrato_obj.imovel_propriedade not in ('T', 'A', 'TA'):
                    lancamento_id = lancamento_pool.copy(cr, uid, modelo_total_pagar)

                    dados = {
                        'company_id': contrato_obj.imovel_id.project_id.company_id.id,
                        'contrato_imovel_id': contrato_obj.id,
                        'parcela_comissao_id': comissao_empresa_obj.id,
                        'data_doccumento': comissao_empresa_obj.data_inicial,
                        'partner_id': comissao_empresa_obj.partner_id.id,
                        'data_vencimento': parcela_obj.data_vencimento,
                        'valor_documento': parcela_obj.valor,
                        'tipo': 'P',
                        'historico': historico,
                        'sugestao_bank_id': contrato_obj.imovel_res_partner_bank_id.id,
                        'tipo_conta': contrato_obj.imovel_project_id.modelo_comissao_total_pagar_id.conta_id.tipo,
                    }

                    numero_documento = 'CPT-' + contrato_obj.numero + '-'
                    numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                    dados['numero_documento'] = numero_documento
                    dados['numero_documento_original'] = numero_documento

                    lancamento_pool.write(cr, uid, [lancamento_id], dados)
                    filtro['company_id'] = dados['company_id']
                    filtro['lancamento_id'] = lancamento_id
                    cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                lancamento_id = lancamento_pool.copy(cr, uid, modelo_total_receber)

                dados = {
                    'company_id': company_empresa_id,
                    'partner_id': contrato_obj.imovel_id.project_id.company_id.partner_id.id,
                    'contrato_imovel_id': contrato_obj.id,
                    'parcela_comissao_id': comissao_empresa_obj.id,
                    'data_doccumento': comissao_empresa_obj.data_inicial,
                    'data_vencimento': parcela_obj.data_vencimento,
                    'valor_documento': parcela_obj.valor,
                    'tipo': 'R',
                    'historico': historico,
                    #'sugestao_bank_id': contrato_obj.imovel_res_partner_bank_id.id,
                    'tipo_conta': contrato_obj.imovel_project_id.modelo_comissao_total_receber_id.conta_id.tipo,
                }

                numero_documento = 'CRT-' + contrato_obj.numero + '-'
                numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                dados['numero_documento'] = numero_documento
                dados['numero_documento_original'] = numero_documento

                #
                # Imóvel de terceiros, quem paga a comissão é o proprietário do imóvel
                #
                if contrato_obj.imovel_propriedade in ('T', 'A', 'TA'):
                    dados['partner_id'] = contrato_obj.imovel_proprietario_id.id

                lancamento_pool.write(cr, uid, [lancamento_id], dados)
                filtro['company_id'] = dados['company_id']
                filtro['lancamento_id'] = lancamento_id
                cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                parcelas_receber[parcela_obj.data_vencimento] = lancamento_id

                i += 1

            for comissao_obj in contrato_obj.comissao_ids:
                modelo_id = None

                if comissao_obj.papel == 'E':
                    if contrato_obj.imovel_project_id.modelo_comissao_pagar_empresa_id:
                        modelo_obj = contrato_obj.imovel_project_id.modelo_comissao_pagar_empresa_id
                        modelo_id = contrato_obj.imovel_project_id.modelo_comissao_pagar_empresa_id.id

                elif comissao_obj.papel == 'G':
                    if contrato_obj.imovel_project_id.modelo_comissao_pagar_gerente_id:
                        modelo_obj = contrato_obj.imovel_project_id.modelo_comissao_pagar_gerente_id
                        modelo_id = contrato_obj.imovel_project_id.modelo_comissao_pagar_gerente_id.id

                elif comissao_obj.papel == 'A':
                    if contrato_obj.imovel_project_id.modelo_comissao_pagar_agenciador_id:
                        modelo_obj = contrato_obj.imovel_project_id.modelo_comissao_pagar_agenciador_id
                        modelo_id = contrato_obj.imovel_project_id.modelo_comissao_pagar_agenciador_id.id

                elif comissao_obj.papel == 'C':
                    if contrato_obj.imovel_project_id.modelo_comissao_pagar_corretor_id:
                        modelo_obj = contrato_obj.imovel_project_id.modelo_comissao_pagar_corretor_id
                        modelo_id = contrato_obj.imovel_project_id.modelo_comissao_pagar_corretor_id.id

                elif comissao_obj.papel == 'O':
                    if contrato_obj.imovel_project_id.modelo_comissao_pagar_outros_id:
                        modelo_obj = contrato_obj.imovel_project_id.modelo_comissao_pagar_outros_id
                        modelo_id = contrato_obj.imovel_project_id.modelo_comissao_pagar_outros_id.id

                if not modelo_id:
                    raise osv.except_osv(u'Inválido !', u'Não existe no projeto modelo financeiro de Comissao papel {a}, para corretor {b}'.format(a=comissao_obj.papel,b=contrato_obj.imovel_project_id.name))

                comissao_pool.gera_parcelas(cr, uid, [comissao_obj.id], valor_total=comissao_obj.valor_comissao, context=context)

                #
                # Não vamos gerar a comissão da empresa pra própria empresa
                #
                if comissao_obj.papel == 'E':
                    continue

                parcela_ids = parcela_pool.search(cr, uid, [('comissao_id', '=', comissao_obj.id)])

                i = 1
                for parcela_obj in parcela_pool.browse(cr, uid, parcela_ids):
                    lancamento_id = lancamento_pool.copy(cr, uid, modelo_id)

                    dados = {
                        'company_id': company_empresa_id,
                        'contrato_imovel_id': contrato_obj.id,
                        'parcela_comissao_id': comissao_obj.id,
                        'data_doccumento': comissao_obj.data_inicial,
                        'partner_id': comissao_obj.partner_id.id,
                        'data_vencimento': parcela_obj.data_vencimento,
                        'valor_documento': parcela_obj.valor,
                        'lancamento_comissao_receber_id': parcelas_receber[parcela_obj.data_vencimento],
                        'tipo': 'P',
                        'historico': historico,
                        #'sugestao_bank_id': contrato_obj.imovel_res_partner_bank_id.id,
                        'tipo_conta': modelo_obj.conta_id.tipo,
                    }

                    numero_documento = 'C' + comissao_obj.papel + '-' + contrato_obj.numero + '-'
                    numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                    dados['numero_documento'] = numero_documento
                    dados['numero_documento_original'] = numero_documento

                    lancamento_pool.write(cr, uid, [lancamento_id], dados)
                    filtro['company_id'] = dados['company_id']
                    filtro['lancamento_id'] = lancamento_id
                    cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                    i += 1

        return True

    def imprimir_contrato_comissao(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)

        rel = Report('FICHA DE CONTROLE PAGAMENTO COMISSÃO', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_contrato_pagamento_comissao.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid

        nome = 'Controle_Pgto_Comissao_' + rel_obj.numero + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.contrato'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'finan.contrato',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def imprimir_contrato_fechamento(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)

        rel = Report('Resumo Fechamento do Contrato de Imóvel', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_contrato_imovel_fechamento.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['UID'] = uid

        nome = 'Fechamento_Contrato_Imovel_' + rel_obj.numero + '.pdf'
        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.contrato'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome,
            'datas_fname': nome,
            'res_model': 'finan.contrato',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def reserva_imovel(self, cr, uid, ids, context={}):
        if not len(ids):
            return {}

        for contrato_obj in self.browse(cr, uid, ids):

            dados = {
                'imovel_id': contrato_obj.imovel_id.id,
                'contrato_id': contrato_obj.id,
            }

            imovel_obj = contrato_obj.imovel_id

            sql = """
                select
                    r.id
                from const_reserva_imovel r
                join const_imovel i on i.id = r.imovel_id
                where
                  i.id = """ + str(contrato_obj.imovel_id.id)

            cr.execute(sql)
            reservas = cr.fetchall()

            if len(reservas) == 0:
                dados['data_inicial'] = fields.datetime.now()
                imovel_obj.write({'situacao': 'R'})
            else:
                self.pool.get('const.imovel').verifica_reserva_imovel(cr, uid, [imovel_obj.id], context=context)

            self.pool.get('const.reserva.imovel').create(cr,uid, dados)



        return True

    def onchange_imovel_id(self, cr, uid, ids, imovel_id):
        if not imovel_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        imovel_obj = self.pool.get('const.imovel').browse(cr, uid, imovel_id)

        if imovel_obj.proprietario_id:
            valores['imovel_proprietario_id'] = imovel_obj.proprietario_id.id

        if imovel_obj.res_partner_bank_id:
            valores['imovel_res_partner_bank_id'] = imovel_obj.res_partner_bank_id.id

        if imovel_obj.project_id:
            valores['imovel_project_id'] = imovel_obj.project_id.id

        valores['imovel_valor_venda'] = imovel_obj.valor_venda
        valores['imovel_codigo'] = imovel_obj.codigo
        valores['imovel_situacao'] = imovel_obj.situacao
        valores['imovel_propriedade'] = imovel_obj.propriedade
        valores['imovel_area_terreno'] = imovel_obj.area_terreno
        valores['imovel_quadra'] = imovel_obj.quadra
        valores['imovel_lote'] = imovel_obj.lote

        if imovel_obj.conta_id:
            valores['imovel_conta_id'] = imovel_obj.conta_id.id

        if imovel_obj.centrocusto_id:
            valores['imovel_centrocusto_id'] = imovel_obj.centrocusto_id.id

        return res


finan_contrato()


class finan_contrato_comissao(osv.Model):
    _name = 'finan.contrato.comissao'
    _inherit = 'finan.contrato.comissao'

    _columns = {

    }

    _defaults = {

    }

    def gera_parcelas(self, cr, uid, ids, valor_total=D(0), context={}):
        parcela_pool = self.pool.get('finan.contrato.comisao.parcela')

        for comissao_obj in self.browse(cr, uid, ids, context=context):

            if not comissao_obj.contrato_id:
                continue

            if not comissao_obj.contrato_id.data_comissao:
                #raise osv.except_osv(u'Inválido !', u'Incluir Data da Comissão!')
                continue

            if not comissao_obj.contrato_id.vezes:
                #raise osv.except_osv(u'Inválido !', u'Incluir Nº de vezes!')
                continue

            for parcela_obj in comissao_obj.parcela_ids:
                parcela_obj.unlink()

            data_base = parse_datetime(comissao_obj.contrato_id.data_comissao or hoje())

            if valor_total and valor_total > 0:
                valor = D(valor_total or 0).quantize(D('0.01'))
            else:
                valor = D(comissao_obj.valor_comissao).quantize(D('0.01'))

            for i in range(comissao_obj.contrato_id.vezes):
                dados = {
                    'comissao_id': comissao_obj.id,
                    'parcela': i + 1,
                    'data_vencimento': str(data_base.date() + relativedelta(months=+i)),
                    'valor':  valor / comissao_obj.contrato_id.vezes,
                }

                parcela_pool.create(cr, uid, dados)

        return True

finan_contrato_comissao()
