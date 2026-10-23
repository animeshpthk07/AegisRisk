'use client';
import { useEffect, useRef, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { money, percent } from '../lib/format.mjs';
import CsvPreview, { type SavedPortfolio } from './csv-preview';
import { renderReportHtml } from '../lib/report-html.mjs';
import ModelLab from './model-lab';

type Facility = { id: string; borrower: string; industry: string; geography: string; rating: string; pd: number; lgd: number; ead: number; expected_loss: number };
type Portfolio = { dataset_id: string | null; dataset_version: string; summary: { facility_count: number; total_ead: number; total_expected_loss: number; weighted_pd: number | null; weighted_lgd: number | null; borrower_hhi: number | null }; facilities: Facility[]; segments: { industry: string; ead: number; expected_loss: number; share: number }[]; warnings: string[] };
type Stress = { baseline_el: number; stressed_el: number; delta_el: number; delta_pct: number | null; assumptions: string[] };
type StressInputs = { pd_multiplier: number; lgd_multiplier: number; ead_multiplier: number; industry: string | null };
async function preparePdf(value: unknown): Promise<Blob> {
  const pdf = value as { media_type?: unknown; base64?: unknown; byte_length?: unknown; sha256?: unknown } | null;
  if (!pdf || pdf.media_type !== 'application/pdf' || typeof pdf.base64 !== 'string' ||
      pdf.base64.length > 5592408 || typeof pdf.byte_length !== 'number' ||
      !Number.isInteger(pdf.byte_length) || pdf.byte_length < 10 || pdf.byte_length > 4194304 ||
      typeof pdf.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(pdf.sha256)) {
    throw new Error('PDF integrity could not be verified. Nothing was downloaded.');
  }
  const bytes = Uint8Array.from(atob(pdf.base64), character => character.charCodeAt(0));
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)))
    .map(value => value.toString(16).padStart(2, '0')).join('');
  if (bytes.length !== pdf.byte_length || new TextDecoder().decode(bytes.slice(0, 5)) !== '%PDF-' || hash !== pdf.sha256) {
    throw new Error('PDF integrity could not be verified. Nothing was downloaded.');
  }
  return new Blob([bytes], { type: 'application/pdf' });
}
function downloadEvidence(report: unknown, filename: string, format: 'json' | 'html' | 'pdf', pdf?: Blob) {
  const content = format === 'html' ? renderReportHtml(report) : JSON.stringify(report, null, 2) + '\n';
  const blob = format === 'pdf' ? pdf : new Blob([content], { type: format === 'html' ? 'text/html;charset=utf-8' : 'application/json' });
  if (!blob) throw new Error('PDF unavailable. Nothing was downloaded.');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = filename + '.' + format;
  document.body.appendChild(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function read(path: string, signal?: AbortSignal) {
  const response = await fetch(`/api/${path}`, { signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error('The data service is unavailable. Check the API, migration and demo seed.');
  return response.json();
}
export default function Dashboard() {
  const [data, setData] = useState<Portfolio | null>(null);
  const [error, setError] = useState('');
  const [connected, setConnected] = useState(false);
  const [narrative, setNarrative] = useState('');
  const [query, setQuery] = useState('');
  const [industry, setIndustry] = useState('');
  const [pd, setPd] = useState('1.5');
  const [lgd, setLgd] = useState('1.1');
  const [ead, setEad] = useState('1');
  const [result, setResult] = useState<Stress | null>(null);
  const [submittedInputs, setSubmittedInputs] = useState<StressInputs | null>(null);
  const [scenarioBusy, setScenarioBusy] = useState(false);
  const [scenarioError, setScenarioError] = useState('');
  const [scenarioMessage, setScenarioMessage] = useState('');
  const scenarioAbort = useRef<AbortController | null>(null);
  const scenarioVersion = useRef(0);
  const [stressError, setStressError] = useState('');
  const [busy, setBusy] = useState(false);
  const [light, setLight] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);
  const [reportError, setReportError] = useState('');
  const [reportMessage, setReportMessage] = useState('');
  const reportAbort = useRef<AbortController | null>(null);
  const [datasetId, setDatasetId] = useState('');
  const [savedPortfolios, setSavedPortfolios] = useState<SavedPortfolio[]>([]);
  const [savingEnabled, setSavingEnabled] = useState(false);
  const [catalogBusy, setCatalogBusy] = useState(false);
  const [catalogError, setCatalogError] = useState('');
  const [nextOffset, setNextOffset] = useState(0);
  const [catalogTotal, setCatalogTotal] = useState(0);
  const loadVersion = useRef(0);
  const stressAbort = useRef<AbortController | null>(null);
  const catalogAbort = useRef<AbortController | null>(null);
  const suffix = datasetId ? '?dataset_id=' + encodeURIComponent(datasetId) : '';
  function invalidateScenario() {
    scenarioVersion.current += 1;
    stressAbort.current?.abort(); stressAbort.current = null;
    scenarioAbort.current?.abort(); scenarioAbort.current = null;
    setResult(null); setSubmittedInputs(null); setStressError(''); setBusy(false);
    setScenarioBusy(false); setScenarioError(''); setScenarioMessage('');
  }
  function chooseDataset(id: string) {
    if (id === datasetId) return;
    loadVersion.current += 1;
    invalidateScenario();
    reportAbort.current?.abort(); reportAbort.current = null;
    setReportBusy(false); setReportError(''); setReportMessage('');
    setDatasetId(id); setData(null); setNarrative(''); setError(''); setConnected(false);
    setResult(null); setStressError(''); setBusy(false); setQuery(''); setIndustry('');
  }
  async function loadCatalog(offset = 0) {
    catalogAbort.current?.abort();
    const controller = new AbortController(); catalogAbort.current = controller;
    setCatalogBusy(true); setCatalogError('');
    try {
      const catalog = await read('saved-portfolios?limit=100&offset=' + offset, controller.signal);
      if (catalogAbort.current !== controller || controller.signal.aborted) return;
      if (typeof catalog.enabled !== 'boolean' || !Array.isArray(catalog.items)) throw new Error('Invalid saved-portfolio response.');
      setSavingEnabled(catalog.enabled);
      setSavedPortfolios(previous => Array.from(new Map<string, SavedPortfolio>(
        [...(offset ? previous : []), ...catalog.items].map(item => [item.id, item])
      ).values()));
      setNextOffset(offset + catalog.items.length); setCatalogTotal(catalog.total);
    } catch (err) {
      if (catalogAbort.current === controller && !controller.signal.aborted) setCatalogError(err instanceof Error ? err.message : 'Saved portfolios unavailable.');
    } finally {
      if (catalogAbort.current === controller) { setCatalogBusy(false); catalogAbort.current = null; }
    }
  }
  function rememberSaved(portfolio: SavedPortfolio) {
    catalogAbort.current?.abort(); catalogAbort.current = null; setCatalogBusy(false); setCatalogError('');
    setSavedPortfolios(previous => [portfolio, ...previous.filter(item => item.id !== portfolio.id)]);
  }
  useEffect(() => {
    void loadCatalog();
    return () => { catalogAbort.current?.abort(); stressAbort.current?.abort(); reportAbort.current?.abort(); scenarioAbort.current?.abort(); };
  }, []);
  useEffect(() => {
    const controller = new AbortController(); const version = ++loadVersion.current;
    setData(null); setNarrative(''); setConnected(false); setError('');
    Promise.all([read('health', controller.signal), read('ready', controller.signal), read('portfolio' + suffix, controller.signal), read('explanation' + suffix, controller.signal)])
      .then(([, , portfolio, explanation]) => {
        if (controller.signal.aborted || version !== loadVersion.current) return;
        if ((portfolio.dataset_id || '') !== datasetId) throw new Error('The selected dataset could not be verified.');
        setConnected(true); setData(portfolio); setNarrative(explanation.text);
      })
      .catch(err => { if (!controller.signal.aborted && version === loadVersion.current) setError(err instanceof Error ? err.message : 'Portfolio unavailable.'); });
    return () => controller.abort();
  }, [datasetId, suffix]);
  async function runStress(event: React.FormEvent) {
    event.preventDefault();
    if (!data || busy || (data.dataset_id || '') !== datasetId) return;
    invalidateScenario();
    const inputs: StressInputs = { pd_multiplier: Number(pd), lgd_multiplier: Number(lgd), ead_multiplier: Number(ead), industry: industry || null };
    const scenarioToken = scenarioVersion.current;
    const version = loadVersion.current; const controller = new AbortController(); stressAbort.current = controller;
    setBusy(true); setStressError(''); setResult(null);
    try {
      const response = await fetch('/api/stress' + suffix, { method: 'POST', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]), headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(inputs) });
      if (!response.ok) throw new Error('Stress calculation failed. Use multipliers between 0 and 10.');
      const calculated = await response.json();
      if (!controller.signal.aborted && version === loadVersion.current && scenarioToken === scenarioVersion.current && stressAbort.current === controller) {
        if (![calculated.baseline_el, calculated.stressed_el, calculated.delta_el].every(Number.isFinite) ||
            (calculated.delta_pct !== null && !Number.isFinite(calculated.delta_pct)) || !Array.isArray(calculated.assumptions)) throw new Error('Invalid scenario result. Please retry.');
        setResult(calculated); setSubmittedInputs(inputs);
      }
    } catch (err) {
      if (!controller.signal.aborted && version === loadVersion.current && scenarioToken === scenarioVersion.current && stressAbort.current === controller) setStressError(err instanceof Error ? err.message : 'Calculation unavailable');
    } finally {
      if (version === loadVersion.current && scenarioToken === scenarioVersion.current && stressAbort.current === controller) { setBusy(false); stressAbort.current = null; }
    }
  }
  async function downloadReport(format: 'json' | 'html' | 'pdf' = 'json') {
    if (!data || reportAbort.current || (data.dataset_id || '') !== datasetId) return;
    const version = loadVersion.current;
    const selectedId = datasetId;
    const controller = new AbortController(); reportAbort.current = controller;
    setReportBusy(true); setReportError(''); setReportMessage('');
    try {
      const payload = await read((format === 'pdf' ? 'report-pdf' : 'report') + suffix, controller.signal);
      const report = format === 'pdf' ? payload.report : payload;
      if (controller.signal.aborted || version !== loadVersion.current || reportAbort.current !== controller) return;
      if (!report || report.schema_version !== 'aegisrisk.baseline-report.v1' ||
          report.dataset_id !== (selectedId || null) || report.dataset_version !== data.dataset_version ||
          report.synthetic !== true || report.scenario_included !== false ||
          report.report_kind !== 'baseline_only' || !Array.isArray(report.source?.input_rows)) {
        throw new Error('Report identity could not be verified. Nothing was downloaded.');
      }
      const pdf = format === 'pdf' ? await preparePdf(payload.pdf) : undefined;
      if (controller.signal.aborted || version !== loadVersion.current || reportAbort.current !== controller) return;
      downloadEvidence(report, 'aegisrisk-baseline-' + (selectedId || 'demo'), format, pdf);
      setReportMessage('Baseline report prepared for download. It does not include a stress scenario.');
    } catch (err) {
      if (!controller.signal.aborted && version === loadVersion.current && reportAbort.current === controller) {
        setReportError(err instanceof Error ? err.message : 'Report unavailable. Please retry.');
      }
    } finally {
      if (version === loadVersion.current && reportAbort.current === controller) { setReportBusy(false); reportAbort.current = null; }
    }
  }
  async function downloadScenarioReport(format: 'json' | 'html' | 'pdf' = 'json') {
    if (!data || !result || !submittedInputs || busy || scenarioAbort.current || (data.dataset_id || '') !== datasetId) return;
    const version = loadVersion.current; const scenarioToken = scenarioVersion.current;
    const selectedId = datasetId; const inputs = { ...submittedInputs }; const expected = result;
    const controller = new AbortController(); scenarioAbort.current = controller;
    setScenarioBusy(true); setScenarioError(''); setScenarioMessage('');
    try {
      const response = await fetch('/api/' + (format === 'pdf' ? 'scenario-report-pdf' : 'scenario-report') + suffix, { method: 'POST', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]), headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(inputs) });
      if (!response.ok) throw new Error('Scenario report unavailable. Please retry.');
      const payload = await response.json();
      const report = format === 'pdf' ? payload.report : payload;
      if (controller.signal.aborted || version !== loadVersion.current || scenarioToken !== scenarioVersion.current || scenarioAbort.current !== controller) return;
      const echoed = report?.scenario?.inputs;
      if (!report || report.schema_version !== 'aegisrisk.scenario-report.v1' ||
          report.report_kind !== 'baseline_and_scenario' || report.scenario_included !== true ||
          report.synthetic !== true || report.dataset_id !== (selectedId || null) || report.dataset_version !== data.dataset_version ||
          report.baseline?.dataset_id !== report.dataset_id || report.baseline?.dataset_version !== report.dataset_version ||
          !Array.isArray(report.baseline?.source?.input_rows) || !echoed ||
          echoed.pd_multiplier !== inputs.pd_multiplier || echoed.lgd_multiplier !== inputs.lgd_multiplier ||
          echoed.ead_multiplier !== inputs.ead_multiplier || echoed.industry !== inputs.industry ||
          report.scenario.baseline_el !== expected.baseline_el || report.scenario.stressed_el !== expected.stressed_el ||
          report.scenario.delta_el !== expected.delta_el || report.scenario.delta_pct !== expected.delta_pct) {
        throw new Error('Scenario report does not match the calculated result. Nothing was downloaded.');
      }
      const pdf = format === 'pdf' ? await preparePdf(payload.pdf) : undefined;
      if (controller.signal.aborted || version !== loadVersion.current || scenarioToken !== scenarioVersion.current || scenarioAbort.current !== controller) return;
      downloadEvidence(report, 'aegisrisk-scenario-' + (selectedId || 'demo'), format, pdf);
      setScenarioMessage('Scenario report prepared for download with the calculated assumptions.');
    } catch (err) {
      if (!controller.signal.aborted && version === loadVersion.current && scenarioToken === scenarioVersion.current && scenarioAbort.current === controller) {
        setScenarioError(err instanceof Error ? err.message : 'Scenario report unavailable.');
      }
    } finally {
      if (version === loadVersion.current && scenarioToken === scenarioVersion.current && scenarioAbort.current === controller) { setScenarioBusy(false); scenarioAbort.current = null; }
    }
  }
  const rows = data?.facilities.filter((r) => `${r.id} ${r.borrower} ${r.industry}`.toLowerCase().includes(query.toLowerCase())) || [];
  return <div className={light ? 'app light' : 'app'}>
    <a className="skip" href="#overview">Skip to dashboard</a>
    <aside><div className="brand"><span className="brandmark">A</span><div>AegisRisk<small>RISK INTELLIGENCE</small></div></div>
      <p className="eyebrow">ANALYST WORKSPACE</p><nav aria-label="Main navigation"><a href="#overview">◈ &nbsp; Portfolio overview</a><a href="#exposures">▤ &nbsp; Credit explorer</a><a href="#stress">↗ &nbsp; Stress laboratory</a><a href="#import-preview">⇧ &nbsp; CSV / Excel preview</a><a href="#model-lab">◇ &nbsp; Synthetic Model Lab</a><a href="#methodology">◇ &nbsp; Methodology</a></nav>
      <div className="side-note"><span className="dot"/> EDUCATIONAL ENVIRONMENT<p>Fictional portfolio.<br/>Real, inspectable calculations.</p></div>
    </aside>
    <main><header><div className="breadcrumb">WORKSPACE <span>/</span> CREDIT RISK</div><button onClick={() => setLight(!light)} aria-label="Toggle light and dark theme">{light ? 'Dark theme' : 'Light theme'}</button></header>
      <div className="title-row" id="overview"><div><p className="eyebrow">PORTFOLIO MONITOR · ONE-YEAR HORIZON</p><h1>Clarity behind every exposure.</h1><p className="subtitle">Credit risk, concentration and scenario sensitivity in one transparent view.</p></div><span className="badge">SYNTHETIC DEMO</span></div>
      <div className="status"><span className={connected ? 'dot' : 'dot pending'}/>{connected ? 'API + database connected' : error ? 'Connection unavailable' : 'Connecting to backend…'}<span>INR · {data?.dataset_version || 'Awaiting dataset'} · No external AI</span></div>
      <section className="panel" aria-label="Dataset selection"><label htmlFor="active-portfolio">Active portfolio</label><select id="active-portfolio" value={datasetId} onChange={event => chooseDataset(event.target.value)}><option value="">Built-in fictional demo (40 facilities)</option>{datasetId && !savedPortfolios.some(item => item.id === datasetId) && <option value={datasetId}>Selected saved portfolio · {datasetId.slice(0, 8)} (outside current list)</option>}{savedPortfolios.map(item => <option key={item.id} value={item.id}>{item.name} · {item.row_count} facilities</option>)}</select><p className="muted">Saved snapshots stay separate from the demo. Switching portfolios clears the previous scenario and calculation note.</p><div className="preview-actions"><button onClick={() => void loadCatalog()} disabled={catalogBusy}>Refresh saved portfolios</button>{nextOffset < catalogTotal && <button onClick={() => void loadCatalog(nextOffset)} disabled={catalogBusy}>Load more portfolios</button>}{catalogBusy && <span role="status">Loading saved portfolios…</span>}</div>{catalogError && <p role="alert">{catalogError}</p>}</section>
      {error && <div role="alert" className="warning">{error} <button onClick={() => window.location.reload()}>Retry</button></div>}
      {!data && !error && <p role="status" className="panel">Loading calculated portfolio metrics…</p>}
      {data && <><section className="kpis" aria-label="Portfolio metrics">
        <article><p>Exposure at default</p><h2>{money(data.summary.total_ead)}</h2><small>{data.summary.facility_count} fictional facilities</small></article>
        <article><p>One-year expected loss</p><h2>{money(data.summary.total_expected_loss)}</h2><small>Σ (PD × LGD × EAD)</small></article>
        <article><p>EAD-weighted PD</p><h2>{percent(data.summary.weighted_pd)}</h2><small>Illustrative probability of default</small></article>
        <article><p>EAD-weighted LGD</p><h2>{percent(data.summary.weighted_lgd)}</h2><small>Illustrative loss given default</small></article>
      </section><div className="two-col"><section className="panel"><div className="section-head"><h2>Where exposure sits</h2><span>BY INDUSTRY</span></div><p className="muted">Exposure at default · INR millions</p><div className="chart" role="img" aria-label="Industry exposure chart; exact values in the adjacent table"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.segments.map(s => ({ ...s, millions: s.ead / 1000000 }))}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#53657755"/><XAxis dataKey="industry" tick={{ fontSize: 10, fill: '#8f9fb4' }} interval={0}/><YAxis tick={{ fill: '#8f9fb4', fontSize: 11 }}/><Tooltip contentStyle={{ background: '#152333', border: '1px solid #456', color: '#fff' }}/><Bar dataKey="millions" name="INR million" fill="#53d6b0" radius={[4, 4, 0, 0]}/></BarChart></ResponsiveContainer></div></section>
      <section className="panel"><div className="section-head"><h2>Concentration lens</h2><span>EXPOSURE SHARE</span></div><table><caption className="sr-only">Industry exposures and shares</caption><thead><tr><th>Industry</th><th>Exposure</th><th>Share</th></tr></thead><tbody>{data.segments.map(s => <tr key={s.industry}><td>{s.industry}</td><td>{money(s.ead)}</td><td>{percent(s.share)}</td></tr>)}</tbody></table><p className="muted">Borrower HHI: <strong>{data.summary.borrower_hhi?.toFixed(4) ?? 'Not defined'}</strong> · scale 0–1</p></section></div>
      <section className="insight"><span className="eyebrow">CALCULATION NOTE · DETERMINISTIC</span><p>{narrative}</p><small>No credit recommendation. Figures are derived from the displayed dataset.</small></section>
      <section className="panel" id="exposures"><div className="section-head"><div><p className="eyebrow">FACILITY-LEVEL EVIDENCE</p><h2>Credit explorer</h2></div><label>Search facilities<input placeholder="Borrower, ID or industry" value={query} onChange={e => setQuery(e.target.value)}/></label></div><div className="table-scroll"><table><caption className="sr-only">Fictional facility metrics, INR and one-year PD</caption><thead><tr><th>Borrower / ID</th><th>Industry</th><th>Rating</th><th>PD</th><th>LGD</th><th>EAD</th><th>Expected loss</th></tr></thead><tbody>{rows.map(r => <tr key={r.id}><td>{r.borrower}<small>{r.id} · {r.geography}</small></td><td>{r.industry}</td><td><span className="rating">{r.rating}</span></td><td>{percent(r.pd)}</td><td>{percent(r.lgd)}</td><td>{money(r.ead)}</td><td>{money(r.expected_loss)}</td></tr>)}</tbody></table>{!rows.length && <p>No facilities match your search.</p>}</div><p className="muted">Showing {rows.length} of {data.facilities.length} facilities. Demo inputs—not predictions.</p></section>
      <section className="panel" id="stress"><p className="eyebrow">SCENARIO SENSITIVITY</p><h2>Explore a change in assumptions.</h2><p className="muted">Multipliers change inputs, not the underlying economic model. PD and LGD are capped at 100%.</p><form onSubmit={runStress}><div className="form-grid"><label>PD multiplier<input type="number" min="0" max="10" step="0.05" required value={pd} onChange={e=>{ invalidateScenario(); setPd(e.target.value); }}/></label><label>LGD multiplier<input type="number" min="0" max="10" step="0.05" required value={lgd} onChange={e=>{ invalidateScenario(); setLgd(e.target.value); }}/></label><label>EAD multiplier<input type="number" min="0" max="10" step="0.05" required value={ead} onChange={e=>{ invalidateScenario(); setEad(e.target.value); }}/></label><label>Scope<select aria-label="Scenario scope" value={industry} onChange={e=>{ invalidateScenario(); setIndustry(e.target.value); }}><option value="">Whole portfolio</option>{data.segments.map(s=><option key={s.industry}>{s.industry}</option>)}</select></label></div><button className="primary" disabled={busy}>{busy ? 'Calculating…' : 'Calculate scenario →'}</button></form>{stressError && <p role="alert">{stressError}</p>}{result && <div aria-live="polite" className="scenario-result"><div>Baseline EL<strong>{money(result.baseline_el)}</strong></div><div>Stressed EL<strong>{money(result.stressed_el)}</strong></div><div>Change<strong>{money(result.delta_el)} · {percent(result.delta_pct)}</strong></div><p>{result.assumptions.join(' ')}</p>{submittedInputs && <p>Calculated assumptions: PD ×{submittedInputs.pd_multiplier}, LGD ×{submittedInputs.lgd_multiplier}, EAD ×{submittedInputs.ead_multiplier}; scope: {submittedInputs.industry || 'Whole portfolio'}.</p>}<button onClick={() => void downloadScenarioReport()} disabled={scenarioBusy}>{scenarioBusy ? 'Preparing scenario report…' : 'Download scenario report (JSON)'}</button><button onClick={() => void downloadScenarioReport('html')} disabled={scenarioBusy}>Download scenario report (printable HTML)</button><button onClick={() => void downloadScenarioReport('pdf')} disabled={scenarioBusy}>Download scenario report (PDF)</button></div>}<p className="muted">Changing any assumption clears the result and cancels its download. Recalculate before exporting. Scenario reports contain assumptions, not forecasts.</p>{scenarioError && <p role="alert">{scenarioError}</p>}{scenarioMessage && <p role="status">{scenarioMessage}</p>}</section>
      <section className="panel" aria-label="Baseline report"><p className="eyebrow">PORTABLE EVIDENCE</p><h2>Take the calculations with you.</h2><p className="muted">Download the active portfolio’s baseline summary, facility inputs, decimal calculation evidence, methodology and source fingerprint as JSON. This does not include your stress scenario and is not an audit or regulatory report.</p><button onClick={() => void downloadReport()} disabled={reportBusy}>{reportBusy ? 'Preparing report…' : 'Download baseline report (JSON)'}</button><button onClick={() => void downloadReport('html')} disabled={reportBusy}>Download baseline report (printable HTML)</button><button onClick={() => void downloadReport('pdf')} disabled={reportBusy}>Download baseline report (PDF)</button><p className="muted">PDF reports are generated by the server from the same evidence. Printable HTML remains available offline. Both contain no scripts or external assets.</p>{reportError && <p role="alert">{reportError}</p>}{reportMessage && <p role="status">{reportMessage}</p>}</section>
      <section id="methodology" className="panel"><p className="eyebrow">GOVERNANCE / FOUNDATION BUILD</p><h2>Know what this does—and doesn’t do.</h2>{data.warnings.map(w=><p key={w}>{w}</p>)}<p>Expected loss is calculated facility by facility using decimal arithmetic. Weighted metrics use EAD; HHI sums squared borrower exposure shares. This is not IFRS 9 ECL, a regulatory capital model or an autonomous approval tool.</p><p>Synthetic CSV and values-only XLSX previews never save data. On explicitly enabled single-user instances, reviewed files can be saved as separate, immutable portfolios. Baseline and scenario-comparison JSON and printable HTML evidence exports are available. An isolated synthetic Model Lab demonstrates training and held-out evaluation; it does not supply portfolio PDs. Server-generated PDF exports are available; authentication and public deployment remain future milestones. No real banking data is used.</p></section></>}
      <CsvPreview enabled={savingEnabled} onSaved={rememberSaved} onOpen={chooseDataset}/>
      <ModelLab/>
      <footer>MATHEMATICS CALCULATES. MODELS ESTIMATE. AI EXPLAINS. HUMANS DECIDE.<span>AegisRisk · Educational portfolio project · Not affiliated with any bank</span></footer>
    </main>
  </div>;
}
