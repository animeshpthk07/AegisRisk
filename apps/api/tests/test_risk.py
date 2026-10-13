from decimal import Decimal
from types import SimpleNamespace

import pytest

from aegisrisk.risk import expected_loss, summarize


def row(pd, lgd, ead, borrower="A"):
    return SimpleNamespace(pd=Decimal(pd), lgd=Decimal(lgd), ead=Decimal(ead), borrower=borrower)


def test_expected_loss():
    assert expected_loss("0.02", "0.45", "1000000") == Decimal(9000)


@pytest.mark.parametrize("values", [(0, 1, 100), (1, 0, 100), (1, 1, 0)])
def test_zero(values):
    assert expected_loss(*values) == 0


@pytest.mark.parametrize(
    "values",
    [
        (-1, 0.5, 100),
        (1.1, 0.5, 100),
        (0.1, 2, 100),
        (0.1, 0.5, -1),
        ("NaN", 0.5, 100),
        (0.1, "Infinity", 100),
        (0.1, 0.5, "Infinity"),
    ],
)
def test_invalid(values):
    with pytest.raises(ValueError):
        expected_loss(*values)


def test_weighted_metrics_and_hhi():
    stats = summarize([row("0.1", "0.5", "100", "A"), row("0.2", "0.4", "300", "B")])
    assert stats["weighted_pd"] == pytest.approx(0.175)
    assert stats["weighted_lgd"] == pytest.approx(0.425)
    assert stats["borrower_hhi"] == pytest.approx(0.625)
    assert stats["total_expected_loss"] == 29


def test_borrower_aggregation():
    assert summarize([row(".1", ".5", "100"), row(".2", ".5", "100")])["borrower_hhi"] == 1


def test_empty_portfolio():
    result = summarize([])
    assert result["total_expected_loss"] == 0
    assert result["weighted_pd"] is None
    assert result["borrower_hhi"] is None
