# -*- coding: utf-8 -*-


CABECALHO_FORM = u'''<?xml version="1.0"?>
<group string="categoria_order_line" position="replace">
'''

RODAPE_FORM = u'''
</group>'''

CORPO_FORM = u'''
    <group string="{categoria_nome}" colspan="10">
        <field name="{nome_campo}" colspan="10" nolabel="1" widget="one2many_list" mode="tree,form" attrs="{{'readonly': [('state', '=', 'done')]}}" context="{{'default_orcamento_categoria_id': {categoria_id}, 'company_id': company_id, 'orcamento_aprovado': orcamento_aprovado, 'default_usa_unitario_minimo': bonificacao_venda, 'operacao_fiscal_produto_id': operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': operacao_fiscal_servico_id}}">
            <form string="{categoria_nome}">
                    <field name="orcamento_categoria_id" invisible="1" />
                    <field name="autoinsert" invisible="1"/>
                    <field name="state" invisible="1"/>
                    <field name="sequence" string="Ordem do item na proposta" />
                    <field colspan="4"
                           domain="['|', ('orcamento_categoria_id.id', '=', {categoria_id}), ('orcamento_categoria_id', '=', False)]"
                           context="{{'default_orcamento_categoria_id': {categoria_id},
                           'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id, 'orcamento_aprovado': parent.orcamento_aprovado}}"
                           name="product_id" required="1"
                           on_change="product_id_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, True, parent.date_order, product_packaging, parent.fiscal_position, False, context)"/>
                    <field name="name" invisible="0" colspan="4" />
                    <field name="product_packaging"
                           context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                           domain="[('product_id','=',product_id)]" groups="base.group_extended"
                           invisible="1"/>
                    <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}"
                           name="product_uom_qty"
                           on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, True, usa_unitario_minimo, context)"/>
                    <newline />
                    <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                           nolabel="1" invisible="1"/>
                    <field groups="product.group_uos" name="product_uos_qty" string="Qty(UoS)" invisible="1" />
                    <field groups="product.group_uos" name="product_uos" string="UoS" invisible="1" />
                    <field name="vr_unitario_custo" readonly="0" invisible="1" groups="base.group_sale_manager" />
                    <field name="tela_vr_unitario_custo" readonly="1" invisible="0" groups="base.group_sale_manager" />
                    <field name="vr_total_custo" invisible="1" groups="base.group_sale_manager" />
                    <field name="tela_vr_total_custo" readonly="1" invisible="0" groups="base.group_sale_manager" />
                    <field name="vr_unitario_minimo" readonly="0" invisible="1" string="Unitário mín. p/ locação" />
                    <field name="tela_vr_unitario_minimo" readonly="1" string="Unitário mín. p/ locação" />
                    <field name="vr_total_minimo" readonly="0" sum="Mínimo" string="Total mín. p/ locação" invisible="1" />
                    <field name="tela_vr_total_minimo" readonly="1" sum="Mínimo" string="Total mín. p/ locação" />
                    <field name="usa_unitario_minimo" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}" />
                    <newline />
                    <field name="vr_unitario_venda" readonly="0" invisible="1" groups="base.group_sale_manager" />
                    <newline />
                    <field name="margem" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}" />
                    <field name="discount" string="Desconto" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id, 'proporcao_imposto': proporcao_imposto}}" />
                    <group colspan="4" col="1">
                        <html>
                            <button type="button">Aplica margem e desconto</button>
                        </html>
                    </group>
                    <newline />
                    <field name="price_unit" groups="base.group_sale_manager" invisible="1" />
                    <newline />
                    <field name="price_subtotal" sum="Subtotal" groups="base.group_sale_manager" invisible="1" />
                    <field name="vr_unitario_margem_desconto" groups="base.group_sale_manager" invisible="1" />
                    <field name="vr_total_margem_desconto" sum="Subtotal" groups="base.group_sale_manager" invisible="1" />
                    <field name="total_imposto" string="Impostos R$" groups="base.group_sale_manager" invisible="1" />
                    <field name="porcentagem_imposto" string="Impostos %" groups="base.group_sale_manager" invisible="1" />
                    <field name="proporcao_imposto" string="Impostos % embut." groups="base.group_sale_manager" invisible="1" />
                    <field name="vr_unitario_venda_impostos" string="Unitário venda" invisible="1" />
                    <field name="tela_vr_unitario_venda_impostos" string="Unitário venda" readonly="1" />
                    <field name="vr_total_venda_impostos" sum="Subtotal" string="Total venda" invisible="1" />
                    <field name="tela_vr_total_venda_impostos" sum="Subtotal" string="Total venda" readonly="1" />
                    <field name="comissao" readonly="0" invisible="1" />
                    <field name="vr_comissao" sum="Comissao" invisible="1" />
                    <field name="tela_vr_comissao" sum="Comissao" readonly="1" invisible="1" />
                    <field name="comissao_venda_id" invisible="1" />
                    <field name="comissao_locacao_id" invisible="1" />
                    <field name="falha_configuracao" readonly="1" invisible="1" />

<!--                    <field name="regime_tributario" invisible="1"/>
                    <field name="emissao" invisible="1"/>
                    <field name="operacao_id" invisible="1"/>
                    <field name="data_emissao" invisible="1"/>
                    <field name="modelo" invisible="1"/>
                     <field name="cfop_id" invisible="1"/>
                    <field name="compoe_total" invisible="1"/>
                    <field name="movimentacao_fisica" invisible="1"/> -->
                    <field name="quantidade" invisible="1"/>
                    <field name="vr_unitario" invisible="1"/>
                    <field name="quantidade_tributacao" invisible="1"/>
                    <field name="vr_unitario_tributacao" invisible="1"/>
                    <field name="vr_produtos" invisible="1"/>
                    <field name="vr_produtos_tributacao" invisible="1"/>
                    <field name="vr_frete" invisible="1"/>
                    <field name="vr_seguro" invisible="1"/>
                    <field name="vr_desconto" invisible="1"/>
                    <field name="vr_outras" invisible="1"/>
                    <field name="vr_operacao" invisible="1"/>
                    <field name="vr_operacao_tributacao" invisible="1"/>
                    <field name="cst_icms" invisible="1"/>
                    <field name="al_icms_proprio" invisible="1"/>
                    <field name="vr_icms_proprio" invisible="1"/>
                    <field name="cst_icms_sn" invisible="1"/>
                    <field name="al_icms_sn" invisible="1"/>
                    <field name="rd_icms_sn" invisible="1"/>
                    <field name="vr_icms_sn" invisible="1"/>
                    <field name="al_icms_st" invisible="1"/>
                    <field name="vr_icms_st" invisible="1"/>
                    <field name="al_ipi" invisible="1"/>
                    <field name="vr_ipi" invisible="1"/>
                    <field name="al_pis_cofins_id" invisible="1"/>
                    <field name="cst_pis" invisible="1"/>
                    <field name="al_pis_proprio" invisible="1"/>
                    <field name="vr_pis_proprio" invisible="1"/>
                    <field name="cst_cofins" invisible="1"/>
                    <field name="al_cofins_proprio" invisible="1"/>
                    <field name="vr_cofins_proprio" invisible="1"/>
                    <field name="al_iss" invisible="1"/>
                    <field name="vr_iss" invisible="1"/>
                    <field name="calcula_diferencial_aliquota" invisible="1"/>
                    <field name="al_diferencial_aliquota" invisible="1"/>
                    <field name="vr_diferencial_aliquota" invisible="1"/>
            </form>
            <tree string="{categoria_nome}" colors="red: (not vr_total_venda_impostos) or (vr_total_venda_impostos &lt;= 0);blue:crm_meeting_id">
                    <field name="orcamento_categoria_id" invisible="1" />
                    <field name="crm_meeting_id" invisible="1"/>
                    <field name="autoinsert" invisible="1"/>
                    <field name="state" invisible="1"/>
                    <field name="sequence" string="Ordem" />
                    <field
                           domain="['|', ('orcamento_categoria_id.id', '=', {categoria_id}), ('orcamento_categoria_id', '=', False)]"
                           context="{{'default_orcamento_categoria_id': {categoria_id},
                           'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id, 'orcamento_aprovado': parent.orcamento_aprovado}}"
                           name="product_id"
                           on_change="product_id_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, True, parent.date_order, product_packaging, parent.fiscal_position, False, context)"/>
                    <field name="name" invisible="0"/>
                    <field name="product_packaging"
                           context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                           domain="[('product_id','=',product_id)]" groups="base.group_extended"
                           invisible="1"/>
                    <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}"
                           name="product_uom_qty"
                           on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, True, usa_unitario_minimo, context)"/>
                    <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                           nolabel="1" invisible="1"/>
                    <field groups="product.group_uos" name="product_uos_qty" string="Qty(UoS)" invisible="1" />
                    <field groups="product.group_uos" name="product_uos" string="UoS" invisible="1" />
                    <field name="vr_unitario_custo" readonly="0" invisible="1" groups="base.group_sale_manager" />
                    <field name="tela_vr_unitario_custo" readonly="1" invisible="0" groups="base.group_sale_manager" />
                    <field name="vr_total_custo" invisible="1" groups="base.group_sale_manager" />
                    <field name="tela_vr_total_custo" readonly="1" invisible="0" groups="base.group_sale_manager" />
                    <field name="vr_unitario_minimo" readonly="0" invisible="1" string="Unitário mín. p/ locação" />
                    <field name="tela_vr_unitario_minimo" readonly="1" string="Unitário mín. p/ locação" />
                    <field name="vr_total_minimo" readonly="0" sum="Mínimo" string="Total mín. p/ locação" invisible="1" />
                    <field name="tela_vr_total_minimo" readonly="1" sum="Mínimo" string="Total mín. p/ locação" />
                    <field name="usa_unitario_minimo" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}" />
                    <field name="vr_unitario_venda" readonly="0" invisible="0" groups="base.group_sale_manager" />
                    <field name="margem" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}" />
                    <field name="discount" string="Desconto" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'operacao_fiscal_produto_id': parent.operacao_fiscal_produto_id, 'operacao_fiscal_servico_id': parent.operacao_fiscal_servico_id, 'company_id': parent.company_id}}" />
                    <field name="price_unit" invisible="0" groups="base.group_sale_manager" />
                    <field name="price_subtotal" sum="Subtotal" invisible="1" groups="base.group_sale_manager" />
                    <field name="vr_unitario_margem_desconto" invisible="0"  groups="base.group_sale_manager" />
                    <field name="vr_total_margem_desconto" sum="Subtotal" invisible="0"  groups="base.group_sale_manager" />
                    <field name="total_imposto" string="Impostos R$" groups="base.group_sale_manager" />
                    <field name="porcentagem_imposto" string="Impostos %" groups="base.group_sale_manager" />
                    <field name="proporcao_imposto" string="Impostos % embut." groups="base.group_sale_manager" />
                    <field name="vr_unitario_venda_impostos" string="Unitário venda" invisible="1" />
                    <field name="tela_vr_unitario_venda_impostos" string="Unitário venda" readonly="1" />
                    <field name="vr_total_venda_impostos" sum="Subtotal" string="Total venda" invisible="1" />
                    <field name="tela_vr_total_venda_impostos" sum="Subtotal" string="Total venda" readonly="1" />
                    <field name="comissao" readonly="0" invisible="1" />
                    <field name="vr_comissao" sum="Comissao" invisible="1" />
                    <field name="tela_vr_comissao" sum="Comissao" readonly="1" invisible="1" />
                    <field name="comissao_venda_id" invisible="1" />
                    <field name="comissao_locacao_id" invisible="1" />
                    <field name="falha_configuracao" readonly="1" />

<!--                    <field name="regime_tributario" invisible="1"/>
                    <field name="emissao" invisible="1"/>
                    <field name="operacao_id" invisible="1"/>
                    <field name="data_emissao" invisible="1"/>
                    <field name="modelo" invisible="1"/>
                     <field name="cfop_id" invisible="1"/>
                    <field name="compoe_total" invisible="1"/>
                    <field name="movimentacao_fisica" invisible="1"/> -->
                    <field name="quantidade" invisible="1"/>
                    <field name="vr_unitario" invisible="1"/>
                    <field name="quantidade_tributacao" invisible="1"/>
                    <field name="vr_unitario_tributacao" invisible="1"/>
                    <field name="vr_produtos" invisible="1"/>
                    <field name="vr_produtos_tributacao" invisible="1"/>
                    <field name="vr_frete" invisible="1"/>
                    <field name="vr_seguro" invisible="1"/>
                    <field name="vr_desconto" invisible="1"/>
                    <field name="vr_outras" invisible="1"/>
                    <field name="vr_operacao" invisible="1"/>
                    <field name="vr_operacao_tributacao" invisible="1"/>
                    <field name="cst_icms" invisible="1"/>
                    <field name="al_icms_proprio" invisible="1"/>
                    <field name="vr_icms_proprio" invisible="1"/>
                    <field name="cst_icms_sn" invisible="1"/>
                    <field name="al_icms_sn" invisible="1"/>
                    <field name="rd_icms_sn" invisible="1"/>
                    <field name="vr_icms_sn" invisible="1"/>
                    <field name="al_icms_st" invisible="1"/>
                    <field name="vr_icms_st" invisible="1"/>
                    <field name="al_ipi" invisible="1"/>
                    <field name="vr_ipi" invisible="1"/>
                    <field name="al_pis_cofins_id" invisible="1"/>
                    <field name="cst_pis" invisible="1"/>
                    <field name="al_pis_proprio" invisible="1"/>
                    <field name="vr_pis_proprio" invisible="1"/>
                    <field name="cst_cofins" invisible="1"/>
                    <field name="al_cofins_proprio" invisible="1"/>
                    <field name="vr_cofins_proprio" invisible="1"/>
                    <field name="al_iss" invisible="1"/>
                    <field name="vr_iss" invisible="1"/>
                    <field name="calcula_diferencial_aliquota" invisible="1"/>
                    <field name="al_diferencial_aliquota" invisible="1"/>
                    <field name="vr_diferencial_aliquota" invisible="1"/>
            </tree>
        </field>
    </group>
'''
