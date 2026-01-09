import { Image } from "../../types";
import LabelDropdown from "../LabelDropdown";
import { FALLBACK_IMAGE_SRC } from "../../utils/constants";

interface OutlierAnnotationStepProps {
  outlierImages: Image[];
  annotations: Map<string, { label: string; isCustom: boolean }>;
  onLabelChange: (imageId: string, label: string, isCustom: boolean) => void;
  onSubmit: () => void;
  disabled: boolean;
  speakers?: string[]; // Phase 7: Dynamic speaker list from episode data
}

/**
 * OutlierAnnotationStep component - Step 2 of Path B workflow.
 *
 * Displays list of outlier images for individual annotation.
 * User assigns a label to each outlier before continuing.
 *
 * Features:
 * - Shows each outlier with filename
 * - Label dropdown for each image
 * - Progress indicator (X of Y annotated)
 * - Submit button (disabled until all annotated)
 */
export default function OutlierAnnotationStep({
  outlierImages,
  annotations,
  onLabelChange,
  onSubmit,
  disabled,
  speakers,
}: OutlierAnnotationStepProps) {
  return (
    <div className="card">
      <h3 className="mb-16">Step 2: Annotate Outliers</h3>

      {/* DK Convention Help Box */}
      <div className="info-box dk-help-box">
        <div className="info-box-header">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <strong>Labeling Unknown Faces</strong>
        </div>
        <p className="info-box-content">
          For unknown faces, use <code>DK1</code>, <code>DK2</code>,{" "}
          <code>DK3</code>, etc. to indicate groups:
        </p>
        <ul className="info-box-list">
          <li>
            <strong>DK1</strong> = All images labeled DK1 are the{" "}
            <em>same</em> unknown person
          </li>
          <li>
            <strong>DK2</strong> = All images labeled DK2 are a{" "}
            <em>different</em> unknown person
          </li>
          <li>
            Use higher numbers (DK3, DK4...) for each additional unique unknown
            person
          </li>
        </ul>
        <p className="info-box-example">
          Example: If 3 outliers are the same extra character, label all 3 as{" "}
          <code>DK1</code>
        </p>
      </div>

      <p className="mt-16 mb-12">
        Assign names to each outlier image ({outlierImages.length} images):
      </p>

      <div>
        {outlierImages.map((image) => (
          <div key={image.id} className="outlier-item">
            {/* Phase 6 Round 4: /uploads/ prefix is CORRECT
                Backend stores: episode/cluster/image.jpg (relative to uploads dir)
                Frontend needs: /uploads/episode/cluster/image.jpg
                Gemini HIGH suggestion to use /${image.file_path} was WRONG */}
            <img
              src={`/uploads/${image.file_path}`}
              alt={image.filename}
              className="outlier-item-image"
              onError={(e) => {
                e.currentTarget.src = FALLBACK_IMAGE_SRC;
              }}
            />
            <div className="outlier-item-content">
              <div className="outlier-item-filename">{image.filename}</div>
              <LabelDropdown
                value={annotations.get(image.id)?.label || ""}
                onChange={(label, isCustom) =>
                  onLabelChange(image.id, label, isCustom)
                }
                disabled={disabled}
                speakers={speakers}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="outlier-progress mt-24">
        <p>
          Annotated {annotations.size} of {outlierImages.length} outliers
        </p>
        <button
          className="button"
          onClick={onSubmit}
          disabled={annotations.size !== outlierImages.length || disabled}
        >
          {disabled ? "Saving..." : "Continue to Label Remaining"}
        </button>
      </div>
    </div>
  );
}
