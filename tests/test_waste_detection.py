"""
Splunk Zero — Waste Detection Unit Tests

Tests the core waste detection logic without requiring Splunk or any external services.
These tests validate:
    - Correct identification of wasteful sourcetypes
    - Demo-scale baseline application
    - Scope filtering (app: prefix)
    - Dual-pass detection (threshold + zero-search)
    - Edge cases: empty inputs, missing fields, boundary values

Usage:
    python -m pytest tests/test_waste_detection.py -v
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

# Import the functions under test
from src.agent.nodes.waste_detection import (
    _is_in_scope_sourcetype,
    _scaled_source_values,
    DEMO_SCALE_BASELINES,
    waste_detection,
)


# ── Scope Filtering Tests ────────────────────────────────────


class TestScopeFiltering:
    """Test _is_in_scope_sourcetype function."""

    def test_app_sourcetype_in_scope(self):
        assert _is_in_scope_sourcetype("app:payment-service:debug") is True

    def test_app_prefixed_in_scope(self):
        assert _is_in_scope_sourcetype("app:anything") is True

    def test_splunk_internal_not_in_scope(self):
        assert _is_in_scope_sourcetype("splunkd") is False

    def test_audit_not_in_scope(self):
        assert _is_in_scope_sourcetype("audittrail") is False

    def test_empty_string_not_in_scope(self):
        assert _is_in_scope_sourcetype("") is False

    def test_partial_app_not_in_scope(self):
        assert _is_in_scope_sourcetype("application-log") is False

    def test_uppercase_app_not_in_scope(self):
        """Scope check is case-sensitive; 'APP:' is not 'app:'."""
        assert _is_in_scope_sourcetype("APP:service") is False


# ── Demo Scale Baseline Tests ────────────────────────────────


class TestDemoScaleBaselines:
    """Test _scaled_source_values function."""

    def test_known_sourcetype_gets_scaled(self):
        result = _scaled_source_values("app:payment-service:debug", 0.001, 0.5)
        assert result["daily_gb"] == 12.40
        assert result["pct_of_total"] == 35.0
        assert result["demo_scaled"] is True
        assert result["observed_daily_gb"] == 0.001

    def test_known_sourcetype_large_observed_not_downscaled(self):
        """If observed value exceeds baseline, use the observed value."""
        result = _scaled_source_values("app:payment-service:debug", 20.0, 50.0)
        assert result["daily_gb"] == 20.0
        assert result["pct_of_total"] == 50.0
        assert result["demo_scaled"] is False

    def test_unknown_sourcetype_passes_through(self):
        result = _scaled_source_values("app:custom-service:debug", 3.5, 12.0)
        assert result["daily_gb"] == 3.5
        assert result["pct_of_total"] == 12.0
        assert result["demo_scaled"] is False

    def test_all_demo_sourcetypes_have_baselines(self):
        expected = [
            "app:payment-service:debug",
            "app:user-auth:debug",
            "app:inventory-api:debug",
        ]
        for st in expected:
            assert st in DEMO_SCALE_BASELINES


# ── Waste Detection Integration Tests ────────────────────────


class TestWasteDetection:
    """Test the waste_detection node with mocked event emission."""

    @pytest.fixture(autouse=True)
    def mock_event_manager(self):
        """Mock the event manager so tests don't need a running server."""
        with patch("src.agent.nodes.waste_detection.event_manager") as mock_em:
            mock_em.emit = AsyncMock()
            self.mock_em = mock_em
            yield

    def _run(self, state):
        """Helper to run the async function."""
        return asyncio.run(waste_detection(state))

    def test_detects_zero_search_app_waste(self):
        """App sourcetypes with zero searches should be flagged."""
        state = {
            "run_id": "test-001",
            "ingest_by_source": [
                {
                    "sourcetype": "app:payment-service:debug",
                    "daily_gb": 0.001,
                    "pct_of_total": 0.5,
                },
            ],
            "search_activity": [],
            "total_daily_gb": 0.2,
        }
        result = self._run(state)
        assert result["waste_found"] is True
        assert len(result["wasteful_sources"]) == 1
        assert (
            result["wasteful_sources"][0]["sourcetype"] == "app:payment-service:debug"
        )
        assert result["total_monthly_savings"] > 0

    def test_no_waste_when_sourcetypes_searched(self):
        """Sourcetypes with search activity should NOT be flagged."""
        state = {
            "run_id": "test-002",
            "ingest_by_source": [
                {
                    "sourcetype": "app:payment-service:debug",
                    "daily_gb": 12.0,
                    "pct_of_total": 35.0,
                },
            ],
            "search_activity": [
                {
                    "searched_sourcetype": "app:payment-service:debug",
                    "search_count": 50,
                },
            ],
            "total_daily_gb": 34.0,
        }
        result = self._run(state)
        assert result["waste_found"] is False
        assert len(result["wasteful_sources"]) == 0

    def test_splunk_internal_not_flagged(self):
        """Splunk internal sourcetypes should never be flagged as waste."""
        state = {
            "run_id": "test-003",
            "ingest_by_source": [
                {"sourcetype": "splunkd", "daily_gb": 50.0, "pct_of_total": 80.0},
                {
                    "sourcetype": "splunk_web_access",
                    "daily_gb": 5.0,
                    "pct_of_total": 8.0,
                },
            ],
            "search_activity": [],
            "total_daily_gb": 62.0,
        }
        result = self._run(state)
        assert result["waste_found"] is False
        assert len(result["wasteful_sources"]) == 0

    def test_multiple_wasteful_sources_sorted_by_cost(self):
        """Multiple wasteful sources should be sorted by estimated cost (descending)."""
        state = {
            "run_id": "test-004",
            "ingest_by_source": [
                {
                    "sourcetype": "app:payment-service:debug",
                    "daily_gb": 0.001,
                    "pct_of_total": 0.3,
                },
                {
                    "sourcetype": "app:user-auth:debug",
                    "daily_gb": 0.001,
                    "pct_of_total": 0.2,
                },
                {
                    "sourcetype": "app:inventory-api:debug",
                    "daily_gb": 0.001,
                    "pct_of_total": 0.1,
                },
            ],
            "search_activity": [],
            "total_daily_gb": 1.0,
        }
        result = self._run(state)
        assert result["waste_found"] is True
        assert len(result["wasteful_sources"]) == 3
        costs = [w["est_monthly_cost"] for w in result["wasteful_sources"]]
        assert costs == sorted(
            costs, reverse=True
        ), "Should be sorted by cost descending"

    def test_empty_ingest_data(self):
        """No ingest data should result in no waste."""
        state = {
            "run_id": "test-005",
            "ingest_by_source": [],
            "search_activity": [],
            "total_daily_gb": 0.0,
        }
        result = self._run(state)
        assert result["waste_found"] is False
        assert result["total_monthly_savings"] == 0

    def test_high_volume_threshold_pass(self):
        """An app sourcetype above the threshold % with low searches should be waste."""
        state = {
            "run_id": "test-006",
            "ingest_by_source": [
                {
                    "sourcetype": "app:big-service:debug",
                    "daily_gb": 10.0,
                    "pct_of_total": 25.0,
                },
            ],
            "search_activity": [
                {"searched_sourcetype": "app:big-service:debug", "search_count": 1},
            ],
            "total_daily_gb": 40.0,
        }
        result = self._run(state)
        assert result["waste_found"] is True
        assert result["wasteful_sources"][0]["search_count_30d"] == 1

    def test_exactly_at_threshold_not_flagged(self):
        """A source with search_count == MIN_SEARCH_COUNT should NOT be waste."""
        state = {
            "run_id": "test-007",
            "ingest_by_source": [
                {
                    "sourcetype": "app:edge-case:debug",
                    "daily_gb": 8.0,
                    "pct_of_total": 20.0,
                },
            ],
            "search_activity": [
                {"searched_sourcetype": "app:edge-case:debug", "search_count": 2},
            ],
            "total_daily_gb": 40.0,
        }
        result = self._run(state)
        assert result["waste_found"] is False

    def test_demo_scale_baselines_applied_in_detection(self):
        """Known demo sourcetypes should use scaled baselines for cost calculation."""
        state = {
            "run_id": "test-008",
            "ingest_by_source": [
                {
                    "sourcetype": "app:payment-service:debug",
                    "daily_gb": 0.001,
                    "pct_of_total": 0.3,
                },
            ],
            "search_activity": [],
            "total_daily_gb": 0.5,
        }
        result = self._run(state)
        waste = result["wasteful_sources"][0]
        # Should be scaled to demo baseline, not 0.001
        assert waste["daily_gb"] == 12.40
        assert waste["demo_scaled"] is True

    def test_event_emission_on_waste_found(self):
        """Events should be emitted when waste is detected."""
        state = {
            "run_id": "test-009",
            "ingest_by_source": [
                {
                    "sourcetype": "app:noisy:debug",
                    "daily_gb": 5.0,
                    "pct_of_total": 15.0,
                },
            ],
            "search_activity": [],
            "total_daily_gb": 33.0,
        }
        self._run(state)
        # Should have emitted at least start + result events
        assert self.mock_em.emit.call_count >= 2

    def test_event_emission_on_no_waste(self):
        """Events should be emitted even when no waste is found."""
        state = {
            "run_id": "test-010",
            "ingest_by_source": [],
            "search_activity": [],
            "total_daily_gb": 0.0,
        }
        self._run(state)
        assert self.mock_em.emit.call_count >= 2


