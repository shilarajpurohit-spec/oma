import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './api';

describe('API Client', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('migrate() calls the /api/migrate endpoint correctly', async () => {
    const mockResponse = { migrated_code: 'def new_code(): pass' };
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await api.migrate({
      module_name: 'test_module',
      source_version: '15.0',
      target_version: '19.0',
      filename: 'models.py',
      file_content: 'def old_code(): pass',
      incremental: false,
    });

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/migrate', expect.objectContaining({
      method: 'POST',
    }));
    expect(result).toEqual(mockResponse);
  });

  it('chat() calls the /api/chat endpoint correctly', async () => {
    const mockResponse = { reply: 'Hello', tokens_used: 10 };
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await api.chat({
      message: 'Hi',
      context: 'some context',
    });

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/chat', expect.objectContaining({
      method: 'POST',
    }));
    expect(result).toEqual(mockResponse);
  });

  it('report() calls the /api/report endpoint correctly', async () => {
    const mockReport = '{"module_name":"test"}';
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ module_name: 'test' }),
      text: async () => mockReport,
    });

    const result = await api.report({
      response: {
        module_name: 'test',
        source_version: '15.0',
        target_version: '19.0',
        original_code: '',
        migrated_code: '',
        diff: '',
        issues: [],
        explanation: '',
      },
      format: 'text',
    });

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/report', expect.objectContaining({
      method: 'POST',
    }));
    expect(result).toBe(mockReport);
  });
});
