"""Test per History e StepRecord."""
import pytest
from macrorefine.history import History, StepRecord


class TestStepRecord:
    def test_create_minimal_record(self):
        record = StepRecord(name="MyStep")
        assert record.name == "MyStep"
        assert record.params == {}
        assert record.metrics == {}

    def test_create_full_record(self):
        record = StepRecord(
            name="FillMissing",
            params={"strategy": "median"},
            metrics={"filled": 12},
        )
        assert record.name == "FillMissing"
        assert record.params["strategy"] == "median"
        assert record.metrics["filled"] == 12

    def test_record_is_frozen(self):
        """StepRecord deve essere immutabile."""
        record = StepRecord(name="X")
        with pytest.raises(Exception):  # FrozenInstanceError
            record.name = "Y"


class TestHistory:
    def test_empty_history(self):
        h = History()
        assert len(h) == 0
        assert list(h) == []

    def test_append_returns_new_history(self):
        """append deve essere immutabile: ritorna nuova History."""
        h1 = History()
        record = StepRecord(name="StepA")
        h2 = h1.append(record)

        assert len(h1) == 0       # h1 invariata
        assert len(h2) == 1
        assert h2[0].name == "StepA"
        assert h1 is not h2

    def test_multiple_appends_preserve_order(self):
        h = History()
        h = h.append(StepRecord(name="A"))
        h = h.append(StepRecord(name="B"))
        h = h.append(StepRecord(name="C"))

        assert [r.name for r in h] == ["A", "B", "C"]

    def test_iteration(self):
        h = History().append(StepRecord(name="A")).append(StepRecord(name="B"))
        names = [r.name for r in h]
        assert names == ["A", "B"]

    def test_repr_is_readable(self):
        h = History().append(StepRecord(name="StepA", params={"x": 1}))
        text = repr(h)
        assert "StepA" in text