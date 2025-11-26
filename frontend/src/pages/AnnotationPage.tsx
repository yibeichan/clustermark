import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { clusterApi, episodeApi } from "../services/api";
import {
  Cluster,
  PaginatedImagesResponse,
  Image,
  OutlierAnnotation,
} from "../types";
import ImageGridSkeleton from "../components/ImageGridSkeleton";
import ReviewStep from "../components/annotation/ReviewStep";
import BatchLabelStep from "../components/annotation/BatchLabelStep";
import OutlierAnnotationStep from "../components/annotation/OutlierAnnotationStep";
import "../styles/AnnotationPage.css";

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
  const [outliersLoadError, setOutliersLoadError] = useState<string | null>(
    null,
  );
  const [outliersLoading, setOutliersLoading] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Workflow state
  const [step, setStep] = useState<WorkflowStep>("review");

  // Store selected outlier images (Map provides both fast lookup and full objects)
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

  // Phase 7: Episode-specific speakers for dynamic dropdown
  const [speakers, setSpeakers] = useState<string[]>([]);
  const [speakersLoading, setSpeakersLoading] = useState(false);

  // Load cluster metadata on mount
  // Fix: Prevent race condition with cleanup function (same pattern as pagination)
  useEffect(() => {
    if (clusterId) {
      let isCancelled = false;

      const loadMetadata = async () => {
        try {
          const response = await clusterApi.get(clusterId);
          if (!isCancelled) {
            setCluster(response.data);
          }
        } catch (err) {
          if (!isCancelled) {
            setError("Failed to load cluster metadata");
          }
        }
      };

      loadMetadata();

      return () => {
        isCancelled = true;
      };
    }
  }, [clusterId]);

  // Phase 7: Fetch episode-specific speakers when cluster metadata is loaded
  useEffect(() => {
    if (cluster?.episode_id) {
      let isCancelled = false;

      const loadSpeakers = async () => {
        setSpeakersLoading(true);
        try {
          const response = await episodeApi.getSpeakers(cluster.episode_id);
          if (!isCancelled) {
            setSpeakers(response.data.speakers);
          }
        } catch (err) {
          if (!isCancelled) {
            // Fallback to empty list (LabelDropdown has default characters)
            console.error("Failed to load speakers:", err);
            setSpeakers([]);
          }
        } finally {
          if (!isCancelled) {
            setSpeakersLoading(false);
          }
        }
      };

      loadSpeakers();

      return () => {
        isCancelled = true;
      };
    }
  }, [cluster?.episode_id]);

  // Phase 6c: Load existing outliers on mount (enables resume workflow)
  useEffect(() => {
    if (clusterId) {
      let isCancelled = false;

      const loadExistingOutliers = async () => {
        setOutliersLoading(true);
        try {
          const response = await clusterApi.getOutliers(clusterId);
          if (!isCancelled && response.data.outliers.length > 0) {
            // Populate selectedOutlierImages with existing outliers
            // Use functional update to prevent race condition with user selections
            const backendOutliers = new Map<string, Image>();
            response.data.outliers.forEach((img) => {
              backendOutliers.set(img.id, img);
            });
            setSelectedOutlierImages((prev) => {
              // Merge: preserve user selections, add backend outliers
              const merged = new Map(prev);
              backendOutliers.forEach((img, id) => {
                if (!merged.has(id)) {
                  merged.set(id, img);
                }
              });
              return merged;
            });
          }
          // Clear any previous errors on successful load
          if (!isCancelled) {
            setOutliersLoadError(null);
          }
        } catch (err) {
          // Don't show error for missing outliers (expected for new clusters)
          if (
            !isCancelled &&
            axios.isAxiosError(err) &&
            err.response?.status !== 404
          ) {
            setOutliersLoadError(
              "Failed to load existing outliers. Cannot continue safely.",
            );
            console.error("Failed to load existing outliers:", err);
          }
        } finally {
          if (!isCancelled) {
            setOutliersLoading(false);
          }
        }
      };

      loadExistingOutliers();

      return () => {
        isCancelled = true;
      };
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

  // Helper: Extract error handling logic (DRY principle)
  const handleApiError = (error: unknown, defaultMessage: string) => {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      setError(error.response.data.detail);
    } else {
      setError(defaultMessage);
    }
  };

  // Toggle outlier selection (Map provides both lookup and storage)
  const toggleOutlier = (image: Image) => {
    setSelectedOutlierImages((prev) => {
      const newMap = new Map(prev);
      if (newMap.has(image.id)) {
        newMap.delete(image.id);
      } else {
        newMap.set(image.id, image);
      }
      return newMap;
    });
  };

  const handleContinue = async () => {
    if (!clusterId) return;

    // Phase 6 Round 6 Fix (Codex P1): Always sync outliers with backend
    // If cluster had pre-existing outliers and user deselected all of them,
    // we MUST call markOutliers([]) to reset them to 'pending' in the database.
    // Otherwise they remain annotation_status='outlier' and never get annotated.
    const needsOutlierSync =
      cluster?.has_outliers || selectedOutlierImages.size > 0;

    if (needsOutlierSync) {
      // Sync outlier state with backend (marks selected, resets deselected)
      setSubmitting(true);
      setError(null);
      try {
        await clusterApi.markOutliers({
          cluster_id: clusterId,
          outlier_image_ids: Array.from(selectedOutlierImages.keys()),
        });

        // Path A: No outliers after sync → batch label
        if (selectedOutlierImages.size === 0) {
          setStep("batch-label");
        } else {
          // Path B: Has outliers → annotate them individually
          setStep("annotate-outliers");
        }
      } catch (err: unknown) {
        handleApiError(err, "Failed to mark outliers");
      } finally {
        setSubmitting(false);
      }
    } else {
      // No outliers selected and cluster never had any → go directly to batch label
      setStep("batch-label");
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
      handleApiError(err, "Failed to save batch annotation");
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
    // Defensive: guard mirrors button's disabled logic
    if (!clusterId || outlierAnnotations.size !== selectedOutlierImages.size)
      return;

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
      handleApiError(err, "Failed to save outlier annotations");
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
    return (
      <div className="card">
        <h2>Loading cluster...</h2>
        <ImageGridSkeleton count={pageSize} />
      </div>
    );
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
        <div className="card annotation-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Phase 6 Round 2: Show error banner if outliers failed to load (P1 fix) */}
      {outliersLoadError && (
        <div className="card annotation-error">
          <strong>Error:</strong> {outliersLoadError}
          <button
            className="button annotation-error-retry-button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      )}

      {/* Step 1: Review and select outliers */}
      {step === "review" && paginatedData && (
        <ReviewStep
          images={paginatedData.images}
          selectedOutliers={selectedOutlierImages}
          onToggleOutlier={toggleOutlier}
          currentPage={paginatedData.page}
          pageSize={pageSize}
          totalCount={paginatedData.total_count}
          hasNext={paginatedData.has_next}
          hasPrev={paginatedData.has_prev}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          onContinue={handleContinue}
          disabled={submitting || outliersLoadError !== null || outliersLoading}
        />
      )}

      {/* Step 2 (Path A): Batch label all images */}
      {step === "batch-label" && (
        <BatchLabelStep
          title="Step 2: Label All Images"
          description="Assign a name to all"
          imageCount={paginatedData?.total_count || 0}
          label={batchLabel}
          onLabelChange={handleBatchLabelChange}
          onSubmit={handleBatchSubmit}
          disabled={submitting || speakersLoading}
          speakers={speakers.length > 0 ? speakers : undefined}
        />
      )}

      {/* Step 2 (Path B): Annotate outliers */}
      {step === "annotate-outliers" && (
        <OutlierAnnotationStep
          outlierImages={outlierImagesArray}
          annotations={outlierAnnotations}
          onLabelChange={handleOutlierLabelChange}
          onSubmit={handleOutliersSubmit}
          disabled={submitting || speakersLoading}
          speakers={speakers.length > 0 ? speakers : undefined}
        />
      )}

      {/* Step 3 (Path B): Label remaining images */}
      {step === "label-remaining" && (
        <BatchLabelStep
          title="Step 3: Label Remaining Images"
          description="Assign a name to the remaining"
          imageCount={
            paginatedData
              ? paginatedData.total_count - selectedOutlierImages.size
              : 0
          }
          label={batchLabel}
          onLabelChange={handleBatchLabelChange}
          onSubmit={handleBatchSubmit}
          disabled={submitting || speakersLoading}
          speakers={speakers.length > 0 ? speakers : undefined}
        />
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
