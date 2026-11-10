'use client';
import { useEffect, useState } from 'react';
import { money, percent } from '../lib/format.mjs';
import { workbenchFetch } from './access';

type Facility = { id: string; borrower: string; industry: string; geography: string; rating: string;
  pd: number; lgd: number; ead: number; expected_loss: number };
type Summary = { facility_count: number; total_ead: number; total_expected_loss: number;
  weighted_pd: number | null; weighted_lgd: number | null };
const ratioLabels = {
  debt_to_assets: 'Debt / assets', interest_coverage: 'Interest coverage',
  current_ratio: 'Current ratio', revenue_growth: 'Revenue growth',
} as const;
type Ratio = keyof typeof ratioLabels;
type Estimate = { model_id: string; calibrated_probability: number; inputs: Record<Ratio, number>;
  contributions: { feature: Ratio; log_odds: number }[] };
type Review = { dataset_id: string | null; dataset_version: string; synthetic: boolean;
  currency: string; horizon: string; facility: Facility; borrower: Summary; portfolio: Summary;
  sensitivity: { stressed_pd: number; stressed_el: number; delta_el: number };
  profile_version: string | null; model: Estimate | null; profile_note: string };

function validSummary(s: Summary) {
  return s && Number.isInteger(s.facility_count) && s.facility_count >= 1
    && [s.total_ead, s.total_expected_loss].every(n => Number.isFinite(n) && n >= 0)
    && [s.weighted_pd, s.weighted_lgd].every(n => s.total_ead === 0 ? n === null :
      typeof n === 'number' && Number.isFinite(n) && n >= 0 && n <= 1);
}
function validModel(m: Estimate | null) {
  if (m === null) return true;
  return m && typeof m.model_id === 'string' && Number.isFinite(m.calibrated_probability)
    && m.calibrated_probability >= 0 && m.calibrated_probability <= 1 && m.inputs
    && Object.keys(ratioLabels).every(key => Number.isFinite(m.inputs[key as Ratio]))
    && Array.isArray(m.contributions) && m.contributions.length === 4
    && m.contributions.every(d => d && Object.prototype.hasOwnProperty.call(ratioLabels, d.feature) && Number.isFinite(d.log_odds))
    && new Set(m.contributions.map(d => d.feature)).size === 4;
}

type Props = { rows: Facility[]; datasetId: string; version: string };
export default function FacilityReview({ rows, datasetId, version }: Props) {
  const [id, setId] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [review, setReview] = useState<Review | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    async function load() {
      const params = new URLSearchParams({ facility_id: id });
      if (datasetId) params.set('dataset_id', datasetId);
      try {
        const response = await workbenchFetch('/api/facility-review?' + params, {
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
        });
        if (!response.ok) throw new Error();
        const data: Review = await response.json();
        if (data.dataset_version !== version || (data.dataset_id || '') !== datasetId
            || data.facility?.id !== id || data.synthetic !== true || data.horizon !== 'one_year'
            || data.currency !== 'INR' || !validSummary(data.borrower) || !validSummary(data.portfolio)
            || !data.sensitivity || ![data.sensitivity.stressed_pd, data.sensitivity.stressed_el,
              data.sensitivity.delta_el, data.facility.expected_loss, data.facility.ead,
              data.facility.pd, data.facility.lgd].every(Number.isFinite) || !validModel(data.model)
            || (datasetId && (data.model !== null || data.profile_version !== null))) throw new Error();
        if (!controller.signal.aborted) setReview(data);
      } catch {
        if (!controller.signal.aborted) setError('Facility review unavailable. Please retry.');
      }
    }
    void load();
    return () => controller.abort();
  }, [id, datasetId, version, attempt]);
  const selected = review?.facility.id === id ? review : null;
  return <section aria-label="Borrower risk review">
    <h3>Borrower risk review</h3>
    <label htmlFor="review-facility">Inspect a facility</label>
    <select id="review-facility" value={id} onChange={e => {
      setReview(null); setError(''); setId(e.target.value);
    }}>
      <option value="">Choose a facility</option>
      {rows.map(row => <option key={row.id} value={row.id}>{row.borrower} · {row.id}</option>)}
    </select>
    {id && !selected && !error && <p role="status">Loading facility review…</p>}
    {error && <div role="alert">{error} <button onClick={() => {
      setError(''); setAttempt(n => n + 1);
    }}>Retry facility review</button></div>}
    {selected && <>
      <h4>{selected.facility.borrower} · {selected.facility.id}</h4>
      <p>{selected.facility.industry} · {selected.facility.geography} · Grade {selected.facility.rating}</p>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Borrower comparison">
        <table><caption>Facility, borrower and portfolio · INR, one year</caption>
          <thead><tr><th scope="col">Metric</th><th scope="col">Facility</th>
            <th scope="col">Borrower</th><th scope="col">Portfolio</th></tr></thead>
          <tbody>{[
            ['Facilities', '1', selected.borrower.facility_count, selected.portfolio.facility_count],
            ['Exposure at default', money(selected.facility.ead), money(selected.borrower.total_ead), money(selected.portfolio.total_ead)],
            ['Expected loss', money(selected.facility.expected_loss), money(selected.borrower.total_expected_loss), money(selected.portfolio.total_expected_loss)],
            ['PD (exposure-weighted for groups)', percent(selected.facility.pd), percent(selected.borrower.weighted_pd), percent(selected.portfolio.weighted_pd)],
            ['LGD (exposure-weighted for groups)', percent(selected.facility.lgd), percent(selected.borrower.weighted_lgd), percent(selected.portfolio.weighted_lgd)],
          ].map(([metric, facility, borrower, portfolio]) => <tr key={metric}>
            <th scope="row">{metric}</th><td>{facility}</td><td>{borrower}</td><td>{portfolio}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <p>Doubling the supplied PD gives {percent(selected.sensitivity.stressed_pd)} after the 100% cap.
        Holding LGD and EAD fixed gives {money(selected.sensitivity.stressed_el)} expected loss,
        a change of {money(selected.sensitivity.delta_el)}.</p>
      <p>{selected.profile_note}</p>
      {selected.model && <>
        <h4>Illustrative model PD · {percent(selected.model.calibrated_probability)}</h4>
        <p>Model {selected.model.model_id} · Financial profile {selected.profile_version}.</p>
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Model risk drivers">
          <table><caption>Fictional financial ratios and raw model contributions</caption>
            <thead><tr><th scope="col">Financial characteristic</th><th scope="col">Input</th>
              <th scope="col">Log-odds contribution</th></tr></thead>
            <tbody>{selected.model.contributions.map(driver => <tr key={driver.feature}>
              <th scope="row">{ratioLabels[driver.feature]}</th>
              <td>{driver.feature === 'revenue_growth' || driver.feature === 'debt_to_assets'
                ? percent(selected.model!.inputs[driver.feature]) : selected.model!.inputs[driver.feature].toFixed(3) + '×'}</td>
              <td>{driver.log_odds.toFixed(3)}</td></tr>)}</tbody>
          </table>
        </div>
        <p>Positive values increase the raw logistic score. Calibration maps the score to the displayed probability.</p>
      </>}
    </>}
  </section>;
}
