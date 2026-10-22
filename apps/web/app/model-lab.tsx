'use client';
import { useEffect, useRef, useState, type FormEvent } from 'react';

const fields = [
  { name: 'debt_to_assets', label: 'Fictional debt / assets', min: 0, max: 1.5, initial: '0.6' },
  { name: 'interest_coverage', label: 'Fictional interest coverage', min: 0, max: 10, initial: '3' },
  { name: 'current_ratio', label: 'Fictional current ratio', min: 0, max: 4, initial: '1.5' },
  { name: 'revenue_growth', label: 'Fictional revenue growth', min: -0.5, max: 0.5, initial: '0.05' },
] as const;
const metrics = ['roc_auc', 'average_precision', 'brier_score', 'log_loss'] as const;
const models = ['training_prior', 'raw_logistic', 'calibrated_logistic'] as const;
type Feature = typeof fields[number]['name'];
type ModelCard = {
  schema_version: string; model_id: string; synthetic: boolean; portfolio_integration: boolean;
  warning: string; dataset_sha256: string;
  splits: Record<string, { rows: number; events: number; event_rate: number; ids_sha256: string }>;
  metrics: Record<typeof models[number], Record<typeof metrics[number], number>>;
  calibration_bins: { lower: number; upper: number; count: number; mean_prediction: number | null; observed_rate: number | null }[];
  limitations: string[]; versions: Record<string, string>;
};
type Prediction = {
  model_id: string; synthetic: boolean; portfolio_integration: boolean;
  inputs: Record<Feature, number>; raw_probability: number; calibrated_probability: number;
  raw_log_odds: number; intercept: number;
  contributions: { feature: Feature; log_odds: number }[];
};
const initial = Object.fromEntries(fields.map(field => [field.name, field.initial])) as Record<Feature, string>;
const pct = (value: number) => (value * 100).toFixed(2) + '%';

