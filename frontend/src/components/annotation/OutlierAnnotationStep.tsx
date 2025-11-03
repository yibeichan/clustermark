import { Image } from "../../types";
import LabelDropdown from "../LabelDropdown";
import { FALLBACK_IMAGE_SRC } from "../../utils/constants";

interface OutlierAnnotationStepProps {
  outlierImages: Image[];
  annotations: Map<string, { label: string; isCustom: boolean }>;
  onLabelChange: (imageId: string, label: string, isCustom: boolean) => void;
  onSubmit: () => void;
  disabled: boolean;
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
}: OutlierAnnotationStepProps) {
  return (
    <div className="card">
      <h3>Step 2: Annotate Outliers</h3>
      <p>Assign names to each outlier image ({outlierImages.length} images):</p>

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
              />
            </div>
          </div>
        ))}
      </div>

      <div className="outlier-progress">
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
