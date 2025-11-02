import { Image } from "../../types";

// Fallback image for broken/missing images
const FALLBACK_IMAGE_SRC =
  "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=";

interface ReviewStepProps {
  images: Image[];
  selectedOutliers: Map<string, Image>;
  onToggleOutlier: (image: Image) => void;
  currentPage: number;
  pageSize: number;
  totalCount: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onContinue: () => void;
  disabled: boolean;
}

/**
 * ReviewStep component - Step 1 of annotation workflow.
 *
 * Displays paginated image grid where user can:
 * - Review all images in the cluster
 * - Select outliers by clicking (red border indicator)
 * - Navigate through pages
 * - Change page size (10/20/50)
 * - Continue to next step
 */
export default function ReviewStep({
  images,
  selectedOutliers,
  onToggleOutlier,
  currentPage,
  pageSize,
  totalCount,
  hasNext,
  hasPrev,
  onPageChange,
  onPageSizeChange,
  onContinue,
  disabled,
}: ReviewStepProps) {
  return (
    <div className="card">
      <h3>Step 1: Review Images</h3>
      <p>Click images that don't belong (outliers). When done, click Continue.</p>
      <p>
        Showing page {currentPage} of {Math.ceil(totalCount / pageSize)} (
        {totalCount} total images)
      </p>

      {/* Page size selector */}
      <div className="page-size-selector">
        <label>
          Images per page:{" "}
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            disabled={disabled}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </label>
      </div>

      {/* Image grid */}
      <div className="image-grid">
        {images.map((image: Image) => {
          const isSelected = selectedOutliers.has(image.id);
          return (
            <button
              key={image.id}
              type="button"
              className={`image-item ${isSelected ? "selected" : ""}`}
              onClick={() => onToggleOutlier(image)}
              disabled={disabled}
            >
              <img
                src={`/uploads/${image.file_path}`}
                alt={image.filename}
                onError={(e) => {
                  e.currentTarget.src = FALLBACK_IMAGE_SRC;
                }}
              />
              {isSelected && (
                <div className="image-item-outlier-label">Outlier</div>
              )}
            </button>
          );
        })}
      </div>

      {/* Pagination controls */}
      <div className="pagination-controls">
        <button
          className="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrev || disabled}
        >
          &larr; Previous
        </button>
        <span>
          Page {currentPage} of {Math.ceil(totalCount / pageSize)}
        </span>
        <button
          className="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext || disabled}
        >
          Next &rarr;
        </button>
      </div>

      {/* Continue button */}
      <div className="continue-section">
        <p>
          {selectedOutliers.size === 0
            ? "No outliers selected. Will batch label all images."
            : `${selectedOutliers.size} outlier(s) selected. Will annotate them individually.`}
        </p>
        <button
          className="button continue-button"
          onClick={onContinue}
          disabled={disabled}
        >
          {disabled ? "Processing..." : "Continue"}
        </button>
      </div>
    </div>
  );
}
