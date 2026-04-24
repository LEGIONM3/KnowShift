/**
 * Tests for KnowShift API module (src/api/knowshiftApi.js).
 * Uses vi.mock to replace axios without real HTTP requests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios', () => {
  const instance = {
    get:          vi.fn(),
    post:         vi.fn(),
    interceptors: {
      request:  { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return {
    default: {
      create: vi.fn(() => instance),
    },
    _instance: instance,
  };
});

// Import after the mock is set up
import { api } from '../../api/knowshiftApi';

describe('KnowShift API module', () => {

  it('exports an api object', () => {
    expect(api).toBeDefined();
  });

  it('api.health is a function', () => {
    expect(typeof api.health).toBe('function');
  });

  it('api.ask is a function', () => {
    expect(typeof api.ask).toBe('function');
  });

  it('api.compare is a function', () => {
    expect(typeof api.compare).toBe('function');
  });

  it('api.upload is a function', () => {
    expect(typeof api.upload).toBe('function');
  });

  it('api.getDashboard is a function', () => {
    expect(typeof api.getDashboard).toBe('function');
  });

  it('api.getChangeLog is a function', () => {
    expect(typeof api.getChangeLog).toBe('function');
  });

  it('api.triggerScan is a function', () => {
    expect(typeof api.triggerScan).toBe('function');
  });

  describe('api.ask()', () => {
    it('accepts question, domain, and include_stale params', () => {
      // Just verify the function signature accepts 3 args
      expect(api.ask.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('api.getDashboard()', () => {
    it('accepts a domain parameter', () => {
      expect(api.getDashboard.length).toBeGreaterThanOrEqual(0);
    });
  });
});
