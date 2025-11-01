import { useState, useEffect } from 'react';

const FRIENDS_CHARACTERS = [
  'Chandler',
  'Joey',
  'Monica',
  'Rachel',
  'Ross',
  'Phoebe',
] as const;

interface LabelDropdownProps {
  value?: string;
  onChange: (label: string, isCustom: boolean) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function LabelDropdown({
  value = '',
  onChange,
  disabled = false,
  placeholder = 'Select character...',
}: LabelDropdownProps) {
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [customLabel, setCustomLabel] = useState<string>('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  useEffect(() => {
    if (value) {
      if (FRIENDS_CHARACTERS.includes(value as any)) {
        setSelectedOption(value);
        setShowCustomInput(false);
      } else if (value !== '') {
        setSelectedOption('Other');
        setCustomLabel(value);
        setShowCustomInput(true);
      }
    }
  }, [value]);

  const handleDropdownChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value;
    setSelectedOption(selected);

    if (selected === 'Other') {
      setShowCustomInput(true);
    } else if (selected) {
      setShowCustomInput(false);
      setCustomLabel('');
      onChange(selected, false);
    }
  };

  const handleCustomLabelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomLabel(e.target.value);
  };

  const handleCustomLabelBlur = () => {
    if (customLabel.trim()) {
      onChange(customLabel.trim(), true);
    }
  };

  const handleCustomLabelKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && customLabel.trim()) {
      onChange(customLabel.trim(), true);
    }
  };

  return (
    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
      <select
        value={selectedOption}
        onChange={handleDropdownChange}
        disabled={disabled}
        style={{
          padding: '8px 12px',
          fontSize: '14px',
          minWidth: '150px',
          borderRadius: '4px',
          border: '1px solid #ccc',
        }}
      >
        <option value="">{placeholder}</option>
        {FRIENDS_CHARACTERS.map((char) => (
          <option key={char} value={char}>
            {char}
          </option>
        ))}
        <option value="Other">Other</option>
      </select>

      {showCustomInput && (
        <input
          type="text"
          value={customLabel}
          onChange={handleCustomLabelChange}
          onBlur={handleCustomLabelBlur}
          onKeyDown={handleCustomLabelKeyDown}
          placeholder="Enter name (e.g., Gunther, Janice)"
          disabled={disabled}
          autoFocus
          style={{
            padding: '8px 12px',
            fontSize: '14px',
            minWidth: '250px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        />
      )}
    </div>
  );
}
