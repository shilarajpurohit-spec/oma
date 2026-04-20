import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import { api } from '../api';

vi.mock('../api', () => ({
  api: {
    chat: vi.fn(),
  }
}));

describe('ChatInterface Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders correctly with default empty state', () => {
    render(<ChatInterface />);
    expect(screen.getByText('Migration Assistant')).toBeInTheDocument();
    expect(screen.getByText('Ask me about the migration or code issues.')).toBeInTheDocument();
  });

  it('allows user to send a message and displays response', async () => {
    (api.chat as any).mockResolvedValue({ reply: 'I am the assistant', tokens_used: 5 });
    
    render(<ChatInterface />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    // Button doesn't have a direct name but we can submit the form directly on the input
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.submit(input.closest('form')!);
    
    // User message should appear immediately
    expect(screen.getByText('Hello')).toBeInTheDocument();
    
    // Wait for assistant response
    await waitFor(() => {
      expect(screen.getByText('I am the assistant')).toBeInTheDocument();
    });
    
    expect(api.chat).toHaveBeenCalledWith(expect.objectContaining({
      message: 'Hello'
    }));
  });
});