export default function ModelLab() {
  const [card, setCard] = useState<ModelCard | null>(null);
  const [cardBusy, setCardBusy] = useState(false);
  const [cardError, setCardError] = useState('');
  const [values, setValues] = useState(initial);
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<Prediction | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const cardAbort = useRef<AbortController | null>(null);
  const predictAbort = useRef<AbortController | null>(null);
  useEffect(() => () => { cardAbort.current?.abort(); predictAbort.current?.abort(); }, []);
  function invalidate() {
    predictAbort.current?.abort(); predictAbort.current = null;
    setResult(null); setBusy(false); setError('');
  }
  async function loadCard() {
    cardAbort.current?.abort(); invalidate(); setCard(null);
    const controller = new AbortController(); cardAbort.current = controller;
    setCardBusy(true); setCardError('');
    try {
      const response = await fetch('/api/model-card', { cache: 'no-store', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) });
      if (!response.ok) throw new Error('Model evidence unavailable. Please retry.');
      const evidence: ModelCard = await response.json();
      if (controller.signal.aborted || cardAbort.current !== controller) return;
      if (evidence.schema_version !== 'aegisrisk.model-card.v1' || evidence.model_id !== 'synthetic-logistic-v1' ||
          evidence.synthetic !== true || evidence.portfolio_integration !== false ||
          !models.every(name => metrics.every(metric => Number.isFinite(evidence.metrics?.[name]?.[metric]))) ||
          !['train', 'calibration', 'test'].every(name => Number.isInteger(evidence.splits?.[name]?.rows)) ||
          !Array.isArray(evidence.calibration_bins) || !Array.isArray(evidence.limitations)) {
        throw new Error('Invalid model evidence. Nothing is displayed; please retry.');
      }
      setCard(evidence);
    } catch (err) {
      if (!controller.signal.aborted && cardAbort.current === controller) setCardError(err instanceof Error ? err.message : 'Model evidence unavailable.');
    } finally {
      if (cardAbort.current === controller) { setCardBusy(false); cardAbort.current = null; }
    }
  }
  async function estimate(event: FormEvent) {
    event.preventDefault();
    if (!card || !consent || busy) return;
    invalidate();
    const inputs = Object.fromEntries(fields.map(field => [field.name, Number(values[field.name])])) as Record<Feature, number>;
    if (fields.some(field => !values[field.name].trim() || !Number.isFinite(inputs[field.name]) || inputs[field.name] < field.min || inputs[field.name] > field.max)) {
      setError('Enter finite fictional ratios within the displayed ranges.'); return;
    }
    const controller = new AbortController(); predictAbort.current = controller; setBusy(true);
    try {
      const response = await fetch('/api/model-predict', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ synthetic: true, ...inputs }), signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) });
      if (!response.ok) throw new Error('Synthetic estimate unavailable. Check the ratios and retry.');
      const prediction: Prediction = await response.json();
      if (controller.signal.aborted || predictAbort.current !== controller) return;
      if (prediction.model_id !== card.model_id || prediction.synthetic !== true || prediction.portfolio_integration !== false ||
          ![prediction.raw_probability, prediction.calibrated_probability].every(value => Number.isFinite(value) && value >= 0 && value <= 1) ||
          ![prediction.raw_log_odds, prediction.intercept].every(Number.isFinite) ||
          !fields.every(field => prediction.inputs?.[field.name] === inputs[field.name]) ||
          !Array.isArray(prediction.contributions) || prediction.contributions.length !== fields.length ||
          !fields.every(field => prediction.contributions.filter(item => item.feature === field.name && Number.isFinite(item.log_odds)).length === 1) ||
          Math.abs(prediction.intercept + prediction.contributions.reduce((sum, item) => sum + item.log_odds, 0) - prediction.raw_log_odds) > 1e-8) {
        throw new Error('Estimate identity could not be verified. Please retry.');
      }
      setResult(prediction);
    } catch (err) {
      if (!controller.signal.aborted && predictAbort.current === controller) setError(err instanceof Error ? err.message : 'Estimate unavailable.');
    } finally {
      if (predictAbort.current === controller) { setBusy(false); predictAbort.current = null; }
    }
  }
  return <section id="model-lab" className="panel" aria-label="Synthetic Model Lab">
    <p className="eyebrow">MODEL LAB / SYNTHETIC RESEARCH</p>
    <h2>Inspect a model. Don’t mistake it for a bank.</h2>
    <p className="muted">Logistic regression trained on 3,000 fictional ratio records. Separate training, calibration and test splits. This lab never changes portfolio PDs, expected losses or reports.</p>
    <button onClick={() => void loadCard()} disabled={cardBusy}>{cardBusy ? 'Loading model evidence…' : 'Load model evidence'}</button>
    {cardError && <p role="alert">{cardError}</p>}
    {card && <div>
      <p role="status">Synthetic model evidence ready · {card.model_id}</p>
      <p className="warning">{card.warning}</p>
      <div className="table-scroll"><table aria-label="Held-out synthetic model metrics"><caption>Untouched synthetic test data · higher AUC / AP, lower Brier / log loss are better</caption><thead><tr><th>Model</th>{metrics.map(metric => <th key={metric}>{metric.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{models.map(name => <tr key={name}><th>{name.replaceAll('_', ' ')}</th>{metrics.map(metric => <td key={metric}>{card.metrics[name][metric].toFixed(4)}</td>)}</tr>)}</tbody></table></div>
      <p>Calibration is not assumed to improve the raw model. These scores measure an artificial generator—not real borrower default prediction.</p>
      <div className="table-scroll"><table aria-label="Model data splits"><thead><tr><th>Split</th><th>Rows</th><th>Simulated events</th><th>Event rate</th></tr></thead><tbody>{Object.entries(card.splits).map(([name, split]) => <tr key={name}><th>{name}</th><td>{split.rows}</td><td>{split.events}</td><td>{pct(split.event_rate)}</td></tr>)}</tbody></table></div>
      <details><summary>Calibration bins, provenance and limitations</summary>
        <div className="table-scroll"><table aria-label="Synthetic calibration bins"><thead><tr><th>Probability bin</th><th>Count</th><th>Mean prediction</th><th>Observed rate</th></tr></thead><tbody>{card.calibration_bins.map(bin => <tr key={bin.lower}><td>{pct(bin.lower)}–{pct(bin.upper)}</td><td>{bin.count}</td><td>{bin.mean_prediction === null ? 'Empty' : pct(bin.mean_prediction)}</td><td>{bin.observed_rate === null ? 'Empty' : pct(bin.observed_rate)}</td></tr>)}</tbody></table></div>
        <p style={{ overflowWrap: 'anywhere' }}>Dataset SHA-256: {card.dataset_sha256}</p>
        <p>Runtime: {Object.entries(card.versions).map(([name, value]) => name + ' ' + value).join(' · ')}</p>
        <ul>{card.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      </details>
      <h3>Try one fictional ratio profile</h3><p>Ratios are unitless; revenue growth 0.05 means 5%. No names, financial documents or real borrower information.</p>
      <form onSubmit={estimate}><div className="form-grid">{fields.map(field => <label key={field.name}>{field.label}<input aria-label={field.label} type="number" required min={field.min} max={field.max} step="any" value={values[field.name]} onChange={event => { invalidate(); setValues(previous => ({ ...previous, [field.name]: event.target.value })); }}/><small>{field.min} to {field.max}</small></label>)}</div>
        <label><input type="checkbox" checked={consent} onChange={event => { invalidate(); setConsent(event.target.checked); }}/> I confirm these ratios are fictional and not for a lending decision.</label>
        <button className="primary" disabled={!consent || busy}>{busy ? 'Estimating synthetic event…' : 'Estimate fictional event'}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {result && <section aria-label="Synthetic estimate" aria-live="polite">
        <h3>Fictional event estimate—not a credit decision</h3><p>Raw logistic: <strong>{pct(result.raw_probability)}</strong> · Calibrated: <strong>{pct(result.calibrated_probability)}</strong></p>
        <p>Raw log-odds: {result.raw_log_odds.toFixed(6)} = intercept {result.intercept.toFixed(6)} + the contributions below. These are standardized logistic contributions, not SHAP values, causal effects or calibrated-probability contributions.</p>
        <div className="table-scroll"><table aria-label="Raw model contributions"><thead><tr><th>Feature</th><th>Submitted value</th><th>Raw log-odds contribution</th></tr></thead><tbody>{result.contributions.map(item => <tr key={item.feature}><th>{item.feature.replaceAll('_', ' ')}</th><td>{result.inputs[item.feature]}</td><td>{item.log_odds.toFixed(6)}</td></tr>)}</tbody></table></div>
      </section>}
      <p className="muted">Changing any input or withdrawing consent clears the estimate and cancels pending requests. This model has no access to the active portfolio.</p>
    </div>}
  </section>;
}
