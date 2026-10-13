export function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
}
export function percent(value) {
  return value === null ? 'Not defined' : `${(value * 100).toFixed(2)}%`;
}
