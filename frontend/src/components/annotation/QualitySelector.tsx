import "./QualitySelector.css";

// Available quality modifiers for face images
const QUALITY_OPTIONS = [
    { value: "@poor", label: "Poor", description: "Low quality or unusable" },
    { value: "@blurry", label: "Blurry", description: "Motion blur or out of focus" },
    { value: "@dark", label: "Dark", description: "Poorly lit face" },
    { value: "@profile", label: "Profile", description: "Side view or extreme angle" },
    { value: "@back", label: "Back", description: "Back of head or not visible" },
] as const;

interface QualitySelectorProps {
    selected: string[];
    onChange: (qualities: string[]) => void;
    disabled?: boolean;
}

/**
 * QualitySelector - Toggle buttons for quality modifiers.
 *
 * Used in outlier annotation to mark face quality issues like:
 * - @poor: General low quality
 * - @blurry: Motion blur or focus issues
 * - @dark: Lighting problems
 * - @profile: Side angles
 * - @back: Back of head
 *
 * These attributes are used to down-weight faces during cluster refinement.
 */
export default function QualitySelector({
    selected,
    onChange,
    disabled = false,
}: QualitySelectorProps) {
    const handleToggle = (value: string) => {
        if (disabled) return;

        if (selected.includes(value)) {
            onChange(selected.filter((item) => item !== value));
        } else {
            onChange([...selected, value]);
        }
    };

    return (
        <div className="quality-selector">
            <div className="quality-selector-label">Quality (optional)</div>
            <div className="quality-selector-buttons">
                {QUALITY_OPTIONS.map((option) => (
                    <button
                        key={option.value}
                        type="button"
                        onClick={() => handleToggle(option.value)}
                        disabled={disabled}
                        title={option.description}
                        className={`quality-button ${selected.includes(option.value) ? "quality-button--selected" : ""} ${disabled ? "quality-button--disabled" : ""}`}
                    >
                        {option.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
