import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { clusterApi } from "../services/api";
import {
  Cluster,
  PaginatedImagesResponse,
  Image,
  OutlierAnnotation,
} from "../types";
import LabelDropdown from "../components/LabelDropdown";

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
  const [selectedOutlierIds, setSelectedOutlierIds] = useState<Set<string>>(
    new Set(),
  );
  const [outlierAnnotations, setOutlierAnnotations] = useState<
    Map<string, string>
  >(new Map());
  const [batchLabel, setBatchLabel] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Load cluster metadata on mount
  useEffect(() => {
    if (clusterId) {
      loadClusterMetadata(clusterId);
    }
  }, [clusterId]);

  // Load paginated images when page or pageSize changes
  useEffect(() => {
    if (clusterId && step === "review") {
      loadPaginatedImages(clusterId, currentPage, pageSize);
    }
  }, [clusterId, currentPage, pageSize, step]);

  const loadClusterMetadata = async (id: string) => {
    try {
      const response = await clusterApi.get(id);
      setCluster(response.data);
    } catch (err) {
      setError("Failed to load cluster metadata");
    }
  };

  const loadPaginatedImages = async (
    id: string,
    page: number,
    size: number,
  ) => {
    setLoading(true);
    setError(null);
    try {
      const response = await clusterApi.getImagesPaginated(id, page, size);
      setPaginatedData(response.data);
    } catch (err) {
      setError("Failed to load images");
    } finally {
      setLoading(false);
    }
  };

  const toggleOutlier = (imageId: string) => {
    setSelectedOutlierIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(imageId)) {
        newSet.delete(imageId);
      } else {
        newSet.add(imageId);
      }
      return newSet;
    });
  };

  const handleContinue = async () => {
    if (!clusterId) return;

    // Path A: No outliers selected → batch label
    if (selectedOutlierIds.size === 0) {
      setStep("batch-label");
      return;
    }

    // Path B: Has outliers → mark outliers first
    setSubmitting(true);
    setError(null);
    try {
      await clusterApi.markOutliers({
        cluster_id: clusterId,
        outlier_image_ids: Array.from(selectedOutlierIds),
      });
      setStep("annotate-outliers");
    } catch (err: any) {
      // Phase 3 lesson: Backend returns detailed error messages
      setError(err.response?.data?.detail || "Failed to mark outliers");
    } finally {
      setSubmitting(false);
    }
  };

  const handleBatchLabelChange = (label: string, _isCustom: boolean) => {
    setBatchLabel(label);
  };

  const handleBatchSubmit = async () => {
    if (!clusterId || !batchLabel.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await clusterApi.annotateBatch(clusterId, {
        person_name: batchLabel.trim(),
        is_custom_label: false, // LabelDropdown already handles this
      });
      setStep("done");
      // Navigate back after short delay
      setTimeout(() => {
        navigate(`/episodes/${cluster?.episode_id}`);
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save batch annotation");
    } finally {
      setSubmitting(false);
    }
  };

  const handleOutlierLabelChange = (
    imageId: string,
    label: string,
    _isCustom: boolean,
  ) => {
    setOutlierAnnotations((prev) => {
      const newMap = new Map(prev);
      if (label) {
        newMap.set(imageId, label);
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
      ).map(([image_id, person_name]) => ({
        image_id,
        person_name: person_name.trim(),
        is_custom_label: false,
      }));
      await clusterApi.annotateOutliers(annotations);
      setStep("label-remaining");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to save outlier annotations",
      );
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
    return <div className="error">Cluster not found</div>;
  }

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
                <div
                  key={image.id}
                  className="image-item"
                  onClick={() => toggleOutlier(image.id)}
                  style={{
                    cursor: "pointer",
                    border: isSelected ? "3px solid red" : "1px solid #ddd",
                    padding: "5px",
                  }}
                >
                  <img
                    src={`/uploads/${image.file_path}`}
                    alt={image.filename}
                    onError={(e) => {
                      e.currentTarget.src =
                        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=";
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
                </div>
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
      {step === "annotate-outliers" && paginatedData && (
        <div className="card">
          <h3>Step 2: Annotate Outliers</h3>
          <p>
            Assign names to each outlier image ({selectedOutlierIds.size}{" "}
            images):
          </p>

          <div>
            {paginatedData.images
              .filter((img) => selectedOutlierIds.has(img.id))
              .map((image) => (
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
                      e.currentTarget.src =
                        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=";
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
                      value={outlierAnnotations.get(image.id) || ""}
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
              Annotated {outlierAnnotations.size} of {selectedOutlierIds.size}{" "}
              outliers
            </p>
            <button
              className="button"
              onClick={handleOutliersSubmit}
              disabled={
                outlierAnnotations.size !== selectedOutlierIds.size ||
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
