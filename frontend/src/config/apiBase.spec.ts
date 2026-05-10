import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('getApiBaseUrl', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('returns empty string when VITE_API_BASE_URL is empty', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '');
    const { getApiBaseUrl } = await import('./apiBase');
    expect(getApiBaseUrl()).toBe('');
  });

  it('strips trailing slashes from VITE_API_BASE_URL', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com///');
    const { getApiBaseUrl } = await import('./apiBase');
    expect(getApiBaseUrl()).toBe('https://api.example.com');
  });
});
