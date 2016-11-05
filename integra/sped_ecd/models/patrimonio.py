# -*- encoding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv, fields



class account_asset_asset(osv.Model):
    _name = 'account.asset.asset'
    _inherit = 'account.asset.asset'   

    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lote', ondelete='restrict'),
    }
    
    #def write(self, cr, uid, ids, dados, context={}):
        
    #    for documento_obj in self.browse(cr, uid, ids):
    #        if documento_obj.lote_id:
    #            raise osv.except_osv(u'Inválido !', u'NF ja importado para contabildade! Lote: ' + str(documento_obj.lote_id.codigo)) 

    #    res = super(sped_documento, self).write(cr, uid, ids, dados, context)
        
    #    return res
    
    def unlink(self, cr, uid, ids, context={}):
        
        for patrimonio_obj in self.browse(cr, uid, ids):
            if patrimonio_obj.lote_id and patrimonio_obj.data_baixa:
                raise osv.except_osv(u'Não é possivel excluir !', u'Patrimonio ja Baixado na contabildade! Lote: ' + str(depreciacao_obj.lote_id.codigo)) 

        res = super(account_asset_asset, self).unlink(cr, uid, ids, context)
        
        return res
    
account_asset_asset()


class account_asset_category(osv.Model):
    _name = 'account.asset.category'
    _inherit = 'account.asset.category'   

    _columns = {
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),  
        'finan_conta_deprecicao': fields.many2one('finan.conta', u'C - Conta de Depreciação', ondelete='restrict', required=True),
        'finan_conta_deprecicao_despesa': fields.many2one('finan.conta', u'D - Depr.Contas de despesas ', ondelete='restrict', required=True),
        'finan_conta_baixa_ativo': fields.many2one('finan.conta', u'D - Conta Baixa do Patrimônio', ondelete='restrict', required=True),
        'finan_conta_ativo': fields.many2one('finan.conta', u'C - Conta do Patrimônio', ondelete='restrict', required=True),
        'finan_conta_depreciacao': fields.many2one('finan.conta', u'D - Conta de Depreciação', ondelete='restrict', required=True),
        'finan_conta_baixa_depreciacao': fields.many2one('finan.conta', u'C - Conta Baixa Depreciação', ondelete='restrict', required=True),
        'historico_id_depreciacao': fields.many2one('finan.historico',u'Cód.Hist', required=True, ondelete='restrict'),
        'historico_id_baixa_patrimonio': fields.many2one('finan.historico',u'Cód.Hist', required=True, ondelete='restrict'),
        'historico_id_baixa_depreciacao': fields.many2one('finan.historico',u'Cód.Hist', required=True, ondelete='restrict'),
    }

    _defaults = {
        
    }
    
account_asset_category()
    
class account_asset_depreciation_line(osv.osv):
    _name = 'account.asset.depreciation.line'
    _inherit = 'account.asset.depreciation.line'   

    
    _columns = {
        'lote_id': fields.many2one('lote.contabilidade',u'Lote'),
    }
    
    #def write(self, cr, uid, ids, dados, context={}):
        
    #    for documento_obj in self.browse(cr, uid, ids):
    #        if documento_obj.lote_id:
    #            raise osv.except_osv(u'Inválido !', u'NF ja importado para contabildade! Lote: ' + str(documento_obj.lote_id.codigo)) 

    #    res = super(sped_documento, self).write(cr, uid, ids, dados, context)
        
    #    return res
    
    def unlink(self, cr, uid, ids, context={}):
        
        for depreciacao_obj in self.browse(cr, uid, ids):
            if depreciacao_obj.lote_id:
                raise osv.except_osv(u'Inválido !', u'Despreciação ja importada para contabildade! Lote: ' + str(depreciacao_obj.lote_id.codigo)) 

        res = super(account_asset_depreciation_line, self).unlink(cr, uid, ids, context)
        
        return res

account_asset_depreciation_line()

