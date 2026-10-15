'use client';

import { useEffect, useRef, useState } from 'react';
import { percent } from '../lib/format.mjs';

const MAX_BYTES = 262144;
const EXAMPLE = 'id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon\n' +
  'SYN-CSV-001,Fictional Orchard,Energy,West,B,0.1,0.5,1000.00,INR,one_year\n' +
  'SYN-CSV-002,Fictional Meadow,Services,South,A,0.02,0.4,2000.00,INR,one_year\n';
const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', minimumFractionDigits: 2, maximumFractionDigits: 2,
});
type Summary = {
  facility_count: number; total_ead: number; total_expected_loss: number;
  weighted_pd: number | null; weighted_lgd: number | null; borrower_hhi: number | null;
};
type Preview = {
  valid: boolean; persisted: false; row_count: number; valid_rows: number; invalid_rows: number;
  issue_count: number; issues_truncated: boolean;
  issues: { row: number; column: string | null; code: string; message: string }[];
  summary: Summary | null; warnings: string[];
};

export default function CsvPreview() {
  const [file, setFile] = useState<Blob | null>(null);
  const [name, setName] = useState('No file selected');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Preview | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const activeRequest = useRef<AbortController | null>(null);
  useEffect(() => () => activeRequest.current?.abort(), []);

  function selectFile(selected: File | undefined) {
    setResult(null); setError(''); setFile(null); setName('No file selected');
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith('.csv')) {
      setError('Choose a .csv file. XLSX and PDF are not supported by this preview.'); return;
    }
    if (selected.size === 0 || selected.size > MAX_BYTES) {
      setError('Choose a non-empty CSV no larger than 256 KiB.'); return;
    }
    setFile(selected); setName(selected.name);
  }

  function example() {
    if (input.current) input.current.value = '';
    setFile(new Blob([EXAMPLE], { type: 'text/csv' }));
    setName('Built-in fictional example (2 facilities)'); setResult(null); setError('');
  }

  async function runPreview(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !confirmed || busy) return;
    setBusy(true); setError(''); setResult(null);
    const controller = new AbortController();
    activeRequest.current = controller;
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch('/api/import-preview', {
        method: 'POST', headers: { 'Content-Type': 'text/csv', 'X-AegisRisk-Synthetic': 'true' },
        body: file, signal: controller.signal,
      });
      const data = await response.json();
      if (typeof data.valid !== 'boolean' || data.persisted !== false ||
          !Array.isArray(data.issues) || !Array.isArray(data.warnings) ||
          (data.valid && (!response.ok || !data.summary))) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Preview unavailable. Please retry.');
      }
      setResult(data as Preview);
    } catch (err) {
      setError(controller.signal.aborted ? 'Preview timed out. Please retry.' :
        err instanceof Error ? err.message : 'Preview unavailable. Please retry.');
    } finally {
      clearTimeout(timeout); activeRequest.current = null; setBusy(false);
    }
  }

  return <section className="panel" id="import-preview" aria-labelledby="csv-preview-title">
    <p className="eyebrow">DATA QUALITY / PREVIEW ONLY</p>
    <h2 id="csv-preview-title">Check a fictional portfolio CSV.</h2>
    <p className="muted">Validate rows and inspect calculated totals before any future import.
      This preview never saves or replaces the active portfolio. Do not upload real customer data.</p>
    <form onSubmit={runPreview} aria-busy={busy}>
      <label htmlFor="portfolio-csv">Synthetic portfolio CSV</label>
      <input ref={input} id="portfolio-csv" type="file" accept=".csv,text/csv" disabled={busy}
        aria-describedby="csv-limits" onChange={event => selectFile(event.target.files?.[0])}/>
      <p id="csv-limits" className="muted">UTF-8 · 256 KiB maximum · 1,000 rows · INR · one-year PD.
        PD/LGD are fractions (0.05 means 5%), not percentages.</p>
      <div className="preview-actions">
        <button type="button" onClick={example} disabled={busy}>Use fictional example</button>
        <a href={'data:text/csv;charset=utf-8,' + encodeURIComponent(EXAMPLE)}
          download="aegisrisk-synthetic-example.csv">Download example CSV</a>
      </div>
      <p role="status">{name}</p>
      <label className="preview-consent">
        <input type="checkbox" checked={confirmed} disabled={busy} onChange={event => {
          setConfirmed(event.target.checked); setResult(null);
        }}/>
        I confirm this file contains only fictional data, with no customer or personal information.
      </label>
      <button className="primary" disabled={!file || !confirmed || busy}>
        {busy ? 'Validating CSV…' : 'Validate and preview'}
      </button>
    </form>
    {error && <p role="alert" className="warning">{error}</p>}
    <div aria-live="polite" aria-atomic="true">
      {result && <p className={result.valid ? 'insight' : 'warning'}>
        {result.valid ? 'Validation passed.' : 'Validation failed. No totals calculated.'}
        {' '}{result.row_count} rows checked; {result.invalid_rows} invalid. Nothing was saved.
      </p>}
    </div>
    {result?.valid && result.summary && <>
      <div className="kpis" aria-label="Uploaded file preview metrics">
        <article><p>Preview facilities</p><h3>{result.summary.facility_count}</h3></article>
        <article><p>Preview EAD</p><h3>{inr.format(result.summary.total_ead)}</h3></article>
        <article><p>Preview one-year EL</p><h3>{inr.format(result.summary.total_expected_loss)}</h3></article>
        <article><p>Preview weighted PD</p><h3>{percent(result.summary.weighted_pd)}</h3></article>
      </div>
      <p>Weighted LGD: {percent(result.summary.weighted_lgd)} · Borrower HHI:
        {' '}{result.summary.borrower_hhi?.toFixed(4) ?? 'Not defined (zero exposure)'}</p>
    </>}
    {result && result.issues.length > 0 && <div className="table-scroll">
      <table><caption>Validation issues — CSV record numbers include the header</caption>
        <thead><tr><th scope="col">Record</th><th scope="col">Field</th><th scope="col">Fix required</th></tr></thead>
        <tbody>{result.issues.map((issue, index) => <tr key={index}>
          <td>{issue.row}</td><td>{issue.column || 'Record'}</td><td>{issue.message}</td>
        </tr>)}</tbody>
      </table>
      {result.issues_truncated && <p>Showing the first 100 of {result.issue_count} issues. Fix and retry.</p>}
    </div>}
    {result && <ul className="muted">{result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>}
    <details><summary>CSV schema and limitations</summary>
      <p className="preview-schema">id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon</p>
      <p>Every row needs all 10 fields; column order may vary. Use INR and one_year.
        IDs must be unique within the file. EAD allows two decimal places; PD/LGD allow ten.
        Use consistent borrower names for concentration calculations.</p>
      <p>Only synthetic CSV preview is supported. Persisted imports, XLSX and production upload security are not complete.</p>
      <a href="https://github.com/animeshpthk07/AegisRisk/blob/main/docs/CONTRACT.md">Full validation contract</a>
    </details>
  </section>;
}
