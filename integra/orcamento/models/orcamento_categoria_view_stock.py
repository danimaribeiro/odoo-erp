# -*- coding: utf-8 -*-


CABECALHO_FORM = u'''<?xml version="1.0"?>
<form string="Delivery Orders">
    <group col="6" colspan="4">
        <group colspan="4" col="4">
            <field name="name" readonly="1"/>
            <field name="origin" readonly="1"/>
            <field name="address_id" on_change="onchange_partner_in(address_id)" context="{'contact_display':'partner'}" colspan="4"/>
            <field name="invoice_state"/>
            <field name="backorder_id" readonly="1" groups="base.group_extended"/>
        </group>
        <group colspan="2" col="2">
            <field name="date"/>
            <field name="min_date" readonly="1"/>
            <field name="stock_journal_id" groups="base.group_extended" widget="selection"/>
        </group>
    </group>
    <notebook colspan="4">
        <page string="Products">
            <field colspan="4" name="move_lines" nolabel="1" widget="one2many_list" context="{'address_out_id': address_id, 'picking_type': type}" invisible="1">
                <tree colors="grey:scrapped==True" string="Stock Moves">
                    <field name="product_id"/>
                    <field name="product_qty" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)"/>
                    <field name="product_uom" string="UoM"/>
                    <field name="product_uos" groups="product.group_uos"/>
                    <button name="%(stock.move_scrap)d" string="Scrap Products" type="action" icon="gtk-convert" context="{'scrap': True}" states="draft,waiting,confirmed,assigned"/>
                    <field name="scrapped" invisible="1"/>
                    <field name="prodlot_id" groups="base.group_extended"/>
                    <button name="%(track_line)d" string="Split in production lots" type="action" icon="terp-stock_effects-object-colorize" attrs="{'invisible': [('prodlot_id','&lt;&gt;',False)]}" states="draft,assigned,confirmed" groups="base.group_extended"/>
                    <field name="tracking_id" groups="base.group_extended"/>
                    <button name="setlast_tracking" string="Put in current pack" type="object" attrs="{'invisible': [('tracking_id','&lt;&gt;',False)]}" groups="base.group_extended" icon="terp-stock_effects-object-colorize" states="draft,assigned,confirmed"/>
                    <button name="%(split_into)d" string="Put in a new pack" type="action" icon="terp-stock_effects-object-colorize" groups="base.group_extended" states="draft,assigned,confirmed"/>
                    <field name="location_id"/>
                    <field name="date"/>
                    <field name="state"/>
                    <button name="%(action_partial_move_server)d" string="Process" type="action" states="confirmed,assigned" icon="gtk-go-forward"/>
                </tree>
                <form string="Stock Moves">
                    <group colspan="2" col="4">
                        <separator colspan="4" string="Move Information"/>
                        <field name="name" invisible="0" colspan="4"/>
                        <field name="product_id" on_change="onchange_product_id(product_id,location_id,location_dest_id, parent.address_id)" colspan="4"/>
                        <field name="product_qty" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)" colspan="3"/>
                        <button name="%(stock.move_scrap)d" string="Scrap" type="action" icon="gtk-convert" context="{'scrap': True}" states="draft,waiting,confirmed,assigned" colspan="1" groups="base.group_extended"/>
                        <field name="product_uom" string="Unit Of Measure" colspan="4"/>
                        <field name="product_uos_qty" groups="product.group_uos" on_change="onchange_uos_quantity(product_id, product_uos_qty, product_uos, product_uom)" colspan="4"/>
                        <field groups="product.group_uos" name="product_uos" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)" colspan="4"/>
                        <field groups="base.group_extended" name="product_packaging" domain="[('product_id','=',product_id)]" colspan="4"/>
                    </group>

                    <group colspan="2" col="2">
                        <separator string="Locations" colspan="2"/>
                        <field name="location_id" domain="[('usage','=','internal')]"/>
                        <field name="location_dest_id" domain="[('usage','&lt;&gt;','view')]"/>
                    </group>

                    <group colspan="2" col="2">
                        <separator string="Dates" colspan="2"/>
                        <field name="create_date" invisible="1"/>
                        <field name="date"/>
                        <field name="date_expected" on_change="onchange_date(date,date_expected)"/>
                    </group>

                    <group colspan="2" col="4" groups="base.group_extended">
                        <separator string="Traceability" colspan="4" groups="base.group_extended"/>
                        <field name="tracking_id" groups="base.group_extended" colspan="3"/>
                          <button name="%(split_into)d" string="New pack" type="action" groups="base.group_extended" icon="terp-stock_effects-object-colorize" states="draft,assigned,confirmed" colspan="1"/>
                        <field name="prodlot_id" groups="base.group_extended" context="{'location_id':location_id, 'product_id':product_id}" domain="[('product_id','=?',product_id)]" on_change="onchange_lot_id(prodlot_id,product_qty, location_id, product_id, product_uom)" colspan="3"/>
                        <button name="%(track_line)d" groups="base.group_extended" states="draft,waiting,confirmed,assigned" string="Split" type="action" icon="terp-stock_effects-object-colorize" colspan="1"/>
                    </group>
                    <label string="" colspan="4"/>
                    <field name="state"/>
                    <group col="4" colspan="2">
                        <button name="action_cancel" states="assigned" string="Cancel" type="object" icon="gtk-cancel"/>
                        <button name="action_confirm" states="draft" string="Confirm" type="object" icon="gtk-apply"/>
                        <button name="force_assign" states="confirmed" string="Force Availability" type="object" icon="gtk-jump-to"/>
                        <button name="cancel_assign" states="assigned" string="Cancel Availability" type="object" icon="gtk-find"/>
                    </group>
                </form>
            </field>
'''

