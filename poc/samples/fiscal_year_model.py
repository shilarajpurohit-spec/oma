# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class AccountFiscalYear(models.Model):
    _name = 'account.fiscal.year'
    _description = 'Fiscal Year'

    name = fields.Char(string='Name', required=True)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.multi
    def action_confirm(self):
        for rec in self:
            if rec.date_from >= rec.date_to:
                raise ValidationError(
                    'End Date must be after Start Date.'
                )
        return True

    @api.one
    def action_close(self):
        self.state = 'closed'

    @api.multi
    def get_summary(self):
        result = []
        for rec in self:
            partner = self.pool['res.partner'].browse(
                self._cr, self._uid, rec.company_id.partner_id.id
            )
            result.append({
                'name': rec.name,
                'partner': partner.name,
            })
        return result

    @api.multi
    def sudo_example(self):
        """Old sudo usage passing a user — invalid in v16+."""
        admin = self.env.ref('base.user_admin')
        records = self.sudo(admin).search([])
        return records
