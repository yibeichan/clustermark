import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { clusterApi } from "../services/api";
import {
  Cluster,
  PaginatedImagesResponse,
  Image,
  OutlierAnnotation,
} from "../types";
import LabelDropdown from "../components/LabelDropdown";

// Fallback image for broken/missing images (DRY principle)
const FALLBACK_IMAGE_SRC =
  "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=";

// Phase 5: Type-safe workflow steps
type WorkflowStep =
  | "review"
  | "batch-label"
  | "annotate-outliers"
  | "label-remaining"
  | "done";

export default function AnnotationPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const navigate = useNavigate();

  // Data state
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [paginatedData, setPaginatedData] =
    useState<PaginatedImagesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Workflow state
  const [step, setStep] = useState<WorkflowStep>("review");

  // Fix 1 (CRITICAL): Store full Image objects, not just IDs
  // - selectedOutlierIds: for UI highlighting (fast Set lookup)
  // - selectedOutlierImages: preserve full Image data across pagination
  const [selectedOutlierIds, setSelectedOutlierIds] = useState<Set<string>>(
    new Set(),
  );
  const [selectedOutlierImages, setSelectedOutlierImages] = useState<
    Map<string, Image>
  >(new Map());

  // Fix 3 (P1): Store both label and isCustom flag for outliers
  const [outlierAnnotations, setOutlierAnnotations] = useState<
    Map<string, { label: string; isCustom: boolean }>
  >(new Map());

  // Fix 2 (P1): Track custom flag for batch label
  const [batchLabel, setBatchLabel] = useState("");
  const [batchIsCustomLabel, setBatchIsCustomLabel] = useState(false);

  const [submitting, setSubmitting] = useState(false);

  // Load cluster metadata on mount
  useEffect(() => {
    if (clusterId) {
      loadClusterMetadata(clusterId);
    }
  }, [clusterId]);

  // Load paginated images when page or pageSize changes
  // Fix: Prevent race condition with cleanup function
  useEffect(() => {
    if (clusterId && step === "review") {
      let isCancelled = false;

      const loadImages = async () => {
        setLoading(true);
        setError(null);
        try {
          const response = await clusterApi.getImagesPaginated(
            clusterId,
            currentPage,
            pageSize,
          );
          if (!isCancelled) {
            setPaginatedData(response.data);
          }
        } catch (err) {
          if (!isCancelled) {
            setError("Failed to load images");
          }
        } finally {
          if (!isCancelled) {
            setLoading(false);
          }
        }
      };

      loadImages();

      return () => {
        isCancelled = true;
      };
    }
  }, [clusterId, currentPage, pageSize, step]);

  // Safe navigation with cleanup and null guard
  useEffect(() => {
    if (step === "done") {
      const timer = setTimeout(() => {
        // Guard: ensure cluster and episode_id exist before navigating
        if (cluster?.episode_id) {
          navigate(`/episodes/${cluster.episode_id}`);
        }
      }, 1500);

      // Cleanup: clear timer if component unmounts
      return () => clearTimeout(timer);
    }
  }, [step, cluster, navigate]);

  const loadClusterMetadata = async (id: string) => {
    try {
      const response = await clusterApi.get(id);
      setCluster(response.data);
    } catch (err) {
      setError("Failed to load cluster metadata");
    }
  };

  // Fix 1 (CRITICAL): Toggle both ID set and Image map
  const toggleOutlier = (image: Image) => {
    const imageId = image.id;
    setSelectedOutlierIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(imageId)) {
        newSet.delete(imageId);
      } else {
        newSet.add(imageId);
      }
      return newSet;
    });

    setSelectedOutlierImages((prev) => {
      const newMap = new Map(prev);
      if (newMap.has(imageId)) {
        newMap.delete(imageId);
      } else {
        newMap.set(imageId, image); // Store full Image object
      }
      return newMap;
    });
  };

  const handleContinue = async () => {
    if (!clusterId) return;

    // Path A: No outliers selected → batch label
    if (selectedOutlierIds.size === 0) {
      setStep("batch-label");
      return;
    }

    // Path B: Has outliers → mark outliers, then use stored Image objects
    setSubmitting(true);
    setError(null);
    try {
      await clusterApi.markOutliers({
        cluster_id: clusterId,
        outlier_image_ids: Array.from(selectedOutlierIds),
      });

      // Fix 1 (CRITICAL): No need to fetch - we already have Image objects in selectedOutlierImages
      setStep("annotate-outliers");
    } catch (err: unknown) {
      // Type-safe error handling with axios type guard
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to mark outliers");
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Fix 2 (P1): Store both label and custom flag
  const handleBatchLabelChange = (label: string, isCustom: boolean) => {
    setBatchLabel(label);
    setBatchIsCustomLabel(isCustom);
  };

  const handleBatchSubmit = async () => {
    if (!clusterId || !batchLabel.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await clusterApi.annotateBatch(clusterId, {
        person_name: batchLabel.trim(),
        is_custom_label: batchIsCustomLabel, // Fix 2: Use tracked custom flag
      });
      setStep("done");
      // Fix 4: Navigation now handled by useEffect
    } catch (err: unknown) {
      // Type-safe error handling with axios type guard
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to save batch annotation");
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Fix 3 (P1): Store both label and custom flag for outliers
  const handleOutlierLabelChange = (
    imageId: string,
    label: string,
    isCustom: boolean,
  ) => {
    setOutlierAnnotations((prev) => {
      const newMap = new Map(prev);
      if (label) {
        newMap.set(imageId, { label, isCustom });
      } else {
        newMap.delete(imageId);
      }
      return newMap;
    });
  };

  const handleOutliersSubmit = async () => {
    if (!clusterId || outlierAnnotations.size === 0) return;

    setSubmitting(true);
    setError(null);
    try {
      const annotations: OutlierAnnotation[] = Array.from(
        outlierAnnotations.entries(),
      ).map(([image_id, { label, isCustom }]) => ({
        image_id,
        person_name: label.trim(),
        is_custom_label: isCustom, // Fix 3: Use stored custom flag
      }));
      await clusterApi.annotateOutliers(annotations);
      setStep("label-remaining");
    } catch (err: unknown) {
      // Type-safe error handling with axios type guard
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to save outlier annotations");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1); // Reset to first page when changing size
  };

  if (loading && !paginatedData) {
    return <div className="loading">Loading cluster...</div>;
  }

  if (!cluster) {
    return <div className="error">{error || "Cluster not found"}</div>;
  }

  // Fix 1 (CRITICAL): Convert Map to Array for rendering
  const outlierImagesArray = Array.from(selectedOutlierImages.values());

  return (
    <div>
      <div className="card">
        <button
          className="button"
          onClick={() => navigate(`/episodes/${cluster.episode_id}`)}
        >
          &larr; Back to Episode
        </button>
        <h2>Annotate {cluster.cluster_name}</h2>
        {cluster.initial_label && <p>Initial label: {cluster.initial_label}</p>}
      </div>

      {error && (
        <div
          className="card"
          style={{ backgroundColor: "#fee", border: "1px solid #fcc" }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Step 1: Review and select outliers */}
      {step === "review" && paginatedData && (
        <div className="card">
          <h3>Step 1: Review Images</h3>
          <p>
            Click images that don't belong (outliers). When done, click
            Continue.
          </p>
          <p>
            Showing page {paginatedData.page} of{" "}
            {Math.ceil(paginatedData.total_count / pageSize)} (
            {paginatedData.total_count} total images)
          </p>

          {/* Page size selector */}
          <div style={{ marginBottom: "15px" }}>
            <label>
              Images per page:{" "}
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                disabled={submitting}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </label>
          </div>

          {/* Image grid */}
          <div className="image-grid">
            {paginatedData.images.map((image: Image) => {
              const isSelected = selectedOutlierIds.has(image.id);
              return (
                <button
                  key={image.id}
                  type="button"
                  className="image-item"
                  onClick={() => toggleOutlier(image)}
                  disabled={submitting}
                  style={{
                    border: isSelected ? "3px solid red" : "1px solid #ddd",
                    padding: "5px",
                    background: "transparent",
                    textAlign: "left",
                    width: "100%",
                    cursor: submitting ? "not-allowed" : "pointer",
                  }}
                >
                  <img
                    src={`/uploads/${image.file_path}`}
                    alt={image.filename}
                    onError={(e) => {
                      e.currentTarget.src = FALLBACK_IMAGE_SRC;
                    }}
                  />
                  {isSelected && (
                    <div
                      style={{
                        color: "red",
                        fontWeight: "bold",
                        marginTop: "5px",
                      }}
                    >
                      Outlier
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Pagination controls */}
          <div
            style={{
              marginTop: "20px",
              display: "flex",
              gap: "10px",
              alignItems: "center",
            }}
          >
            <button
              className="button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={!paginatedData.has_prev || submitting}
            >
              &larr; Previous
            </button>
            <span>
              Page {paginatedData.page} of{" "}
              {Math.ceil(paginatedData.total_count / pageSize)}
            </span>
            <button
              className="button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!paginatedData.has_next || submitting}
            >
              Next &rarr;
            </button>
          </div>

          {/* Continue button */}
          <div style={{ marginTop: "20px" }}>
            <p>
              {selectedOutlierIds.size === 0
                ? "No outliers selected. Will batch label all images."
                : `${selectedOutlierIds.size} outlier(s) selected. Will annotate them individually.`}
            </p>
            <button
              className="button"
              onClick={handleContinue}
              disabled={submitting}
              style={{ fontSize: "18px", padding: "12px 24px" }}
            >
              {submitting ? "Processing..." : "Continue"}
            </button>
          </div>
        </div>
      )}

      {/* Step 2 (Path A): Batch label all images */}
      {step === "batch-label" && (
        <div className="card">
          <h3>Step 2: Label All Images</h3>
          <p>
            Assign a name to all {paginatedData?.total_count} images in this
            cluster:
          </p>
          <div style={{ marginTop: "15px", marginBottom: "15px" }}>
            <LabelDropdown
              value={batchLabel}
              onChange={handleBatchLabelChange}
              disabled={submitting}
            />
          </div>
          <button
            className="button"
            onClick={handleBatchSubmit}
            disabled={!batchLabel.trim() || submitting}
          >
            {submitting ? "Saving..." : "Save Annotation"}
          </button>
        </div>
      )}

      {/* Step 2 (Path B): Annotate outliers */}
      {/* Fix 1 (CRITICAL): Use selectedOutlierImages instead of paginatedData filter */}
      {step === "annotate-outliers" && (
        <div className="card">
          <h3>Step 2: Annotate Outliers</h3>
          <p>
            Assign names to each outlier image ({outlierImagesArray.length}{" "}
            images):
          </p>

          <div>
            {outlierImagesArray.map((image) => (
              <div
                key={image.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "15px",
                  marginBottom: "15px",
                  padding: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
              >
                <img
                  src={`/uploads/${image.file_path}`}
                  alt={image.filename}
                  style={{
                    width: "100px",
                    height: "100px",
                    objectFit: "cover",
                  }}
                  onError={(e) => {
                    e.currentTarget.src = FALLBACK_IMAGE_SRC;
                  }}
                />
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      marginBottom: "5px",
                      fontSize: "12px",
                      color: "#666",
                    }}
                  >
                    {image.filename}
                  </div>
                  <LabelDropdown
                    value={outlierAnnotations.get(image.id)?.label || ""}
                    onChange={(label, isCustom) =>
                      handleOutlierLabelChange(image.id, label, isCustom)
                    }
                    disabled={submitting}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: "20px" }}>
            <p>
              Annotated {outlierAnnotations.size} of {outlierImagesArray.length}{" "}
              outliers
            </p>
            <button
              className="button"
              onClick={handleOutliersSubmit}
              disabled={
                outlierAnnotations.size !== outlierImagesArray.length ||
                submitting
              }
            >
              {submitting ? "Saving..." : "Continue to Label Remaining"}
            </button>
          </div>
        </div>
      )}

      {/* Step 3 (Path B): Label remaining images */}
      {step === "label-remaining" && (
        <div className="card">
          <h3>Step 3: Label Remaining Images</h3>
          <p>
            Assign a name to the remaining{" "}
            {paginatedData
              ? paginatedData.total_count - selectedOutlierIds.size
              : 0}{" "}
            images:
          </p>
          <div style={{ marginTop: "15px", marginBottom: "15px" }}>
            <LabelDropdown
              value={batchLabel}
              onChange={handleBatchLabelChange}
              disabled={submitting}
            />
          </div>
          <button
            className="button"
            onClick={handleBatchSubmit}
            disabled={!batchLabel.trim() || submitting}
          >
            {submitting ? "Saving..." : "Save Annotation"}
          </button>
        </div>
      )}

      {/* Step 4: Done */}
      {step === "done" && (
        <div className="card">
          <h3>✓ Annotation Complete</h3>
          <p>Redirecting back to episode...</p>
        </div>
      )}
    </div>
  );
}
