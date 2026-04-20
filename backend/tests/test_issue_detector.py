"""
Tests for backend.issue_detector (Module 08)
"""

from backend.issue_detector import detect_issues
from backend.schemas import OdooVersion, Severity


def test_detect_issues_v15_deprecated():
    code = '''
from openerp import models

class MyModel(osv.osv):
    _name = "my.model"

    def some_method(self, cr, uid, ids, context=None):
        my_pool = self.pool["res.partner"]
        my_pool.sudo(uid)
    '''
    
    issues = detect_issues(code, OdooVersion.V15)
    
    assert len(issues) >= 4
    
    messages = [i.message for i in issues]
    assert any("openerp" in m for m in messages)
    assert any("osv.osv" in m for m in messages)
    assert any("self.pool" in m for m in messages)
    assert any("sudo(user)" in m for m in messages)

    # Check line numbers mapped correctly
    openerp_issue = next(i for i in issues if "openerp" in i.message)
    assert openerp_issue.line == 2
    assert openerp_issue.severity == Severity.CRITICAL


def test_detect_issues_filters_by_version():
    code = "from openerp import models"
    
    # v15 should flag openerp
    issues_v15 = detect_issues(code, OdooVersion.V15)
    assert len(issues_v15) == 1
    
    # v18 shouldn't (or rather, the rule doesn't apply to v18 migrations since
    # openerp was gone long ago, so a v18 module shouldn't have it and the scanner ignores it)
    issues_v18 = detect_issues(code, OdooVersion.V18)
    assert len(issues_v18) == 0


def test_detect_issues_owl():
    code = "class MyComponent extends owl.Component {}"
    
    issues = detect_issues(code, OdooVersion.V16)
    assert len(issues) == 1
    assert issues[0].severity == Severity.HIGH
    assert "OWL2" in issues[0].message
