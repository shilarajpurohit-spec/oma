"""
Tests for backend.code_analyzer (Module 05)
"""

from backend.code_analyzer import analyze_code

ODOO_MODEL_CODE = '''
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Order Reference", required=True)
    amount_total = fields.Float(compute="_compute_amount", store=True)
    state = fields.Selection([("draft", "Quotation"), ("sale", "Sales Order")])

    @api.depends("order_line.price_subtotal")
    def _compute_amount(self):
        for order in self:
            order.amount_total = sum(order.order_line.mapped("price_subtotal"))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.payment_term_id = self.partner_id.property_payment_term_id
'''


def test_analyze_code_extracts_classes_and_methods():
    result = analyze_code(ODOO_MODEL_CODE, "sale.py")
    assert "SaleOrder" in result.classes
    assert "_compute_amount" in result.methods
    assert "_onchange_partner_id" in result.methods


def test_analyze_code_extracts_imports():
    result = analyze_code(ODOO_MODEL_CODE)
    # Using module.name format from ast.ImportFrom
    assert "odoo.models" in result.imports
    assert "odoo.fields" in result.imports
    assert "odoo.api" in result.imports


def test_analyze_code_detects_odoo_patterns():
    result = analyze_code(ODOO_MODEL_CODE)
    
    assert result.has_compute is True
    assert result.has_onchange is True
    assert result.has_api_depends is True
    assert result.has_inherit is True
    assert "sale.order" in result.model_names
    
    # Check fields
    field_names = [f["name"] for f in result.fields]
    assert "name" in field_names
    assert "amount_total" in field_names
    assert "state" in field_names
    
    field_types = [f["type"] for f in result.fields]
    assert "Char" in field_types
    assert "Float" in field_types
    assert "Selection" in field_types


def test_analyze_code_handles_syntax_error():
    # Will fail AST parse, but regex fallback should still work
    bad_code = '''
class BadModel(models.Model):
    _name = "bad.model"
    name = fields.Char()
    this is invalid python syntax
    '''
    result = analyze_code(bad_code)
    
    # AST won't get class
    assert "BadModel" not in result.classes
    # But regex will still get models and fields
    assert "bad.model" in result.model_names
    assert any(f["name"] == "name" and f["type"] == "Char" for f in result.fields)
    assert result.line_count == 6


def test_analyze_code_empty():
    result = analyze_code("")
    assert result.line_count == 0
    assert not result.classes
