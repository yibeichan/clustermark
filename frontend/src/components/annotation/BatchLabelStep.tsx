import LabelDropdown from "../LabelDropdown";

interface BatchLabelStepProps {
  title: string;
  description: string;
  imageCount: number;
  label: string;
  onLabelChange: (label: string, isCustom: boolean) => void;
  onSubmit: () => void;
  disabled: boolean;
  speakers?: string[]; // Phase 7: Dynamic speaker list from episode data
}

/**
 * BatchLabelStep component - Used for both Path A and Path B final step.
 *
 * Path A: "Label All Images" - batch label entire cluster
 * Path B: "Label Remaining Images" - batch label after outliers annotated
 *
 * Displays:
 * - Title (Step 2 or Step 3)
 * - Description with image count
 * - Label dropdown (Friends characters + Others)
 * - Submit button
 */
export default function BatchLabelStep({
  title,
  description,
  imageCount,
  label,
  onLabelChange,
  onSubmit,
  disabled,
  speakers,
}: BatchLabelStepProps) {
  return (
    <div className="card">
      <h3 className="mb-16">{title}</h3>
      {description} {imageCount} images:
    </p>

      {/* Naming Convention Help Box */ }
      <div className="info-box naming-help-box mb-16">
        <div className="info-box-header">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <strong>Using "Others" Label</strong>
        </div>
        <ul className="info-box-list text-sm">
            <li>Use descriptive names: <code>woman1</code>, <code>man2</code>, <code>kid1</code></li>
            <li>Or short descriptions: <code>man on wheelchair</code> (max 5 words)</li>
            <li><strong>Unique IDs:</strong> Unless they are the exact same person, do NOT use the same label (e.g. <code>woman1</code>) again in this episode.</li>
        </ul>
      </div>
      <div className="batch-label-section mt-12 mb-20">
        <LabelDropdown
          value={label}
          onChange={onLabelChange}
          disabled={disabled}
          speakers={speakers}
        />
      </div>
      <button
        className="button mt-24"
        onClick={onSubmit}
        disabled={!label.trim() || disabled}
      >
        {disabled ? "Saving..." : "Save Annotation"}
      </button>
    </div >
  );
}
