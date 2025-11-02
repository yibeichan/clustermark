/**
 * ImageGridSkeleton component for loading states.
 *
 * Shows animated placeholder boxes while images are being fetched.
 * Improves perceived performance and UX compared to generic "Loading..." text.
 *
 * Usage:
 *   {loading ? <ImageGridSkeleton count={pageSize} /> : <ActualImageGrid />}
 */

interface ImageGridSkeletonProps {
  count?: number;
}

export default function ImageGridSkeleton({ count = 20 }: ImageGridSkeletonProps) {
  return (
    <div className="image-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="image-item skeleton">
          <div className="skeleton-content" />
        </div>
      ))}
    </div>
  );
}
