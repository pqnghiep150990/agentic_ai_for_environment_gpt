from agentic_env_ai.demo import run_demo


def test_demo_report_has_required_sections():
    report = run_demo()
    assert "summary" in report
    assert "evaluation" in report
    assert "reliability" in report
    assert "governance" in report
