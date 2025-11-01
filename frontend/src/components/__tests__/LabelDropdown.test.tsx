import { render, screen, fireEvent } from '@testing-library/react';
import LabelDropdown from '../LabelDropdown';

describe('LabelDropdown', () => {
  it('renders with default placeholder', () => {
    render(<LabelDropdown onChange={jest.fn()} />);
    expect(screen.getByText('Select character...')).toBeInTheDocument();
  });

  it('shows all Friends characters', () => {
    render(<LabelDropdown onChange={jest.fn()} />);
    expect(screen.getByText('Chandler')).toBeInTheDocument();
    expect(screen.getByText('Joey')).toBeInTheDocument();
    expect(screen.getByText('Monica')).toBeInTheDocument();
    expect(screen.getByText('Rachel')).toBeInTheDocument();
    expect(screen.getByText('Ross')).toBeInTheDocument();
    expect(screen.getByText('Phoebe')).toBeInTheDocument();
    expect(screen.getByText('Other')).toBeInTheDocument();
  });

  it('calls onChange immediately when selecting a character', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Rachel' } });
    
    expect(onChange).toHaveBeenCalledWith('Rachel', false);
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('shows custom input when Other is selected', () => {
    render(<LabelDropdown onChange={jest.fn()} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    expect(screen.getByPlaceholderText(/Enter name/)).toBeInTheDocument();
  });

  it('does NOT call onChange on every keystroke', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: 'Gunther' } });
    
    expect(onChange).not.toHaveBeenCalled();
  });

  it('calls onChange on blur with custom label', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: 'Gunther' } });
    fireEvent.blur(input);
    
    expect(onChange).toHaveBeenCalledWith('Gunther', true);
  });

  it('calls onChange on Enter key', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: 'Janice' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(onChange).toHaveBeenCalledWith('Janice', true);
  });

  it('trims whitespace from custom labels', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: '  Gunther  ' } });
    fireEvent.blur(input);
    
    expect(onChange).toHaveBeenCalledWith('Gunther', true);
  });

  it('does not call onChange if empty', () => {
    const onChange = jest.fn();
    render(<LabelDropdown onChange={onChange} />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Other' } });
    
    const input = screen.getByPlaceholderText(/Enter name/);
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.blur(input);
    
    expect(onChange).not.toHaveBeenCalled();
  });

  it('initializes with predefined character', () => {
    render(<LabelDropdown onChange={jest.fn()} value="Rachel" />);
    
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('Rachel');
  });

  it('initializes with custom value', () => {
    render(<LabelDropdown onChange={jest.fn()} value="Gunther" />);
    
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('Other');
    
    const input = screen.getByPlaceholderText(/Enter name/) as HTMLInputElement;
    expect(input.value).toBe('Gunther');
  });

  it('disables when disabled prop is true', () => {
    render(<LabelDropdown onChange={jest.fn()} disabled={true} />);
    
    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
  });
});
