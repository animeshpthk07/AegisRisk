"""Transparent one-year illustrative EL, not IFRS 9 ECL or regulatory capital."""

from collections import defaultdict
from decimal import Decimal


def decimal_value(value, *, probability=False):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0 or (probability and value > 1):
        raise ValueError("Values must be finite, non-negative; probabilities cannot exceed one")
    return value


def expected_loss(pd, lgd, ead):
    return (
        decimal_value(pd, probability=True)
        * decimal_value(lgd, probability=True)
        * decimal_value(ead)
    )


def summarize(rows):
    total = sum((decimal_value(row.ead) for row in rows), Decimal(0))
    el = sum((expected_loss(row.pd, row.lgd, row.ead) for row in rows), Decimal(0))
    borrowers = defaultdict(Decimal)
    for row in rows:
        borrowers[row.borrower] += row.ead
    return {
        "facility_count": len(rows),
        "total_ead": float(total),
        "total_expected_loss": float(el),
        "weighted_pd": float(sum((r.pd * r.ead for r in rows), Decimal(0)) / total)
        if total
        else None,
        "weighted_lgd": float(sum((r.lgd * r.ead for r in rows), Decimal(0)) / total)
        if total
        else None,
        "borrower_hhi": float(sum(((v / total) ** 2 for v in borrowers.values()), Decimal(0)))
        if total
        else None,
    }


def portfolio_analytics(rows):
    """Decimal concentration and contributions for one currency/horizon snapshot."""
    values = [
        (row, decimal_value(row.ead), expected_loss(row.pd, row.lgd, row.ead))
        for row in rows
    ]
    total_ead = sum((ead for _, ead, _ in values), Decimal(0))
    total_el = sum((el for _, _, el in values), Decimal(0))

    def contribution(ead, el):
        return {
            "ead": float(ead), "expected_loss": float(el),
            "exposure_share": float(ead / total_ead) if total_ead else None,
            "loss_share": float(el / total_el) if total_el else None,
        }

    breakdowns = {}
    for dimension in ("industry", "geography", "rating", "borrower"):
        groups = defaultdict(lambda: {"ead": Decimal(0), "el": Decimal(0), "count": 0})
        for row, ead, el in values:
            group = groups[getattr(row, dimension)]
            group["ead"] += ead
            group["el"] += el
            group["count"] += 1
        breakdowns[dimension] = {
            "hhi": float(sum(
                ((group["ead"] / total_ead) ** 2 for group in groups.values()),
                Decimal(0),
            )) if total_ead else None,
            "groups": [
                {"label": label, "facility_count": group["count"],
                 **contribution(group["ead"], group["el"])}
                for label, group in sorted(groups.items())
            ],
        }
    ranked = sorted(values, key=lambda item: (-item[2], item[0].id))[:10]
    return {
        "breakdowns": breakdowns,
        "top_facilities": [
            {"id": row.id, "borrower": row.borrower, "industry": row.industry,
             "geography": row.geography, "rating": row.rating,
             **contribution(ead, el)}
            for row, ead, el in ranked
        ],
        "top_limit": 10,
        "ranking": "Expected loss descending; facility ID ascending for ties",
        "hhi_scale": "0_to_1",
    }