RODAPE_FORM = u'''
            <group col="12" colspan="4">
                <field name="state" readonly="1" widget="statusbar" statusbar_visible="draft,confirmed,assigned,done" statusbar_colors="{&quot;auto&quot;:&quot;blue&quot;, &quot;confirmed&quot;:&quot;blue&quot;}"/>
                <button name="button_cancel" states="assigned,confirmed,draft" string="_Cancel" icon="gtk-cancel"/>
                <button name="draft_force_assign" states="draft" string="Process Later" type="object" icon="gtk-ok"/>
                <button name="draft_validate" states="draft" string="Process Now" type="object" icon="gtk-yes"/>
                <button name="action_assign" states="confirmed" string="Check Availability" type="object" groups="base.group_extended" icon="gtk-find"/>
                <button name="force_assign" states="confirmed" string="Force Availability" type="object" icon="gtk-jump-to"/>
                <button name="action_process" states="assigned" string="Process" type="object" icon="gtk-go-forward"/>
                <button name="%(act_stock_return_picking)d" string="Return Products" states="done" type="action" icon="gtk-execute"/>
                <button name="%(action_stock_invoice_onshipping)d" string="Create Invoice" attrs="{'invisible': ['|','|',('state','&lt;&gt;','done'),('invoice_state','=','invoiced'),('invoice_state','=','none')]}" type="action" icon="terp-gtk-go-back-rtl"/>
            </group>
        </page>
        <page string="Additional info" groups="base.group_extended,base.group_multi_company">
            <field name="auto_picking" groups="base.group_extended"/>
            <field name="date_done" groups="base.group_extended"/>
            <field name="move_type" groups="base.group_extended"/>
            <field name="type" groups="base.group_extended"/>
            <field name="company_id" groups="base.group_multi_company" widget="selection"/>
        </page>
        <page string="Notes">
            <field colspan="4" name="note" nolabel="1"/>
        </page>
    </notebook>
</form>'''


