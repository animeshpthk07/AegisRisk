import { money } from '../lib/format.mjs';

export const presets = {
  baseline: { label: 'Baseline', pd: '1', lgd: '1', ead: '1' },
  mild: { label: 'Mild recession', pd: '1.5', lgd: '1.1', ead: '1' },
  severe: { label: 'Severe recession', pd: '2', lgd: '1.25', ead: '1.1' },
  sector: { label: 'Sector shock', pd: '2.5', lgd: '1.2', ead: '1.1' },
} as const;
export type Preset = keyof typeof presets | 'custom';

type LossChange = { baseline_el: number; stressed_el: number; delta_el: number };
type IndustryImpact = LossChange & { industry: string };
type FacilityImpact = IndustryImpact & { id: string };
export type Stress = LossChange & {
  delta_pct: number | null;
  assumptions: string[];
  industry_impacts: IndustryImpact[];
  largest_changes: FacilityImpact[];
};

function close(a: number, b: number, scale = Math.max(Math.abs(a), Math.abs(b))) {
  return Math.abs(a - b) <= 1e-9 * Math.max(1, scale);
}
function validLoss(row: LossChange) {
  return row && [row.baseline_el, row.stressed_el, row.delta_el].every(Number.isFinite)
    && row.baseline_el >= 0 && row.stressed_el >= 0
    && close(row.stressed_el - row.baseline_el, row.delta_el,
      Math.max(row.baseline_el, row.stressed_el));
}
export function validScenario(result: Stress, segments: { industry: string; expected_loss: number }[]) {
  if (!validLoss(result) || !Array.isArray(result.assumptions)
      || !result.assumptions.every(note => typeof note === 'string')
      || !Array.isArray(result.industry_impacts) || !Array.isArray(result.largest_changes)) return false;
  if (result.baseline_el === 0 ? result.delta_pct !== null :
      !Number.isFinite(result.delta_pct) || !close(result.delta_pct!, result.delta_el / result.baseline_el)) return false;
  const groups = result.industry_impacts;
  const baselines = new Map(segments.map(row => [row.industry, row.expected_loss]));
  if (groups.length !== baselines.size || new Set(groups.map(row => row?.industry)).size !== groups.length) return false;
  if (!groups.every(row => validLoss(row) && baselines.has(row.industry)
      && close(row.baseline_el, baselines.get(row.industry)!))) return false;
  const sum = (key: keyof LossChange) => groups.reduce((total, row) => total + row[key], 0);
  if (!close(sum('baseline_el'), result.baseline_el) || !close(sum('stressed_el'), result.stressed_el)
      || !close(sum('delta_el'), result.delta_el, Math.max(result.baseline_el, result.stressed_el))) return false;
  const movers = result.largest_changes;
  return movers.length <= 10 && new Set(movers.map(row => row?.id)).size === movers.length
    && movers.every((row, i) => validLoss(row) && typeof row.id === 'string' && row.id.length > 0
      && baselines.has(row.industry) && row.delta_el !== 0
      && (i === 0 || Math.abs(movers[i - 1].delta_el) >= Math.abs(row.delta_el)));
}

export default function StressAttribution({ result }: { result: Stress }) {
  return <section aria-label="Scenario loss attribution">
    <h3>Expected loss by industry</h3>
    <div className="table-scroll" role="region" aria-label="Industry stress results" tabIndex={0}>
      <table><caption className="sr-only">Scenario losses by industry in INR</caption>
        <thead><tr><th scope="col">Industry</th><th scope="col">Baseline EL</th>
          <th scope="col">Stressed EL</th><th scope="col">Change</th></tr></thead>
        <tbody>{result.industry_impacts.map(row => <tr key={row.industry}>
          <th scope="row">{row.industry}</th><td>{money(row.baseline_el)}</td>
          <td>{money(row.stressed_el)}</td><td>{money(row.delta_el)}</td></tr>)}</tbody>
      </table>
    </div>
    <h3>Largest facility changes</h3>
    {result.largest_changes.length ? <>
      <p>Up to ten facilities, ranked by absolute change in one-year expected loss.</p>
      <div className="table-scroll" role="region" aria-label="Facility stress results" tabIndex={0}>
        <table><caption className="sr-only">Largest facility loss changes in INR</caption>
          <thead><tr><th scope="col">Facility ID</th><th scope="col">Industry</th>
            <th scope="col">Baseline EL</th><th scope="col">Stressed EL</th><th scope="col">Change</th></tr></thead>
          <tbody>{result.largest_changes.map(row => <tr key={row.id}>
            <th scope="row">{row.id}</th><td>{row.industry}</td><td>{money(row.baseline_el)}</td>
            <td>{money(row.stressed_el)}</td><td>{money(row.delta_el)}</td></tr>)}</tbody>
        </table>
      </div></> : <p>No facility changed expected loss under these assumptions.</p>}
  </section>;
}
