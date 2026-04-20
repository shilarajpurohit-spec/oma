"""
Tests for backend.version_detector (Module 04)
"""

import pytest
from backend.version_detector import detect_version, VersionDetectionError
from backend.schemas import OdooVersion


def test_detect_version_manifest():
    code_v18 = "{'version': '18.0.1.0'}"
    assert detect_version(code_v18) == OdooVersion.V18
    
    code_v15 = '"version": "15.0.0.1"'
    assert detect_version(code_v15) == OdooVersion.V15


def test_detect_version_imports():
    code_v16 = "from odoo.cli.command import Command"
    assert detect_version(code_v16) == OdooVersion.V16
    
    code_v17 = "from odoo.addons.web.core import Foo\nclass Component:\n    setup()"
    assert detect_version(code_v17) == OdooVersion.V17


def test_detect_version_fallback():
    code_v15 = "from odoo import models, fields"
    assert detect_version(code_v15) == OdooVersion.V15


def test_detect_version_empty_or_unknown():
    with pytest.raises(VersionDetectionError):
        detect_version("")

    with pytest.raises(VersionDetectionError):
        detect_version("import sys\nprint('hello')")