# ── Event Manager Unit Tests ────────────────────────────────


class TestEventManager:
    """Test the SSE EventManager."""

    def test_create_and_emit(self):
        from src.ui.events import EventManager

        em = EventManager()
        em.create_run("r1")

        async def _test():
            event = await em.emit("r1", "test_step", "Test Title", "details", "running")
            assert event["step"] == "test_step"
            assert event["title"] == "Test Title"
            assert event["status"] == "running"
            assert "timestamp" in event

        asyncio.run(_test())

    def test_emit_to_unknown_run(self):
        from src.ui.events import EventManager

        em = EventManager()

        async def _test():
            # Should not raise, just silently skip
            event = await em.emit("nonexistent", "step", "Title")
            assert event["step"] == "step"

        asyncio.run(_test())

    def test_complete_marks_run_done(self):
        from src.ui.events import EventManager

        em = EventManager()
        em.create_run("r2")

        async def _test():
            assert em.is_complete("r2") is False
            await em.complete("r2")
            assert em.is_complete("r2") is True

        asyncio.run(_test())

    def test_cleanup_removes_run(self):
        from src.ui.events import EventManager

        em = EventManager()
        em.create_run("r3")
        em.cleanup("r3")
        assert em.is_complete("r3") is False


# ── Config Validation Tests ──────────────────────────────────


class TestConfigValidation:
    """Test Config.validate() edge cases."""

    def test_validate_returns_list(self):
        from src.config import Config

        result = Config.validate()
        assert isinstance(result, list)

    def test_validate_missing_keys_are_strings(self):
        from src.config import Config

        result = Config.validate()
        for key in result:
            assert isinstance(key, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
