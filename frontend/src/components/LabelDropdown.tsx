import { useState, useEffect } from "react";

// Default fallback characters (used when no speakers provided)
const DEFAULT_CHARACTERS = [
  "Chandler",
  "Joey",
  "Monica",
  "Rachel",
  "Ross",
  "Phoebe",
];

interface LabelDropdownProps {
  value?: string;
  onChange: (label: string, isCustom: boolean) => void;
  disabled?: boolean;
  placeholder?: string;
  speakers?: string[]; // Phase 7: Dynamic speaker list from episode data
}

export default function LabelDropdown({
  value = "",
  onChange,
  disabled = false,
  placeholder = "Select character...",
  speakers = DEFAULT_CHARACTERS, // Fallback to default if not provided
}: LabelDropdownProps) {
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [customLabel, setCustomLabel] = useState<string>("");
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Gemini HIGH + Codex P1: Handle value prop changes including resets
  // Phase 7: Use dynamic speakers list for matching (case-insensitive)
  useEffect(() => {
    if (value) {
      // Case-insensitive match against speakers list or special "non-face" option
      const matchedSpeaker = speakers.find(
        (s) => s.toLowerCase() === value.toLowerCase(),
      );
      if (matchedSpeaker || value.toLowerCase() === "non-face") {
        setSelectedOption(matchedSpeaker || "non-face");
        setShowCustomInput(false);
        setCustomLabel("");
      } else {
        setSelectedOption("Other");
        setCustomLabel(value);
        setShowCustomInput(true);
      }
    } else {
      // Reset state when value is cleared (e.g., after saving annotation)
      setSelectedOption("");
      setCustomLabel("");
      setShowCustomInput(false);
    }
  }, [value, speakers]);

  // Gemini HIGH + Codex P1: Handle all dropdown selections including placeholder
  const handleDropdownChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value;
    setSelectedOption(selected);

    if (selected === "Other") {
      setShowCustomInput(true);
      setCustomLabel(""); // Clear any previous custom label
    } else {
      // Hide custom input for any non-Other selection (including placeholder)
      setShowCustomInput(false);
      setCustomLabel("");
      // Notify parent even when placeholder is selected (allows clearing selection)
      onChange(selected, false);
    }
  };

  const handleCustomLabelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomLabel(e.target.value);
  };

  // Gemini MEDIUM: Extract duplicate logic (DRY principle)
  const commitCustomLabel = () => {
    const trimmedLabel = customLabel.trim();
    if (trimmedLabel) {
      onChange(trimmedLabel, true);
    }
  };

  const handleCustomLabelBlur = () => {
    commitCustomLabel();
  };

  const handleCustomLabelKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Enter") {
      commitCustomLabel();
    }
  };

  return (
    <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
      <select
        value={selectedOption}
        onChange={handleDropdownChange}
        disabled={disabled}
        className="form-select"
      >
        <option value="">{placeholder}</option>
        <option value="non-face">non-face</option>
        {speakers.map((speaker) => (
          <option key={speaker} value={speaker}>
            {speaker}
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
          className="form-input"
        />
      )}
    </div>
  );
}
