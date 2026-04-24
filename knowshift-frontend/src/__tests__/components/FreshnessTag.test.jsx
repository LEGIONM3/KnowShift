/**
 * Component tests for FreshnessTag.jsx
 * Tests rendering for all three freshness states and prop variations.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FreshnessTag } from '../../components/shared/FreshnessTag';


// ── Fresh state ───────────────────────────────────────────────────────────────

describe('FreshnessTag — Fresh state (score >= 0.7)', () => {
  it('renders "Fresh" label', () => {
    render(<FreshnessTag score={0.92} />);
    expect(screen.getByText('Fresh')).toBeInTheDocument();
  });

  it('renders ✅ emoji', () => {
    render(<FreshnessTag score={0.9} />);
    expect(screen.getByText('✅')).toBeInTheDocument();
  });

  it('shows score percentage when showScore=true (default)', () => {
    render(<FreshnessTag score={0.92} showScore={true} />);
    expect(screen.getByText('(92%)')).toBeInTheDocument();
  });

  it('does not show percentage when showScore=false', () => {
    render(<FreshnessTag score={0.92} showScore={false} />);
    expect(screen.queryByText('(92%)')).not.toBeInTheDocument();
  });
});


// ── Aging state ───────────────────────────────────────────────────────────────

describe('FreshnessTag — Aging state (0.4 <= score < 0.7)', () => {
  it('renders "Aging" label', () => {
    render(<FreshnessTag score={0.55} />);
    expect(screen.getByText('Aging')).toBeInTheDocument();
  });

  it('renders ⏳ emoji', () => {
    render(<FreshnessTag score={0.55} />);
    expect(screen.getByText('⏳')).toBeInTheDocument();
  });

  it('shows 55% for score 0.55', () => {
    render(<FreshnessTag score={0.55} />);
    expect(screen.getByText('(55%)')).toBeInTheDocument();
  });
});


// ── Stale state ───────────────────────────────────────────────────────────────

describe('FreshnessTag — Stale state (score < 0.4)', () => {
  it('renders "Stale" label', () => {
    render(<FreshnessTag score={0.15} />);
    expect(screen.getByText('Stale')).toBeInTheDocument();
  });

  it('renders ⚠️ emoji', () => {
    render(<FreshnessTag score={0.15} />);
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });

  it('shows correct percentage for stale score', () => {
    render(<FreshnessTag score={0.08} />);
    expect(screen.getByText('(8%)')).toBeInTheDocument();
  });
});


// ── showScore default ─────────────────────────────────────────────────────────

describe('FreshnessTag — showScore prop', () => {
  it('shows score by default (showScore not specified)', () => {
    render(<FreshnessTag score={0.8} />);
    expect(screen.getByText('(80%)')).toBeInTheDocument();
  });

  it('hides score when showScore=false for any state', () => {
    ['stale', 'aging', 'fresh'].forEach((_, i) => {
      const score = [0.1, 0.55, 0.9][i];
      const { unmount } = render(<FreshnessTag score={score} showScore={false} />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
      unmount();
    });
  });
});


// ── Size variants ─────────────────────────────────────────────────────────────

describe('FreshnessTag — size prop', () => {
  it('renders without crashing for size="sm"', () => {
    const { container } = render(<FreshnessTag score={0.8} size="sm" />);
    expect(container.firstChild).toBeTruthy();
  });

  it('renders without crashing for size="md"', () => {
    const { container } = render(<FreshnessTag score={0.8} size="md" />);
    expect(container.firstChild).toBeTruthy();
  });

  it('renders without crashing for size="lg"', () => {
    const { container } = render(<FreshnessTag score={0.8} size="lg" />);
    expect(container.firstChild).toBeTruthy();
  });

  it('renders as a <span> element', () => {
    render(<FreshnessTag score={0.9} />);
    const el = screen.getByText('Fresh').closest('span');
    expect(el).toBeInTheDocument();
  });
});


// ── Edge cases ────────────────────────────────────────────────────────────────

describe('FreshnessTag — edge cases', () => {
  it('handles score=0 (minimum)', () => {
    render(<FreshnessTag score={0} />);
    expect(screen.getByText('Stale')).toBeInTheDocument();
  });

  it('handles score=1.0 (maximum)', () => {
    render(<FreshnessTag score={1.0} />);
    expect(screen.getByText('Fresh')).toBeInTheDocument();
    expect(screen.getByText('(100%)')).toBeInTheDocument();
  });

  it('handles exact boundary 0.7 as Fresh', () => {
    render(<FreshnessTag score={0.7} />);
    expect(screen.getByText('Fresh')).toBeInTheDocument();
  });

  it('handles exact boundary 0.4 as Aging', () => {
    render(<FreshnessTag score={0.4} />);
    expect(screen.getByText('Aging')).toBeInTheDocument();
  });
});
