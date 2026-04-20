import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReportPage } from './ReportPage';
import { api, MigrationResponse } from '../api';

vi.mock('../api', () => ({
  api: {
    report: vi.fn(),
  }
}));

const mockResult: MigrationResponse = {
  module_name: 'test_mod',
  source_version: '15.0',
  target_version: '19.0',
  original_code: 'print("hello")',
  migrated_code: 'print("world")',
  diff: 'diff mock',
  explanation: 'explanation mock',
  issues: [
    { severity: 'high', message: 'Deprecated API usage', line: 5 }
  ],
};

describe('ReportPage Component', () => {
  const originalCreateObjectURL = global.URL.createObjectURL;
  const originalRevokeObjectURL = global.URL.revokeObjectURL;

  beforeEach(() => {
    vi.clearAllMocks();
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();
    global.alert = vi.fn();
  });

  afterEach(() => {
    global.URL.createObjectURL = originalCreateObjectURL;
    global.URL.revokeObjectURL = originalRevokeObjectURL;
  });

  it('renders the export UI with both format buttons', () => {
    render(<ReportPage result={mockResult} />);
    expect(screen.getByText('Export Report')).toBeInTheDocument();
    expect(screen.getByText('Migration Summary')).toBeInTheDocument();
    expect(screen.getByText('Export as JSON')).toBeInTheDocument();
    expect(screen.getByText('Export as Text')).toBeInTheDocument();
  });

  it('calls api.report with JSON format when JSON button is clicked', async () => {
    (api.report as any).mockResolvedValue('{"module_name":"test_mod"}');

    render(<ReportPage result={mockResult} />);
    
    fireEvent.click(screen.getByText('Export as JSON'));
    
    await waitFor(() => {
      expect(api.report).toHaveBeenCalledWith({
        response: mockResult,
        format: 'json',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Successfully generated JSON report!')).toBeInTheDocument();
    });
  });

  it('calls api.report with text format when Text button is clicked', async () => {
    (api.report as any).mockResolvedValue('Plain text report content');

    render(<ReportPage result={mockResult} />);
    
    fireEvent.click(screen.getByText('Export as Text'));

    await waitFor(() => {
      expect(api.report).toHaveBeenCalledWith({
        response: mockResult,
        format: 'text',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Successfully generated TEXT report!')).toBeInTheDocument();
    });
  });
});
