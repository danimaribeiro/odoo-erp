# -*- coding: utf-8 -*-


CABECALHO_FORM = u'''<?xml version="1.0"?>
<group string="categoria_order_line" position="replace">
'''

RODAPE_FORM = u'''
</group>'''

CORPO_FORM = u'''
    <group string="{categoria_nome}" colspan="10">
        <field name="{nome_campo}" colspan="10" nolabel="1" widget="one2many_list" mode="tree,form" attrs="{{'readonly': [('state', '!=', 'draft')]}}">
            <form string="{categoria_nome}">
                <field name="state" invisible="1"/>
                <field name="autoinsert" invisible="1"/>
                <notebook>
                    <page string="Item">
                        <group colspan="4" col="5">
                            <field colspan="3"
                                   domain="[('orcamento_categoria_id.id', '=', {categoria_id})]"
                                   context="{{'default_orcamento_categoria_id': {categoria_id},                                    'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True}}"
                                   name="product_id"
                                   on_change="product_id_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, True, parent.date_order, product_packaging, parent.fiscal_position, False, context)"/>
                            <field name="name"/>
                            <field name="product_packaging"
                                   context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                                   domain="[('product_id','=',product_id)]" groups="base.group_extended"
                                   colspan="3" invisible="1" />
                            <newline/>
                            <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}"
                                name="product_uom_qty"
                                on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, True, usa_unitario_minimo, context)"/>
                            <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                                   nolabel="1"/>
                            <newline/>
                            <field name="vr_unitario_custo" readonly="1" />
                            <field name="vr_total_custo" invisible="1" />
                            <field name="vr_unitario_minimo" readonly="1" />
                            <field name="usa_unitario_minimo" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" />
                            <field name="vr_unitario_venda" readonly="1" />
                            <newline/>
                            <field name="margem" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)"/>
                            <field name="comissao_venda_id" invisible="1" />
                            <field name="comissao_locacao_id" invisible="1" />
                            <field name="discount" string="Desconto" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)"/>
                            <newline/>
                            <field name="price_unit" readonly="1" />
                            <field name="price_subtotal" />
                            <separator colspan="5" string="Notes"/>
                            <field colspan="5" name="notes" nolabel="1"/>
                            <!-- <separator colspan="5" string="Taxes"/>
                            <field colspan="5" name="tax_id" nolabel="1" domain="[('parent_id','=',False),('type_tax_use','&lt;&gt;','purchase')]"/>
                            -->
                            <group colspan="5" col="5" groups="base.group_extended">
                                <separator colspan="5" string="States"/>
                                <field name="state" widget="statusbar" statusbar_visible="draft,confirmed,done" statusbar_colors='{{"exception":"red","cancel":"red"}}'/>
                                <field name="invoiced"/>
                                <group attrs="{{'invisible':[('invoiced','=',True)]}}">
                                    <button colspan="1" name="%(sale.action_view_sale_order_line_make_invoice)d" states="confirmed" string="Make Invoices" type="action" icon="terp-document-new"/>
                                </group>
                            </group>
                        </group>
                    </page>
                    <page groups="base.group_extended" string="Extra Info">
                        <field name="type"/>
                        <field name="delay"/>
                        <field name="th_weight"/>
                        <field name="address_allotment_id"/>
                        <separator colspan="4" string="Properties"/>
                        <field name="property_ids" colspan="4" nolabel="1"/>
                    </page>
                    <page string="History" groups="base.group_extended">
                        <separator colspan="4" string="Invoice Lines"/>
                        <field colspan="4" name="invoice_lines" nolabel="1"/>
                        <separator colspan="4" string="Stock Moves"/>
                        <field colspan="4" name="move_ids" nolabel="1" widget="many2many"/>
                    </page>
                </notebook>
            </form>
            <tree string="{categoria_nome}" editable="top">
                    <field name="orcamento_categoria_id" invisible="1" />
                    <field name="autoinsert" invisible="1"/>
                    <field name="state" invisible="1"/>
                    <field name="sequence"/>
                    <field
                           domain="[('orcamento_categoria_id.id', '=', {categoria_id})]"
                           context="{{'default_orcamento_categoria_id': {categoria_id},
                           'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True}}"
                           name="product_id"
                           on_change="product_id_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, True, parent.date_order, product_packaging, parent.fiscal_position, False, context)"/>
                    <field name="name" invisible="1"/>
                    <field name="product_packaging"
                           context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                           domain="[('product_id','=',product_id)]" groups="base.group_extended"
                           invisible="1"/>
                    <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}"
                           name="product_uom_qty"
                           on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, True, usa_unitario_minimo, context)"/>
                    <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                           nolabel="1"/>
                    <field groups="product.group_uos" name="product_uos_qty" string="Qty(UoS)" invisible="1" />
                    <field groups="product.group_uos" name="product_uos" string="UoS" invisible="1" />
                    <field name="vr_unitario_custo" readonly="1" />
                    <field name="vr_total_custo" />
                    <field name="vr_unitario_minimo" readonly="1" />
                    <field name="usa_unitario_minimo" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" />
                    <field name="vr_unitario_venda" readonly="1" />
                    <field name="margem" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)"/>
                    <field name="discount" string="Desconto (%%)" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)"/>
                    <field name="price_unit" invisible="1" />
                    <field name="price_subtotal" sum="Subtotal" invisible="1" />
                    <field name="vr_total_margem_desconto" sum="Subtotal" />
                    <field name="comissao" readonly="1"/>
                    <field name="vr_comissao" sum="Comissao" readonly="1"/>
                    <field name="comissao_venda_id" invisible="1" />
                    <field name="comissao_locacao_id" invisible="1" />
            </tree>
        </field>
    </group>
'''
