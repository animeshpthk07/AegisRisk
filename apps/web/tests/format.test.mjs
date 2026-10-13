import { test } from 'node:test';
import assert from 'node:assert/strict';
import { money, percent } from '../lib/format.mjs';
test('probabilities render as percentages', () => assert.equal(percent(0.025), '2.50%'));
test('undefined weighted metric is not zero', () => assert.equal(percent(null), 'Not defined'));
test('currency includes INR marker and grouping', () => assert.match(money(100000), /1,00,000/));
