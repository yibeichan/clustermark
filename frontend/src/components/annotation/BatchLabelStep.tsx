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
      <p>
        {description} {imageCount} images:
      </p>
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
    </div>
  );
}
