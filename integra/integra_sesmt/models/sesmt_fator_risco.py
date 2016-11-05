# -*- coding: utf-8 -*-


from osv import fields, osv
from integra_sesmt.constante_sesmt import *


class sesmt_fator_risco(osv.Model):
    _name = 'sesmt.fator_risco'
    _description = u'Fatores de risco'
    _rec_name = 'nome'
    _order = 'nome'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}
        #txt = u''
        #for registro in self.browse(cursor, user_id, ids):
            #txt = registro.codigo #+ ' - Entrando às ' + registro.ocupacao

            #if registro.hora_saida_intervalo_1 and registro.hora_retorno_intervalo_1:
                #txt += u', 1º interv. de ' + float_time(registro.hora_saida_intervalo_1)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_1)[:5]

            #if registro.hora_saida_intervalo_2 and registro.hora_retorno_intervalo_2:
                #txt += u', 2º interv. de ' + float_time(registro.hora_saida_intervalo_2)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_2)[:5]

            #if registro.hora_saida_intervalo_3 and registro.hora_retorno_intervalo_3:
                #txt += u', 3º interv. de ' + float_time(registro.hora_saida_intervalo_3)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_3)[:5]

            #if registro.hora_saida_intervalo_4 and registro.hora_retorno_intervalo_4:
                #txt += u', 4º interv. de ' + float_time(registro.hora_saida_intervalo_4)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_4)[:5]

            #if registro.hora_saida_intervalo_5 and registro.hora_retorno_intervalo_5:
                #txt += u', 5º interv. de ' + float_time(registro.hora_saida_intervalo_5)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_5)[:5]

            #retorno[registro.id] = txt

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #('codigo', 'like', texto)
        #]
        #return procura

    _columns = {
        'tipo': fields.selection(TIPO_FATOR_RISCO, u'Tipo', select=True),
        'data_inicial': fields.date(u'Data inicial', required=True, select=True),
        'data_final': fields.date(u'Data final', select=True),
        'nome': fields.char(u'Descrição', size=50, select=True, required=True),
        'comprometimento_saude_id': fields.many2one('sesmt.comprometimento_saude', u'Comprometimento da saúde'),
        'comprometimento_saude_texto': fields.text(u'Comprometimento da saúde'),
        'fonte_geradora_id': fields.many2one('sesmt.fonte_geradora', u'Fonte geradora'),
        'fonte_geradora_texto': fields.text(u'Fonte geradora'),
        'meio_propagacao_id': fields.many2one('sesmt.meio_propagacao', u'Meio de propagação'),
        'meio_propagacao_texto': fields.text(u'Meio de propagação'),
        'dano_saude_id': fields.many2one('sesmt.dano_saude', u'Danos à saúde'),
        'dano_saude_texto': fields.text(u'Danos à saúde'),
        'medida_controle_id': fields.many2one('sesmt.medida_controle', u'Medidas de controle'),
        'medida_controle_texto': fields.text(u'Medidas de controle'),
        'recomendacao_id': fields.many2one('sesmt.recomendacao', u'Recomendações'),
        'recomendacao_texto': fields.text(u'Recomendações'),
        'obs': fields.text(u'Observações'),

        'fator_risco_epi_ids': fields.one2many('sesmt.fator_risco_epi', 'fator_risco_id', u'EPIs'),
    }

    _defaults = {
    }

sesmt_fator_risco()


class sesmt_fator_risco_epi(osv.Model):
    _name = 'sesmt.fator_risco_epi'
    _description = u'EPIs para os Fatores de risco'

    _columns = {
        'fator_risco_id': fields.many2one('sesmt.fator_risco', u'Fator de risco', ondelete='cascade', select=True),
        'epi_id': fields.many2one('sesmt.epi', u'EPI', ondelete='restrict'),
        'eficaz': fields.boolean(u'O EPI é eficaze?'),
        'treinamento': fields.boolean(u'Treinamentos realizados?'),
        'ficha': fields.boolean(u'Fichas de entrega preenchidas e assinadas?'),
        'conclusao_ppra': fields.text(u'Conclusão PPRA'),
        'conclusao_ltcat': fields.text(u'Conclusão LTCAT'),
    }

    _defaults = {
        'eficaz': True,
        'treinamento': True,
        'ficha': True,
    }


sesmt_fator_risco_epi()