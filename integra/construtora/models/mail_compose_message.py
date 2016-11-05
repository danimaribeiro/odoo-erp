# -*- coding: utf-8 -*-

from osv import osv, fields
from const_imovel import TIPO_IMOVEL_DIC
from pybrasil.data import formata_data
from pybrasil.valor import formata_valor


class mail_compose_message(osv.osv_memory):
    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    _columns = {
        'tipo_negociacao': fields.selection([('P', u'Proposta'), ('C', u'Contraproposta')], u'Tipo de negociação'),
        'valor': fields.float(u'Valor'),
    }

    _defaults = {
        'tipo_negociacao': 'P',
    }

    def get_value(self, cr, uid, model, res_id, context=None):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'finan.contrato':
            contrato_obj = self.pool.get('finan.contrato').browse(cr, uid, res_id)

            if contrato_obj.natureza == 'RI':
                res['email_to'] = contrato_obj.vendedor_id.user_email

                email_cc = ''

                for agenciador_obj in contrato_obj.imovel_id.agenciador_ids:
                    if not agenciador_obj.email:
                        continue

                    if email_cc:
                        email_cc += ','

                    email_cc += agenciador_obj.email

                res['email_cc'] = email_cc

                assunto = contrato_obj.partner_id.name
                assunto += u' comprando '
                assunto += TIPO_IMOVEL_DIC[contrato_obj.imovel_id.tipo]
                assunto += u' cód. '
                assunto += contrato_obj.imovel_id.codigo or ''

                if contrato_obj.imovel_id.municipio_id:
                    assunto += ' em '
                    assunto += contrato_obj.imovel_id.municipio_id.nome
                    assunto += '-'
                    assunto += contrato_obj.imovel_id.municipio_id.estado

                    if contrato_obj.imovel_id.bairro:
                        assunto += ', '
                        assunto += contrato_obj.imovel_id.bairro

                res['subject'] = assunto

                url = u'Acesso direto à proposta:\n'
                url += contrato_obj.get_url_compartilhamento() or ''

                body = u'\n\n'
                body += url

                if len(contrato_obj.negociacao_ids):
                    body = u'\n\nHistórico de negociações:\n'
                    for negociacao_obj in contrato_obj.negociacao_ids:
                        body += formata_data(negociacao_obj.date)
                        body += ' - '
                        if negociacao_obj.tipo_negociacao == 'P':
                            body += 'proposta de R$ '
                            body += formata_valor(negociacao_obj.valor or 0)
                            body += '\n'
                        else:
                            body += 'contraproposta de R$ '
                            body += formata_valor(negociacao_obj.valor or 0)
                            body += '\n'

                    texto_anterior = u''
                    for negociacao_obj in contrato_obj.negociacao_ids:
                        texto_anterior = '\n' + (negociacao_obj.body_text or '') + '\n' + texto_anterior
                        texto_anterior = texto_anterior.replace(url, '')
                        texto_anterior = texto_anterior.replace('\n', '\n>')

                    if texto_anterior:
                        body += '\n' + texto_anterior

                res['body_text'] = body

        return res


mail_compose_message()
