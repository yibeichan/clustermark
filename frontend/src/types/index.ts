export interface Episode {
  id: string;
  name: string;
  upload_timestamp: string;
  status: string;
  total_clusters: number;
  annotated_clusters: number;
}

export interface Cluster {
  id: string;
  episode_id: string;
  cluster_name: string;
  image_paths: string[];
  is_single_person?: boolean;
  person_name?: string;
  annotation_status: string;
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

// New types for image-by-image annotation
export interface Image {
  id: string;
  cluster_id: string;
  episode_id: string;
  file_path: string;
  filename: string;
  initial_label: string | null;
  current_label: string | null;
  annotation_status: 'pending' | 'completed';
  annotated_at: string | null;
}

export interface ImageAnnotateRequest {
  label: string;
}

export interface NextImageResponse {
  message?: string;
  image: Image | null;
}

export interface LabelsResponse {
  labels: string[];
}