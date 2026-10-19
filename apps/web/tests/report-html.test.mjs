import test from 'node:test';
import assert from 'node:assert/strict';
import { renderReportHtml } from '../lib/report-html.mjs';

function baseline() {
  return {
    schema_version: 'aegisrisk.baseline-report.v1', report_kind: 'baseline_only',
    scenario_included: false, synthetic: true, dataset_id: null, dataset_version: 'demo-v1',
    currency: 'INR', horizon: 'one_year', generated_at: '2026-10-19T08:00:00+00:00',
    summary: { facility_count: 1, weighted_pd: 0.1, weighted_lgd: 0.5, borrower_hhi: 1 },
    source: { canonical_sha256: 'a'.repeat(64), canonicalization: 'Not a signature.', input_rows: [
      { id: 'SYN-1', borrower: 'Fictional Birch', industry: 'Energy', geography: 'West', rating: 'B',
        pd: '0.1', lgd: '0.5', ead: '1000' },
    ] },
    calculation: { formula: 'EL = sum(PD * LGD * EAD)', probability_unit: 'fraction_0_to_1',
      decimal_precision: 28, decimal_rounding: 'ROUND_HALF_EVEN', total_ead_decimal: '1000',
      total_expected_loss_decimal: '50.0000000000000000000001',
      facility_expected_loss_decimal: [{ id: 'SYN-1', expected_loss: '50' }], notes: ['Educational only.'] },
    explanation: { text: 'Fictional calculation.', disclaimer: 'No lending decision.' },
    warnings: ['Not trained model estimates.'],
  };
}
function scenario() {
  const base = baseline();
  return {
    ...base, schema_version: 'aegisrisk.scenario-report.v1', report_kind: 'baseline_and_scenario',
    scenario_included: true, baseline: base,
    scenario: { inputs: { pd_multiplier: 2, lgd_multiplier: 1, ead_multiplier: 1, industry: null },
      assumptions: ['Assumptions, not forecasts.'], calculation: {
        decimal_precision: 28, decimal_rounding: 'ROUND_HALF_EVEN', affected_facility_count: 1,
        baseline_el_decimal: '50', stressed_el_decimal: '100', delta_el_decimal: '50', delta_pct_decimal: '1',
        notes: ['PD and LGD are capped at 1.'], facilities: [{ id: 'SYN-1', affected: true,
          pd_capped: false, lgd_capped: false, stressed_pd: '0.2', stressed_lgd: '0.5',
          stressed_ead: '1000', baseline_el: '50', stressed_el: '100', delta_el: '50' }],
      } },
  };
}

test('baseline is complete, offline, printable and preserves decimal evidence', () => {
  const html = renderReportHtml(baseline());
  for (const value of ['<!doctype html>', 'Baseline portfolio report', 'Fictional Birch', '10.00%',
    '50.0000000000000000000001', 'ROUND_HALF_EVEN', 'a'.repeat(64), 'FICTIONAL DATA ONLY', '@media print',
    'default-src', 'form-action', 'No lending decision.']) assert.ok(html.includes(value), value);
  assert.doesNotMatch(html, /<script|<iframe|<img|<link|\son\w+=|\ssrc=/i);
  assert.ok(!html.includes('<h2>Calculated scenario assumptions</h2>'));
});

test('all untrusted text is escaped and Unicode labels are preserved', () => {
  const report = baseline();
  report.source.input_rows[0].borrower = 'Fictional <script>alert("x")</script> & \'नाम\'';
  report.explanation.text = '<img src=x onerror=alert(1)>';
  report.warnings = ['</style><script>bad()</script>'];
  const html = renderReportHtml(report);
  assert.ok(html.includes('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'));
  assert.ok(html.includes('&amp; &#39;नाम&#39;'));
  assert.ok(html.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.doesNotMatch(html, /<script|<img|<\/style><script/i);
});

test('scenario includes assumptions, scope, caps and full decimal comparison', () => {
  const report = scenario();
  report.scenario.calculation.facilities[0].pd_capped = true;
  const html = renderReportHtml(report);
  for (const value of ['Scenario comparison', 'PD ×2', 'Scope: Whole portfolio', 'Fractional change',
    'Scenario facility evidence', '<td>100</td>', '<td>PD </td>', 'Assumptions, not forecasts.']) {
    assert.ok(html.includes(value), value);
  }
});

test('empty and zero-exposure evidence never implies defined ratios', () => {
  const report = scenario();
  report.baseline.source.input_rows = [];
  report.baseline.summary = { facility_count: 0, weighted_pd: null, weighted_lgd: null, borrower_hhi: null };
  report.baseline.calculation.facility_expected_loss_decimal = [];
  report.baseline.calculation.total_ead_decimal = '0';
  report.baseline.calculation.total_expected_loss_decimal = '0';
  Object.assign(report.scenario.calculation, { facilities: [], affected_facility_count: 0,
    baseline_el_decimal: '0', stressed_el_decimal: '0', delta_el_decimal: '0', delta_pct_decimal: null });
  const html = renderReportHtml(report);
  assert.ok(html.includes('Not defined (zero baseline EL)'));
  assert.ok(html.includes('No facilities in this dataset.'));
  assert.ok(!html.includes('NaN') && !html.includes('Infinity'));
});

for (const [name, change] of [
  ['wrong schema', report => { report.schema_version = 'other'; }],
  ['non-synthetic', report => { report.synthetic = false; }],
  ['wrong currency', report => { report.currency = 'EUR'; }],
  ['identity mismatch', report => { report.dataset_version = 'saved-v1:wrong'; }],
  ['invalid timestamp', report => { report.generated_at = 'tomorrow'; }],
  ['missing evidence', report => { report.calculation.facility_expected_loss_decimal = []; }],
  ['duplicate evidence', report => { report.calculation.facility_expected_loss_decimal.push({ id: 'SYN-1', expected_loss: '1' }); }],
  ['wrong count', report => { report.summary.facility_count = 2; }],
  ['nonfinite metric', report => { report.summary.weighted_pd = Infinity; }],
  ['malicious decimal', report => { report.source.input_rows[0].ead = '<img>'; }],
  ['wrong fingerprint', report => { report.source.canonical_sha256 = 'not a digest'; }],
]) test('rejects ' + name, () => {
  const report = baseline();
  change(report);
  assert.throws(() => renderReportHtml(report));
});

test('scenario mismatches and unsupported assumptions fail closed', () => {
  for (const change of [
    report => { report.baseline.dataset_version = 'wrong'; },
    report => { report.baseline.generated_at = '2026-10-18T00:00:00Z'; },
    report => { report.scenario.inputs.pd_multiplier = 11; },
    report => { report.scenario.calculation.facilities[0].id = 'wrong'; },
    report => { report.scenario.calculation.facilities[0].pd_capped = 'yes'; },
  ]) {
    const report = scenario();
    change(report);
    assert.throws(() => renderReportHtml(report));
  }
});
