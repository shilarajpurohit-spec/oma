"""
OMA Agent — Tests for SQL detection in code_analyzer (Phase 2)
"""

import pytest
from backend.code_analyzer import analyze_code


# ── Raw SQL via cr.execute ────────────────────────────────────────

def test_detect_self_env_cr_execute():
    code = """
from odoo import models
class SaleOrder(models.Model):
    _name = 'sale.order'
    def get_totals(self):
        self.env.cr.execute("SELECT id FROM sale_order WHERE state='done'")
    """
    result = analyze_code(code, "models/sale_order.py")
    assert result.has_raw_sql is True
    assert len(result.raw_sql_lines) >= 1


def test_detect_self_cr_execute():
    code = """
from odoo import models
class ResPartner(models.Model):
    _name = 'res.partner'
    def custom_query(self):
        self._cr.execute("SELECT id, name FROM res_partner")
    """
    result = analyze_code(code, "models/res_partner.py")
    assert result.has_raw_sql is True


def test_detect_cr_execute_direct():
    code = """
def _update_records(cr):
    cr.execute("UPDATE account_move SET state='posted' WHERE id IN %s", (ids,))
    """
    result = analyze_code(code, "migrations/0001_update.py")
    assert result.has_raw_sql is True


def test_raw_sql_line_numbers_reported():
    code = "from odoo import models\n" \
           "class M(models.Model):\n" \
           "    _name = 'x'\n" \
           "    def q(self):\n" \
           "        self.env.cr.execute('SELECT 1')\n"
    result = analyze_code(code)
    assert result.has_raw_sql is True
    assert 5 in result.raw_sql_lines


# ── Inline SQL strings ────────────────────────────────────────────

def test_detect_inline_select_string():
    code = """
class ReportModel:
    def _compute(self):
        query = 'SELECT id, name FROM product_template WHERE active = True'
        self.env.cr.execute(query)
    """
    result = analyze_code(code)
    assert result.has_raw_sql is True


def test_detect_fstring_sql():
    code = """
def run(self):
    self._cr.execute(f"SELECT * FROM {self._table} WHERE id = %s", [self.id])
    """
    result = analyze_code(code)
    assert result.has_raw_sql is True


def test_detect_insert_sql():
    code = """
def migrate(cr, version):
    cr.execute("INSERT INTO account_move (name, state) VALUES (%s, %s)", ['INV001', 'draft'])
    """
    result = analyze_code(code)
    assert result.has_raw_sql is True


def test_no_false_positive_on_orm():
    """Pure ORM code should NOT trigger has_raw_sql."""
    code = """
from odoo import models, fields, api
class SaleOrder(models.Model):
    _name = 'sale.order'
    name = fields.Char(required=True)

    def action_confirm(self):
        self.write({'state': 'sale'})
        return self.env['sale.order'].search([('state', '=', 'sale')])
    """
    result = analyze_code(code)
    assert result.has_raw_sql is False
    assert result.raw_sql_lines == []


def test_no_false_positive_on_execute_method_name():
    """A method called execute that isn't database should not trigger."""
    code = """
class Workflow:
    def run(self):
        self.task.execute(payload={'key': 'value'})
    """
    result = analyze_code(code)
    assert result.has_raw_sql is False


# ── to_dict includes sql fields ───────────────────────────────────

def test_to_dict_includes_raw_sql_fields():
    code = "self.env.cr.execute('SELECT 1')\n"
    result = analyze_code(code)
    d = result.to_dict()
    assert "has_raw_sql" in d
    assert "raw_sql_lines" in d
    assert d["has_raw_sql"] is True