CORPO_FORM = u'''
            <group string="{categoria_nome}" colspan="10">
                <field colspan="4" name="{nome_campo}" nolabel="1" widget="one2many_list" context="{{'address_out_id': address_id, 'picking_type': type}}">
                    <tree colors="grey:scrapped==True" string="Stock Moves">
                        <field name="product_id"/>
                        <field name="product_qty" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)"/>
                        <field name="product_uom" string="UoM"/>
                        <field name="product_uos" groups="product.group_uos"/>
                        <button name="357" string="Scrap Products" type="action" icon="gtk-convert" context="{{'scrap': True}}" states="draft,waiting,confirmed,assigned"/>
                        <field name="scrapped" invisible="1"/>
                        <field name="prodlot_id" groups="base.group_extended"/>
                        <button name="358" string="Split in production lots" type="action" icon="terp-stock_effects-object-colorize" attrs="{{'invisible': [('prodlot_id','&lt;&gt;',False)]}}" states="draft,assigned,confirmed" groups="base.group_extended"/>
                        <field name="tracking_id" groups="base.group_extended"/>
                        <button name="setlast_tracking" string="Put in current pack" type="object" attrs="{{'invisible': [('tracking_id','&lt;&gt;',False)]}}" groups="base.group_extended" icon="terp-stock_effects-object-colorize" states="draft,assigned,confirmed"/>
                        <button name="366" string="Put in a new pack" type="action" icon="terp-stock_effects-object-colorize" groups="base.group_extended" states="draft,assigned,confirmed"/>
                        <field name="location_id"/>
                        <field name="date"/>
                        <field name="state"/>
                        <button name="361" string="Process" type="action" states="confirmed,assigned" icon="gtk-go-forward"/>
                    </tree>
                    <form string="Stock Moves">
                        <group colspan="2" col="4">
                            <separator colspan="4" string="Move Information"/>
                            <field name="name" invisible="0" colspan="4"/>
                            <field name="product_id" on_change="onchange_product_id(product_id,location_id,location_dest_id, parent.address_id)" colspan="4" domain="[('orcamento_categoria_id.id', '=', {categoria_id})]" context="{{'default_orcamento_categoria_id': {categoria_id}}}" />
                            <field name="product_qty" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)" colspan="3"/>
                            <button name="357" string="Scrap" type="action" icon="gtk-convert" context="{{'scrap': True}}" states="draft,waiting,confirmed,assigned" colspan="1" groups="base.group_extended"/>
                            <field name="product_uom" string="Unit Of Measure" colspan="4"/>
                            <field name="product_uos_qty" groups="product.group_uos" on_change="onchange_uos_quantity(product_id, product_uos_qty, product_uos, product_uom)" colspan="4"/>
                            <field groups="product.group_uos" name="product_uos" on_change="onchange_quantity(product_id, product_qty, product_uom, product_uos)" colspan="4"/>
                            <field groups="base.group_extended" name="product_packaging" domain="[('product_id','=',product_id)]" colspan="4"/>
                        </group>

                        <group colspan="2" col="2">
                            <separator string="Locations" colspan="2"/>
                            <field name="location_id" domain="[('usage','=','internal')]"/>
                            <field name="location_dest_id" domain="[('usage','&lt;&gt;','view')]"/>
                        </group>

                        <group colspan="2" col="2">
                            <separator string="Dates" colspan="2"/>
                            <field name="create_date" invisible="1"/>
                            <field name="date"/>
                            <field name="date_expected" on_change="onchange_date(date,date_expected)"/>
                        </group>

                        <group colspan="2" col="4" groups="base.group_extended">
                            <separator string="Traceability" colspan="4" groups="base.group_extended"/>
                            <field name="tracking_id" groups="base.group_extended" colspan="3"/>
                              <button name="366" string="New pack" type="action" groups="base.group_extended" icon="terp-stock_effects-object-colorize" states="draft,assigned,confirmed" colspan="1"/>
                            <field name="prodlot_id" groups="base.group_extended" context="{{'location_id':location_id, 'product_id':product_id}}" domain="[('product_id','=?',product_id)]" on_change="onchange_lot_id(prodlot_id,product_qty, location_id, product_id, product_uom)" colspan="3"/>
                            <button name="358" groups="base.group_extended" states="draft,waiting,confirmed,assigned" string="Split" type="action" icon="terp-stock_effects-object-colorize" colspan="1"/>
                        </group>
                        <label string="" colspan="4"/>
                        <field name="state"/>
                        <group col="4" colspan="2">
                            <button name="action_cancel" states="assigned" string="Cancel" type="object" icon="gtk-cancel"/>
                            <button name="action_confirm" states="draft" string="Confirm" type="object" icon="gtk-apply"/>
                            <button name="force_assign" states="confirmed" string="Force Availability" type="object" icon="gtk-jump-to"/>
                            <button name="cancel_assign" states="assigned" string="Cancel Availability" type="object" icon="gtk-find"/>
                        </group>
                    </form>
                </field>
            </group>
'''
