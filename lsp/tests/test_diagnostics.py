"""
Tests for Vyper diagnostic extraction.
"""

import json
from subprocess import CompletedProcess

from serpent_lsp.features import diagnostics


class FakeEnvironment:
    def get_search_paths(self, include_sys_path: bool = True) -> list[str]:
        return []

    def run_script(self, script: str, cwd=None) -> CompletedProcess:
        return CompletedProcess(args=[], returncode=0, stdout=json.dumps(self.output), stderr="")


def test_compile_diagnostics_extracts_vyper_exception_list(monkeypatch) -> None:
    env = FakeEnvironment()
    env.output = {
        "success": False,
        "error_type": "VyperException",
        "errors": [
            {
                "message": "invalid syntax (<unknown>, line 4)\n\n  line 4:7",
                "error_type": "SyntaxException",
                "lineno": 4,
                "col_offset": 7,
            },
            {
                "message": "expected ':' (<unknown>, line 6)\n\n  line 6:11",
                "error_type": "SyntaxException",
                "lineno": 6,
                "col_offset": 11,
            },
        ],
    }
    monkeypatch.setattr(diagnostics, "resolve_environment", lambda version: env)

    found = diagnostics.compile_and_get_diagnostics(
        "/tmp/test_multi.vy", "0.4.1", workspace_path="/tmp"
    )

    assert len(found) == 2
    assert found[0].range.start.line == 3
    assert found[0].range.start.character == 7
    assert "[SyntaxException] invalid syntax" in found[0].message
    assert found[1].range.start.line == 5
    assert found[1].range.start.character == 11
    assert "[SyntaxException] expected ':'" in found[1].message
