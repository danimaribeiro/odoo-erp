# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from pybrasil.valor.decimal import Decimal as D
from osv import osv, fields
from sped.constante_tributaria import *
from fields import *
from sped_calcula_impostos import calcula_item
from copy import copy


#
# tabela_alterada:
#  lambda que retorna os ids da tabela atual a sere alterados, quando algum campo da tabela alterada for alterado
#  lista de campos da tabela alterada a serem monitorados por alteraçoes
#  número que define a prioridade/ordem em que serao analisados os varios parametros store
#
STORE_CUSTO = {
    'sped.documentoitem': (
        lambda docitem_pool, cr, uid, ids, context={}: ids,
        ['regime_tributario', 'emissao', 'operacao_id', 'partner_id', 'data_emissao', 'modelo', 'cfop_id', 'compoe_total',
         'movimentacao_fisica', 'produto_id', 'quantidade', 'vr_unitario', 'quantidade_tributacao', 'vr_unitario_tributacao',
         'vr_produtos', 'vr_produtos_tributacao', 'vr_frete', 'vr_seguro', 'vr_desconto', 'vr_outras', 'vr_operacao',
         'vr_operacao_tributacao', 'org_icms', 'cst_icms', 'partilha', 'al_bc_icms_proprio_partilha', 'uf_partilha_id',
         'repasse', 'md_icms_proprio', 'pr_icms_proprio', 'rd_icms_proprio', 'bc_icms_proprio_com_ipi', 'bc_icms_proprio',
         'al_icms_proprio', 'vr_icms_proprio', 'cst_icms_sn', 'al_icms_sn', 'rd_icms_sn', 'vr_icms_sn', 'md_icms_st',
         'pr_icms_st', 'rd_icms_st', 'bc_icms_st_com_ipi', 'bc_icms_st', 'al_icms_st', 'vr_icms_st', 'md_icms_st_retido',
         'pr_icms_st_retido', 'rd_icms_st_retido', 'bc_icms_st_retido', 'al_icms_st_retido', 'vr_icms_st_retido',
         'apuracao_ipi', 'cst_ipi', 'md_ipi', 'bc_ipi', 'al_ipi', 'vr_ipi', 'bc_ii', 'vr_despesas_aduaneiras', 'vr_ii',
         'vr_iof', 'al_pis_cofins_id', 'cst_pis', 'md_pis_proprio', 'bc_pis_proprio', 'al_pis_proprio', 'vr_pis_proprio',
         'cst_cofins', 'md_cofins_proprio', 'bc_cofins_proprio', 'al_cofins_proprio', 'vr_cofins_proprio', 'md_pis_st',
         'bc_pis_st', 'al_pis_st', 'vr_pis_st', 'md_cofins_st', 'bc_cofins_st', 'al_cofins_st', 'vr_cofins_st', 'vr_servicos',
         'cst_iss', 'bc_iss', 'al_iss', 'vr_iss', 'vr_pis_servico', 'vr_cofins_servico', 'vr_nf', 'vr_fatura', 'al_ibpt',
         'vr_ibpt', 'previdencia_retido', 'bc_previdencia', 'al_previdencia', 'vr_previdencia', 'fator_quantidade',
         'vr_diferencial_aliquota', 'vr_diferencial_aliquota_st', 'vr_simples',
         'credita_icms_proprio', 'credita_icms_st', 'credita_ipi', 'credita_pis_cofins',
         'forca_recalculo_st_compra', 'al_icms_st_compra', 'md_icms_st_compra', 'pr_icms_st_compra', 'rd_icms_st_compra',
         'bc_icms_st_compra', 'vr_icms_st_compra'],
        10
    ),
    'sped.documento': (
        lambda doc_pool, cr, uid, ids, context={}: doc_pool.pool.get('sped.documentoitem').search(cr, uid, [['documento_id', 'in', ids]]),
        ['vr_frete_rateio', 'vr_seguro_rateio', 'vr_desconto_rateio',
         'vr_outras_rateio'],
        20  #  Prioridade
    )
}


