import axios from "axios";
import {
  Episode,
  Cluster,
  ClusterImages,
  AnnotationRequest,
  SplitAnnotationRequest,
  PaginatedImagesResponse,
  OutlierSelectionRequest,
  ClusterAnnotateBatch,
  OutlierAnnotation,
  Image,
} from "../types";

const API_BASE = "/api";

const api = axios.create({
  baseURL: API_BASE,
});

export const episodeApi = {
  list: () => api.get<Episode[]>("/episodes"),
  get: (id: string) => api.get<Episode>(`/episodes/${id}`),
  getClusters: (id: string) => api.get<Cluster[]>(`/episodes/${id}/clusters`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<Episode>("/episodes/upload", formData);
  },
  export: (id: string) => api.get(`/episodes/${id}/export`),
};

export const clusterApi = {
  // Legacy endpoints (keep for backward compatibility)
  get: (id: string) => api.get<Cluster>(`/clusters/${id}`),
  getImages: (id: string) => api.get<ClusterImages>(`/clusters/${id}/images`),
  annotate: (id: string, annotation: AnnotationRequest) =>
    api.post(`/clusters/${id}/annotate`, annotation),

  // Phase 3: New endpoints for paginated review and outlier workflow
  getImagesPaginated: (id: string, page: number = 1, pageSize: number = 20) =>
    api.get<PaginatedImagesResponse>(`/clusters/${id}/images/paginated`, {
      params: { page, page_size: pageSize },
    }),

  markOutliers: (request: OutlierSelectionRequest) =>
    api.post(`/clusters/${request.cluster_id}/outliers`, request),

  annotateBatch: (id: string, annotation: ClusterAnnotateBatch) =>
    api.post(`/clusters/${id}/annotate-batch`, annotation),

  annotateOutliers: (annotations: OutlierAnnotation[]) =>
    api.post("/clusters/annotate-outliers", annotations),

  // Phase 6b: Get existing outliers (enables resume workflow)
  getOutliers: (clusterId: string) =>
    api.get<{ cluster_id: string; outliers: Image[]; count: number }>(
      `/clusters/${clusterId}/outliers`,
    ),
};

export const annotationApi = {
  createSplit: (annotations: SplitAnnotationRequest[]) =>
    api.post("/annotations/split", annotations),
  getNextTask: (sessionToken: string) =>
    api.get("/annotations/tasks/next", {
      params: { session_token: sessionToken },
    }),
  completeTask: (taskId: string, sessionToken: string) =>
    api.post(`/annotations/tasks/${taskId}/complete`, {
      session_token: sessionToken,
    }),
};
