# -*- coding: utf-8 -*-

from osv import fields, osv
from pybrasil.data import dia_util_pagamento
from datetime import date
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta


class hr_sefip(osv.Model):
    _name = 'hr.sefip'
    _inherit = 'hr.sefip'

    _columns = {
        'lancamento_inss_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do INSS', select=True, ondelete='restrict'),
        'lancamento_inss_judicial_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do INSS', select=True, ondelete='restrict'),
        'lancamento_fgts_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do FGTS', select=True, ondelete='restrict'),
        'lancamento_fgts_menor_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do FGTS menor aprendiz', select=True, ondelete='restrict'),
        'lancamento_irpf_id': fields.many2one('finan.lancamento', u'Lançamento financeiro do IRPF', select=True, ondelete='restrict'),
    }

    def fecha_arquivo(self, cr, uid, ids, context={}):
        super(hr_sefip, self).fecha_arquivo(cr, uid, ids, context=context)

    def _gera_lancamento_impostos(self, cr, uid, ids, context={}, rubrica='INSS', aliquota_fgts=8, judicial=False):
        rubrica_pool = self.pool.get('hr.salary.rule')
        documento_pool = self.pool.get('finan.documento')
        lancamento_pool = self.pool.get('finan.lancamento')
        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        rubrica_ids = rubrica_pool.search(cr, 1, [('code', '=', rubrica)])
        rubrica_obj = rubrica_pool.browse(cr, 1, rubrica_ids[0])

        #
        # Rubricas, de acordo com o tributo
        #
        if rubrica == 'INSS':
            doc_rubrica_id = documento_pool.id_inss(cr, 1)

        elif rubrica == 'FGTS':
            doc_rubrica_id = documento_pool.id_fgts(cr, 1)

        elif rubrica == 'IRPF':
            doc_rubrica_id = documento_pool.id_irpf(cr, 1)

        for sefip_obj in self.browse(cr, uid, ids):
            dados = {
                'tipo': 'P',
                'data_documento': sefip_obj.data[:10],
                'company_id': sefip_obj.company_id.id,
                'partner_id': sefip_obj.company_id.partner_id.id,
                'documento_id': doc_rubrica_id,
                'provisionado': False,
                'conta_id': rubrica_obj.finan_conta_despesa_id.id,
                'valor_documento': sefip_obj.vr_inss_empresa,
                'numero_documento': rubrica + '-' + str(sefip_obj.id).zfill(4),
            }

            #
            # Rubricas, de acordo com o tributo
            #
            lanc_id = False
            lanc_obj = None
            if rubrica == 'INSS':
                dados['data_vencimento'] = sefip_obj.data_recolhimento_gps
                if judicial:
                    dados['valor_documento'] = sefip_obj.vr_inss_rat
                    dados['numero_documento'] = rubrica + 'JUD-' + str(sefip_obj.id).zfill(4)
                    if sefip_obj.lancamento_inss_judicial_id:
                        lanc_obj = sefip_obj.lancamento_inss_judicial_id
                        lanc_id = lanc_obj.id
                else:
                    if sefip_obj.lancamento_inss_id:
                        lanc_obj = sefip_obj.lancamento_inss_id
                        lanc_id = lanc_obj.id

            elif rubrica == 'FGTS':
                dados['numero_documento'] = rubrica + str(aliquota_fgts) + '%-' + str(sefip_obj.id).zfill(4)
                dados['data_vencimento'] = sefip_obj.data_recolhimento_fgts
                if aliquota_fgts == 8 and sefip_obj.lancamento_fgts_id:
                    lanc_obj = sefip_obj.lancamento_fgts_id
                    lanc_id = lanc_obj.id

                elif aliquota_fgts == 2 and sefip_obj.lancamento_fgts_menor_id:
                    lanc_obj = sefip_obj.lancamento_fgts_menor_id
                    lanc_id = lanc_obj.id

            elif rubrica == 'IRPF':
                company_obj = sefip_obj.company_id
                data_ref = date(sefip_obj.ano, int(sefip_obj.mes), 1)
                data_ref += relativedelta(months=+1)
                estado = company_obj.partner_id.estado or ''
                municipio = company_obj.partner_id.cidade or ''
                venc_irpf = date(data_ref.year, data_ref.month, 20)
                dados['data_vencimento'] = str(venc_irpf)

                if sefip_obj.lancamento_irpf_id:
                    lanc_obj = sefip_obj.lancamento_irpf_id
                    lanc_id = lanc_obj.id

            if lanc_id:
                lancamento_pool.write(cr, uid, [lanc_id], dados)
                lanc_obj = lancamento_pool.browse(cr, uid, lanc_id)
                for ro in lanc_obj.rateio_ids:
                    ro.unlink()

            else:
                lanc_id = lancamento_pool.create(cr, uid, dados)
                lanc_obj = lancamento_pool.browse(cr, uid, lanc_id)

                if rubrica == 'INSS':
                    if judicial:
                        sefip_obj.write({'lancamento_inss_judicial_id': lanc_id})
                    else:
                        sefip_obj.write({'lancamento_inss_id': lanc_id})
                elif rubrica == 'FGTS':
                    if aliquota_fgts == 8:
                        sefip_obj.write({'lancamento_fgts_id': lanc_id})
                    elif aliquota_fgts == 2:
                        sefip_obj.write({'lancamento_fgts_menor_id': lanc_id})

                elif rubrica == 'IRPF':
                    sefip_obj.write({'lancamento_irpf_id': lanc_id})

            #
            # Prepara agora o rateio
            #
            rateio = {}
            total_irpf = 0
            total_fgts = 0
            total_inss = 0
            for h_obj in sefip_obj.payslip_ids:
                if rubrica == 'FGTS':
                    if h_obj.aliquota_fgts == aliquota_fgts:
                        h_obj.realiza_rateio(rateio=rateio, campo_valor=rubrica)
                        total_fgts += h_obj.valor_fgts
                else:
                    h_obj.realiza_rateio(rateio=rateio, campo_valor=rubrica)
                    total_irpf += h_obj.valor_irpf
                    total_inss += h_obj.valor_inss

            if rubrica == 'INSS':
                if judicial:
                    valor_total = sefip_obj.vr_inss_rat
                else:
                    valor_total = sefip_obj.vr_inss_empresa

                if valor_total == 0:
                    if judicial:
                        sefip_obj.write({'lancamento_inss_judicial_id': False})
                    else:
                        sefip_obj.write({'lancamento_inss_id': False})

            elif rubrica == 'FGTS':
                valor_total = total_fgts

                if valor_total == 0:
                    if aliquota_fgts == 8:
                        sefip_obj.write({'lancamento_fgts_id': False})
                    elif aliquota_fgts == 2:
                        sefip_obj.write({'lancamento_fgts_menor_id': False})

            elif rubrica == 'IRPF':
                valor_total = total_irpf

                if valor_total == 0:
                    sefip_obj.write({'lancamento_irpf_id': False})

            if valor_total == 0:
                lancamento_pool.unlink(cr, uid, lanc_id)
                continue

            if rubrica == 'INSS':
                dados = cc_pool.monta_dados(rateio, campos, lista_dados=[], valor=total_inss, forcar_valor=valor_total)
            else:
                dados = cc_pool.monta_dados(rateio, campos, lista_dados=[], valor=valor_total)

            rateio_ids = []
            for d in dados:
                if d['valor_documento'] != 0 and d['porcentagem'] != 0:
                    rateio_ids += [(0, lanc_id, d)]

            lancamento_pool.write(cr, uid, [lanc_id], {'valor_documento': valor_total})
            lancamento_pool.write(cr, uid, [lanc_id], {'rateio_ids': rateio_ids})

        return True

    def gera_lancamento_impostos(self, cr, uid, ids, context={}):
        self._gera_lancamento_impostos(cr, uid, ids, context=context, rubrica='INSS')
        self._gera_lancamento_impostos(cr, uid, ids, context=context, rubrica='INSS', judicial=True)
        self._gera_lancamento_impostos(cr, uid, ids, context=context, rubrica='FGTS', aliquota_fgts=8)
        self._gera_lancamento_impostos(cr, uid, ids, context=context, rubrica='FGTS', aliquota_fgts=2)
        self._gera_lancamento_impostos(cr, uid, ids, context=context, rubrica='IRPF')

hr_sefip()
