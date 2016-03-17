# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Fernando Marcato Rodrigues
#    Copyright (C) 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import StringIO
from openerp import api, models, fields
from openerp.tools.translate import _
from .file_cnab240_parser import Cnab240Parser as cnabparser


_logger = logging.getLogger(__name__)


MODOS_IMPORTACAO_CNAB = [
    ('bradesco_pag_for', u'Bradesco PagFor 500'),
    ('bradesco_cobranca_240', u'Bradesco Cobrança 240'),
    ('itau_cobranca_240', u'Itaú Cobrança 240'),
    ('cef_cobranca_240', u'CEF Cobrança 240'),
]


class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    import_modes = fields.Selection(
        MODOS_IMPORTACAO_CNAB,
        string=u'Opções de importação', select=True, required=True)

    @api.model
    def _check_cnab(self, data_file):
        if cnabparser is None:
            return False
        try:
            cnab_file = cnabparser.parse(StringIO.StringIO(data_file))
        except:
            return False
        return cnab_file

    @api.model
    def _find_bank_account_id(self, account_number):
        """ Get res.partner.bank ID """
        bank_account_id = None
        if account_number:
            bank_account_ids = self.env['res.partner.bank'].search(
                [('acc_number', '=', str(account_number))], limit=1)
            if bank_account_ids:
                bank_account_id = bank_account_ids[0].id
        return bank_account_id

    @api.model
    def _complete_statement(self, stmt_vals, journal_id, account_number):
        """Complete statement from information passed.
            unique_import_id is assumed to already be unique at the moment of
            CNAB exportation."""
        stmt_vals['journal_id'] = journal_id
        for line_vals in stmt_vals['transactions']:
            unique_import_id = line_vals.get('unique_import_id', False)
            if unique_import_id:
                line_vals['unique_import_id'] = unique_import_id
            if not line_vals.get('bank_account_id'):
                # Find the partner and his bank account or create the bank
                # account. The partner selected during the reconciliation
                # process will be linked to the bank when the statement is
                # closed.
                partner_id = False
                bank_account_id = False
                partner_account_number = line_vals.get('account_number')
                if partner_account_number:
                    bank_model = self.env['res.partner.bank']
                    banks = bank_model.search(
                        [('acc_number', '=', partner_account_number)], limit=1)
                    if banks:
                        bank_account_id = banks[0].id
                        partner_id = banks[0].partner_id.id
                    else:
                        bank_obj = self._create_bank_account(
                            partner_account_number)
                        bank_account_id = bank_obj and bank_obj.id or False
                line_vals['partner_id'] = partner_id
                line_vals['bank_account_id'] = bank_account_id
        return stmt_vals

    @api.multi
    def _parse_file(self, data_file):
        """Parse a CNAB file."""
        self.ensure_one()
        parser = cnabparser()
        try:
            _logger.debug("Try parsing with CNAB.")
            return parser.parse(data_file, self.import_modes)
        except ValueError:
            # Not a CNAB file, returning super will call next candidate:
            _logger.debug("Statement file was not a CNAB  file.",
                          exc_info=True)
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    @api.model
    def _create_bank_statement(self, stmt_vals):
        """ Create bank statement from imported values, filtering out
        already imported transactions, and return data used by the
        reconciliation widget
        """
        bs_model = self.env['account.bank.statement']
        bsl_model = self.env['account.bank.statement.line']
        acc_line = self.env['account.move.line']
        # Filter out already imported transactions and create statement
        ignored_line_ids = []
        filtered_st_lines = []
        for line_vals in stmt_vals['transactions']:
            if 'name' in line_vals:
                trans_id = line_vals.get('unique_import_id')
                num_trans = u'%s/%s-%s' %(trans_id[:3], trans_id[3:11], trans_id[11:12])
                trans_id = acc_line.search(
                    [('transaction_ref', '=', num_trans)], limit=1)
                if trans_id:
                    line_vals['name'] = u'%s' %(trans_id.ref)
                if not line_vals.get('partner_id'):
                    line_vals['partner_id'] = trans_id.partner_id.id
                
            unique_id = (
                'unique_import_id' in line_vals and
                line_vals['unique_import_id']
            )
            if not unique_id or not bool(bsl_model.sudo().search(
                    [('unique_import_id', '=', unique_id)], limit=1)):
                filtered_st_lines.append(line_vals)
            else:
                ignored_line_ids.append(unique_id)
        statement_id = False
        if len(filtered_st_lines) > 0:
            # Remove values that won't be used to create records
            stmt_vals.pop('transactions', None)
            for line_vals in filtered_st_lines:
                line_vals.pop('account_number', None)

            # Create the statement
            stmt_vals['line_ids'] = [
                [0, False, line] for line in filtered_st_lines]
            statement_id = bs_model.create(stmt_vals).id
        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_line_ids)
        if num_ignored > 0:
            notifications += [{
                'type': 'warning',
                'message':
                    _("%d transactions had already been imported and "
                      "were ignored.") % num_ignored
                    if num_ignored > 1
                    else _("1 transaction had already been imported and "
                           "was ignored."),
                'details': {
                    'name': _('Already imported items'),
                    'model': 'account.bank.statement.line',
                    'ids': bsl_model.search(
                        [('unique_import_id', 'in', ignored_line_ids)]).ids}
            }]
        return statement_id, notifications
