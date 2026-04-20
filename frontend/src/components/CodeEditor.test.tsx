import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import { CodeEditor } from './CodeEditor';

// Mock monaco editor to avoid importing actual monaco dependencies during JSDOM tests
vi.mock('@monaco-editor/react', () => {
  return {
    default: ({ value, defaultLanguage }: any) => (
      <textarea data-testid="mock-editor" defaultValue={value} data-language={defaultLanguage} />
    )
  };
});

describe('CodeEditor Component', () => {
  it('renders the editor with correct language label', () => {
    render(<CodeEditor value="print('hello')" onChange={() => {}} language="python" />);
    expect(screen.getByText('PYTHON')).toBeInTheDocument();
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument();
  });

  it('binds the initial value', () => {
    const code = "print('world')";
    render(<CodeEditor value={code} onChange={() => {}} language="python" />);
    const editor = screen.getByTestId('mock-editor') as HTMLTextAreaElement;
    expect(editor.value).toBe(code);
  });
});
