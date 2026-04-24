/**
 * Tests for src/utils/freshness.js
 * Uses actual function imports — no mocks needed (pure functions).
 */

import { describe, it, expect } from 'vitest';
import {
  getFreshnessCategory,
  getFreshnessColors,
  getFreshnessEmoji,
  getFreshnessLabel,
  formatFreshnessPercent,
  calculateHealthScore,
  FRESHNESS_THRESHOLDS,
  FRESHNESS_COLORS,
} from '../../utils/freshness';


// ── FRESHNESS_THRESHOLDS ──────────────────────────────────────────────────────

describe('FRESHNESS_THRESHOLDS', () => {
  it('FRESH threshold is 0.7', () => {
    expect(FRESHNESS_THRESHOLDS.FRESH).toBe(0.7);
  });
  it('AGING threshold is 0.4', () => {
    expect(FRESHNESS_THRESHOLDS.AGING).toBe(0.4);
  });
  it('STALE threshold is 0.0', () => {
    expect(FRESHNESS_THRESHOLDS.STALE).toBe(0.0);
  });
});


// ── getFreshnessCategory ──────────────────────────────────────────────────────

describe('getFreshnessCategory()', () => {
  it('returns "fresh" for score >= 0.7', () => {
    expect(getFreshnessCategory(0.7)).toBe('fresh');
    expect(getFreshnessCategory(0.9)).toBe('fresh');
    expect(getFreshnessCategory(1.0)).toBe('fresh');
  });

  it('returns "aging" for score in [0.4, 0.7)', () => {
    expect(getFreshnessCategory(0.4)).toBe('aging');
    expect(getFreshnessCategory(0.55)).toBe('aging');
    expect(getFreshnessCategory(0.69)).toBe('aging');
  });

  it('returns "stale" for score < 0.4', () => {
    expect(getFreshnessCategory(0.0)).toBe('stale');
    expect(getFreshnessCategory(0.2)).toBe('stale');
    expect(getFreshnessCategory(0.39)).toBe('stale');
  });

  it('handles exactly 0.7 as fresh', () => {
    expect(getFreshnessCategory(0.7)).toBe('fresh');
  });

  it('handles exactly 0.4 as aging', () => {
    expect(getFreshnessCategory(0.4)).toBe('aging');
  });
});


// ── getFreshnessEmoji ─────────────────────────────────────────────────────────

describe('getFreshnessEmoji()', () => {
  it('returns ✅ for fresh scores', () => {
    expect(getFreshnessEmoji(0.9)).toBe('✅');
  });
  it('returns ⏳ for aging scores', () => {
    expect(getFreshnessEmoji(0.55)).toBe('⏳');
  });
  it('returns ⚠️ for stale scores', () => {
    expect(getFreshnessEmoji(0.2)).toBe('⚠️');
  });
});


// ── getFreshnessLabel ─────────────────────────────────────────────────────────

describe('getFreshnessLabel()', () => {
  it('returns "Fresh" for high scores', ()  => expect(getFreshnessLabel(0.9)).toBe('Fresh'));
  it('returns "Aging" for medium scores', () => expect(getFreshnessLabel(0.55)).toBe('Aging'));
  it('returns "Stale" for low scores', ()   => expect(getFreshnessLabel(0.2)).toBe('Stale'));
});


// ── getFreshnessColors ────────────────────────────────────────────────────────

describe('getFreshnessColors()', () => {
  it('returns colors object with hex and text fields', () => {
    const colors = getFreshnessColors(0.9);
    expect(colors).toHaveProperty('hex');
    expect(colors).toHaveProperty('text');
  });

  it('returns green-ish hex for fresh', () => {
    const { hex } = getFreshnessColors(0.9);
    expect(hex).toBe(FRESHNESS_COLORS.fresh.hex);
  });

  it('returns red-ish hex for stale', () => {
    const { hex } = getFreshnessColors(0.1);
    expect(hex).toBe(FRESHNESS_COLORS.stale.hex);
  });
});


// ── formatFreshnessPercent ────────────────────────────────────────────────────

describe('formatFreshnessPercent()', () => {
  it('formats 0.92 as "92%"', () => expect(formatFreshnessPercent(0.92)).toBe('92%'));
  it('formats 0.5  as "50%"', () => expect(formatFreshnessPercent(0.5)).toBe('50%'));
  it('formats 1.0  as "100%"', () => expect(formatFreshnessPercent(1.0)).toBe('100%'));
  it('formats 0.0  as "0%"',  () => expect(formatFreshnessPercent(0.0)).toBe('0%'));
  it('rounds fractional percentages', () => {
    // 0.876 → 88%
    expect(formatFreshnessPercent(0.876)).toBe('88%');
  });
});


// ── calculateHealthScore ──────────────────────────────────────────────────────

describe('calculateHealthScore()', () => {
  it('calculates percent of fresh chunks', () => {
    expect(calculateHealthScore({ total: 100, fresh: 70 })).toBe(70);
  });

  it('returns 0 for null input', () => {
    expect(calculateHealthScore(null)).toBe(0);
  });

  it('returns 0 when total is 0', () => {
    expect(calculateHealthScore({ total: 0, fresh: 0 })).toBe(0);
  });

  it('returns 100 when all chunks are fresh', () => {
    expect(calculateHealthScore({ total: 50, fresh: 50 })).toBe(100);
  });

  it('returns 0 when no chunks are fresh', () => {
    expect(calculateHealthScore({ total: 50, fresh: 0 })).toBe(0);
  });

  it('rounds to integer', () => {
    const result = calculateHealthScore({ total: 3, fresh: 1 });
    expect(Number.isInteger(result)).toBe(true);
  });
});
