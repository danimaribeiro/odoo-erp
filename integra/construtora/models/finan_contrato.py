# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields
import os
import base64
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report
from decimal import Decimal as D
from sped.models.fields import *
#from mail.mail_message import to_email
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes, idade_meses_sem_dia, agora, formata_data, data_por_extenso
from pybrasil.valor import formata_valor
from copy import copy
from collections import OrderedDict
from const_imovel import SITUACAO_IMOVEL, PROPRIEDADE

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


SITUACAO_CONTRATO_IMOVEL = (
    ('P', u'Pendente'),
    ('N', u'Análise'),
    ('A', u'Aprovado'),
    ('R', u'Rejeitado'),
)


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'
    _orde = ''

    _columns = {
        'crm_lead_id': fields.many2one('crm.lead', u'Prospecto'),
        'situacao_imovel': fields.selection(SITUACAO_CONTRATO_IMOVEL, u'Situação'),
        'cliente_ids': fields.one2many('finan.contrato.cliente', 'contrato_id', u'Clientes'),
        'project_id': fields.many2one('project.project', u'Projeto', ondelete='restrict'),
        'imovel_ids': fields.one2many('finan.contrato.imovel', 'contrato_id', u'Imóveis'),
        'comissao_ids': fields.one2many('finan.contrato.comissao', 'contrato_id', u'Comissões do contrato'),
        'condicao_ids': fields.one2many('finan.contrato.condicao', 'contrato_id', u'Condições de pagamento'),
        'condicao_original_ids': fields.one2many('finan.contrato.condicao', 'contrato_id', u'Condições de pagamento', domain=[('tipo', '=', 'O')]),
        'condicao_renegociacao_ids': fields.one2many('finan.contrato.condicao', 'contrato_id', u'Condições de pagamento', domain=[('tipo', '=', 'R')]),
        'parcela_ids': fields.one2many('finan.contrato.condicao.parcela', 'contrato_id', u'Parcelas'),
        'percentual_comissao': fields.float(u'Comissão'),

        'etapa_id': fields.many2one('finan.contrato.etapa', u'Etapa', ondelete='restrict'),
        'codigo': fields.related('etapa_id', 'codigo', type='char', string=u'Código', store=False, select=True),
        'filtro_etapa': fields.related('etapa_id', 'filtro_etapa', type='char', string=u'filtro', store=False, select=True),
        'proxima_etapa_id': fields.many2one('finan.contrato.etapa', u'Próxima Etapa'),
        'etapa_seguinte_ids': fields.related('etapa_id','etapa_seguinte_ids',  type='many2many', relation='finan.contrato.etapa', string=u'Proxima Etapa', store=False),
        'parcelas_manual': fields.boolean(u'Parcelas em modo manual?'),
        'checklist_ids': fields.one2many('checklist.contrato.item', 'contrato_id', u'Check-list Itens' ),

        'imovel_id': fields.many2one('const.imovel', u'Imóvel', ondelete='restrict'),
        'imovel_proprietario_id': fields.related('imovel_id','proprietario_id',  type='many2one', string=u'Proprietário', relation='res.partner', store=False),
        'imovel_res_partner_bank_id': fields.related('imovel_id','res_partner_bank_id',  type='many2one', string=u'Conta Bancária', relation='res.partner.bank', store=False),
        'imovel_project_id': fields.related('imovel_id','project_id',  type='many2one', string=u'Projeto', relation='project.project', store=False),
        'imovel_valor_venda': fields.related('imovel_id','valor_venda',  type='float', string=u'Valor', store=False),
        'imovel_codigo': fields.related('imovel_id','codigo',  type='char', string=u'Código', store=False),
        'imovel_situacao': fields.related('imovel_id','situacao',  type='selection', relation='const.imovel', selection=SITUACAO_IMOVEL, string=u'Situação comercial', store=False),
        'imovel_propriedade': fields.related('imovel_id','propriedade',  type='selection', relation='const.imovel', selection=PROPRIEDADE, string=u'Propriedade', store=False),
        'imovel_area_terreno': fields.related('imovel_id','area_terreno',  type='float', string=u'Área terreno (m²)', store=False),
        'imovel_area_total': fields.related('imovel_id','area_terreno',  type='float', string=u'Área total (m²)', store=False),
        'imovel_quadra': fields.related('imovel_id','quadra',  type='char', string=u'Quadra', store=False),
        'imovel_lote': fields.related('imovel_id','lote',  type='char', string=u'Lote', store=False),

        'data_distrato': fields.date(u'Data de distrato'),
        'motivo_baixa_id': fields.many2one('finan.motivobaixa', u'Motivo Baixa', select=True),

        'negociacao_ids': fields.one2many('mail.message', 'res_id', u'Negociações', readonly=True, domain=[('tipo_negociacao', '!=', False)]),

        'url_compartilhamento': fields.char(u'URL de compartilhamento', size=255),

        'valor_comissao': fields.float(u'Valor de comissão', digits=(18, 2)),
        'comissao_parcelas_diferente': fields.boolean(u'Diferença nas comissões'),
        'vezes': fields.integer(u'Vezes'),

        'pagamento_direto_proprietario': fields.boolean(u'O pagamento será direto ao proprietário?'),

        'lancamento_imovel_ids': fields.one2many('finan.lancamento', 'contrato_imovel_id', u'Lançamentos financeiros de comissão e administração', ondelete='cascade'),
    }

    _defaults = {
        'situacao_imovel': 'P',
        'percentual_comissao': 10,
        'etapa_id': 1,
        'vendedor_id': lambda self, cr, uid, ids, context={}: uid,
        'vezes': 0,
    }

    def get_url_compartilhamento(self, cr, uid, ids, context={}):
        share_pool = self.pool.get('share.wizard')
        contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, ids[0])
        action_pool = self.pool.get('ir.model.data')
        action_ids = action_pool.search(cr, uid, [('name', '=', 'finan_contrato_proposta_imovel_acao')])
        action_obj = action_pool.browse(cr, uid, action_ids[0])

        if contrato_obj.url_compartilhamento:
            return contrato_obj.url_compartilhamento

        dados = {
            'action_id': action_obj.res_id,
            'view_type': 'form',
            'domain': "[('id', '=', {id})]".format(id=ids[0]),
            'user_type': 'embedded',
            'access_mode': 'readonly',
            'name': u'Proposta nº ',
        }

        share_id = share_pool.create(cr, 1, dados)
        share_obj = share_pool.browse(cr, 1, share_id)
        share_obj.go_step_2(context=context)

        print('share_obj.embed_url')
        print(share_obj.embed_url)
        contrato_obj.write({'url_compartilhamento': share_obj.embed_url})

        return share_obj.embed_url

    def ajusta_imovel_ids(self, cr, uid, dados):
        if 'imovel_id' in dados and dados['imovel_id']:
            dados['imovel_ids'] = [[0, False, {'imovel_id': dados['imovel_id']}]]

        if 'imovel_ids' in dados:
            imovel_id = dados['imovel_ids'][0][2]['imovel_id']
            dados_projeto = self.pool.get('const.imovel').read(cr, uid, [imovel_id], ['project_id'])

            if dados_projeto[0]['project_id']:
                project_id = dados_projeto[0]['project_id'][0]
                dados_empresa = self.pool.get('project.project').read(cr, uid, [project_id], ['company_id','conta_id'])

                if dados_empresa[0]['company_id']:
                    dados['company_id'] = dados_empresa[0]['company_id'][0]

                if dados_empresa[0]['conta_id']:
                    dados['conta_id'] = dados_empresa[0]['conta_id'][0]

            if 'res_partner_bank_id' not in dados:
                dados_banco = self.pool.get('const.imovel').read(cr, uid, [imovel_id], ['res_partner_bank_id'])

                if dados_banco[0]['res_partner_bank_id']:
                    dados['res_partner_bank_id'] = dados_banco[0]['res_partner_bank_id'][0]

            #
            # Por fim, exclui os outros imóveis e deixa somente o selecionado
            #
            if 'imovel_id' in dados and dados['imovel_id']:
                dados['imovel_ids'] = [[5, False, {}], [0, False, {'imovel_id': dados['imovel_id']}]]

    def create(self, cr, uid, dados, context={}):
        self.pool.get('finan.contrato').ajusta_imovel_ids(cr, uid, dados)

        res = super(finan_contrato, self).create(cr, uid, dados, context=context)

        self.copia_checklist(cr, uid, [res], context)
        self.copia_comissao(cr, uid, [res], context)
        self.verifica_valor_prosposta(cr, uid, [res], context)
        self.verifica_valor_comissao(cr, uid, [res], context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        self.pool.get('finan.contrato').ajusta_imovel_ids(cr, uid, dados)

        res = super(finan_contrato, self).write(cr, uid, ids, dados, context=context)

        self.copia_checklist(cr, uid, ids, context)
        self.copia_comissao(cr, uid, ids, context)
        self.verifica_valor_prosposta(cr, uid, ids, context)
        self.verifica_valor_comissao(cr, uid, ids, context)
        self.verifica_exclusao_condicoes(cr, uid, ids, context)

        return res

    def verifica_exclusao_condicoes(self, cr, uid, ids, context={}):
        #
        # Se removeram todas as condições de pagamento, remover também as comissões e outros
        # lançamentos
        #
        for contrato_obj in self.browse(cr, uid, ids):
            if len(contrato_obj.condicao_original_ids) == 0 and len(contrato_obj.condicao_renegociacao_ids) == 0:
                for comissao_obj in contrato_obj.comissao_ids:
                    comissao_obj.unlink()

    def copia_checklist(self, cr, uid, ids, vals={}, context={}):
        item_pool = self.pool.get('checklist.contrato.item')

        for contrato_obj in self.browse(cr, uid, ids):
            if len(contrato_obj.checklist_ids) == 0:
                if contrato_obj.imovel_ids:
                    imovel_obj = contrato_obj.imovel_ids[0]

                    if imovel_obj.project_id:
                        project_obj = imovel_obj.project_id

                        if project_obj.checklist_id:
                            checklist_obj = project_obj.checklist_id

                            for item_obj in checklist_obj.item_ids:
                                if not item_obj.contrato_id:
                                    item_pool.copy(cr, uid, item_obj.id, {'contrato_id': contrato_obj.id, 'clecklist_id': False})

        return

    def copia_comissao(self, cr, uid, ids, vals={}, context={}):
        item_pool = self.pool.get('finan.contrato.comissao')

        for contrato_obj in self.browse(cr, uid, ids):
            if len(contrato_obj.comissao_ids) == 0:
                if contrato_obj.imovel_ids:
                    imovel_obj = contrato_obj.imovel_ids[0]

                    if imovel_obj.project_id:
                        project_obj = imovel_obj.project_id

                        if project_obj.comissao_id:
                            comissao_obj = project_obj.comissao_id

                        if project_obj.comissao_id:
                            for item_obj in comissao_obj.item_ids:
                                if not item_obj.contrato_id:
                                    item_id = item_pool.copy(cr, uid, item_obj.id, {'contrato_id': contrato_obj.id, 'finan_comissao_id': False})
                                    novo_item_obj = item_pool.browse(cr, uid, item_id)

                                    if  novo_item_obj.partner_id:
                                        continue

                                    if novo_item_obj.papel == 'C':
                                        if contrato_obj.vendedor_id and contrato_obj.vendedor_id.partner_corretor_id:
                                            novo_item_obj.write({'partner_id': contrato_obj.vendedor_id.partner_corretor_id.id})

                                    elif novo_item_obj.papel == 'E':
                                        novo_item_obj.write({'partner_id': contrato_obj.company_id.partner_id.id})

                                    elif novo_item_obj.papel == 'A':
                                        if len(contrato_obj.imovel_id.agenciador_ids):
                                            valor = D(novo_item_obj.porcentagem or 0)
                                            valor /= len(contrato_obj.imovel_id.agenciador_ids)

                                            for agenciador_obj in contrato_obj.imovel_id.agenciador_ids:
                                                item_agenciador_id = item_pool.copy(cr, uid, novo_item_obj.id)
                                                item_agenciador_obj = item_pool.browse(cr, uid, item_agenciador_id)
                                                item_agenciador_obj.write({'partner_id': agenciador_obj.id, 'porcentagem': valor})

                                            novo_item_obj.unlink()

        return


    def avanca_etapa(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        proposta_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'construtora', 'finan_contrato_proposta_imovel_form')[1]
        financeiro_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'construtora', 'finan_contrato_analise_financeiro_imovel_form')[1]
        juridico_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'construtora', 'finan_contrato_analise_juridico_imovel_form')[1]
        contrato_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'construtora', 'finan_contrato_receber_imovel_form')[1]

        res = {
            'type': 'ir.actions.act_window',
            'name': 'Proposta',
            'res_model': 'finan.contrato',
            'res_id': False,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': proposta_form_id,
            #'target': 'new',  # isto faz abrir numa janela no meio da tela
            'target': 'inline',  # Abre na mesma janela, sem ser no meio da tela
            'context': {'form_view_ref': 'construtora.finan_contrato_proposta_imovel_form', 'tree_view_ref': 'construtora.finan_contrato_proposta_imovel_tree', 'search_view_ref': 'construtora.finan_contrato_proposta_imovel_search'}
        }


        for contrato_obj in self.browse(cr, uid, ids):
            if not contrato_obj.proxima_etapa_id:
                raise osv.except_osv(u'Inválido !', u'Selecione a próxima etapa')

            dados = {
                'etapa_id': contrato_obj.proxima_etapa_id.id,
                'proxima_etapa_id': False,
                #'data_proxima_etapa': fields.datetime.now(),
                #'data_ultima_etapa': contrato_obj.data_proxima_etapa or contrato_obj.create_date,
                #'etapa_historico_ids': [[0, False, {'etapa_id': contrato_obj.proxima_etapa_id.id, 'data_proxima_etapa': fields.datetime.now(), 'data_ultima_etapa': contrato_obj.data_proxima_etapa or contrato_obj.create_date}]]
            }

            contrato_obj.write(dados)

            if contrato_obj.proxima_etapa_id.tipo == 'J':
                res['name'] = u'Análise Jurídico'
                res['view_id'] = juridico_form_id
                res['context'] = {'form_view_ref': 'construtora.finan_contrato_analise_juridico_imovel_form', 'tree_view_ref': 'construtora.finan_contrato_analise_juridico_imovel_tree', 'search_view_ref': 'construtora.finan_contrato_analise_juridico_imovel_search'}

            elif contrato_obj.proxima_etapa_id.tipo == 'A':
                res['name'] = u'Análise Financeiro'
                res['view_id'] = financeiro_form_id
                res['context'] = {'form_view_ref': 'construtora.finan_contrato_analise_financeiro_imovel_form', 'tree_view_ref': 'construtora.finan_contrato_analise_financeiro_imovel_tree', 'search_view_ref': 'construtora.finan_contrato_analise_financeiro_imovel_search'}
            #
            # Aprovando a proposta
            #
            elif contrato_obj.proxima_etapa_id.tipo == 'R':
                contrato_obj.imovel_id.write({'situacao': 'A'})
                res['name'] = u'Contrato de imóvel'
                res['view_id'] = contrato_form_id
                res['context'] = {'form_view_ref': 'construtora.finan_contrato_receber_imovel_form', 'tree_view_ref': 'construtora.finan_contrato_receber_imovel_tree', 'search_view_ref': 'construtora.finan_contrato_receber_imovel_search'}

            res['res_id'] = contrato_obj.id

        return res

    def verifica_valor_prosposta(self, cr, uid, ids, vals={}, context={}):
        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.natureza != 'RI':
                continue

            if contrato_obj.valor and len(contrato_obj.condicao_ids) > 0:
                total_contrato = D(contrato_obj.valor).quantize(D('0.01'))
                total_condicao = D(0)

                for condicao_obj in  contrato_obj.condicao_ids:
                    total_condicao += D(condicao_obj.valor_principal).quantize(D('0.01'))

                if total_contrato != total_condicao:
                    raise osv.except_osv(u'Atenção!', u'Total das condições R$ ' + formata_valor(total_condicao) + u', diferente do Valor proposto R$ ' + formata_valor(total_contrato))

    def verifica_valor_comissao(self, cr, uid, ids, vals={}, context={}):
        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.natureza != 'RI':
                continue

            if not contrato_obj.valor_comissao:
                continue

            comissao_ok = True
            comissao = D(contrato_obj.valor_comissao or 0).quantize(D('0.01'))

            valor = D(0)
            for comissao_obj in contrato_obj.comissao_ids:
                if not comissao_ok:
                    continue

                com = D(comissao_obj.valor_comissao or 0).quantize(D('0.01'))

                parc = D(0)
                for parcela_obj in comissao_obj.parcela_ids:
                    parc += D(parcela_obj.valor or 0)

                parc = parc.quantize(D('0.01'))
                valor += parc

                if comissao_ok:
                    comissao_ok = parc == com

            valor = valor.quantize(D('0.01'))

            if comissao_ok:
                comissao_ok = valor == comissao

            print('valor, comissao, comissao_ok')
            print(valor, comissao, valor == comissao)

            if comissao_ok:
                cr.execute('update finan_contrato set comissao_parcelas_diferente = False where id = {id};'.format(id=contrato_obj.id))
            else:
                cr.execute('update finan_contrato set comissao_parcelas_diferente = True where id = {id};'.format(id=contrato_obj.id))
                raise osv.except_osv(u'Atenção!', u'O total das parcelas das comissões é de R$ ' + formata_valor(valor) + u', e é diferente do valor de comissões informado de R$ ' + formata_valor(comissao))

    def atualiza_valor(self, cr, uid, ids, vals={}, context={}):
        #pass
        for contrato_obj in self.browse(cr, uid, ids):
            for condicao_obj in contrato_obj.condicao_ids:
                condicao_obj.gera_parcelas()

        #for contrato_obj in self.browse(cr, uid, ids):
            #for parcela_obj in contrato_obj.parcela_ids:
                #parcela_obj.atualiza_valor()


            #if contrato_obj.natureza == 'RI':
                #cr.execute("""update finan_contrato fc set valor =
                            #(select coalesce(sum(i.valor_venda),0)
                            #from finan_contrato_imovel fi
                            #join const_imovel i on i.id = fi.imovel_id
                            #where fi.contrato_id = {id})
                            #where fc.id = {id}""".format(id=contrato_obj.id))

    def gera_provisao(self, cr, uid, ids, context={}):
        condicao_pool = self.pool.get('finan.contrato.condicao')
        lancamento_pool = self.pool.get('finan.lancamento')

        SQL_ATUALIZA_RATEIO = """
        update finan_lancamento_rateio flr set
            company_id = coalesce(flr.company_id, {company_id}),
            contrato_id = coalesce(flr.contrato_id, {contrato_id}),
            project_id = coalesce(flr.project_id, {project_id}),
            imovel_id = coalesce(flr.imovel_id, {imovel_id})
        where
            flr.lancamento_id = {lancamento_id};
        """

        for contrato_obj in self.browse(cr, uid, ids, context=context):
            #self.atualiza_valor(cr, uid, ids, context={})
            if contrato_obj.natureza != 'RI':
                super(finan_contrato, self).gera_provisao(cr, uid, [contrato_obj.id], context=context)
                #self.pool.get('finan.contrato').gera_provisao(cr, uid, [contrato_obj.id], context=context)
                continue

            if contrato_obj.situacao_imovel != 'A':
                continue

            if contrato_obj.imovel_propriedade in ('T', 'A', 'TA') and contrato_obj.pagamento_direto_proprietario:
                continue

            filtro = {
                'company_id':  contrato_obj.imovel_id.project_id.company_id.id,
                'contrato_id': contrato_obj.id,
                'project_id': contrato_obj.imovel_id.project_id.id,
                'imovel_id': contrato_obj.imovel_id.id,
                'lancamento_id': False,
            }

            #
            # A prioridade do projeto no rateio é do centro de custo vinculado ao imóvel, e não
            # o projeto do próprio imóvel
            #
            if contrato_obj.imovel_id and contrato_obj.imovel_id.centrocusto_id and contrato_obj.imovel_id.centrocusto_id.project_id:
                filtro['project_id'] = contrato_obj.imovel_id.centrocusto_id.project_id.id

            historico = contrato_obj.imovel_id.descricao_lista or ''
            historico += '\n'
            historico += contrato_obj.partner_id.name or ''

            ##
            ## Temporariamente liberando regerar lançamento mesmo depois do imóvel vendido
            ##
            ##for imovel_obj in contrato_obj.imovel_ids:
                ##if imovel_obj.situacao == 'C':
                    ##raise osv.except_osv(u'Inválido !', u'Imóvel código {codigo} está cancelado!'.format(codigo=imovel_obj.codigo))
                ##elif imovel_obj.situacao == 'V':
                    ##raise osv.except_osv(u'Inválido !', u'Imóvel código {codigo} já foi vendido!'.format(codigo=imovel_obj.codigo))
                ##elif imovel_obj.situacao == 'A':
                    ##raise osv.except_osv(u'Inválido !', u'Imóvel código {codigo} está alugado!'.format(codigo=imovel_obj.codigo))
                ##elif imovel_obj.situacao == 'ND':
                    ##raise osv.except_osv(u'Inválido !', u'Imóvel código {codigo} não está disponível!'.format(codigo=imovel_obj.codigo))
                ##elif imovel_obj.situacao == 'NL':
                    ##raise osv.except_osv(u'Inválido !', u'Imóvel código {codigo} não está liberado!'.format(codigo=imovel_obj.codigo))

            #
            # Apaga as parcelas anteriores, exceto aquelas que são comissão
            #
            for lanc_obj in contrato_obj.lancamento_imovel_ids:
                if not lanc_obj.lancamento_recebimento_imovel_id:
                    continue

                lanc_obj.unlink()

            for lanc_obj in contrato_obj.lancamento_ids:
                lanc_obj.unlink()

            novos_dados = {}
            numero_condicao = {}
            i = 1
            for parcela_obj in contrato_obj.parcela_ids:
                if parcela_obj.condicao_id:
                    condicao_id = parcela_obj.condicao_id.id
                else:
                    condicao_id = None

                if condicao_id not in novos_dados:
                    novos_dados[condicao_id] = {}
                    numero_condicao[condicao_id] = i
                    i += 1

                if parcela_obj.data_vencimento not in novos_dados[condicao_id]:
                    novos_dados[condicao_id][parcela_obj.data_vencimento] = []

                dados = {
                    #'company_id': contrato_obj.company_id.id,
                    'company_id': contrato_obj.imovel_id.project_id.company_id.id,
                    'tipo': contrato_obj.natureza[0],  # Primeira letra do tipo P/R
                    'contrato_id': contrato_obj.id,
                    'provisionado': contrato_obj.provisionado,
                    'partner_id': contrato_obj.partner_id.id,
                    'historico': historico,

                    #
                    # Dados necessários para controle de documentos a receber ou a pagar
                    #
                    #'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                    #'numero_documento': fields.char(u'Número do documento', size=30),
                    'data_documento': parcela_obj.data_base,
                    'valor_documento': parcela_obj.valor,
                    'valor_original_contrato': parcela_obj.valor,
                    'data_vencimento': parcela_obj.data_vencimento,
                    'data_vencimento_original': parcela_obj.data_vencimento,
                    'valor_documento_moeda': parcela_obj.valor,
                    'parcela_obj': parcela_obj,
                    'finan_contrato_condicao_parcela_id': parcela_obj.id,
                    'finan_contrato_condicao_id': condicao_id,
                }

                #
                # Campos obrigatórios
                #
                if parcela_obj.conta_id:
                    dados['conta_id'] = parcela_obj.conta_id.id
                else:
                    dados['conta_id'] = contrato_obj.conta_id.id

                if parcela_obj.documento_id:
                    dados['documento_id'] = parcela_obj.documento_id.id
                else:
                    dados['documento_id'] = contrato_obj.documento_id.id

                if parcela_obj.formapagamento_id:
                    dados['formapagamento_id'] = parcela_obj.formapagamento_id.id
                else:
                    dados['formapagamento_id'] = contrato_obj.formapagamento_id.id

                #
                # Campos opcionais
                #
                if parcela_obj.centrocusto_id:
                    dados['centrocusto_id'] = parcela_obj.centrocusto_id.id
                elif contrato_obj.centrocusto_id:
                    dados['centrocusto_id'] = contrato_obj.centrocusto_id.id

                if parcela_obj.res_partner_address_id:
                    dados['res_partner_address_id'] = parcela_obj.res_partner_address_id.id
                elif contrato_obj.res_partner_address_id:
                    dados['res_partner_address_id'] = contrato_obj.res_partner_address_id.id

                if parcela_obj.res_partner_bank_id:
                    dados['res_partner_bank_id'] = parcela_obj.res_partner_bank_id.id
                    dados['sugestao_bank_id'] = parcela_obj.res_partner_bank_id.id
                elif contrato_obj.res_partner_bank_id:
                    dados['res_partner_bank_id'] = contrato_obj.res_partner_bank_id.id
                    dados['sugestao_bank_id'] = contrato_obj.res_partner_bank_id.id

                #if parcela_obj.currency_id:
                    #dados['currency_id'] = parcela_obj.currency_id.id
                #elif contrato_obj.currency_id:
                    #dados['currency_id'] = contrato_obj.currency_id.id

                if parcela_obj.carteira_id:
                    dados['carteira_id'] = parcela_obj.carteira_id.id
                elif contrato_obj.carteira_id:
                    dados['carteira_id'] = contrato_obj.carteira_id.id

                if len(parcela_obj.atualizacao_ids):
                    #
                    # Seguindo a regra louca da Exata, seja o que Deus quiser....
                    #
                    #dados['valor_documento'] = parcela_obj.atualizacao_ids[-1].valor
                    #dados['valor_documento_moeda'] = parcela_obj.atualizacao_ids[-1].valor
                    valor = D(parcela_obj.valor or 0)
                    valor += D(parcela_obj.atualizacao_ids[-1].valor_multa_carteira or 0)

                    for atualizacao_obj in parcela_obj.atualizacao_ids:
                        valor += D(atualizacao_obj.valor_juros_carteira or 0)
                        valor += D(atualizacao_obj.correcao or 0)
                        valor += D(atualizacao_obj.valor_juros_sacoc or 0)
                        valor += D(atualizacao_obj.valor_seguro or 0)

                    dados['valor_documento'] = valor
                    dados['valor_documento_moeda'] = valor

                novos_dados[condicao_id][parcela_obj.data_vencimento].append(dados)

            #
            # Agora que temos todas as parcelas, vamos atribuir a numeração correta
            #
            for condicao_id in novos_dados:
                novos_dados[condicao_id] = OrderedDict(sorted(novos_dados[condicao_id].items()))

                #
                # Acumula o total de parcelas por condição de pagamento
                #
                total_parcelas = 0
                for data_vencimento in novos_dados[condicao_id]:
                    total_parcelas += len(novos_dados[condicao_id][data_vencimento])
                i = 1

                if condicao_id:
                    condicao_obj = condicao_pool.browse(cr, uid, condicao_id)
                    if condicao_obj.ajusta_quantidade_parcelas:
                        i = condicao_obj.ajusta_quantidade_parcelas - total_parcelas + 1
                        total_parcelas = condicao_obj.ajusta_quantidade_parcelas

                for data_vencimento in novos_dados[condicao_id]:
                    for dados in novos_dados[condicao_id][data_vencimento]:
                        numero_documento = contrato_obj.numero + '-'
                        numero_documento += str(numero_condicao[condicao_id]).zfill(2) + '-'
                        numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                        dados['numero_documento'] = numero_documento
                        dados['numero_documento_original'] = numero_documento

                        valor_original = D(dados['parcela_obj'].valor_original or 0).quantize(D('0.01'))
                        historico_parcela = historico + '\n'
                        historico_parcela += 'Valor original R$ ' + formata_valor(valor_original)

                        valor_capital = D(dados['parcela_obj'].valor_capital or 0).quantize(D('0.01'))
                        historico_parcela = historico + '\n'
                        historico_parcela += 'Capital R$ ' + formata_valor(valor_capital)


                        valor_capital_juros = D(dados['parcela_obj'].valor_capital_juros or 0).quantize(D('0.01'))
                        valor_capital_juros -= valor_capital

                        if valor_capital_juros > 0:
                            historico_parcela = historico + '\n'
                            historico_parcela += 'Juros R$ ' + formata_valor(valor_capital_juros)

                        correcao = D(dados['parcela_obj'].valor_capital_juros_correcao or 0).quantize(D('0.01'))
                        correcao -= valor_original

                        if valor_capital_juros > 0 and correcao > 0:
                            historico_parcela += '\n'
                            historico_parcela += u'Correção R$ ' + formata_valor(correcao)

                        dados['historico'] = historico_parcela

                        lancamento_id = lancamento_pool.create(cr, uid, dados)
                        parcela_obj.write({'lancamento_id': lancamento_id})

                        if 'centrocusto_id' in dados and dados['centrocusto_id']:
                            lancamento_obj = self.pool.get('finan.lancamento').browse(cr, uid, lancamento_id)

                            contexto_rateio = {
                                'contrato_id': contrato_obj.id,
                                'imovel_id': contrato_obj.imovel_id.id,
                                'project_id': contrato_obj.imovel_id.project_id.id,
                            }

                            #
                            # A prioridade do projeto no rateio é do centro de custo vinculado ao imóvel, e não
                            # o projeto do próprio imóvel
                            #
                            if contrato_obj.imovel_id.centrocusto_id and contrato_obj.imovel_id.centrocusto_id.project_id:
                                contexto_rateio['project_id'] = contrato_obj.imovel_id.centrocusto_id.project_id.id

                            if contrato_obj.hr_department_id:
                                contexto_rateio['hr_department_id'] = contrato_obj.hr_department_id.id

                            rateio = lancamento_obj.onchange_centrocusto_id(dados['centrocusto_id'], dados['valor_documento'], 0, dados['company_id'], dados['conta_id'], dados['partner_id'], dados['data_vencimento'], dados['data_documento'], context=contexto_rateio)
                            if 'value' in rateio:
                                rateio_ids = [[5, False, False]]
                                for rat in rateio['value']['rateio_ids']:
                                    rateio_ids.append([0, False, rat])

                                lancamento_obj.write({'rateio_ids': rateio_ids})

                        filtro['lancamento_id'] = lancamento_id
                        cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))
                        lancamento_pool._ajusta_situacao_juros(cr, uid, [lancamento_id], context=context)
                        cr.commit()

                        #
                        # Segundo o que o Marcelo desdefiniu e redefiniu no dia 22/08/2016, não é mais nada disso...
                        #
                        ##
                        ## Segundo o Marcelo definiu no dia 27/07/2016, o valor devido da última parcela reajustada
                        ## pelo currency_id deve ser replicado para todas as parcelas em aberto que estejam vencidas
                        ##
                        #if dados['parcela_obj'].indice:
                            #vencido_ids = lancamento_pool.search(cr, uid, [('contrato_id', '=', contrato_obj.id), ('situacao', '=', 'Vencido')])
                            #for vencido_obj in lancamento_pool.browse(cr, uid, vencido_ids):
                                #vencido_obj.write({'valor_documento': dados['valor_documento']})
                                #filtro['lancamento_id'] = vencido_obj.id
                                #cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))
                                #lancamento_pool._ajusta_situacao_juros(cr, uid, [vencido_obj.id], context=context)
                                #cr.commit()

                        if contrato_obj.imovel_id.project_id.modelo_administracao_venda_pagar_id:
                            pagamento_id = lancamento_pool.copy(cr, uid, contrato_obj.imovel_id.project_id.modelo_administracao_venda_pagar_id.id)

                            dados_pagamento = {
                                'tipo': 'P',
                                'company_id': dados['company_id'],
                                'contrato_imovel_id': contrato_obj.id,
                                'data_documento': dados['data_documento'],
                                'partner_id': contrato_obj.imovel_proprietario_id.id,
                                'data_vencimento': dados['data_vencimento'],
                                'valor_documento': dados['valor_documento'],
                                'lancamento_recebimento_imovel_id': lancamento_id,
                                'historico': historico,
                            }
                            numero_documento = 'AV-' + contrato_obj.numero + '-'
                            numero_documento += str(numero_condicao[condicao_id]).zfill(2) + '-'
                            numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                            dados_pagamento['numero_documento'] = numero_documento
                            dados_pagamento['numero_documento_original'] = numero_documento

                            lancamento_pool.write(cr, uid, [pagamento_id], dados_pagamento)

                            rateio = lancamento_pool.onchange_centrocusto_id(cr, uid, [pagamento_id], dados_pagamento['centrocusto_id'], dados_pagamento['valor_documento'], 0, dados_pagamento['company_id'], dados_pagamento['conta_id'], dados_pagamento['partner_id'], dados_pagamento['data_vencimento'], dados_pagamento['data_documento'], context=contexto_rateio)
                            if 'value' in rateio:
                                rateio_ids = [[5, False, False]]
                                for rat in rateio['value']['rateio_ids']:
                                    rateio_ids.append([0, False, rat])

                                lancamento_pool.write(cr, uid, [pagamento_id], {'rateio_ids': rateio_ids})

                            filtro['lancamento_id'] = pagamento_id
                            cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                        #
                        # Imóveis de 3º, se o pagamento não for para o proprietário direto,
                        # gera o contas a pagar para o proprietário
                        #
                        if contrato_obj.imovel_id.propriedade in ('T', 'TA') and (not contrato_obj.pagamento_direto_proprietario):
                            if not contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id:
                                raise osv.except_osv(u'Inválido !', u'Imóvel de Terceiro!!! Inserir um Modelo de Pagamento de Terceiro no Projeto')

                            pagamento_id = lancamento_pool.copy(cr, uid, contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.id)

                            dados_pagamento = {
                                'tipo': 'P',
                                'company_id': contrato_obj.imovel_id.company_id.id,
                                'contrato_imovel_id': contrato_obj.id,
                                'data_documento': dados['data_documento'],
                                'partner_id': contrato_obj.imovel_proprietario_id.id,
                                'data_vencimento': dados['data_vencimento'],
                                'valor_documento': dados['valor_documento'],
                                'lancamento_recebimento_imovel_id': lancamento_id,
                                'historico': historico,
                                'sugestao_bank_id': dados['sugestao_bank_id'],
                                'centrocusto_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.centrocusto_id.id,
                                'conta_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.conta_id.id,
                            }
                            numero_documento = u'3P-' + contrato_obj.numero + '-'
                            numero_documento += str(numero_condicao[condicao_id]).zfill(2) + '-'
                            numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                            dados_pagamento['numero_documento'] = numero_documento
                            dados_pagamento['numero_documento_original'] = numero_documento
                            lancamento_pool.write(cr, uid, [pagamento_id], dados_pagamento)

                            rateio = lancamento_pool.onchange_centrocusto_id(cr, uid, [pagamento_id], dados_pagamento['centrocusto_id'], dados_pagamento['valor_documento'], 0, dados_pagamento['company_id'], dados_pagamento['conta_id'], dados_pagamento['partner_id'], dados_pagamento['data_vencimento'], dados_pagamento['data_documento'], context=contexto_rateio)
                            if 'value' in rateio:
                                rateio_ids = [[5, False, False]]
                                for rat in rateio['value']['rateio_ids']:
                                    rateio_ids.append([0, False, rat])

                                lancamento_pool.write(cr, uid, [pagamento_id], {'rateio_ids': rateio_ids})

                            filtro['lancamento_id'] = pagamento_id
                            cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                        #
                        # Imóveis de 3º associado, faz o tratamentos dos recebimentos e pagamentos
                        # de acordo
                        #
                        elif contrato_obj.imovel_id.propriedade == 'A':
                            if not (contrato_obj.imovel_id.project_id.modelo_terceiro_associado_receber_id and contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id):
                                raise osv.except_osv(u'Inválido !', u'Imóvel de Terceiro Associado!!! Inserir um Modelo de Recebimento e Pagamento de Terceiro no Projeto')

                            proprietario_company = self.pool.get('res.company').search(cr, uid, [('partner_id','=', contrato_obj.imovel_proprietario_id.id)])

                            if len(proprietario_company) == 0:
                                raise osv.except_osv(u'Inválido !', u'Proprietario do Imovel Não é uma Empresa Cadastrada no Sistema"')

                            proprietario_company = proprietario_company[0]

                            recebimento_id = lancamento_pool.copy(cr, uid, contrato_obj.imovel_id.project_id.modelo_terceiro_associado_receber_id.id)

                            dados_recebimento = {
                                'tipo': 'R',
                                'company_id': proprietario_company,
                                'contrato_imovel_id': contrato_obj.id,
                                'data_documento': dados['data_documento'],
                                'partner_id': contrato_obj.imovel_id.company_id.partner_id.id,
                                'data_vencimento': dados['data_vencimento'],
                                'valor_documento': dados['valor_documento'],
                                'lancamento_recebimento_imovel_id': lancamento_id,
                                'historico': historico,
                                'centrocusto_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_receber_id.centrocusto_id.id,
                                'conta_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_receber_id.conta_id.id,
                            }
                            numero_documento = '3AR-' + contrato_obj.numero + '-'
                            numero_documento += str(numero_condicao[condicao_id]).zfill(2) + '-'
                            numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                            dados_recebimento['numero_documento'] = numero_documento
                            dados_recebimento['numero_documento_original'] = numero_documento

                            if contrato_obj.imovel_id.res_partner_bank_id:
                                dados_recebimento['sugestao_bank_id'] = contrato_obj.imovel_id.res_partner_bank_id.id

                            lancamento_pool.write(cr, uid, [recebimento_id], dados_recebimento)

                            rateio = lancamento_pool.onchange_centrocusto_id(cr, uid, [recebimento_id], dados_recebimento['centrocusto_id'], dados_recebimento['valor_documento'], 0, dados_recebimento['company_id'], dados_recebimento['conta_id'], dados_recebimento['partner_id'], dados_recebimento['data_vencimento'], dados_recebimento['data_documento'], context=contexto_rateio)
                            if 'value' in rateio:
                                rateio_ids = [[5, False, False]]
                                for rat in rateio['value']['rateio_ids']:
                                    rateio_ids.append([0, False, rat])

                                lancamento_pool.write(cr, uid, [recebimento_id], {'rateio_ids': rateio_ids})

                            filtro['lancamento_id'] = recebimento_id
                            cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                            pagamento_id = lancamento_pool.copy(cr, uid, contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.id)

                            dados_pagamento = {
                                'tipo': 'P',
                                'company_id': contrato_obj.imovel_id.company_id.id,
                                'contrato_imovel_id': contrato_obj.id,
                                'data_documento': dados['data_documento'],
                                'partner_id': contrato_obj.imovel_proprietario_id.id,
                                'data_vencimento': dados['data_vencimento'],
                                'valor_documento': dados['valor_documento'],
                                'lancamento_recebimento_imovel_id': lancamento_id,
                                'historico': historico,
                                'sugestao_bank_id': dados['sugestao_bank_id'],
                                'centrocusto_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.centrocusto_id.id,
                                'conta_id': contrato_obj.imovel_id.project_id.modelo_terceiro_associado_pagar_id.conta_id.id,
                            }
                            numero_documento = '3AP-' + contrato_obj.numero + '-'
                            numero_documento += str(numero_condicao[condicao_id]).zfill(2) + '-'
                            numero_documento += str(i).zfill(3) + '/' + str(total_parcelas).zfill(3)
                            dados_pagamento['numero_documento'] = numero_documento
                            dados_pagamento['numero_documento_original'] = numero_documento
                            lancamento_pool.write(cr, uid, [pagamento_id], dados_pagamento)

                            rateio = lancamento_pool.onchange_centrocusto_id(cr, uid, [pagamento_id], dados_pagamento['centrocusto_id'], dados_pagamento['valor_documento'], 0, dados_pagamento['company_id'], dados_pagamento['conta_id'], dados_pagamento['partner_id'], dados_pagamento['data_vencimento'], dados_pagamento['data_documento'], context=contexto_rateio)
                            if 'value' in rateio:
                                rateio_ids = [[5, False, False]]
                                for rat in rateio['value']['rateio_ids']:
                                    rateio_ids.append([0, False, rat])

                                lancamento_pool.write(cr, uid, [pagamento_id], {'rateio_ids': rateio_ids})

                            filtro['lancamento_id'] = pagamento_id
                            cr.execute(SQL_ATUALIZA_RATEIO.format(**filtro))

                        i += 1
            #
            # Define a situação dos imóveis como "Vendido"
            #
            for imovel_obj in contrato_obj.imovel_ids:
                imovel_obj.write({'situacao': 'V'})

    def imprime_nota_promissoria(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Nota Promissória', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'nota_promissoria.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'


        nome = 'NP_' + rel_obj.numero + '.pdf'
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

    def imprime_proposta(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)
        rel = Report('Proposta de Compra', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_proposta_compra.jrxml')
        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'


        nome = 'PC_' + rel_obj.numero + '.pdf'
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

    def imprimir_checklist(self, cr, uid, ids, context={}):
        if not ids:
            return False
        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel_obj = self.browse(cr, uid, id)

        sql = """
        select
            fc.id,
            fc.numero as numero,
            rp.name as cliente,
            cci.ordem as ordem,
            cci.atividade as descricao,
            cci.data_conclusao as data_conclusao,
            cci.cargo as cargo,
            ru.name as usuario,
            cci.obs

            from checklist_contrato_item cci
            join finan_contrato fc on fc.id = cci.contrato_id
            join res_partner rp on rp.id = fc.partner_id
            left join res_users ru on ru.id = cci.user_id

            where
            fc.id =  """ + str(rel_obj.id)

        rel = Report('Relatório de Checklist Contrato', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_contrato_relatorio_checklist.jrxml')
        rel.parametros['SQL'] = sql
        rel.parametros['UID'] = uid

        nome = 'CHECKLIST_' + rel_obj.numero + '.pdf'
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

    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        modelo_pool = self.pool.get('lo.modelo')

        for contrato_obj in self.browse(cr, uid, ids):
            modelos_objs = modelo_pool.search(cr, uid, [('tabela','=','finan.contrato')])

            for imovel_obj in contrato_obj.imovel_ids:
                for modelo_obj in modelo_pool.browse(cr, uid, modelos_objs):
                    dados = {
                        'finan_contrato_obj': contrato_obj,
                        'comprador_obj': contrato_obj.partner_id,
                        'imovel_obj': imovel_obj.imovel_id,
                        'vendedor_obj': imovel_obj.imovel_id.proprietario_id,
                    }

                    variaveis = {
                    }

                    nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                    nome_arquivo += '_' + contrato_obj.numero

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.contrato'), ('res_id', '=', contrato_obj.id), ('name', 'like', nome_arquivo)])
                    attachment_pool.unlink(cr, uid, attachment_ids)

                    nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                    nome_arquivo += '.'
                    nome_arquivo += modelo_obj.formato or 'doc'

                    arquivo = modelo_obj.gera_modelo(dados,formato=modelo_obj.formato, novas_variaveis=variaveis)

                    dados = {
                        'datas': arquivo,
                        'name': nome_arquivo,
                        'datas_fname': nome_arquivo,
                        'res_model': 'finan.contrato',
                        'res_id': contrato_obj.id,
                        'file_type': 'application/msword',
                    }
                    attachment_pool.create(cr, uid, dados)

        return

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

        return res

    def baixa_contrato(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for contrato_obj in self.browse(cr, uid, ids):

            if not contrato_obj.data_distrato or not contrato_obj.motivo_baixa_id :
                raise osv.except_osv(u'Inválido !', u'Selecione a Data ou Motivo')
            else:
                for lancamento_obj in contrato_obj.lancamento_ids:

                    if lancamento_obj.situacao in ('A vencer', 'Vencido', 'Vence hoje'):

                        dados = {
                                'situacao': 'Baixado',
                                'data_baixa': contrato_obj.data_distrato,
                                'motivo_baixa_id':contrato_obj.motivo_baixa_id.id,
                        }
                        lancamento_obj.write(dados)

        return


finan_contrato()


PAPEL_VENDA = (
    ('E', u'Empresa'),
    ('A', u'Agenciador'),
    ('C', u'Corretor'),
    ('G', u'Gerente'),
    ('O', u'Outros'),
)

class finan_contrato_cliente(osv.Model):
    _description = u'Clientes do contrato'
    _name = 'finan.contrato.cliente'

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', u'Cliente', ondelete='restrict'),
        'porcentagem': fields.float(u'Porcentagem'),
    }

    _defaults = {
        'porcentagem': 0,
    }


finan_contrato_cliente()

class finan_comissao(osv.Model):
    _description = u'Comissões'
    _name = 'finan.comissao'
    _rec_name = 'nome'

    _columns = {
        'data': fields.date(u'Data inicial'),
        'nome': fields.char(u'Nome', size=60),
        'item_ids': fields.one2many('finan.contrato.comissao', 'finan_comissao_id', u'Comissão'),
    }

    _defaults = {
        'data': fields.datetime.now,
    }


finan_comissao()



class finan_contrato_comissao(osv.Model):
    _description = u'Comissões do contrato'
    _name = 'finan.contrato.comissao'
    _rec_name = 'partner_id'

    def _valor_comissao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for comissao_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if comissao_obj.contrato_id.percentual_comissao:
                for parcela_obj in comissao_obj.contrato_id.parcela_ids:
                    valor += D(parcela_obj.valor or 0)

                #valor = D(comissao_obj.contrato_id.valor or 0)
                valor *= D(comissao_obj.contrato_id.percentual_comissao or 0) / D(100)
                valor *= D(comissao_obj.porcentagem or 0) / D(100)
                valor = valor.quantize(D('0.01'))

            res[comissao_obj.id] = valor

        return res

    _columns = {
        'finan_comissao_id': fields.many2one('finan.comissao', u'Comissão', ondelete="restrict"),
        'project_id': fields.many2one('finan.contrato.comissao', u'Projeto'),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', u'Corretor', ondelete='restrict'),
        'papel': fields.selection(PAPEL_VENDA, u'Papel'),
        'payment_term_id': fields.many2one('account.payment.term', u'Condição de pagamento'),
        'porcentagem': fields.float(u'Porcentagem', digits=(21, 11)),
        'valor_comissao': fields.float(u'Valor', digits=(18, 2)),
        #'valor_comissao': fields.function(_valor_comissao, type='float', string=u'Valor'),
        'data_inicial': fields.date(u'Data inicial'),
        'vezes': fields.integer(u'Vezes'),
        'parcela_ids': fields.one2many('finan.contrato.comisao.parcela', 'comissao_id', u'Parcelas da comissão'),
        'lancamento_ids': fields.one2many('finan.lancamento', 'parcela_comissao_id', u'Lançamentos da comissão'),
        'parcelas_manual': fields.boolean(u'Parcelas em modo manual?'),
    }

    _defaults = {
        'porcentagem': 0,
        'data_inicial': fields.datetime.now,
    }

    def create(self, cr, uid, dados, context={}):

        res = super(finan_contrato_comissao, self).create(cr, uid, dados, context)

        self.pool.get('finan.contrato.comissao').gera_parcelas(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):

        res = super(finan_contrato_comissao, self).write(cr, uid, ids, dados, context)

        self.pool.get('finan.contrato.comissao').gera_parcelas(cr, uid, ids, context=context)

        return res

    def gera_parcelas(self, cr, uid, ids, valor_total=D(0), context={}):

        parcela_pool = self.pool.get('finan.contrato.comisao.parcela')

        for comissao_obj in self.browse(cr, uid, ids, context=context):
            if comissao_obj.contrato_id and comissao_obj.parcelas_manual:
                continue

            if not comissao_obj.data_inicial:
                continue

            for parcela_obj in comissao_obj.parcela_ids:
                parcela_obj.unlink()

            data_base = parse_datetime(comissao_obj.data_inicial or hoje())

            if valor_total and valor_total > 0:
                valor = D(valor_total or 0).quantize(D('0.01'))
            else:
                valor = D(comissao_obj.valor_comissao).quantize(D('0.01'))

            for i in range(comissao_obj.vezes):
                dados = {
                    'comissao_id': comissao_obj.id,
                    'parcela': i + 1,
                    'data_vencimento': str(data_base.date() + relativedelta(months=+i)),
                    'valor':  valor / comissao_obj.vezes,
                }

                parcela_pool.create(cr, uid, dados)

        return True

    def onchange_porcentagem_valor(self, cr, uid, ids, valor_contrato, porcentagem_contrato, porcentagem=None, valor=None, context={}):
        valores = {}
        res = {'value': valores}


        if not valor_contrato:
            return res

        if not porcentagem_contrato:
            return res

        valor_contrato = D(valor_contrato or 0).quantize(D('0.01'))
        porcentagem_contrato = D(porcentagem_contrato or 0)
        valor_contrato *= porcentagem_contrato / 100

        if porcentagem is not None:
            porcentagem = D(porcentagem or 0)
            valor = valor_contrato
            valor *= porcentagem / D(100)
            valor = valor.quantize(D('0.01'))
            print('p', valor, porcentagem)

        elif valor is not None:
            valor = D(valor or 0).quantize(D('0.01'))
            porcentagem = valor / valor_contrato
            porcentagem *= 100

            print('v', valor, porcentagem)

        else:
            porcentagem = D(0)
            valor = D(0)

        valores['porcentagem'] = porcentagem
        valores['valor_comissao'] = valor

        return res


finan_contrato_comissao()


class finan_contrato_comissao_parcela(osv.Model):
    _description = u'Parcela das comissao do contrato'
    _name = 'finan.contrato.comisao.parcela'
    _rec_name = 'comissao_id'
    _order =  'comissao_id, data_vencimento, parcela'

    _columns = {
        'comissao_id': fields.many2one('finan.contrato.comissao', u'Comissao', required=True, ondelete="cascade"),
        'contrato_id': fields.related('comissao_id', 'contrato_id', type='many2one', relation='finan.contrato', string=u'Contrato', store=True),
        'partner_id': fields.related('comissao_id', 'partner_id', type='many2one', relation='res.partner', string=u'Corretor', store=True),
        'parcela': fields.integer(u'Parcela'),
        'data_vencimento': fields.date(u'Vencimento'),
        'valor': fields.float(u'Valor'),
    }

finan_contrato_comissao_parcela()



class finan_contrato_imovel(osv.Model):
    _description = u'Imóveis do contrato'
    _name = 'finan.contrato.imovel'

    _columns = {
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="cascade"),
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', ondelete='restrict'),
        'proprietario_id': fields.related('imovel_id','proprietario_id',  type='many2one', string=u'Proprietário', relation='res.partner', store=False),
        'res_partner_bank_id': fields.related('imovel_id','res_partner_bank_id',  type='many2one', string=u'Conta Bancária', relation='res.partner.bank', store=False),
        'project_id': fields.related('imovel_id','project_id',  type='many2one', string=u'Projeto', relation='project.project', store=False),
        'valor_venda': fields.related('imovel_id','valor_venda',  type='float', string=u'Valor', store=False),
        'codigo': fields.related('imovel_id','codigo',  type='char', string=u'Código', store=False),
        'situacao': fields.related('imovel_id','situacao',  type='selection', relation='const.imovel', selection=SITUACAO_IMOVEL, string=u'Situação comercial', store=False),
        'propriedade': fields.related('imovel_id','propriedade',  type='selection', relation='const.imovel', selection=PROPRIEDADE, string=u'Propriedade', store=False),
        'area_terreno': fields.related('imovel_id','area_terreno',  type='float', string=u'Área terreno (m²)', store=False),
        'area_total': fields.related('imovel_id','area_terreno',  type='float', string=u'Área total (m²)', store=False),
        'quadra': fields.related('imovel_id','quadra',  type='char', string=u'Quadra', store=False),
        'lote': fields.related('imovel_id','lote',  type='char', string=u'Lote', store=False),
    }

    def onchange_imovel_id(self, cr, uid, ids, imovel_id):
        if not imovel_id:
            return {}

        res = {}
        valores = {}
        res['value'] = valores

        imovel_obj = self.pool.get('const.imovel').browse(cr, uid, imovel_id)

        if imovel_obj.proprietario_id:
            valores['proprietario_id'] = imovel_obj.proprietario_id.id

        if imovel_obj.res_partner_bank_id:
            valores['res_partner_bank_id'] = imovel_obj.res_partner_bank_id.id

        if imovel_obj.project_id:
            valores['project_id'] = imovel_obj.project_id.id

        valores['valor_venda'] = imovel_obj.valor_venda
        valores['codigo'] = imovel_obj.codigo
        valores['situacao'] = imovel_obj.situacao
        valores['propriedade'] = imovel_obj.propriedade
        valores['area_terreno'] = imovel_obj.area_terreno
        valores['quadra'] = imovel_obj.quadra
        valores['lote'] = imovel_obj.lote

        return res


finan_contrato_imovel()
