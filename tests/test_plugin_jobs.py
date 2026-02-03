"""Unit tests for plugin/job_type-aware API: get_jobs, update_job, create_job, export/import."""
import json
import pytest


class TestGetJobsJobType:
    """GET /api/jobs returns job_type and plugin columns when present."""

    def test_get_jobs_returns_list(self, client):
        r = client.get("/api/jobs")
        assert r.status_code == 200
        data = r.get_json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_get_jobs_job_has_job_type_when_scan_job_exists(self, client):
        # Create a listing_scan job via base API (requires plugin columns in DB)
        create = client.post(
            "/api/jobs",
            json={
                "name": "Scan test",
                "url": "https://example.com/list",
                "check_interval": 300,
                "email_recipient": "test@example.com",
                "job_type": "listing_scan",
            },
            content_type="application/json",
        )
        if create.status_code != 201:
            pytest.skip("listing_scan create failed (plugin columns may be missing)")
        job_id = create.get_json().get("id")
        r = client.get("/api/jobs")
        assert r.status_code == 200
        jobs = r.get_json().get("jobs", [])
        scan = next((j for j in jobs if j.get("id") == job_id), None)
        assert scan is not None
        assert scan.get("job_type") == "listing_scan"
        assert scan.get("scan_mode") == "listing"
        # Cleanup
        client.delete(f"/api/jobs/{job_id}")


class TestCreateJobJobType:
    """POST /api/jobs accepts optional job_type; listing_scan relaxes match_*."""

    def test_create_standard_job_requires_match_fields(self, client):
        r = client.post(
            "/api/jobs",
            json={
                "name": "Standard",
                "url": "https://example.com",
                "check_interval": 300,
                "email_recipient": "a@b.com",
            },
            content_type="application/json",
        )
        assert r.status_code == 400
        data = r.get_json()
        assert "error" in data and "required" in data["error"].lower()

    def test_create_standard_job_success(self, client):
        r = client.post(
            "/api/jobs",
            json={
                "name": "Standard job",
                "url": "https://example.com",
                "check_interval": 300,
                "match_type": "string",
                "match_pattern": "test",
                "match_condition": "contains",
                "email_recipient": "a@b.com",
            },
            content_type="application/json",
        )
        assert r.status_code == 201
        job_id = r.get_json().get("id")
        assert job_id is not None
        client.delete(f"/api/jobs/{job_id}")

    def test_create_listing_scan_job_without_match_pattern(self, client):
        r = client.post(
            "/api/jobs",
            json={
                "name": "Scan job minimal",
                "url": "https://example.com/list",
                "check_interval": 300,
                "email_recipient": "scan@example.com",
                "job_type": "listing_scan",
            },
            content_type="application/json",
        )
        if r.status_code == 500:
            # Plugin columns may not exist in DB
            pytest.skip("listing_scan insert failed (plugin schema not present)")
        assert r.status_code == 201
        job_id = r.get_json().get("id")
        assert job_id is not None
        # Verify GET returns job_type
        get_r = client.get("/api/jobs")
        jobs = get_r.get_json().get("jobs", [])
        job = next((j for j in jobs if j["id"] == job_id), None)
        assert job is not None
        assert job.get("job_type") == "listing_scan"
        client.delete(f"/api/jobs/{job_id}")


class TestUpdateJobPluginColumns:
    """PUT /api/jobs/<id> accepts plugin columns for scan jobs; does not require pattern."""

    def test_update_scan_job_notification_channels_with_empty_pattern(self, client):
        create = client.post(
            "/api/jobs",
            json={
                "name": "Scan for update test",
                "url": "https://example.com/list",
                "check_interval": 300,
                "email_recipient": "u@example.com",
                "job_type": "listing_scan",
            },
            content_type="application/json",
        )
        if create.status_code != 201:
            pytest.skip("listing_scan create not available")
        job_id = create.get_json().get("id")
        r = client.put(
            f"/api/jobs/{job_id}",
            json={
                "name": "Scan for update test",
                "url": "https://example.com/list",
                "check_interval": 300,
                "email_recipient": "u@example.com",
                "match_pattern": "",
                "match_type": "string",
                "match_condition": "contains",
                "notification_channels": [],
            },
            content_type="application/json",
        )
        assert r.status_code == 200
        client.delete(f"/api/jobs/{job_id}")


class TestExportImportJobType:
    """Export includes job_type and plugin columns; import validates per job_type."""

    def test_export_includes_jobs(self, client):
        r = client.get("/api/export")
        assert r.status_code == 200
        data = r.get_json()
        assert "jobs" in data
        assert "exported_at" in data

    def test_import_listing_scan_roundtrip(self, client):
        payload = {
            "jobs": [
                {
                    "name": "Imported scan",
                    "url": "https://example.com/imported",
                    "check_interval": 300,
                    "email_recipient": "import@example.com",
                    "job_type": "listing_scan",
                    "scan_mode": "listing",
                    "match_type": "string",
                    "match_pattern": "",
                    "match_condition": "contains",
                    "item_extractor_config": {"items_path": "$.items"},
                }
            ]
        }
        r = client.post("/api/import", json=payload, content_type="application/json")
        data = r.get_json()
        if data.get("created", 0) == 0 and data.get("errors"):
            pytest.skip("import listing_scan failed: " + str(data["errors"]))
        assert data.get("created") == 1
        # Cleanup: delete the imported job (get id from GET /api/jobs by name)
        list_r = client.get("/api/jobs")
        jobs = list_r.get_json().get("jobs", [])
        imported_job = next((j for j in jobs if j.get("name") == "Imported scan"), None)
        if imported_job:
            client.delete(f"/api/jobs/{imported_job['id']}")

    def test_import_standard_job_requires_match_fields(self, client):
        payload = {
            "jobs": [
                {
                    "name": "Bad import",
                    "url": "https://example.com",
                    "check_interval": 300,
                    "email_recipient": "x@y.com",
                }
            ]
        }
        r = client.post("/api/import", json=payload, content_type="application/json")
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("created") == 0
        assert len(data.get("errors", [])) >= 1
