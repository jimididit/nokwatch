"""Unit tests for services.template_service (plan: test template system with sample templates)."""
import pytest
from services.template_service import (
    get_all_templates,
    get_template_by_id,
    apply_template_to_job_data,
)


class TestGetAllTemplates:
    def test_returns_list(self):
        templates = get_all_templates()
        assert isinstance(templates, list)

    def test_templates_have_expected_keys(self):
        templates = get_all_templates()
        for t in templates:
            assert "id" in t or "name" in t
            # May have description, check_interval, match_type, etc.


class TestGetTemplateById:
    def test_unknown_id_returns_none(self):
        assert get_template_by_id("nonexistent") is None
        assert get_template_by_id(99999) is None

    def test_known_id_returns_template(self):
        templates = get_all_templates()
        if templates:
            first_id = templates[0].get("id")
            if first_id is not None:
                t = get_template_by_id(first_id)
                assert t is not None
                assert t.get("id") == first_id


class TestApplyTemplateToJobData:
    def test_none_template_id_does_nothing(self):
        job_data = {"name": "Job", "check_interval": 300}
        apply_template_to_job_data(None, job_data)
        assert job_data["check_interval"] == 300

    def test_unknown_template_id_does_nothing(self):
        job_data = {"match_pattern": "x"}
        apply_template_to_job_data("bad_id", job_data)
        assert job_data["match_pattern"] == "x"

    def test_template_overrides_job_data_in_place(self):
        templates = get_all_templates()
        if not templates:
            pytest.skip("No templates in monitor_templates.json")
        t = next((x for x in templates if x.get("check_interval") is not None), None)
        if not t:
            pytest.skip("No template with check_interval")
        job_data = {"name": "Job", "check_interval": 999}
        apply_template_to_job_data(t["id"], job_data)
        assert job_data["check_interval"] != 999
        assert job_data["check_interval"] == t["check_interval"]
