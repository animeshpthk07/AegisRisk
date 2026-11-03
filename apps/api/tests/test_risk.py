from decimal import Decimal
from types import SimpleNamespace

import pytest

from aegisrisk.risk import expected_loss, portfolio_analytics, summarize


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


def analytic_rows():
    values = [row(".1", ".5", "100", "A"), row(".2", ".5", "100", "A"),
              row("0", "1", "200", "B")]
    for item, identity, industry, geography, rating in zip(
        values, ["SYN-A", "SYN-B", "SYN-C"], ["Energy", "Energy", "Tech"],
        ["West", "East", "East"], ["A", "B", "C"], strict=True,
    ):
        item.id, item.industry = identity, industry
        item.geography, item.rating = geography, rating
    return values


def test_contributions_conserve_exposure_loss_and_facility_counts():
    result = portfolio_analytics(analytic_rows())
    expected_hhi = {"industry": .5, "geography": .625, "rating": .375, "borrower": .5}
    assert set(result["breakdowns"]) == set(expected_hhi)
    for dimension, value in result["breakdowns"].items():
        groups = value["groups"]
        assert sum(g["facility_count"] for g in groups) == 3
        assert sum(g["ead"] for g in groups) == 400
        assert sum(g["expected_loss"] for g in groups) == 15
        assert sum(g["exposure_share"] for g in groups) == pytest.approx(1)
        assert sum(g["loss_share"] for g in groups) == pytest.approx(1)
        assert value["hhi"] == pytest.approx(expected_hhi[dimension])
    energy = result["breakdowns"]["industry"]["groups"][0]
    assert energy == {"label": "Energy", "facility_count": 2, "ead": 200,
                      "expected_loss": 15, "exposure_share": .5, "loss_share": 1}
    assert [r["id"] for r in result["top_facilities"]] == ["SYN-B", "SYN-A", "SYN-C"]
    assert result["top_facilities"][0]["loss_share"] == pytest.approx(2 / 3)
    assert result == portfolio_analytics(list(reversed(analytic_rows())))


def test_zero_exposure_and_zero_loss_have_explicit_undefined_shares():
    values = analytic_rows()
    for item in values:
        item.pd = Decimal(0)
    lossless = portfolio_analytics(values)
    assert all(r["loss_share"] is None for r in lossless["top_facilities"])
    assert lossless["breakdowns"]["industry"]["hhi"] == .5
    for item in values:
        item.ead = Decimal(0)
    empty_exposure = portfolio_analytics(values)
    for breakdown in empty_exposure["breakdowns"].values():
        assert breakdown["hhi"] is None
        assert all(g["exposure_share"] is None and g["loss_share"] is None
                   for g in breakdown["groups"])
    assert portfolio_analytics([])["top_facilities"] == []
    assert all(b == {"hhi": None, "groups": []}
               for b in portfolio_analytics([])["breakdowns"].values())


def test_top_contributors_are_bounded_and_ties_use_stable_ids():
    values = []
    for i in reversed(range(12)):
        item = analytic_rows()[0]
        item.id = f"SYN-{i:02d}"
        values.append(item)
    result = portfolio_analytics(values)
    assert result["top_limit"] == 10
    assert [r["id"] for r in result["top_facilities"]] == [
        f"SYN-{i:02d}" for i in range(10)
    ]


def test_portfolio_and_json_report_use_the_same_analytics():
    from aegisrisk.main import baseline_report_payload, portfolio_payload

    values = analytic_rows()
    expected = portfolio_analytics(values)
    assert portfolio_payload(values, None)["analytics"] == expected
    report = baseline_report_payload(values, None)
    assert report["analytics"] == expected
    assert report["summary"]["total_expected_loss"] == 15

