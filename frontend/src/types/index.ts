export interface Episode {
  id: string;
  name: string;
  upload_timestamp: string;
  status: string;
  total_clusters: number;
  annotated_clusters: number;
  season?: number; // Phase 3: Parsed from SxxEyy folder format
  episode_number?: number; // Phase 3: Parsed from SxxEyy folder format
}

export interface Cluster {
  id: string;
  episode_id: string;
  cluster_name: string;
  image_paths: string[];
  is_single_person?: boolean;
  person_name?: string;
  annotation_status: string;
  initial_label?: string; // Phase 3: Parsed from folder name
  cluster_number?: number; // Phase 3: Parsed from folder name
  has_outliers: boolean; // Phase 3: Whether outliers have been marked
  outlier_count: number; // Phase 3: Number of outlier images
}

export interface SplitAnnotation {
  id: string;
  cluster_id: string;
  scene_track_pattern: string;
  person_name: string;
  image_paths: string[];
}

export interface ClusterImages {
  cluster_id: string;
  cluster_name: string;
  all_images: string[];
  grouped_by_track: Record<string, string[]>;
}

export interface AnnotationRequest {
  is_single_person: boolean;
  person_name?: string;
}

export interface SplitAnnotationRequest {
  cluster_id: string;
  scene_track_pattern: string;
  person_name: string;
  image_paths: string[];
}

// Phase 3: New types for paginated cluster review and outlier workflow

export interface Image {
  id: string; // UUID serialized as string
  cluster_id: string;
  episode_id: string;
  file_path: string;
  filename: string;
  initial_label?: string;
  current_label?: string;
  annotation_status: string; // "pending" | "outlier" | "annotated"
  annotated_at?: string; // ISO datetime string
}

export interface PaginatedImagesResponse {
  cluster_id: string;
  cluster_name: string;
  initial_label?: string;
  images: Image[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface OutlierSelectionRequest {
  cluster_id: string;
  outlier_image_ids: string[]; // Array of UUID strings
}

export interface ClusterAnnotateBatch {
  person_name: string;
  is_custom_label: boolean;
}

export interface OutlierAnnotation {
  image_id: string;
  person_name: string;
  is_custom_label: boolean;
}
