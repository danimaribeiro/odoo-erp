
def onchange_produto(self, cr, uid, ids, produto_id, context):
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

    if modelo == '57':
        return

    #
    # Vamos trazer todos os registros necessários
    #
    company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
    partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)
    operacao_obj = self.pool.get('sped.operacao').browse(cr, uid, operacao_id)
    produto_obj = self.pool.get('product.product').browse(cr, uid, produto_id)

    if not partner_obj.municipio_id:
        raise osv.except_osv(u'Erro!', u'O cliente “%s”, CNPJ/CPF “%s”, está sem o município preenchido!' % (partner_obj.name, partner_obj.cnpj_cpf))

    if municipio_fato_gerador_id:
        municipio_fato_gerador_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_fato_gerador_id)
    else:
        municipio_fato_gerador_obj = partner_obj.municipio_id

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
    if produto_obj.familiatributaria_id:
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

    print(uf_origem, uf_destino)
    dentro_estado = uf_origem == uf_destino
    fora_estado = uf_origem != uf_destino
    fora_pais = uf_destino == 'EX'

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
        elif fora_estado:
            mensagem += 'com CFOP para fora do estado!'
        else:
            mensagem += 'com CFOP para fora do país!'

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
        elif fora_estado:
            mensagem += 'com CFOP para fora do estado!'
        else:
            mensagem += 'com CFOP para fora do país!'

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
            if produto_obj.ncm_id:
                raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s” (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name, produto_obj.ncm_id.codigo))
            else:
                raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s” (produto “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name))

        familiatributaria_item_obj = self.pool.get('sped.familiatributariaitem').browse(cr, uid, lista_familiatributariaitem_ids[0])

        print('estado origem', familiatributaria_item_obj.estado_origem_id.uf)
        print('estado destin', familiatributaria_item_obj.estado_destino_id.uf)

        #
        # Agora que já encontramos, definimos os valores do item do documento
        # pelos valores do item da família tributária
        #
        if familiatributaria_item_obj.al_icms_proprio_id:
            if valores['org_icms'] in ORIGEM_MERCADORIA_ALIQUOTA_4 and uf_origem != uf_destino:
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
        if operacao_obj.calcula_diferencial_aliquota:
            #
            # Busca a alíquota padrão para dentro do estado
            #
            lista_familiatributariaitem_interna_ids = self.pool.get('sped.familiatributariaitem').search(
                cr,
                uid,
                [
                    ('familiatributaria_id', '=', familiatributaria_obj.id),
                    ('estado_origem_id.uf', '=', uf_destino),
                    ('estado_destino_id.uf', '=', uf_destino),
                    ('data_inicio', '<=', data_emissao),
                ], limit=1, order='data_inicio DESC')

            if not lista_familiatributariaitem_interna_ids:
                if produto_obj.ncm_id:
                    raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do diferencial de alíquota (produto “%s”, NCM “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name, produto_obj.ncm_id.codigo))
                else:
                    raise osv.except_osv(u'Erro!', u'Não há um item da família tributária “%s”, configurado do estado “%s” para o estado “%s”, para o cálculo do diferencial de alíquota (produto “%s”)' % (familiatributaria_obj.descricao, uf_origem, uf_destino, produto_obj.name))

            familiatributaria_item_interna_obj = self.pool.get('sped.familiatributariaitem').browse(cr, uid, lista_familiatributariaitem_interna_ids[0])
            al_diferencial_aliquota = (familiatributaria_item_interna_obj.al_icms_proprio_id.al_icms or 0)

            valores['al_diferencial_aliquota'] -= valores['al_icms_proprio']
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
        print(familiatributaria_item_obj.id, familiatributaria_item_obj.al_icms_st_id)
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
                    if mva_obj.estado_id.uf == uf_origem:
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
                        if mva_obj.estado_id.uf == uf_origem:
                            if valores['regime_tributario'] == REGIME_TRIBUTARIO_SIMPLES:
                                valores['pr_icms_st_compra'] = mva_obj.mva_simples or 0
                            else:
                                valores['pr_icms_st_compra'] = mva_obj.mva_normal or 0
                            break

        #if familiatributaria_item_obj.al_icms_st_retido_id:
                #valores['al_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.al_icms
                #valores['md_icms_st_retido'] = familiatributaria_item_obj.al_icms_st_retido_id.md_icms
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

    else:
        valores['credita_icms_proprio'] = True
        valores['informa_icms_st'] = True

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
            valores['cst_ipi'] = operacao_item_obj.cst_ipi

            if operacao_item_obj.cst_ipi in ST_IPI_CALCULA:
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
