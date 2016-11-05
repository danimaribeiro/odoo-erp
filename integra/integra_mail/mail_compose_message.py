# -*- coding: utf-8 -*-

from osv import osv


class mail_compose_message(osv.osv_memory):
    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context=None):
        """Returns a defaults-like dict with initial values for the composition
           wizard when sending an email related to the document record identified
           by ``model`` and ``res_id``.

           The default implementation returns an empty dictionary, and is meant
           to be overridden by subclasses.

           :param str model: model name of the document record this mail is related to.
           :param int res_id: id of the document record this mail is related to.
           :param dict context: several context values will modify the behavior
                                of the wizard, cfr. the class description.
        """
        res = {}
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', model), ('res_id', '=', res_id)])
        if len(attachment_ids):
            res['attachment_ids'] = attachment_ids
        return res


mail_compose_message()