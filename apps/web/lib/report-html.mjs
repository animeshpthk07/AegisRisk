// Self-contained presentation of API evidence. No recalculation or external assets.
function text(value) {
  if (typeof value !== 'string' || value.length > 4000) throw new Error('Invalid report text.');
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}
function decimal(value) {
  if (typeof value !== 'string' || value.length > 100 || !/^-?\d+(\.\d+)?$/.test(value)) {
    throw new Error('Invalid decimal evidence.');
  }
  return text(value);
}
function display(value, ratio = false) {
  if (value === null) return 'Not defined';
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid display metric.');
  return ratio ? (value * 100).toFixed(2) + '%' : value.toLocaleString('en-IN', { maximumFractionDigits: 4 });
}
function list(values) {
  if (!Array.isArray(values) || values.length > 100) throw new Error('Invalid report notes.');
  return '<ul>' + values.map(value => '<li>' + text(value) + '</li>').join('') + '</ul>';
}
function table(caption, headers, rows) {
  return '<div class="table-wrap"><table><caption>' + text(caption) + '</caption><thead><tr>' +
    headers.map(value => '<th scope="col">' + text(value) + '</th>').join('') +
    '</tr></thead><tbody>' + (rows.length ? rows.map(row => '<tr>' +
      row.map(value => '<td>' + value + '</td>').join('') + '</tr>').join('') :
      '<tr><td colspan="' + headers.length + '">No facilities in this dataset.</td></tr>') +
    '</tbody></table></div>';
}
function identity(report) {
  if (!report || report.synthetic !== true || report.currency !== 'INR' || report.horizon !== 'one_year' ||
      !(report.dataset_id === null || /^[a-f0-9-]{36}$/.test(report.dataset_id)) ||
      report.dataset_version !== (report.dataset_id ? 'saved-v1:' + report.dataset_id : 'demo-v1') ||
      typeof report.generated_at !== 'string' || !Number.isFinite(Date.parse(report.generated_at))) {
    throw new Error('Invalid report identity.');
  }
}
export function renderReportHtml(report) {
  identity(report);
  const isScenario = report.schema_version === 'aegisrisk.scenario-report.v1';
  if (isScenario ? report.report_kind !== 'baseline_and_scenario' || report.scenario_included !== true :
    report.schema_version !== 'aegisrisk.baseline-report.v1' || report.report_kind !== 'baseline_only' ||
    report.scenario_included !== false) throw new Error('Unsupported report schema.');
  const base = isScenario ? report.baseline : report;
  identity(base);
  if (base.schema_version !== 'aegisrisk.baseline-report.v1' || base.report_kind !== 'baseline_only' ||
      base.scenario_included !== false || base.dataset_id !== report.dataset_id ||
      base.dataset_version !== report.dataset_version || base.generated_at !== report.generated_at ||
      !/^[a-f0-9]{64}$/.test(base.source?.canonical_sha256) ||
      !Array.isArray(base.source?.input_rows) || base.source.input_rows.length > 1000 ||
      !Array.isArray(base.calculation?.facility_expected_loss_decimal) ||
      base.summary?.facility_count !== base.source.input_rows.length) {
    throw new Error('Incomplete baseline evidence.');
  }
  const rows = base.source.input_rows;
  const evidence = base.calculation.facility_expected_loss_decimal;
  const losses = new Map(evidence.map(item => [item.id, item.expected_loss]));
  if (losses.size !== rows.length || evidence.length !== rows.length ||
      new Set(rows.map(row => row.id)).size !== rows.length) throw new Error('Inconsistent facility evidence.');
  const title = isScenario ? 'Scenario comparison' : 'Baseline portfolio report';
  const calculation = base.calculation;
  let content = '<section><h2>Baseline summary</h2><div class="metrics">' +
    '<article><span>Facilities</span><strong>' + display(base.summary.facility_count) + '</strong></article>' +
    '<article><span>Total EAD · INR</span><strong>' + decimal(calculation.total_ead_decimal) + '</strong></article>' +
    '<article><span>One-year expected loss · INR</span><strong>' + decimal(calculation.total_expected_loss_decimal) + '</strong></article>' +
    '</div><p>EAD-weighted PD: ' + display(base.summary.weighted_pd, true) +
    ' · EAD-weighted LGD: ' + display(base.summary.weighted_lgd, true) +
    ' · Borrower HHI (0–1): ' + display(base.summary.borrower_hhi) + '</p></section>';
  if (isScenario) {
    const scenario = report.scenario;
    const details = scenario?.calculation;
    const inputs = scenario?.inputs;
    if (!inputs || !details || !Array.isArray(details.facilities) ||
        details.facilities.length !== rows.length) throw new Error('Incomplete scenario evidence.');
    for (const key of ['pd_multiplier', 'lgd_multiplier', 'ead_multiplier']) {
      if (typeof inputs[key] !== 'number' || !Number.isFinite(inputs[key]) || inputs[key] < 0 || inputs[key] > 10) {
        throw new Error('Invalid scenario assumptions.');
      }
    }
    const byId = new Map(details.facilities.map(item => [item.id, item]));
    if (byId.size !== rows.length) throw new Error('Duplicate scenario evidence.');
    const scenarioRows = rows.map(row => {
      const item = byId.get(row.id);
      if (!item || ![item.affected, item.pd_capped, item.lgd_capped].every(value => typeof value === 'boolean')) {
        throw new Error('Inconsistent scenario evidence.');
      }
      return [text(item.id), item.affected ? 'Yes' : 'No', decimal(item.stressed_pd), decimal(item.stressed_lgd),
        decimal(item.stressed_ead), decimal(item.baseline_el), decimal(item.stressed_el), decimal(item.delta_el),
        (item.pd_capped ? 'PD ' : '') + (item.lgd_capped ? 'LGD' : '') || 'None'];
    });
    content += '<section><h2>Calculated scenario assumptions</h2><p>PD ×' + display(inputs.pd_multiplier) +
      ' · LGD ×' + display(inputs.lgd_multiplier) + ' · EAD ×' + display(inputs.ead_multiplier) +
      ' · Scope: ' + (inputs.industry === null ? 'Whole portfolio' : text(inputs.industry)) + '</p>' +
      table('Comparison · unrounded decimal evidence, INR', ['Baseline EL', 'Stressed EL', 'Change in EL', 'Fractional change'], [[
        decimal(details.baseline_el_decimal), decimal(details.stressed_el_decimal), decimal(details.delta_el_decimal),
        details.delta_pct_decimal === null ? 'Not defined (zero baseline EL)' : decimal(details.delta_pct_decimal),
      ]]) + '<p>Fractional change ×100 gives percentage change. Affected facilities: ' +
      display(details.affected_facility_count) + '.</p>' + list(scenario.assumptions) +
      table('Scenario facility evidence · probabilities are fractions; EAD and EL are INR',
        ['ID', 'Affected', 'PD', 'LGD', 'EAD', 'Baseline EL', 'Stressed EL', 'Delta EL', 'Caps'], scenarioRows) +
      '<p>Scenario Decimal precision: ' + display(details.decimal_precision) +
      ' · Rounding: ' + text(details.decimal_rounding) + '</p>' + list(details.notes) + '</section>';
  }
  content += '<section><h2>Calculation note</h2><p>' + text(base.explanation.text) + '</p><p>' +
    text(base.explanation.disclaimer) + '</p></section><section><h2>Baseline facility evidence</h2>' +
    table('Inputs and expected loss · probabilities are fractions; monetary values are INR',
      ['ID / Borrower', 'Industry / Geography / Rating', 'PD', 'LGD', 'EAD', 'Expected loss'],
      rows.map(row => [text(row.id) + '<br>' + text(row.borrower),
        text(row.industry) + '<br>' + text(row.geography) + ' / ' + text(row.rating),
        decimal(row.pd), decimal(row.lgd), decimal(row.ead), decimal(losses.get(row.id))])) + '</section>' +
    '<section><h2>Methodology and reproducibility</h2><p>' + text(calculation.formula) +
    ' · Probability unit: ' + text(calculation.probability_unit) + '</p><p>Decimal precision: ' +
    display(calculation.decimal_precision) + ' · Rounding: ' + text(calculation.decimal_rounding) +
    '</p><p>Totals and facility evidence are reproduced as supplied decimal strings. Weighted ratios and HHI are rounded for display. No financial calculations are performed by this document renderer.</p>' +
    list(calculation.notes) + list(base.warnings) + '<h3>Canonical source SHA-256</h3><p class="fingerprint">' +
    text(base.source.canonical_sha256) + '</p><p>' + text(base.source.canonicalization) + '</p></section>';
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
    "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">" +
    '<title>AegisRisk — ' + title + '</title><style>' +
    '*{box-sizing:border-box}body{margin:0;background:#eef2f5;color:#172535;font:15px/1.55 system-ui,sans-serif}' +
    'main{max-width:1080px;margin:32px auto;background:white;padding:40px;border-top:6px solid #137a65}' +
    'header{border-bottom:1px solid #ccd7de;padding-bottom:24px}h1{font-size:32px;line-height:1.15;margin:12px 0}h2{font-size:21px;margin:28px 0 12px}' +
    '.eyebrow{font-weight:700;letter-spacing:.14em;color:#137a65}.notice{padding:12px 16px;background:#fff5d8;border-left:4px solid #ad7900}' +
    '.metadata,.fingerprint{overflow-wrap:anywhere}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}' +
    '.metrics article{background:#f0f6f5;padding:16px;overflow-wrap:anywhere}.metrics span{display:block;font-size:13px}.metrics strong{font-size:24px}' +
    '.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px;margin:12px 0}caption{text-align:left;font-weight:600;padding-bottom:8px}' +
    'th,td{text-align:left;vertical-align:top;border-bottom:1px solid #d5dfe5;padding:8px;overflow-wrap:anywhere}th{background:#e9f1f4}footer{margin-top:32px;border-top:1px solid #ccd7de;padding-top:12px;font-size:12px}' +
    '@media(max-width:650px){main{margin:0;padding:20px}.metrics{grid-template-columns:1fr}h1{font-size:27px}}' +
    '@page{size:A4;margin:14mm}@media print{body{background:white;font-size:10pt}main{max-width:none;margin:0;padding:0;border:0}.screen-only{display:none}.table-wrap{overflow:visible}table{table-layout:fixed;font-size:8pt}thead{display:table-header-group}tr,article{break-inside:avoid}h2,h3,caption{break-after:avoid}a{color:inherit}.metrics{grid-template-columns:repeat(3,minmax(0,1fr))}.metrics strong{font-size:16pt}}' +
    '</style></head><body><main><header><p class="eyebrow">AEGISRISK / EVIDENCE REPORT</p><h1>' + title + '</h1>' +
    '<p class="notice">FICTIONAL DATA ONLY · Educational one-year sensitivity analysis. Not a credit decision, forecast, audit opinion, IFRS 9 ECL or regulatory-capital report.</p>' +
    '<p class="metadata">Dataset: ' + text(report.dataset_version) + '<br>Generated: ' + text(report.generated_at) +
    '<br>Currency: INR · Horizon: one year · External AI: disabled</p>' +
    '<p class="screen-only">Open your browser’s Print command to print or save a PDF. This offline document has no scripts, external assets or network dependencies. Keep the JSON export for machine-readable evidence.</p></header>' +
    content + '<footer>AegisRisk · Educational portfolio project · Not affiliated with any bank. Fingerprints identify content, not authenticity.</footer></main></body></html>\n';
}
