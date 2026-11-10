'use client';
import { useState } from 'react';
import { money, percent } from '../lib/format.mjs';

const dimensions = ['industry', 'geography', 'rating', 'borrower'] as const;
type Dimension = typeof dimensions[number];
type Contribution = { ead: number; expected_loss: number; exposure_share: number | null; loss_share: number | null };
type Group = Contribution & { label: string; facility_count: number };
export type PortfolioAnalytics = {
  breakdowns: Record<Dimension, { hhi: number | null; groups: Group[] }>;
  top_facilities: (Contribution & { id: string; borrower: string; industry: string; geography: string; rating: string })[];
  top_limit: number; hhi_scale: string;
};
type Summary = { facility_count: number; total_ead: number; total_expected_loss: number };
const near = (a: number, b: number) => Number.isFinite(a) && Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b));
const shareMatches = (share: number | null, value: number, total: number) =>
  total === 0 ? share === null : typeof share === 'number' && share >= 0 && share <= 1 && near(share, value / total);
function valid(data: PortfolioAnalytics, summary: Summary) {
  if (!data || data.hhi_scale !== '0_to_1' || data.top_limit !== 10 ||
      !Number.isSafeInteger(summary.facility_count) || summary.facility_count < 0 ||
      ![summary.total_ead, summary.total_expected_loss].every(n => Number.isFinite(n) && n >= 0)) return false;
  const contributionValid = (row: Contribution) => row &&
    [row.ead, row.expected_loss].every(n => Number.isFinite(n) && n >= 0) &&
    row.expected_loss <= row.ead && shareMatches(row.exposure_share, row.ead, summary.total_ead) &&
    shareMatches(row.loss_share, row.expected_loss, summary.total_expected_loss);
  if (!dimensions.every(dimension => {
    const breakdown = data.breakdowns?.[dimension];
    if (!breakdown || !Array.isArray(breakdown.groups)) return false;
    const groups = breakdown.groups;
    if (!groups.every(g => contributionValid(g) && typeof g.label === 'string' &&
        Number.isSafeInteger(g.facility_count) && g.facility_count > 0) ||
        new Set(groups.map(g => g.label)).size !== groups.length ||
        groups.reduce((n, g) => n + g.facility_count, 0) !== summary.facility_count ||
        !near(groups.reduce((n, g) => n + g.ead, 0), summary.total_ead) ||
        !near(groups.reduce((n, g) => n + g.expected_loss, 0), summary.total_expected_loss)) return false;
    return summary.total_ead === 0 ? breakdown.hhi === null :
      typeof breakdown.hhi === 'number' && near(breakdown.hhi, groups.reduce((n, g) => n + (g.exposure_share ?? 0) ** 2, 0));
  })) return false;
  return Array.isArray(data.top_facilities) && data.top_facilities.length === Math.min(10, summary.facility_count) &&
    new Set(data.top_facilities.map(row => row?.id)).size === data.top_facilities.length &&
    data.top_facilities.every((row, index) => contributionValid(row) &&
      [row.id, row.borrower, row.industry, row.geography, row.rating].every(value => typeof value === 'string') &&
      (index === 0 || data.top_facilities[index - 1].expected_loss >= row.expected_loss));
}

export default function ConcentrationAnalysis({ data, summary }: { data: PortfolioAnalytics; summary: Summary }) {
  const [dimension, setDimension] = useState<Dimension>('industry');
  if (!valid(data, summary)) return <section className="panel" aria-label="Portfolio analytics">
    <h2>Portfolio contributions</h2><p role="alert">Concentration evidence could not be verified. Reload the portfolio before using this analysis.</p>
  </section>;
  const breakdown = data.breakdowns[dimension];
  return <section className="panel" aria-label="Portfolio analytics">
    <p className="eyebrow">CONCENTRATION / LOSS CONTRIBUTIONS</p>
    <h2>Which exposures drive the risk?</h2>
    <p className="muted">Whole active portfolio · INR · one-year supplied PDs. Exposure share and expected-loss share use different totals. Facility search below does not change these portfolio-wide calculations.</p>
    <label>Group portfolio by<select aria-label="Group portfolio by" value={dimension} onChange={event => setDimension(event.target.value as Dimension)}>
      {dimensions.map(value => <option key={value} value={value}>{value === 'rating' ? 'Rating band' : value[0].toUpperCase() + value.slice(1)}</option>)}
    </select></label>
    <p aria-live="polite">{dimension === 'rating' ? 'Rating band' : dimension} exposure HHI: <strong>{breakdown.hhi === null ? 'Not defined' : breakdown.hhi.toFixed(4)}</strong> · scale 0–1. Higher values indicate greater concentration, not a default probability.</p>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Portfolio contribution table">
      <table aria-label="Portfolio group contributions"><caption>Complete {dimension} breakdown · shares of the whole active portfolio</caption>
        <thead><tr><th scope="col">Group</th><th scope="col">Facilities</th><th scope="col">Exposure</th><th scope="col">Exposure share</th><th scope="col">Expected loss</th><th scope="col">Loss share</th></tr></thead>
        <tbody>{breakdown.groups.map(group => <tr key={group.label}><th scope="row">{group.label}</th><td>{group.facility_count}</td><td>{money(group.ead)}</td><td>{percent(group.exposure_share)}</td><td>{money(group.expected_loss)}</td><td>{percent(group.loss_share)}</td></tr>)}</tbody>
      </table>{!breakdown.groups.length && <p>No facilities in this portfolio.</p>}
    </div>
    <h3>Largest expected-loss contributors</h3>
    <p className="muted">Top {data.top_facilities.length} of {summary.facility_count} facilities, ordered by expected loss. Ties use facility ID. Contributions are relative to the entire portfolio; the displayed subset need not sum to 100%.</p>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Top risk contribution table">
      <table aria-label="Top expected-loss contributors"><caption>Facility-level contributions from supplied assumptions</caption>
        <thead><tr><th scope="col">Borrower / ID</th><th scope="col">Industry / geography</th><th scope="col">Rating</th><th scope="col">Exposure</th><th scope="col">Exposure share</th><th scope="col">Expected loss</th><th scope="col">Loss share</th></tr></thead>
        <tbody>{data.top_facilities.map(row => <tr key={row.id}><th scope="row">{row.borrower}<small>{row.id}</small></th><td>{row.industry}<small>{row.geography}</small></td><td>{row.rating}</td><td>{money(row.ead)}</td><td>{percent(row.exposure_share)}</td><td>{money(row.expected_loss)}</td><td>{percent(row.loss_share)}</td></tr>)}</tbody>
      </table>
    </div>
    <p className="muted">Zero denominators produce undefined shares or HHI. Rating bands are dataset labels, not agency ratings. A low exposure share can still have a high loss contribution. The structured JSON report includes this evidence.</p>
  </section>;
}