class sped_documentoitem(osv.Model):
    _description = 'Itens de documentos SPED'
    _name = 'sped.documentoitem'

    def onchange_produto_entrada(self, cr, uid, ids, produto_id, cfop_original_id, cfop_id, context):
        if not produto_id:
            return {}

        res = self.pool.get('sped.documentoitem').onchange_produto(cr, uid, ids, produto_id, context)
        valores_calculados = res['value']

        valores = {}
        valores['forca_recalculo_st_compra'] = valores_calculados['forca_recalculo_st_compra']
        valores['al_icms_st_compra'] = valores_calculados['al_icms_st_compra']
        valores['md_icms_st_compra'] = valores_calculados['md_icms_st_compra']
        valores['pr_icms_st_compra'] = valores_calculados['pr_icms_st_compra']
        valores['rd_icms_st_compra'] = valores_calculados['rd_icms_st_compra']
        valores['calcula_diferencial_aliquota'] = valores_calculados['calcula_diferencial_aliquota']
        valores['cfop_id'] = valores_calculados['cfop_id']
        valores['stock_location_id'] = valores_calculados.get('stock_location_id', False)
        valores['stock_location_dest_id'] = valores_calculados.get('stock_location_dest_id', False)

        if not 'default_regime_tributario' in context:
            raise osv.except_osv(u'Erro!', u'O regime tributário não foi informado!')
        else:
            regime_tributario = context['default_regime_tributario']

        company_obj = self.pool.get('res.company').browse(cr, uid, context['default_company_id'])
        cfop_obj = self.pool.get('sped.cfop').browse(cr, uid, valores['cfop_id'])

        valores['credita_pis_cofins'] = False
        if company_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL and cfop_obj.gera_pis_cofins:
            if regime_tributario != REGIME_TRIBUTARIO_SIMPLES and 'bc_pis_proprio' in valores_calculados:
                valores['credita_pis_cofins'] = True
                valores['cst_pis'] = valores_calculados['cst_pis']
                valores['md_pis_cofins'] = valores_calculados['md_pis_proprio']
                valores['bc_pis_proprio'] = valores_calculados['bc_pis_proprio']
                valores['al_pis_proprio'] = valores_calculados['al_pis_proprio']
                valores['vr_pis_proprio'] = valores_calculados['vr_pis_proprio']
                valores['cst_cofins'] = valores_calculados['cst_cofins']
                valores['md_cofins_cofins'] = valores_calculados['md_cofins_proprio']
                valores['bc_cofins_proprio'] = valores_calculados['bc_cofins_proprio']
                valores['al_cofins_proprio'] = valores_calculados['al_cofins_proprio']
                valores['vr_cofins_proprio'] = valores_calculados['vr_cofins_proprio']

        res = {'value': valores}

        cfop_pool = self.pool.get('sped.cfop')

        cfop_original_obj = False
        if cfop_original_id:
            cfop_original_obj = cfop_pool.browse(cr, uid, cfop_original_id)

        cfop_obj = False
        if cfop_id:
            cfop_obj = cfop_pool.browse(cr, uid, cfop_id)

        produto_obj = self.pool.get('product.product').browse(cr, uid, produto_id)
        valores['uom_id'] = produto_obj.uom_id.id
        valores['produto_type'] = produto_obj.type

        if cfop_original_id and cfop_original_obj.codigo in ['5933', '6933']:
            if produto_obj.type != 'service':
                raise osv.except_osv(u'Erro!', u'Para CFOP ' + cfop_original_obj.codigo + ' é obrigatório escolher um serviço!')

            if cfop_original_id.codigo == '5933':
                valores['cfop_id'] = cfop_pool.search(cr, uid, [('codigo', '=', '1933')])[0]
            elif cfop_original_id.codigo == '6933':
                valores['cfop_id'] = cfop_pool.search(cr, uid, [('codigo', '=', '2933')])[0]

        if regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
            #valores['credita_icms_proprio'] = True
            if cfop_obj:
                valores['credita_icms_proprio'] = cfop_obj.gera_icms_proprio
            else:
                valores['credita_icms_proprio'] = True

            valores['informa_icms_st'] = True

        #
        # Agora que temos o produto e a CFOP, vamos buscar se há outra NF
        # de entrada, do mesmo fornecedor, para a mesma empresa, do mesmo
        # produto e CFOP, e vamos assumir as regras de crédito de imposto,
        # e o fator de conversão de quantidade, dessa última nota
        #
        sql = '''
select
    di.id

from
    sped_documentoitem di
    join sped_documento d on d.id = di.documento_id
    join res_company c on c.id = d.company_id
    join res_partner p on p.id = c.partner_id

where
    p.cnpj_cpf = '{cnpj}'
    and d.partner_id = {partner_id}
    and d.emissao = '1' and d.entrada_saida = '0'
    and d.situacao in ('00', '01', '08')
    and di.produto_id = {product_id}
    and di.cfop_id = {cfop_id}
    {filtro_item_id}

order by
    d.data_emissao_brasilia desc

limit 1;'''

        filtro = {
            'cnpj': company_obj.partner_id.cnpj_cpf,
            'partner_id': context['default_partner_id'],
            'product_id': produto_obj.id,
            'cfop_id': valores['cfop_id'],
            'filtro_item_id': '',
        }

        if ids:
            filtro['filtro_item_id'] = 'and di.id != ' + str(ids[0])

        sql = sql.format(**filtro)
        #print(sql)
        cr.execute(sql)
        dados_anterior = cr.fetchall()

        if len(dados_anterior):
            item_anterior_id = dados_anterior[0][0]
            item_anterior_obj = self.pool.get('sped.documentoitem').browse(cr, uid, item_anterior_id)
            valores.update({
                'credita_icms_proprio': item_anterior_obj.credita_icms_proprio,
                'credita_icms_st': item_anterior_obj.credita_icms_st,
                'credita_ipi': item_anterior_obj.credita_ipi,
                'credita_pis_cofins': item_anterior_obj.credita_pis_cofins,
                'fator_quantidade': item_anterior_obj.fator_quantidade or 1,
                #'quantidade_estoque': (item_anterior_obj.fator_quantidade or 1) * item_obj.quantidade,
            })

        return res

    def onchange_produto(self, cr, uid, ids, produto_id, context):
        if not produto_id:
            return {}

        #
        # Validamos se todos os parâmetros necessários foram passados no contexto
        #
        if not 'default_company_id' in context:
            raise osv.except_osv(u'Erro!', u'A empresa ativa não foi definida!')
        else:
            company_id = context['default_company_id']

        if not 'default_partner_id' in context:
            raise osv.except_osv(u'Erro!', u'O destinatário/remetente não foi informado!')
        else:
            partner_id = context['default_partner_id']

        if not 'default_operacao_id' in context:
            raise osv.except_osv(u'Erro!', u'A operação fiscal não foi informada!')
        else:
            operacao_id = context['default_operacao_id']

        if not 'default_entrada_saida' in context:
            raise osv.except_osv(u'Erro!', u'O tipo da emissão, se de entrada ou saída, não foi informado!')
        else:
            entrada_saida = context['default_entrada_saida']

        if not 'default_regime_tributario' in context:
            raise osv.except_osv(u'Erro!', u'O regime tributário não foi informado!')
        else:
            regime_tributario = context['default_regime_tributario']

        if not 'default_emissao' in context:
            raise osv.except_osv(u'Erro!', u'O tipo da emissão, se própria ou de terceiros, não foi informado!')
        else:
            emissao = context['default_emissao']

        data_emissao = context.get('default_data_emissao', None)
        municipio_fato_gerador_id = context.get('default_municipio_fato_gerador_id', None)
        contribuinte = context.get('default_contribuinte', '1')
        modelo = context.get('default_modelo', '55')

        #
        # O tipo do contribuinte só tem nexo para NF-e modelo 55
        # nos demais casos, definir fixo como '1'
        #
        if modelo != '55' or emissao != '0':
            contribuinte = '1'

        #if modelo == '57':
            #return

        #
        # Vamos trazer todos os registros necessários
        #
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)
        contribuinte = partner_obj.contribuinte
        operacao_obj = self.pool.get('sped.operacao').browse(cr, uid, operacao_id)
        produto_obj = self.pool.get('product.product').browse(cr, uid, produto_id)

        if (not partner_obj.municipio_id):
            if ('sale_order_line' not in context):
                raise osv.except_osv(u'Erro!', u'O cliente “%s”, CNPJ/CPF “%s”, está sem o município preenchido!' % (partner_obj.name, partner_obj.cnpj_cpf))
            else:
                partner_obj.municipio_id = company_obj.partner_id.municipio_id

        #
        # Buscando a UF de origem e destino
        #
        if entrada_saida == ENTRADA_SAIDA_SAIDA:
            try:
                uf_origem = company_obj.partner_id.municipio_id.estado_id.uf
            except:
                raise osv.except_osv(u'Erro!', u'Não há município para a empresa “' + company_obj.name + u'”')

            try:
                uf_destino = partner_obj.municipio_id.estado_id.uf
            except:
                raise osv.except_osv(u'Erro!', u'Não há município para o cliente/fornecedor “' + partner_obj.name + u'”')

        else:
            try:
                uf_origem = partner_obj.municipio_id.estado_id.uf
            except:
                raise osv.except_osv(u'Erro!', u'Não há município para o cliente/fornecedor “' + partner_obj.name + u'”')

            try:
                uf_destino = company_obj.partner_id.municipio_id.estado_id.uf
            except:
                raise osv.except_osv(u'Erro!', u'Não há município para a empresa “' + company_obj.name + u'”')

        if entrada_saida == ENTRADA_SAIDA_ENTRADA:
            uf_aplicacao_familia = company_obj.partner_id.municipio_id.estado_id.uf
        else:
            uf_aplicacao_familia = partner_obj.municipio_id.estado_id.uf

        #
        # Achamos a família tributária do ICMS, que vai determinar
        # as alíquotas do ICMS e a CFOP
        #
        familiatributaria_obj = None
        if produto_obj.familiatributaria_id and (not getattr(operacao_obj, 'prioriza_familia_ncm', False)):
            familiatributaria_obj = produto_obj.familiatributaria_id

        elif produto_obj.ncm_id and len(produto_obj.ncm_id.familiatributaria_ids) >= 1:

            #
            # Trata as famílias vinculadas ao NCM, verificando se valem para o estado
            # em questão
            #
            for famtrib_obj in produto_obj.ncm_id.familiatributaria_ids:
                if not famtrib_obj.familiatributariaestado_ids:
                    familiatributaria_obj = famtrib_obj
                    break

                else:
                    for estado_obj in famtrib_obj.familiatributariaestado_ids:
                        if estado_obj.estado_id.uf == uf_aplicacao_familia:
                            familiatributaria_obj = famtrib_obj
                            break

                if familiatributaria_obj is not None:
                    break

        if familiatributaria_obj is None and getattr(operacao_obj, 'prioriza_familia_ncm', False) and produto_obj.familiatributaria_id:
            familiatributaria_obj = produto_obj.familiatributaria_id

        if familiatributaria_obj is None and company_obj.familiatributaria_id:
            familiatributaria_obj = company_obj.familiatributaria_id

        if familiatributaria_obj is None:
            if produto_obj.ncm_id:
                raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, nem família tributária definida no produto/serviço “%s”, nem no NCM “%s”!' % (produto_obj.name, produto_obj.ncm_id.codigo))
            else:
                raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, nem família tributária definida no produto/serviço “%s”!' % produto_obj.name)

        #
        # Tratando famílias tributárias que só valem para determinados estados
        # Caso não seja possível usar a família determinada, por restrição dos
        # estados permitidos, usar a família global da empresa
        #
        if len(familiatributaria_obj.familiatributariaestado_ids) > 0:
            usa_familia_padrao = True

            for estado_obj in familiatributaria_obj.familiatributariaestado_ids:
                if estado_obj.estado_id.uf == uf_aplicacao_familia:
                    usa_familia_padrao = False
                    break

            if usa_familia_padrao:
                if not company_obj.familiatributaria_id:
                    if produto_obj.ncm_id:
                        raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, e a família tributária “%s” não pode ser usada para o estado “%s” (produto “%s”, NCM “%s”)!' % (familiatributaria_obj.descricao, uf_aplicacao_familia, produto_obj.name, produto_obj.ncm_id.codigo))
                    else:
                        raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, e a família tributária “%s” não pode ser usada para o estado “%s” (produto “%s”)!' % (familiatributaria_obj.descricao, uf_aplicacao_familia, produto_obj.name))

                familiatributaria_obj = company_obj.familiatributaria_id

        #
        # Guarda a família tributária original
        #
        familiatributaria_original_obj = familiatributaria_obj

        dentro_estado = uf_origem == uf_destino
        fora_pais = uf_destino == 'EX' or uf_origem == 'EX'
        fora_estado = uf_origem != uf_destino and (not fora_pais)
        #print(uf_origem, uf_destino, dentro_estado, fora_estado, fora_pais)

        #
        # E vamos localizar o item da operação com a CFOP correta para o caso
        #
        lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
            cr,
            uid,
            [
                ('operacao_id', '=', operacao_obj.id),
                ('familiatributaria_id', '=', familiatributaria_obj.id),
                ('cfop_id.dentro_estado', '=', dentro_estado),
                ('cfop_id.fora_estado', '=', fora_estado),
                ('cfop_id.fora_pais', '=', fora_pais),
                '|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
            ]
        )

        #
        # Caso não haja um item da operação específico para a família, busca
        # o genérico (item da operação sem família)
        #
        if len(lista_operacaoitem_ids) == 0:
            lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
                cr,
                uid,
                [
                    ('operacao_id', '=', operacao_obj.id),
                    ('familiatributaria_id', '=', False),
                    ('cfop_id.dentro_estado', '=', dentro_estado),
                    ('cfop_id.fora_estado', '=', fora_estado),
                    ('cfop_id.fora_pais', '=', fora_pais),
                    '|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
                ]
            )

        if len(lista_operacaoitem_ids) == 0:
            if produto_obj.ncm_id:
                mensagem = u'Não há um item da operação “%s” configurado para o produto “%s”, NCM “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, produto_obj.ncm_id.codigo, familiatributaria_obj.descricao)
            else:
                mensagem = u'Não há um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)

            if contribuinte == '1':
                mensagem += ' para contribuinte com IE '
            elif contribuinte == '2':
                mensagem += ' para contribuinte isento '
            elif contribuinte == '9':
                mensagem += ' para estrangeiro '

            if dentro_estado:
                mensagem += 'com CFOP para dentro do estado!'
            elif fora_pais:
                mensagem += 'com CFOP para fora do país!'
            else:
                mensagem += 'com CFOP para fora do estado!'

            raise osv.except_osv(u'Erro!', mensagem)

        elif len(lista_operacaoitem_ids) > 1:
            if produto_obj.ncm_id:
                mensagem = u'Há mais de um item da operação “%s” configurado para o produto “%s”, NCM “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, produto_obj.ncm_id.codigo, familiatributaria_obj.descricao)
            else:
                mensagem = u'Há mais de um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)

            if contribuinte == '1':
                mensagem += ' para contribuinte com IE '
            elif contribuinte == '2':
                mensagem += ' para contribuinte isento '
            elif contribuinte == '9':
                mensagem += ' para estrangeiro '

            if dentro_estado:
                mensagem += 'com CFOP para dentro do estado!'
            elif fora_pais:
                mensagem += 'com CFOP para fora do país!'
            else:
                mensagem += 'com CFOP para fora do estado!'

            raise osv.except_osv(u'Erro!', mensagem)

        lista_operacaoitem_id = lista_operacaoitem_ids[0]
        operacao_item_obj = self.pool.get('sped.operacaoitem').browse(cr, uid, lista_operacaoitem_id)

        #
        # Caso haja família tributária alternativa
        #
        if operacao_item_obj.familiatributaria_alternativa_id:
            familiatributaria_obj = operacao_item_obj.familiatributaria_alternativa_id

        #
        # Agora que já encontramos, definimos os valores do item do documento
        # pelos valores do item da operação
        #
        valores = {}
        valores['cfop_id'] = operacao_item_obj.cfop_id.id
        valores['compoe_total'] = operacao_item_obj.compoe_total
        valores['movimentacao_fisica'] = operacao_item_obj.movimentacao_fisica
        valores['bc_icms_proprio_com_ipi'] = operacao_item_obj.bc_icms_proprio_com_ipi
        valores['bc_icms_st_com_ipi'] = operacao_item_obj.bc_icms_st_com_ipi
        valores['cst_icms'] = operacao_item_obj.cst_icms
        valores['cst_icms_sn'] = operacao_item_obj.cst_icms_sn
        valores['cst_ipi'] = operacao_item_obj.cst_ipi
        valores['cst_iss'] = operacao_item_obj.cst_iss
        valores['previdencia_retido'] = operacao_item_obj.previdencia_retido or False
        valores['al_previdencia'] = familiatributaria_obj.al_previdencia or 0
        valores['contribuinte'] = operacao_item_obj.contribuinte or '1'
        valores['regime_tributario'] = operacao_obj.regime_tributario or REGIME_TRIBUTARIO_SIMPLES
        valores['forca_recalculo_st_compra'] = operacao_obj.forca_recalculo_st_compra
        valores['calcula_diferencial_aliquota'] = operacao_obj.calcula_diferencial_aliquota

        #
        # Seleciona os créditos de PIS-COFINS de acordo com o CFOP
        #
        if entrada_saida == ENTRADA_SAIDA_ENTRADA and company_obj.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL and regime_tributario != REGIME_TRIBUTARIO_SIMPLES:
            valores['credita_pis_cofins'] = operacao_item_obj.cfop_id.gera_pis_cofins

        #
        # Para integração com estoque
        #
        valores['stock_location_id'] = False
        valores['stock_location_dest_id'] = False
        if getattr(operacao_item_obj, 'stock_location_id', False):
            valores['stock_location_id'] = getattr(operacao_item_obj, 'stock_location_id', False).id

        if getattr(operacao_item_obj, 'stock_location_dest_id', False):
            valores['stock_location_dest_id'] = getattr(operacao_item_obj, 'stock_location_dest_id', False).id

        if getattr(operacao_obj, 'traz_custo_medio', False):
            vr_unitario = D('0')

            if operacao_item_obj.stock_location_id:
                #
                # Busca o custo unitário médio do produto no momento
                #
                custo_pool = self.pool.get('product.custo')
                unit, qtd, tot = custo_pool.busca_custo(cr, 1, company_id=company_id, location_id=operacao_item_obj.stock_location_id.id, product_id=produto_obj.id)
                vr_unitario = D(unit)

            #print('valor unitario aqui', vr_unitario)
            if vr_unitario <= D('0'):
                for local_custo_obj in operacao_obj.local_custo_ids:
                    #
                    # Busca o custo unitário médio do produto no momento
                    #
                    custo_pool = self.pool.get('product.custo')
                    unit, qtd, tot = custo_pool.busca_custo(cr, 1, company_id=company_id, location_id=local_custo_obj.stock_location_id.id, product_id=produto_obj.id)
                    #print('local', local_custo_obj.stock_location_id.name)
                    #print('valores', qtd, unit, tot)
                    vr_unitario = D(unit)

                    if vr_unitario:
                        break

            #print('valor unitario aqui 2', vr_unitario)
            if vr_unitario <= D('0'):
                vr_unitario = D(produto_obj.standard_price)

            valores['vr_unitario'] = vr_unitario.quantize(D('0.0000000001'))
            valores['vr_unitario_tributacao'] = vr_unitario.quantize(D('0.0000000001'))

        if produto_obj.org_icms:
            valores['org_icms'] = produto_obj.org_icms
        else:
            valores['org_icms'] = operacao_item_obj.org_icms or ORIGEM_MERCADORIA_NACIONAL

        #
        # Caso a operação seja do SIMPLES trazer a alíquota do crédito da company
        #
        if company_obj.al_icms_sn_id:
            valores['al_icms_sn'] = company_obj.al_icms_sn_id.al_icms or 0
            valores['rd_icms_sn'] = company_obj.al_icms_sn_id.rd_icms or 0

        #
        # Vamos buscar a alíquota do ISS
        #
        if operacao_item_obj.cst_iss:
            if municipio_fato_gerador_id:
                municipio_fato_gerador_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_fato_gerador_id)
            elif operacao_obj.natureza_tributacao_nfse == NAT_OP_TRIBUTADA_FORA_MUNICIPIO:
                municipio_fato_gerador_obj = partner_obj.municipio_id
            else:
                municipio_fato_gerador_obj = company_obj.partner_id.municipio_id

            lista_familiatributariaitemservico_ids = self.pool.get('sped.familiatributariaitemservico').search(
                cr,
                uid,
                [
                    ('familiatributaria_id', '=', familiatributaria_obj.id),
                    ('municipio_id', '=', municipio_fato_gerador_obj.id),
                ], limit=1, order='al_iss_id DESC')

            if not lista_familiatributariaitemservico_ids:
                raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado para o município “%s” (serviço “%s”)' % (familiatributaria_obj.descricao, municipio_fato_gerador_obj.descricao, produto_obj.name))

            familiatributaria_itemservico_obj = self.pool.get('sped.familiatributariaitemservico').browse(cr, uid, lista_familiatributariaitemservico_ids[0])
            valores['al_iss'] = familiatributaria_itemservico_obj.al_iss_id.al_iss or 0

            if produto_obj.servico_id:
                valores['al_ibpt'] = produto_obj.servico_id.al_ibpt_nacional or 0
            else:
                valores['al_ibpt'] = 0

        else:
            #
            # Agora, vamos trazer o item da família tributária, que contém as
            # alíquotas do ICMS próprio e ST
            #
            lista_familiatributariaitem_ids = self.pool.get('sped.familiatributariaitem').search(
                cr,
                uid,
                [
                    ('familiatributaria_id', '=', familiatributaria_obj.id),
                    ('estado_origem_id.uf', '=', uf_origem),
                    ('estado_destino_id.uf', '=', uf_destino),
                    ('data_inicio', '<=', data_emissao),
                ], limit=1, order='data_inicio DESC')

            if not lista_familiatributariaitem_ids:
                #
                # Verifica a família tributária padrão da empresa, se houver:
                if company_obj.familiatributaria_id:
                    lista_familiatributariaitem_ids = self.pool.get('sped.familiatributariaitem').search(
                        cr,
                        uid,
                        [
                            ('familiatributaria_id', '=', company_obj.familiatributaria_id.id),
                            ('estado_origem_id.uf', '=', uf_origem),
                            ('estado_destino_id.uf', '=', uf_destino),
                            ('data_inicio', '<=', data_emissao),
                        ], limit=1, order='data_inicio DESC')

            if not lista_familiatributariaitem_ids:
                #
                if produto_obj.ncm_id:
                    raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s” (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name, produto_obj.ncm_id.codigo))
                else:
                    raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s” (produto “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name))

            familiatributaria_item_obj = self.pool.get('sped.familiatributariaitem').browse(cr, uid, lista_familiatributariaitem_ids[0])

            #print('estado origem', familiatributaria_item_obj.estado_origem_id.uf)
            #print('estado destin', familiatributaria_item_obj.estado_destino_id.uf)

            #
            # Agora que já encontramos, definimos os valores do item do documento
            # pelos valores do item da família tributária
            #
            if familiatributaria_item_obj.al_icms_proprio_id:
                if valores['org_icms'] in ORIGEM_MERCADORIA_ALIQUOTA_4 and fora_estado:
                    aliquota_importado_ids = self.pool.get('sped.aliquotaicmsproprio').search(cr, 1, [('importado', '=', True)])
                    aliquota_importado_obj = self.pool.get('sped.aliquotaicmsproprio').browse(cr, 1, aliquota_importado_ids[0])

                    if len(aliquota_importado_ids) >= 1:
                        valores['al_icms_proprio'] = aliquota_importado_obj.al_icms or 4
                        valores['md_icms_proprio'] = aliquota_importado_obj.md_icms or MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
                        valores['pr_icms_proprio'] = aliquota_importado_obj.pr_icms or 0
                        valores['rd_icms_proprio'] = aliquota_importado_obj.rd_icms or 0

                    else:
                        valores['al_icms_proprio'] = 4
                        valores['md_icms_proprio'] = MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
                        valores['pr_icms_proprio'] = 0
                        valores['rd_icms_proprio'] = 0

                else:
                    valores['al_icms_proprio'] = familiatributaria_item_obj.al_icms_proprio_id.al_icms or 0
                    valores['md_icms_proprio'] = familiatributaria_item_obj.al_icms_proprio_id.md_icms or MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
                    valores['pr_icms_proprio'] = familiatributaria_item_obj.al_icms_proprio_id.pr_icms or 0
                    valores['rd_icms_proprio'] = familiatributaria_item_obj.al_icms_proprio_id.rd_icms or 0

            valores['al_diferencial_aliquota'] = 0
            valores['calcula_diferencial_aliquota'] = operacao_obj.calcula_diferencial_aliquota
            if operacao_obj.calcula_diferencial_aliquota and (uf_origem != uf_destino) and (contribuinte == '2'):
                ####
                #### Busca a alíquota padrão para dentro do estado
                ####
                ###lista_familiatributariaitem_interna_ids = self.pool.get('sped.familiatributariaitem').search(
                    ###cr,
                    ###uid,
                    ###[
                        ###('familiatributaria_id', '=', familiatributaria_obj.id),
                        ###('estado_origem_id.uf', '=', uf_destino),
                        ###('estado_destino_id.uf', '=', uf_destino),
                        ###('data_inicio', '<=', data_emissao),
                    ###], limit=1, order='data_inicio DESC')

                ###if not lista_familiatributariaitem_interna_ids:
                    ####
                    #### Verifica a família tributária padrão da empresa, se houver:
                    ###if company_obj.familiatributaria_id:
                        ###lista_familiatributariaitem_interna_ids = self.pool.get('sped.familiatributariaitem').search(
                            ###cr,
                            ###uid,
                            ###[
                                ###('familiatributaria_id', '=', company_obj.familiatributaria_id.id),
                                ###('estado_origem_id.uf', '=', uf_destino),
                                ###('estado_destino_id.uf', '=', uf_destino),
                                ###('data_inicio', '<=', data_emissao),
                            ###], limit=1, order='data_inicio DESC')

                ###if lista_familiatributariaitem_interna_ids:
                    ###familiatributaria_item_interna_obj = self.pool.get('sped.familiatributariaitem').browse(cr, uid, lista_familiatributariaitem_interna_ids[0])
                    ###al_diferencial_aliquota = (familiatributaria_item_interna_obj.al_icms_proprio_id.al_icms or 0)
                ###else:
                    ###if produto_obj.ncm_id:
                        ###raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do diferencial de alíquota (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, uf_destino, uf_destino, produto_obj.name, produto_obj.ncm_id.codigo))
                    ###else:
                        ###raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do diferencial de alíquota (produto “%s”)' % (familiatributaria_obj.descricao, uf_destino, uf_destino, produto_obj.name))
                valores['al_diferencial_aliquota'] = ALIQUOTAS_ICMS[uf_destino][uf_destino]
                valores['al_diferencial_aliquota'] -= D(valores['al_icms_proprio'] or 0)

                if valores['al_diferencial_aliquota'] < 0:
                    valores['al_diferencial_aliquota'] = 0

            valores['al_icms_st'] = 0
            valores['md_icms_st'] = MODALIDADE_BASE_ICMS_ST_PAUTA
            valores['pr_icms_st'] = 0
            valores['rd_icms_st'] = 0
            valores['al_icms_st_compra'] = 0
            valores['md_icms_st_compra'] = MODALIDADE_BASE_ICMS_ST_PAUTA
            valores['pr_icms_st_compra'] = 0
            valores['rd_icms_st_compra'] = 0
            #print(familiatributaria_item_obj.id, familiatributaria_item_obj.al_icms_st_id)
            if familiatributaria_item_obj.al_icms_st_id:
                valores['al_icms_st'] = familiatributaria_item_obj.al_icms_st_id.al_icms or 0
                valores['md_icms_st'] = familiatributaria_item_obj.al_icms_st_id.md_icms
                valores['pr_icms_st'] = familiatributaria_item_obj.al_icms_st_id.pr_icms or 0
                valores['rd_icms_st'] = familiatributaria_item_obj.al_icms_st_id.rd_icms or 0

                #
                # Caso o MVA seja zerado, busca o MVA do NCM
                #
                if not valores['pr_icms_st'] and produto_obj.ncm_id and len(produto_obj.ncm_id.mva_ids):
                    for mva_obj in produto_obj.ncm_id.mva_ids:
                        if mva_obj.estado_id.uf == uf_destino:
                            if valores['regime_tributario'] == REGIME_TRIBUTARIO_SIMPLES:
                                valores['pr_icms_st'] = mva_obj.mva_simples or 0
                            else:
                                valores['pr_icms_st'] = mva_obj.mva_normal or 0
                            break
                    #
                    # Caso o MVA seja zerado, busca o MVA do NCM
                    #
                    if not valores['pr_icms_st_compra'] and produto_obj.ncm_id and len(produto_obj.ncm_id.mva_ids):
                        for mva_obj in produto_obj.ncm_id.mva_ids:
                            if mva_obj.estado_id.uf == uf_destino:
                                if valores['regime_tributario'] == REGIME_TRIBUTARIO_SIMPLES:
                                    valores['pr_icms_st_compra'] = mva_obj.mva_simples or 0
                                else:
                                    valores['pr_icms_st_compra'] = mva_obj.mva_normal or 0
                                break

            #if familiatributaria_item_obj.al_icms_st_retido_id:
                    #valores['al_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.al_icms
                    #valores['md_icms_st_re         #valores['md_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.md_icms
                    #valores['pr_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.pr_icms
                    #valores['rd_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.rd_icms

            #
            # No caso de MVA ajustado, vamos precisar da
            # alíquota interna do produto também
            #
            if familiatributaria_obj.usa_mva_ajustado:
                lista_familiatributariaitem_ids = self.pool.get('sped.familiatributariaitem').search(
                    cr,
                    uid,
                    [
                        ('familiatributaria_id', '=', familiatributaria_obj.id),
                        ('estado_origem_id.uf', '=', uf_origem),
                        ('estado_destino_id.uf', '=', uf_origem),
                        ('data_inicio', '<=', data_emissao),
                    ], limit=1, order='data_inicio DESC')

                if not lista_familiatributariaitem_ids:
                    if produto_obj.ncm_id:
                        raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do MVA ajustado na origem (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_origem, produto_obj.name, produto_obj.ncm_id.codigo))
                    else:
                        raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do MVA ajustado na origem (produto “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_origem, produto_obj.name))

                familiatributaria_origem_obj = self.pool.get('sped.familiatributariaitem').browse(cr, uid, lista_familiatributariaitem_ids[0])

                if not familiatributaria_origem_obj.al_icms_st_id:
                    if produto_obj.ncm_id:
                        raise osv.except_osv(u'Erro!', u'Não há definição do MVA original para o cálculo do MVA ajustado, para a família tributária “%s” (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, produto_obj.name, produto_obj.ncm_id.codigo))
                    else:
                        raise osv.except_osv(u'Erro!', u'Não há definição do MVA original para o cálculo do MVA ajustado, para a família tributária “%s” (produto “%s”)' % (familiatributaria_obj.descricao, produto_obj.name))

                al_interna = D(100) - D(valores['al_icms_proprio'])
                al_interna /= D(100)
                al_interestadual = D(100) - D(valores['al_icms_st'])
                al_interestadual /= D(100)

                #
                # Verifique se o MVA virá do NCM
                #
                mva_ajustado = D(0)
                if familiatributaria_origem_obj.al_icms_st_id.pr_icms:
                    mva_ajustado = D(familiatributaria_origem_obj.al_icms_st_id.pr_icms or 0)
                elif produto_obj.ncm_id and len(produto_obj.ncm_id.mva_ids):
                    for mva_obj in produto_obj.ncm_id.mva_ids:
                        if mva_obj.estado_id.uf == uf_origem:
                            #
                            # Em SC, o RICMS especifica que o regime tributário do cliente
                            # é que vale...
                            #
                            if uf_origem == 'SC' or uf_destino == 'SC':
                                if entrada_saida == 'S':
                                    if getattr(partner_obj, 'regime_tributario', REGIME_TRIBUTARIO_SIMPLES) == REGIME_TRIBUTARIO_SIMPLES:
                                        mva_ajustado = D(mva_obj.mva_simples or 0)
                                    else:
                                        mva_ajustado = D(mva_obj.mva_normal or 0)

                                else:
                                    if getattr(company_obj, 'regime_tributario', REGIME_TRIBUTARIO_SIMPLES) == REGIME_TRIBUTARIO_SIMPLES:
                                        mva_ajustado = D(mva_obj.mva_simples or 0)
                                    else:
                                        mva_ajustado = D(mva_obj.mva_normal or 0)

                            else:
                                if valores['regime_tributario'] == REGIME_TRIBUTARIO_SIMPLES:
                                    mva_ajustado = D(mva_obj.mva_simples or 0)
                                else:
                                    mva_ajustado = D(mva_obj.mva_normal or 0)
                            break

                mva_ajustado += D(100)
                mva_ajustado /= D(100)
                mva_ajustado *= al_interna / al_interestadual
                mva_ajustado -= 1
                mva_ajustado *= D(100)
                mva_ajustado = mva_ajustado.quantize(D('0.01'))

                valores['pr_icms_st'] = mva_ajustado

            if operacao_obj.forca_recalculo_st_compra:
                valores['al_icms_st_compra'] = valores['al_icms_st']
                valores['md_icms_st_compra'] = valores['md_icms_st']
                valores['pr_icms_st_compra'] = valores['pr_icms_st']
                valores['rd_icms_st_compra'] = valores['rd_icms_st']

            valores['infcomplementar'] = familiatributaria_item_obj.infadic or ''

            if produto_obj.ncm_id:
                valores['al_ibpt'] = produto_obj.ncm_id.al_ibpt_nacional or 0
            else:
                valores['al_ibpt'] = 0

        #
        # Por fim, baseado no NCM, somente para o regime tributário normal
        # busca as alíquotas do IPI, PIS e COFINS
        #
        if regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            #
            # Força a CST do PIS, COFINS e IPI para o SIMPLES
            #
            valores['cst_ipi'] = ''  # NF-e do SIMPLES não destaca IPI nunca
            valores['cst_pis'] = ST_PIS_OUTRAS
            valores['cst_cofins'] = ST_COFINS_OUTRAS
            valores['al_pis_cofins_id'] = company_obj.al_pis_cofins_id.id

            #
            # Calculo do SIMPLES Nacional
            #
            al_simples = SIMPLES_NACIONAL_TABELAS[company_obj.simples_anexo][company_obj.simples_teto]['al_simples']
            valores['al_simples'] = al_simples
            valores['vr_simples'] = D(0)

        else:
            valores['credita_icms_proprio'] = True
            valores['informa_icms_st'] = True

            #
            # Calculo do SIMPLES Nacional
            #
            valores['al_simples'] = D(0)
            valores['vr_simples'] = D(0)

            #
            # Determina a alíquota do PIS-COFINS:
            # 1º - se o produto tem uma específica
            # 2º - se o NCM tem uma específica
            # 3º - a geral da empresa
            #
            if produto_obj.al_pis_cofins_id:
                al_pis_cofins_obj = produto_obj.al_pis_cofins_id
            elif produto_obj.ncm_id.al_pis_cofins_id:
                al_pis_cofins_obj = produto_obj.ncm_id.al_pis_cofins_id
            else:
                al_pis_cofins_obj = company_obj.al_pis_cofins_id

            #
            # Determina a alíquota do IPI:
            # 1º - se o produto tem uma específica
            # 2º - se o NCM tem uma específica
            #
            if produto_obj.al_ipi_id:
                al_ipi_obj = produto_obj.al_ipi_id
            elif produto_obj.ncm_id.al_ipi_id:
                al_ipi_obj = produto_obj.ncm_id.al_ipi_id
            else:
                al_ipi_obj = None

            #
            # Quando a CST do PIS-COFINS for a mesma que é padrão da empresa
            # usar a específica do produto ou do NCM, caso contrário,
            # usar a específica do item da operação
            #
            if operacao_item_obj.al_pis_cofins_id and operacao_item_obj.al_pis_cofins_id.id != company_obj.al_pis_cofins_id.id:
                al_pis_cofins_obj = operacao_item_obj.al_pis_cofins_id

            #
            # Modalidade de cálculo e alíquotas já definidos
            #
            valores['al_pis_cofins_id'] = al_pis_cofins_obj.id
            valores['md_pis_proprio'] = al_pis_cofins_obj.md_pis_cofins
            valores['al_pis_proprio'] = al_pis_cofins_obj.al_pis or 0
            valores['md_cofins_proprio'] = al_pis_cofins_obj.md_pis_cofins
            valores['al_cofins_proprio'] = al_pis_cofins_obj.al_cofins or 0

            if entrada_saida == ENTRADA_SAIDA_ENTRADA:
                valores['cst_pis'] = al_pis_cofins_obj.cst_pis_cofins_entrada
                valores['cst_cofins'] = al_pis_cofins_obj.cst_pis_cofins_entrada
            else:
                valores['cst_pis'] = al_pis_cofins_obj.cst_pis_cofins_saida
                valores['cst_cofins'] = al_pis_cofins_obj.cst_pis_cofins_saida

            #
            # Verificar a CST do IPI; se o produto não possuir alíquota do IPI,
            # zera e não calcula o IPI
            #
            if not al_ipi_obj:
                valores['cst_ipi'] = ''
                valores['bc_ipi'] = D('0')
                valores['al_ipi'] = D('0')
                valores['vr_ipi'] = D('0')
            else:
                if operacao_item_obj.cst_ipi:
                    valores['cst_ipi'] = operacao_item_obj.cst_ipi
                elif entrada_saida == ENTRADA_SAIDA_ENTRADA:
                    valores['cst_ipi'] = al_ipi_obj.cst_ipi_entrada
                else:
                    valores['cst_ipi'] = al_ipi_obj.cst_ipi_saida

                if valores['cst_ipi'] in ST_IPI_CALCULA:
                    valores['md_ipi'] = al_ipi_obj.md_ipi
                    valores['al_ipi'] = al_ipi_obj.al_ipi

        #print('valores onchange_produto', valores)
        valores['uom_id'] = produto_obj.uom_id.id

        #
        # Ajusta alíquotas negativas nos casos de não tributado
        #
        for chave in valores:
            if isinstance(valores[chave], (int, float, D)) and valores[chave] < 0:
                valores[chave] = D('0')

        return {'value':  valores}

    def action_calcula_item(self, cr, uid, ids, context=None):
        retorno = {}
        for item_obj in self.browse(cr, uid, ids):
            dados = calcula_item(self, cr, uid, item_obj)
            retorno[item_obj.id] = self.pool.get('sped.documentoitem').write(cr, uid, [item_obj.id], dados)

        return retorno

    def onchange_calcula_item(self, cr, uid, ids, regime_tributario, emissao, operacao_id, partner_id, data_emissao, modelo, cfop_id, compoe_total, movimentacao_fisica, produto_id, quantidade, vr_unitario, quantidade_tributacao, vr_unitario_tributacao, vr_produtos, vr_produtos_tributacao, vr_frete, vr_seguro, vr_desconto, vr_outras, vr_operacao, vr_operacao_tributacao, org_icms, cst_icms, partilha, al_bc_icms_proprio_partilha, uf_partilha_id, repasse, md_icms_proprio, pr_icms_proprio, rd_icms_proprio, bc_icms_proprio_com_ipi, bc_icms_proprio, al_icms_proprio, vr_icms_proprio, cst_icms_sn, al_icms_sn, rd_icms_sn, vr_icms_sn, md_icms_st, pr_icms_st, rd_icms_st, bc_icms_st_com_ipi, bc_icms_st, al_icms_st, vr_icms_st, md_icms_st_retido, pr_icms_st_retido, rd_icms_st_retido, bc_icms_st_retido, al_icms_st_retido, vr_icms_st_retido, apuracao_ipi, cst_ipi, md_ipi, bc_ipi, al_ipi, vr_ipi, bc_ii, vr_despesas_aduaneiras, vr_ii, vr_iof, al_pis_cofins_id, cst_pis, md_pis_proprio, bc_pis_proprio, al_pis_proprio, vr_pis_proprio, cst_cofins, md_cofins_proprio, bc_cofins_proprio, al_cofins_proprio, vr_cofins_proprio, md_pis_st, bc_pis_st, al_pis_st, vr_pis_st, md_cofins_st, bc_cofins_st, al_cofins_st, vr_cofins_st, vr_servicos, cst_iss, bc_iss, al_iss, vr_iss, vr_pis_servico, vr_cofins_servico, vr_nf, vr_fatura, al_ibpt, vr_ibpt, previdencia_retido, bc_previdencia, al_previdencia, vr_previdencia, forca_recalculo_st_compra, md_icms_st_compra, pr_icms_st_compra, rd_icms_st_compra, bc_icms_st_compra, al_icms_st_compra, vr_icms_st_compra, calcula_diferencial_aliquota, al_diferencial_aliquota, vr_diferencial_aliquota, al_simples, vr_simples, context):
        if not produto_id:
            return {}

        cfop_obj = self.pool.get('sped.cfop').browse(cr, uid, cfop_id)

        valores = {
            'regime_tributario': regime_tributario,
            'emissao': emissao,
            'operacao_id': operacao_id,
            'partner_id': partner_id,
            'data_emissao': data_emissao,
            'modelo': modelo,
            'cfop_id': cfop_id,
            'cfop': cfop_obj.codigo,
            'compoe_total': compoe_total,
            'movimentacao_fisica': movimentacao_fisica,
            'produto_id': produto_id,
            'quantidade': quantidade,
            'vr_unitario': vr_unitario,
            'quantidade_tributacao': quantidade_tributacao,
            'vr_unitario_tributacao': vr_unitario_tributacao,
            'vr_produtos': vr_produtos,
            'vr_produtos_tributacao': vr_produtos_tributacao,
            'vr_frete': vr_frete,
            'vr_seguro': vr_seguro,
            'vr_desconto': vr_desconto,
            'vr_outras': vr_outras,
            'vr_operacao': vr_operacao,
            'vr_operacao_tributacao': vr_operacao_tributacao,
            'org_icms': org_icms,
            'cst_icms': cst_icms,
            'partilha': partilha,
            'al_bc_icms_proprio_partilha': al_bc_icms_proprio_partilha,
            'uf_partilha_id': uf_partilha_id,
            'repasse': repasse,
            'md_icms_proprio': md_icms_proprio,
            'pr_icms_proprio': pr_icms_proprio,
            'rd_icms_proprio': rd_icms_proprio,
            'bc_icms_proprio_com_ipi': bc_icms_proprio_com_ipi,
            'bc_icms_proprio': bc_icms_proprio,
            'al_icms_proprio': al_icms_proprio,
            'vr_icms_proprio': vr_icms_proprio,
            'cst_icms_sn': cst_icms_sn,
            'al_icms_sn': al_icms_sn,
            'rd_icms_sn': rd_icms_sn,
            'vr_icms_sn': vr_icms_sn,
            'al_simples': al_simples,
            'vr_simples': vr_simples,
            'md_icms_st': md_icms_st,
            'pr_icms_st': pr_icms_st,
            'rd_icms_st': rd_icms_st,
            'bc_icms_st_com_ipi': bc_icms_st_com_ipi,
            'bc_icms_st': bc_icms_st,
            'al_icms_st': al_icms_st,
            'vr_icms_st': vr_icms_st,
            'md_icms_st_retido': md_icms_st_retido,
            'pr_icms_st_retido': pr_icms_st_retido,
            'rd_icms_st_retido': rd_icms_st_retido,
            'bc_icms_st_retido': bc_icms_st_retido,
            'al_icms_st_retido': al_icms_st_retido,
            'vr_icms_st_retido': vr_icms_st_retido,
            'apuracao_ipi': apuracao_ipi,
            'cst_ipi': cst_ipi,
            'md_ipi': md_ipi,
            'bc_ipi': bc_ipi,
            'al_ipi': al_ipi,
            'vr_ipi': vr_ipi,
            'bc_ii': bc_ii,
            'vr_despesas_aduaneiras': vr_despesas_aduaneiras,
            'vr_ii': vr_ii,
            'vr_iof': vr_iof,
            'al_pis_cofins_id': al_pis_cofins_id,
            'cst_pis': cst_pis,
            'md_pis_proprio': md_pis_proprio,
            'bc_pis_proprio': bc_pis_proprio,
            'al_pis_proprio': al_pis_proprio,
            'vr_pis_proprio': vr_pis_proprio,
            'cst_cofins': cst_cofins,
            'md_cofins_proprio': md_cofins_proprio,
            'bc_cofins_proprio': bc_cofins_proprio,
            'al_cofins_proprio': al_cofins_proprio,
            'vr_cofins_proprio': vr_cofins_proprio,
            'md_pis_st': md_pis_st,
            'bc_pis_st': bc_pis_st,
            'al_pis_st': al_pis_st,
            'vr_pis_st': vr_pis_st,
            'md_cofins_st': md_cofins_st,
            'bc_cofins_st': bc_cofins_st,
            'al_cofins_st': al_cofins_st,
            'vr_cofins_st': vr_cofins_st,
            'vr_servicos': vr_servicos,
            'cst_iss': cst_iss,
            'bc_iss': bc_iss,
            'al_iss': al_iss,
            'vr_iss': vr_iss,
            'vr_pis_servico': vr_pis_servico,
            'vr_cofins_servico': vr_cofins_servico,
            'vr_nf': vr_nf,
            'vr_fatura': vr_fatura,
            'al_ibpt': al_ibpt,
            'vr_ibpt': vr_ibpt,
            'previdencia_retido': previdencia_retido,
            'bc_previdencia': bc_previdencia,
            'al_previdencia': al_previdencia,
            'vr_previdencia': vr_previdencia,
            'forca_recalculo_st_compra': forca_recalculo_st_compra,
            'md_icms_st_compra': md_icms_st_compra,
            'pr_icms_st_compra': pr_icms_st_compra,
            'rd_icms_st_compra': rd_icms_st_compra,
            'bc_icms_st_compra': bc_icms_st_compra,
            'al_icms_st_compra': al_icms_st_compra,
            'vr_icms_st_compra': vr_icms_st_compra,
            'calcula_diferencial_aliquota': calcula_diferencial_aliquota,
            'al_diferencial_aliquota': al_diferencial_aliquota,
            'vr_diferencial_aliquota': vr_diferencial_aliquota,
        }

        dados = calcula_item(self, cr, uid, valores)
        #print('valores onchange_calcula_item', dados)

        return {'value': dados}

    def _get_company_id_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sped.documento', context=context)

        return context.get('company_id') or company_id

    def _get_regime_tributario_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        company_id = self._get_company_id_padrao(cr, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, [company_id])[0]

        return context.get('regime_tributario') or company.regime_tributario or REGIME_TRIBUTARIO_SIMPLES

    def _get_emissao_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        return context.get('emissao') or TIPO_EMISSAO_PROPRIA

    def _get_operacao_id_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        return context.get('operacao_id')

    def _get_data_emissao_padrao(self, cr, uid, context):
        if context is None:
            context = {}

        return context.get('data_emissao')

    def _get_quantidade_estoque(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.fator_quantidade:
                res[item_obj.id] = item_obj.quantidade * item_obj.fator_quantidade
            else:
                res[item_obj.id] = item_obj.quantidade

        return res

    def _get_calcula_custo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            vr_custo = D(item_obj.vr_produtos or 0)
            vr_custo += D(item_obj.vr_frete or 0)
            vr_custo += D(item_obj.vr_seguro or 0)
            vr_custo += D(item_obj.vr_outras or 0)
            vr_custo -= D(item_obj.vr_desconto or 0)
            vr_custo += D(item_obj.vr_ipi or 0)
            vr_custo += D(item_obj.vr_simples or 0)

            if item_obj.forca_recalculo_st_compra:
                vr_custo += D(item_obj.vr_icms_st_compra or 0)
            else:
                vr_custo += D(item_obj.vr_icms_st or 0)

            vr_custo += D(item_obj.vr_ii or 0)
            vr_custo += D(item_obj.vr_diferencial_aliquota or 0)
            vr_custo += D(item_obj.vr_diferencial_aliquota_st or 0)

            #
            # Crédito de ICMS para compra do ativo imobilizado é recebido em 48 ×
            # por isso, como a empresa pode não receber esse crédito de fato,
            # não considera o abatimento do crédito na formação do custo
            #
            if item_obj.credita_icms_proprio and item_obj.cfop_id.codigo not in ['1551', '2551']:
                vr_custo -= D(item_obj.vr_icms_proprio or 0)
                vr_custo -= D(item_obj.vr_icms_sn or 0)

            #if item_obj.credita_icms_st:
                #vr_custo -= D(item_obj.vr_icms_st or 0)
            if item_obj.credita_ipi:
                vr_custo -= D(item_obj.vr_ipi or 0)
            if item_obj.credita_pis_cofins:
                vr_custo -= D(item_obj.vr_pis_proprio or 0)
                vr_custo -= D(item_obj.vr_cofins_proprio or 0)

            if item_obj.documento_id.vr_produtos is not None \
                and item_obj.documento_id.vr_produtos > 0 \
                and item_obj.vr_produtos is not None \
                and item_obj.vr_produtos > 0:
                proporcao_item = D(item_obj.vr_produtos or 0) / D(item_obj.documento_id.vr_produtos or 0)
            else:
                proporcao_item = D('0')

            vr_frete_rateio = D('0')
            vr_seguro_rateio = D('0')
            vr_outras_rateio = D('0')
            vr_desconto_rateio = D('0')

            #
            # Ajusta o rateio dos valores avulsos
            #
            if item_obj.documento_id.vr_frete_rateio:
                vr_frete_rateio = D(item_obj.documento_id.vr_frete_rateio or 0) * proporcao_item
                vr_custo += vr_frete_rateio
            if item_obj.documento_id.vr_seguro_rateio:
                vr_seguro_rateio = D(item_obj.documento_id.vr_seguro_rateio or 0) * proporcao_item
                vr_custo += vr_seguro_rateio
            if item_obj.documento_id.vr_desconto_rateio:
                vr_desconto_rateio = D(item_obj.documento_id.vr_desconto_rateio or 0) * proporcao_item
                vr_custo -= vr_desconto_rateio
            if item_obj.documento_id.vr_outras_rateio:
                vr_outras_rateio = D(item_obj.documento_id.vr_outras_rateio or 0) * proporcao_item
                vr_custo += vr_outras_rateio

            vr_custo = vr_custo.quantize(D('0.01'))

            if item_obj.quantidade_estoque:
                vr_unitario_custo = vr_custo / D(item_obj.quantidade_estoque or 0)
                vr_unitario_custo = vr_unitario_custo.quantize(D('0.0000000001'))
            else:
                vr_unitario_custo = D('0')

            if nome_campo == 'vr_custo':
                res[item_obj.id] = vr_custo
            elif nome_campo == 'vr_unitario_custo':
                res[item_obj.id] = vr_unitario_custo
            elif nome_campo == 'vr_frete_rateio':
                res[item_obj.id] = vr_frete_rateio
            elif nome_campo == 'vr_seguro_rateio':
                res[item_obj.id] = vr_seguro_rateio
            elif nome_campo == 'vr_outras_rateio':
                res[item_obj.id] = vr_outras_rateio
            elif nome_campo == 'vr_desconto_rateio':
                res[item_obj.id] = vr_desconto_rateio

        return res

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', required=True, ondelete='cascade', select=True),
        'company_id': fields.related('documento_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=True, select=True),
        'regime_tributario': fields.related('documento_id', 'regime_tributario', type='char', string=u'Regime tributário', store=True, select=True),
        'emissao': fields.related('documento_id', 'emissao', type='char', string=u'Tipo de emissão', store=True, select=True),
        'numero': fields.related('documento_id', 'numero', type='integer', string=u'Número'),
        'operacao_id': fields.related('documento_id', 'operacao_id', type='many2one', string=u'Operação fiscal', relation='sped.operacao', store=True, select=True),
        #'participante_id': fields.related('documento_id', 'participante_id', type='many2one', string=u'Participante', relation='sped.participante'),
        'partner_id': fields.related('documento_id', 'partner_id', type='many2one', string=u'Destinatário/remetente', relation='res.partner', store=True, select=True),
        'data_emissao': fields.related('documento_id', 'data_emissao_brasilia', type='date', string=u'Data de emissão', store=True, select=True),
        'modelo': fields.related('documento_id', 'modelo', type='char', string=u'Modelo', store=True, select=True),

        'cfop_id': fields.many2one('sped.cfop', u'CFOP', ondelete='restrict', select=True),
        'compoe_total': fields.boolean(u'Compõe o valor total da NF-e?', select=True),
        'movimentacao_fisica': fields.boolean(u'Há movimentação física do produto?'),

        # Dados do produto/serviço
        'produto_id': fields.many2one('product.product', u'Produto/Serviço', ondelete='restrict', select=True),
        'uom_id': fields.related('produto_id', 'uom_id', type='many2one', relation='product.uom', string=u'Unidade', select=True),
        'quantidade': CampoQuantidade(u'Quantidade'),
        # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
        'vr_unitario': CampoValorUnitario(u'Valor unitário'),

        # Quantidade de tributação
        'quantidade_tributacao': CampoQuantidade(u'Quantidade para tributação'),
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': CampoValorUnitario(u'Valor unitário para tributação'),

        # Valor total dos produtos
        'vr_produtos': CampoDinheiro(u'Valor do produto/serviço'),
        'vr_produtos_tributacao': CampoDinheiro(u'Valor do produto/serviço para tributação'),

        # Outros valores acessórios
        'vr_frete': CampoDinheiro(u'Valor do frete'),
        'vr_seguro': CampoDinheiro(u'Valor do seguro'),
        'vr_desconto': CampoDinheiro(u'Valor do desconto'),
        'vr_outras': CampoDinheiro(u'Outras despesas acessórias'),
        'vr_operacao': CampoDinheiro(u'Valor da operação'),
        'vr_operacao_tributacao': CampoDinheiro(u'Valor da operação para tributação'),

        #
        # ICMS próprio
        #
        'contribuinte': fields.related('partner_id', 'contribuinte', type='char', string=u'Contribuinte', store=False, select=True),
        'org_icms': fields.selection(ORIGEM_MERCADORIA, u'Origem da mercadoria', select=True),
        'cst_icms': fields.selection(ST_ICMS, u'Situação tributária do ICMS', select=True),
        'partilha': fields.boolean(u'Partilha de ICMS entre estados (CST 10 ou 90)?'),
        'al_bc_icms_proprio_partilha': CampoPorcentagem(u'% da base de cálculo da operação própria'),
        'uf_partilha_id': fields.many2one('sped.estado', u'Estado para o qual é devido o ICMS ST', select=True),
        'repasse': fields.boolean(u'Repasse de ICMS retido anteriosvente entre estados (CST 41)?', select=True),
        'md_icms_proprio': fields.selection(MODALIDADE_BASE_ICMS_PROPRIO, u'Modalidade da base de cálculo do ICMS próprio'),
        'pr_icms_proprio': CampoQuantidade(u'Parâmetro do ICMS próprio'),
        'rd_icms_proprio': CampoPorcentagem(u'% de redução da base de cálculo do ICMS próprio'),
        'bc_icms_proprio_com_ipi': fields.boolean('IPI integra a base do ICMS próprio?'),
        'bc_icms_proprio': CampoDinheiro(u'Base do ICMS próprio'),
        'al_icms_proprio': CampoPorcentagem(u'alíquota do ICMS próprio'),
        'vr_icms_proprio': CampoDinheiro(u'valor do ICMS próprio'),

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': fields.selection(ST_ICMS_SN, u'Situação tributária do ICMS - Simples Nacional', select=True),
        'al_icms_sn': CampoPorcentagem(u'Alíquota do crédito de ICMS'),
        'rd_icms_sn': CampoPorcentagem(u'% estadual de redução da alíquota de ICMS'),
        'vr_icms_sn': CampoDinheiro(u'valor do crédito de ICMS - SIMPLES Nacional'),
        'al_simples': CampoDinheiro(u'Alíquota do SIMPLES Nacional'),
        'vr_simples': CampoDinheiro(u'Valor do SIMPLES Nacional'),

        #
        # ICMS ST
        #
        'md_icms_st': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo do ICMS ST'),
        'pr_icms_st': CampoQuantidade(u'Parâmetro do ICMS ST'),
        'rd_icms_st': CampoPorcentagem(u'% de redução da base de cálculo do ICMS ST'),
        'bc_icms_st_com_ipi': fields.boolean(u'IPI integra a base do ICMS ST?'),
        'bc_icms_st': CampoDinheiro(u'Base do ICMS ST'),
        'al_icms_st': CampoPorcentagem(u'Alíquota do ICMS ST'),
        'vr_icms_st': CampoDinheiro(u'Valor do ICMS ST'),

        #
        # Parâmetros relativos ao ICMS retido anteriosvente por substituição tributária
        # na origem
        #
        'md_icms_st_retido': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo'),
        'pr_icms_st_retido': CampoQuantidade(u'Parâmetro da base de cáculo'),
        'rd_icms_st_retido': CampoPorcentagem(u'% de redução da base de cálculo do ICMS retido'),
        'bc_icms_st_retido': CampoDinheiro(u'Base do ICMS ST retido na origem'),
        'al_icms_st_retido': CampoPorcentagem(u'Alíquota do ICMS ST retido na origem'),
        'vr_icms_st_retido': CampoDinheiro(u'Valor do ICMS ST retido na origem'),

        #
        # IPI padrão
        #
        'apuracao_ipi': fields.selection(APURACAO_IPI, u'Período de apuração do IPI', select=True),
        'cst_ipi': fields.selection(ST_IPI, u'Situação tributária do IPI', select=True),
        'md_ipi': fields.selection(MODALIDADE_BASE_IPI, u'Modalidade de cálculo do IPI'),
        'bc_ipi': CampoDinheiro(u'Base do IPI'),
        'al_ipi': CampoQuantidade(u'Alíquota do IPI'),
        'vr_ipi': CampoDinheiro(u'Valor do IPI'),

        #
        # Imposto de importação
        #
        'bc_ii': CampoDinheiro(u'Base do imposto de importação'),
        'vr_despesas_aduaneiras': CampoDinheiro(u'Despesas aduaneiras'),
        'vr_ii': CampoDinheiro(u'Valor do imposto de importação'),
        'vr_iof': CampoDinheiro(u'Valor do IOF'),
        'numero_fci': fields.char('Nº controle FCI', size=36),

        #
        # PIS próprio
        #
        'al_pis_cofins_id': fields.many2one('sped.aliquotapiscofins', u'Alíquota e CST do PIS-COFINS', select=True),
        'cst_pis': fields.selection(ST_PIS, u'Situação tributária do PIS', select=True),
        'md_pis_proprio': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS próprio'),
        'bc_pis_proprio': CampoDinheiro(u'Base do PIS próprio'),
        'al_pis_proprio': CampoQuantidade(u'Alíquota do PIS próprio'),
        'vr_pis_proprio': CampoDinheiro(u'Valor do PIS próprio'),

        #
        # COFINS própria
        #
        'cst_cofins': fields.selection(ST_COFINS, u'Situação tributária da COFINS', select=True),
        'md_cofins_proprio': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS própria'),
        'bc_cofins_proprio': CampoDinheiro(u'Base do COFINS próprio'),
        'al_cofins_proprio': CampoQuantidade(u'Alíquota da COFINS própria'),
        'vr_cofins_proprio': CampoDinheiro(u'Valor do COFINS próprio'),

        #
        # PIS ST
        #
        'md_pis_st': fields.selection(MODALIDADE_BASE_PIS, u'Modalidade de cálculo do PIS ST'),
        'bc_pis_st': CampoDinheiro(u'Base do PIS ST'),
        'al_pis_st': CampoQuantidade(u'Alíquota do PIS ST'),
        'vr_pis_st': CampoDinheiro(u'Valor do PIS ST'),

        #
        # COFINS ST
        #
        'md_cofins_st': fields.selection(MODALIDADE_BASE_COFINS, u'Modalidade de cálculo da COFINS ST'),
        'bc_cofins_st': CampoDinheiro(u'Base do COFINS ST'),
        'al_cofins_st': CampoQuantidade(u'Alíquota da COFINS ST'),
        'vr_cofins_st': CampoDinheiro(u'Valor do COFINS ST'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': CampoDinheiro(u'Valor dos serviços'),

        # ISS
        'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS', select=True),
        'bc_iss': CampoDinheiro(u'Base do ISS'),
        'al_iss': CampoDinheiro(u'Alíquota do ISS'),
        'vr_iss': CampoDinheiro(u'Valor do ISS'),

        # PIS e COFINS
        'vr_pis_servico': CampoDinheiro(u'PIS sobre serviços'),
        'vr_cofins_servico': CampoDinheiro(u'COFINS sobre serviços'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': CampoDinheiro(u'Valor da NF', required=True),
        'vr_fatura': CampoDinheiro(u'Valor da fatura'),
        'al_ibpt': CampoPorcentagem(u'Alíquota IBPT'),
        'vr_ibpt': CampoDinheiro(u'Valor IBPT'),

        # Previdência social
        'previdencia_retido': fields.boolean(u'INSS retido?', select=True),
        'bc_previdencia': CampoDinheiro(u'Base do INSS'),
        'al_previdencia': CampoPorcentagem(u'Alíquota do INSS'),
        'vr_previdencia': CampoDinheiro(u'Valor do INSS'),

        # Informações adicionais
        'infcomplementar': fields.text(u'Informações complementares'),

        #
        # Dados especiais para troca de informações entre empresas
        #
        'numero_pedido': fields.char(u'Número do pedido', size=15),
        'numero_item_pedido': fields.integer(u'Número do item pedido'),

        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),

        #
        # Campos para a validação das entradas
        #
        'produto_codigo': fields.char(u'Código do produto original', size=60, select=True),
        'produto_descricao': fields.char(u'Descrição do produto original', size=60, select=True),
        'produto_ncm': fields.char(u'NCM do produto original', size=60, select=True),
        'produto_codigo_barras': fields.char(u'Código de barras do produto original', size=60, select=True),
        'unidade': fields.char(u'Unidade do produto original', size=6, select=True),
        'unidade_tributacao': fields.char(u'Unidade de tributação do produto original', size=6, select=True),
        'fator_quantidade': fields.float(u'Fator de conversão da quantidade'),
        'quantidade_original': CampoQuantidade(u'Quantidade'),
        'quantidade_estoque': fields.function(_get_quantidade_estoque, type='float', string=u'Quantidade', store=False, digits=(18, 4)),
        'cfop_original_id': fields.many2one('sped.cfop', u'CFOP original', select=True),

        'credita_icms_proprio': fields.boolean(u'Credita ICMS próprio?', select=True),
        'credita_icms_st': fields.boolean(u'Credita ICMS ST?', select=True),
        'informa_icms_st': fields.boolean(u'Informa ICMS ST?', select=True),
        'credita_ipi': fields.boolean(u'Credita IPI?', select=True),
        'credita_pis_cofins': fields.boolean(u'Credita PIS-COFINS?', select=True),

        #
        # Campos para rateio de custo
        #
        'vr_frete_rateio': fields.function(_get_calcula_custo, type='float', string=u'Valor do frete', store=STORE_CUSTO, digits=(18, 2)),
        'vr_seguro_rateio': fields.function(_get_calcula_custo, type='float', string=u'Valor do seguro', store=STORE_CUSTO, digits=(18, 2)),
        'vr_outras_rateio': fields.function(_get_calcula_custo, type='float', string=u'Outras despesas acessórias', store=STORE_CUSTO, digits=(18, 2)),
        'vr_desconto_rateio': fields.function(_get_calcula_custo, type='float', string=u'Valor do desconto', store=STORE_CUSTO, digits=(18, 2)),
        'vr_unitario_custo': fields.function(_get_calcula_custo, type='float', string=u'Custo unitário', store=STORE_CUSTO, digits=(18, 4)),
        'vr_custo': fields.function(_get_calcula_custo, type='float', string=u'Custo', store=STORE_CUSTO, digits=(18, 2)),

        #
        # Parâmetros relativos ao ICMS ST compra
        # na origem
        #
        'forca_recalculo_st_compra': fields.boolean(u'Força recálculo do ST na compra?'),
        'md_icms_st_compra': fields.selection(MODALIDADE_BASE_ICMS_ST, u'Modalidade da base de cálculo'),
        'pr_icms_st_compra': CampoQuantidade(u'Parâmetro da base de cáculo'),
        'rd_icms_st_compra': CampoPorcentagem(u'% de redução da base de cálculo do ICMS compra'),
        'bc_icms_st_compra': CampoDinheiro(u'Base do ICMS ST compra'),
        'al_icms_st_compra': CampoPorcentagem(u'Alíquota do ICMS ST compra'),
        'vr_icms_st_compra': CampoDinheiro(u'Valor do ICMS ST compra'),
        'calcula_diferencial_aliquota': fields.boolean(u'Calcula diferencial de alíquota?'),
        'al_diferencial_aliquota': CampoPorcentagem(u'Alíquota diferencial ICMS próprio'),
        'vr_diferencial_aliquota': CampoDinheiro(u'Valor do diferencial de alíquota ICMS próprio'),
        'al_diferencial_aliquota_st': CampoPorcentagem(u'Alíquota diferencial ICMS ST'),
        'vr_diferencial_aliquota_st': CampoDinheiro(u'Valor do diferencial de alíquota ICMS ST'),
    }

    _defaults = {
        #
        # Campos replicados do documento, para o cálculo na emissão própria
        #
        # 'company_id': _get_company_id_padrao,
        'regime_tributario': _get_regime_tributario_padrao,
        # 'emissao': _get_emissao_padrao,
        # 'operacao_id': _get_operacao_id_padrao,
        # 'participante_id': _get_participante_id_padrao,
        # 'data_emissao': _get_data_emissao_padrao,

        'compoe_total': True,
        'movimentacao_fisica': True,

        # Dados do produto/serviço
        # 'produto': fields.many2one('sped.participante', u'Participante', required=True),
        'quantidade': D('1'),
        # 'unidade' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade'), related_name=u'fis_notafiscalitem_unidade', null=True, blank=True)
        'vr_unitario': D('0'),

        # Quantidade de tributação
        'quantidade_tributacao': D('1'),
        # 'unidade_tributacao' = models.ForeignKey('cadastro.Unidade', verbose_name=_(u'unidade para tributação'), related_name=u'fis_notafiscalitem_unidade_tributacao', blank=True, null=True)
        'vr_unitario_tributacao': D('0'),


        # Valor total dos produtos
        'vr_produtos': D('0'),

        # Outros valores acessórios
        'vr_frete': D('0'),
        'vr_seguro': D('0'),
        'vr_desconto': D('0'),
        'vr_outras': D('0'),

        #
        # ICMS próprio
        #
        'org_icms': ORIGEM_MERCADORIA_NACIONAL,
        'cst_icms': ST_ICMS_ISENTA,
        'partilha': False,
        'al_bc_icms_proprio_partilha': D('0'),
        # 'uf_partilha': ,
        'repasse': False,
        'md_icms_proprio': MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO,
        'pr_icms_proprio': D('0'),
        'rd_icms_proprio': D('0'),
        'bc_icms_proprio_com_ipi': False,
        'bc_icms_proprio': D('0'),
        'al_icms_proprio': D('0'),
        'vr_icms_proprio': D('0'),

        #
        # Parâmetros relativos ao ICMS Simples Nacional
        #
        'cst_icms_sn': ST_ICMS_SN_NAO_TRIBUTADA,
        'al_icms_sn': D('0'),
        'rd_icms_sn': D('0'),
        'vr_icms_sn': D('0'),

        #
        # ICMS ST
        #
        'md_icms_st': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms_st': D('0'),
        'rd_icms_st': D('0'),
        'bc_icms_st_com_ipi': False,
        'bc_icms_st': D('0'),
        'al_icms_st': D('0'),
        'vr_icms_st': D('0'),

        #
        # Parâmetros relativos ao ICMS retido anteriosvente por substituição tributária
        # na origem
        #
        'md_icms_st_retido': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms_st_retido': D('0'),
        'rd_icms_st_retido': D('0'),
        'bc_icms_st_retido': D('0'),
        'al_icms_st_retido': D('0'),
        'vr_icms_st_retido': D('0'),

        #
        # IPI padrão
        #
        'apuracao_ipi': APURACAO_IPI_MENSAL,
        'cst_ipi': ST_IPI_SAIDA_NAO_TRIBUTADA,
        'md_ipi': MODALIDADE_BASE_IPI_ALIQUOTA,
        'bc_ipi': D('0'),
        'al_ipi': D('0'),
        'vr_ipi': D('0'),

        #
        # Imposto de importação
        #
        'bc_ii': D('0'),
        'vr_despesas_aduaneiras': D('0'),
        'vr_ii': D('0'),
        'vr_iof': D('0'),

        #
        # PIS próprio
        #
        'cst_pis': ST_PIS_SEM_INCIDENCIA,
        'md_pis_proprio': MODALIDADE_BASE_PIS_ALIQUOTA,
        'bc_pis_proprio': D('0'),
        'al_pis_proprio': D('0'),
        'vr_pis_proprio': D('0'),

        #
        # PIS ST
        #
        'md_pis_st': MODALIDADE_BASE_PIS_ALIQUOTA,
        'bc_pis_st': D('0'),
        'al_pis_st': D('0'),
        'vr_pis_st': D('0'),

        #
        # COFINS própria
        #
        'cst_cofins': ST_COFINS_SEM_INCIDENCIA,
        'md_cofins_proprio': MODALIDADE_BASE_COFINS_ALIQUOTA,
        'bc_cofins_proprio': D('0'),
        'al_cofins_proprio': D('0'),
        'vr_cofins_proprio': D('0'),

        #
        # COFINS ST
        #
        'md_cofins_st': MODALIDADE_BASE_COFINS_ALIQUOTA,
        'bc_cofins_st': D('0'),
        'al_cofins_st': D('0'),
        'vr_cofins_st': D('0'),

        #
        # Totais dos itens (grupo ISS)
        #

        # Valor total dos serviços
        'vr_servicos': D('0'),

        # ISS
        # 'cst_iss': fields.selection(ST_ISS, u'Situação tributária do ISS'),
        'bc_iss': D('0'),
        'al_iss': D('0'),
        'vr_iss': D('0'),

        # PIS e COFINS
        'vr_pis_servico': D('0'),
        'vr_cofins_servico': D('0'),

        #
        # Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
        #
        'vr_nf': D('0'),
        'vr_fatura': D('0'),

        # Informações adicionais
        'infcomplementar': u'',

        #
        # Dados especiais para troca de informações entre empresas
        #
        'numero_pedido': u'',
        'numero_item_pedido': D('0'),

        'produto_codigo': u'',
        'produto_descricao': u'',
        'produto_ncm': u'',
        'produto_codigo_barras': u'',
        'unidade': u'',
        'unidade_tributacao': u'',
        'fator_quantidade': 1,
        'quantidade_original': D('0'),
        'quantidade_estoque': D('0'),
        'cfop_original_id': False,

        'credita_icms_proprio': False,
        'credita_icms_st': False,
        'informa_icms_st': False,
        'credita_ipi': False,
        'credita_pis_cofins': False,

        'vr_frete_rateio': D('0'),
        'vr_seguro_rateio': D('0'),
        'vr_desconto_rateio': D('0'),
        'vr_outras_rateio': D('0'),
        'vr_unitario_custo': D('0'),
        'vr_custo': D('0'),

        #
        # Parâmetros relativos ao ICMS ST compra
        #
        'forca_recalculo_st_compra': False,
        'md_icms_st_compra': MODALIDADE_BASE_ICMS_ST_PAUTA,
        'pr_icms_st_compra': D('0'),
        'rd_icms_st_compra': D('0'),
        'bc_icms_st_compra': D('0'),
        'al_icms_st_compra': D('0'),
        'vr_icms_st_compra': D('0'),
        'calcula_diferencial_aliquota': False,
        'al_diferencial_aliquota': D('0'),
        'vr_diferencial_aliquota': D('0')
    }

    def onchange_fator_quantidade(self, cr, uid, ids, quantidade, fator_quantidade, context={}):
        if not quantidade:
            return {}

        if not fator_quantidade:
            return {}

        ret = {}
        valores = {}
        ret['value'] = valores

        valores['quantidade_estoque'] = quantidade * fator_quantidade

        return ret

    def calcula_remoto(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('sped.documentoitem')
        nota_pool = self.pool.get('sped.documento')

        notas = []
        for id in ids:
            item_obj = item_pool.browse(cr, uid, id)
            nota_obj = item_obj.documento_id

            if nota_obj.id not in notas:
                notas.append(nota_obj.id)

            dados = {
                'company_id': nota_obj.company_id.id,
                'modelo': nota_obj.modelo,
                'emissao': nota_obj.emissao,
                'data_emissao': nota_obj.data_emissao,
                'data_entrada_saida': nota_obj.data_entrada_saida,
                'partner_id': nota_obj.partner_id.id,
                'operacao_id': nota_obj.operacao_id.id,
                'entrada_saida': nota_obj.entrada_saida,
                'regime_tributario': nota_obj.regime_tributario,
            }

            contexto_item = copy(dados)
            for chave in dados:
                if 'default_' not in chave:
                    contexto_item['default_' + chave] = dados[chave]

            dados_item = item_obj.onchange_produto(item_obj.produto_id.id, context=contexto_item)
            dados = dados_item['value']

            item_obj.write(dados)
            item_obj = item_pool.browse(cr, uid, id)

            dados_item = item_obj.onchange_calcula_item(item_obj.regime_tributario, item_obj.emissao, item_obj.operacao_id, item_obj.partner_id, item_obj.data_emissao, item_obj.modelo, item_obj.cfop_id, item_obj.compoe_total, item_obj.movimentacao_fisica, item_obj.produto_id, item_obj.quantidade, item_obj.vr_unitario, item_obj.quantidade_tributacao, item_obj.vr_unitario_tributacao, item_obj.vr_produtos, item_obj.vr_produtos_tributacao, item_obj.vr_frete, item_obj.vr_seguro, item_obj.vr_desconto, item_obj.vr_outras, item_obj.vr_operacao, item_obj.vr_operacao_tributacao, item_obj.org_icms, item_obj.cst_icms, item_obj.partilha, item_obj.al_bc_icms_proprio_partilha, item_obj.uf_partilha_id, item_obj.repasse, item_obj.md_icms_proprio, item_obj.pr_icms_proprio, item_obj.rd_icms_proprio, item_obj.bc_icms_proprio_com_ipi, item_obj.bc_icms_proprio, item_obj.al_icms_proprio, item_obj.vr_icms_proprio, item_obj.cst_icms_sn, item_obj.al_icms_sn, item_obj.rd_icms_sn, item_obj.vr_icms_sn, item_obj.md_icms_st, item_obj.pr_icms_st, item_obj.rd_icms_st, item_obj.bc_icms_st_com_ipi, item_obj.bc_icms_st, item_obj.al_icms_st, item_obj.vr_icms_st, item_obj.md_icms_st_retido, item_obj.pr_icms_st_retido, item_obj.rd_icms_st_retido, item_obj.bc_icms_st_retido, item_obj.al_icms_st_retido, item_obj.vr_icms_st_retido, item_obj.apuracao_ipi, item_obj.cst_ipi, item_obj.md_ipi, item_obj.bc_ipi, item_obj.al_ipi, item_obj.vr_ipi, item_obj.bc_ii, item_obj.vr_despesas_aduaneiras, item_obj.vr_ii, item_obj.vr_iof, item_obj.al_pis_cofins_id, item_obj.cst_pis, item_obj.md_pis_proprio, item_obj.bc_pis_proprio, item_obj.al_pis_proprio, item_obj.vr_pis_proprio, item_obj.cst_cofins, item_obj.md_cofins_proprio, item_obj.bc_cofins_proprio, item_obj.al_cofins_proprio, item_obj.vr_cofins_proprio, item_obj.md_pis_st, item_obj.bc_pis_st, item_obj.al_pis_st, item_obj.vr_pis_st, item_obj.md_cofins_st, item_obj.bc_cofins_st, item_obj.al_cofins_st, item_obj.vr_cofins_st, item_obj.vr_servicos, item_obj.cst_iss, item_obj.bc_iss, item_obj.al_iss, item_obj.vr_iss, item_obj.vr_pis_servico, item_obj.vr_cofins_servico, item_obj.vr_nf, item_obj.vr_fatura, item_obj.al_ibpt, item_obj.vr_ibpt, item_obj.previdencia_retido, item_obj.bc_previdencia, item_obj.al_previdencia, item_obj.vr_previdencia, item_obj.forca_recalculo_st_compra, item_obj.md_icms_st_compra, item_obj.pr_icms_st_compra, item_obj.rd_icms_st_compra, item_obj.bc_icms_st_compra, item_obj.al_icms_st_compra, item_obj.vr_icms_st_compra, item_obj.calcula_diferencial_aliquota, item_obj.al_diferencial_aliquota, item_obj.vr_diferencial_aliquota, item_obj.al_simples, item_obj.vr_simples, context=contexto_item)
            dados = dados_item['value']
            item_obj.write(dados)




        for id in notas:
            nota_pool.ajusta_impostos_retidos(cr, uid, [id])
            nota_pool.action_gera_danfe(cr, uid, [id])

        return True

    def write(self, cr, uid, ids, dados, context={}):
        if 'contribuinte' in dados:
            del dados['contribuinte']

        res = super(sped_documentoitem, self).write(cr, uid, ids, dados, context=context)

        return res


sped_documentoitem()

