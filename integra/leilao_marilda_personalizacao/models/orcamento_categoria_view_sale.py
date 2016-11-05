# -*- coding: utf-8 -*-


CABECALHO_FORM = u'''<?xml version="1.0"?>
<group string="categoria_order_line" position="replace">
'''

RODAPE_FORM = u'''
</group>'''

CORPO_FORM = u'''
    <group string="{categoria_nome}" colspan="10">
        <field name="{nome_campo}" colspan="10" nolabel="1" widget="one2many_list" mode="tree,form" attrs="{{'readonly': [('state', '!=', 'draft')]}}" context="{{'default_orcamento_categoria_id': {categoria_id} }}">
            <form string="{categoria_nome}">
                <field name="state" invisible="1"/>
                <field name="autoinsert" invisible="1"/>
                <field name="orcamento_categoria_id" invisible="1" />
                <group colspan="4">
                    <field name="aprovado"/>
                    <field colspan="4"
                            domain="['|', ('orcamento_categoria_id.id', '=', {categoria_id}), ('orcamento_categoria_id', '=', False)]"
                            context="{{'default_orcamento_categoria_id': {categoria_id},                                    'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True}}"
                            name="product_id" required="1"
                            on_change="product_id_change(parent.pricelist_id,product_id,qty=product_uom_qty,partner_id=parent.partner_id, date_order=parent.date_order,context=context,comissao=comissao)"/>
                    <newline />
                    <field name="name"/>
                    <field name="product_packaging"
                            context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                            domain="[('product_id','=',product_id)]" groups="base.group_extended"
                            colspan="3" invisible="1" />
                    <newline/>
                    <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}"
                        name="product_uom_qty"
                        on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, qty=product_uom_qty, partner_id=parent.partner_id, date_order=parent.date_order, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=discount, autoinsert=autoinsert, mudou_quantidade=True, usa_unitario_minimo=usa_unitario_minimo, context=context, comissao=comissao)"/>
                    <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                            nolabel="1" invisible="1" />
                    <newline/>
                    <field name="vr_unitario_custo" readonly="0" invisible="1" />
                    <field name="vr_total_custo" invisible="1" />
                    <field name="vr_unitario_minimo" readonly="0" invisible="1" />
                    <field name="usa_unitario_minimo" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, qty=product_uom_qty, partner_id=parent.partner_id, date_order=parent.date_order, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=discount, autoinsert=autoinsert, mudou_quantidade=False, usa_unitario_minimo=usa_unitario_minimo, context=context, comissao=comissao)" invisible="1" />
                    <field name="vr_unitario_venda" />
                    <newline/>
                    <field name="margem" string="Margem (R$)" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, qty=product_uom_qty, partner_id=parent.partner_id, date_order=parent.date_order, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=discount, autoinsert=autoinsert, mudou_quantidade=True, usa_unitario_minimo=usa_unitario_minimo, context=context, comissao=comissao)"/>
                    <field name="comissao_venda_id" invisible="1" />
                    <field name="comissao_locacao_id" invisible="1" />
                    <newline/>
                    <field name="discount" string="Desconto (R$)" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, qty=product_uom_qty, partner_id=parent.partner_id, date_order=parent.date_order, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=discount, autoinsert=autoinsert, mudou_quantidade=True, usa_unitario_minimo=usa_unitario_minimo, context=context, comissao=comissao)"/>
                    <newline/>
                    <field name="price_unit" readonly="0" invisible="1" />
                    <newline/>
                    <field name="price_subtotal" invisible="1" />
                    <newline />
                    <field name="comissao" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, qty=product_uom_qty, partner_id=parent.partner_id, date_order=parent.date_order, vr_unitario_custo=vr_unitario_custo, vr_unitario_minimo=vr_unitario_minimo, vr_unitario_venda=vr_unitario_venda, margem=margem, desconto=discount, autoinsert=autoinsert, mudou_quantidade=True, usa_unitario_minimo=usa_unitario_minimo, context=context, comissao=comissao)" />
                    <newline />
                    <field name="vr_comissao" />
                </group>
                <field name="type" invisible="1" />
                <field name="delay" invisible="1" />
                <field name="th_weight" invisible="1" />
                <field name="address_allotment_id" invisible="1" />
                <field name="property_ids" colspan="4" nolabel="1" invisible="1" />
            </form>
            <tree string="{categoria_nome}" editable="top">
                    <field name="orcamento_categoria_id" invisible="1" />
                    <field name="autoinsert" invisible="1"/>
                    <field name="state" invisible="1"/>
                    <field name="aprovado"/>
                    <field name="sequence"/>
                    <field
                           domain="['|', ('orcamento_categoria_id.id', '=', {categoria_id}), ('orcamento_categoria_id', '=', False)]"
                           context="{{'default_orcamento_categoria_id': {categoria_id},
                           'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom, 'force_product_uom': True}}"
                           name="product_id"
                           on_change="product_id_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, True, parent.date_order, product_packaging, parent.fiscal_position, False, context)"/>
                    <field name="name" invisible="0"/>
                    <field name="product_packaging"
                           context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}" on_change="product_packaging_change(parent.pricelist_id, product_id, product_uom_qty, product_uom, parent.partner_id, product_packaging, True, context)"
                           domain="[('product_id','=',product_id)]" groups="base.group_extended"
                           invisible="1"/>
                    <field context="{{'partner_id':parent.partner_id, 'quantity':product_uom_qty, 'pricelist':parent.pricelist_id, 'shop':parent.shop_id, 'uom':product_uom}}"
                           name="product_uom_qty"
                           on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, True, usa_unitario_minimo, context, desconto_direto=True, margem_direta=True)"/>
                    <field name="product_uom" on_change="product_uom_change(parent.pricelist_id,product_id,product_uom_qty,product_uom,product_uos_qty,product_uos,name,parent.partner_id, False, False, parent.date_order, context)"
                           nolabel="1" invisible="1"/>
                    <field groups="product.group_uos" name="product_uos_qty" string="Qty(UoS)" invisible="1" />
                    <field groups="product.group_uos" name="product_uos" string="UoS" invisible="1" />
                    <field name="vr_unitario_custo" readonly="0" invisible="1" />
                    <field name="vr_total_custo" invisible="1" />
                    <field name="vr_unitario_minimo" invisible="1" readonly="0" />
                    <field name="vr_total_minimo" invisible="1" readonly="0" sum="Mínimo" />
                    <field name="usa_unitario_minimo" invisible="1" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context)" />
                    <field name="vr_unitario_venda" readonly="0" />
                    <field name="margem" invisible="0" string="Margem (R$)" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context, desconto_direto=True, margem_direta=True)"/>
                    <field name="discount" invisible="0" string="Desconto (R$)" on_change="on_change_quantidade_margem_desconto(parent.pricelist_id, product_id, product_uom_qty, product_uom, product_uos_qty, product_uos, name, parent.partner_id, False, False, parent.date_order, product_packaging, parent.fiscal_position, False, vr_unitario_custo, vr_unitario_minimo, vr_unitario_venda, margem, discount, autoinsert, False, usa_unitario_minimo, context, desconto_direto=True, margem_direta=True)"/>
                    <field name="price_unit" invisible="1" />
                    <field name="price_subtotal" sum="Subtotal" invisible="1" />
                    <field name="vr_unitario_margem_desconto" invisible="1" />
                    <field name="vr_total_margem_desconto" sum="Subtotal" />
                    <field name="comissao" readonly="0"/>
                    <field name="vr_comissao" sum="Comissao" readonly="0"/>
                    <field name="comissao_venda_id" invisible="1" />
                    <field name="comissao_locacao_id" invisible="1" />
            </tree>
        </field>
    </group>
'''
