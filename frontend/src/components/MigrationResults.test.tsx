import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MigrationResults } from './MigrationResults';
import { MigrationResponse } from '../api';

const mockResponse: MigrationResponse = {
  module_name: 'test_mod',
  source_version: '15.0',
  target_version: '19.0',
  original_code: 'print("hello")',
  migrated_code: 'print("world")',
  diff: 'diff mock',
  explanation: 'explanation mock',
  issues: [
    { severity: 'high', message: 'Something is wrong', line: 10 }
  ]
};

// Mock DiffEditor
vi.mock('@monaco-editor/react', () => {
  return {
    DiffEditor: () => <div data-testid="mock-diff-editor" />
  };
});

describe('MigrationResults Component', () => {
  it('renders the diff editor and issue list correctly', () => {
    render(<MigrationResults result={mockResponse} fileName="test.py" />);
    
    expect(screen.getByText('Migration Output')).toBeInTheDocument();
    expect(screen.getByText('19.0')).toBeInTheDocument();
    expect(screen.getByText('test_mod/test.py')).toBeInTheDocument();
    
    expect(screen.getByTestId('mock-diff-editor')).toBeInTheDocument();
    
    expect(screen.getByText('Detected Issues')).toBeInTheDocument();
    expect(screen.getByText('high Issue')).toBeInTheDocument();
    expect(screen.getByText('Something is wrong')).toBeInTheDocument();
    expect(screen.getByText('Line 10')).toBeInTheDocument();
  });

  it('renders a success message when there are no issues', () => {
    const noIssueResponse = { ...mockResponse, issues: [] };
    render(<MigrationResults result={noIssueResponse} fileName="test.py" />);
    
    expect(screen.getByText(/No issues detected!/i)).toBeInTheDocument();
  });
});
