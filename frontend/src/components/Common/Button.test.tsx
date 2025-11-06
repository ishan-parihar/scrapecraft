import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from './Button';

// Simple test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

describe('Button Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders button with text', () => {
    render(
      <TestWrapper>
        <Button>Test Button</Button>
      </TestWrapper>
    );

    expect(screen.getByRole('button', { name: /test button/i })).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    
    render(
      <TestWrapper>
        <Button onClick={handleClick}>Click me</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /click me/i });
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant styles correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button variant="primary">Primary</Button>
      </TestWrapper>
    );

    const primaryButton = screen.getByRole('button', { name: /primary/i });
    expect(primaryButton).toHaveClass('bg-blue-600');

    rerender(
      <TestWrapper>
        <Button variant="secondary">Secondary</Button>
      </TestWrapper>
    );

    const secondaryButton = screen.getByRole('button', { name: /secondary/i });
    expect(secondaryButton).toHaveClass('bg-gray-600');
  });

  it('shows loading state', () => {
    render(
      <TestWrapper>
        <Button loading>Loading</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /loading/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('is disabled when disabled prop is true', () => {
    render(
      <TestWrapper>
        <Button disabled>Disabled</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /disabled/i });
    expect(button).toBeDisabled();
  });

  it('does not trigger click when disabled', async () => {
    const handleClick = jest.fn();
    
    render(
      <TestWrapper>
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /disabled/i });
    await user.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('supports custom className', () => {
    render(
      <TestWrapper>
        <Button className="custom-class">Custom</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /custom/i });
    expect(button).toHaveClass('custom-class');
  });

  it('renders as different element when as prop is provided', () => {
    render(
      <TestWrapper>
        <Button as="a" href="https://example.com">
          Link
        </Button>
      </TestWrapper>
    );

    const link = screen.getByRole('link', { name: /link/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  it('has proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <Button aria-label="Custom label">Button</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /custom label/i });
    expect(button).toHaveAttribute('aria-label', 'Custom label');
  });

  it('supports keyboard navigation', async () => {
    const handleClick = jest.fn();
    
    render(
      <TestWrapper>
        <Button onClick={handleClick}>Keyboard</Button>
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /keyboard/i });
    button.focus();
    expect(button).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalledTimes(1);

    handleClick.mockClear();
    await user.keyboard(' ');
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});