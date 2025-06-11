import axios from 'axios';
import { Episode, Cluster, ClusterImages, AnnotationRequest, SplitAnnotationRequest } from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
});

export const episodeApi = {
  list: () => api.get<Episode[]>('/episodes'),
  get: (id: string) => api.get<Episode>(`/episodes/${id}`),
  getClusters: (id: string) => api.get<Cluster[]>(`/episodes/${id}/clusters`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Episode>('/episodes/upload', formData);
  },
  export: (id: string) => api.get(`/episodes/${id}/export`),
};

export const clusterApi = {
  get: (id: string) => api.get<Cluster>(`/clusters/${id}`),
  getImages: (id: string) => api.get<ClusterImages>(`/clusters/${id}/images`),
  annotate: (id: string, annotation: AnnotationRequest) => 
    api.post(`/clusters/${id}/annotate`, annotation),
};

export const annotationApi = {
  createSplit: (annotations: SplitAnnotationRequest[]) =>
    api.post('/annotations/split', annotations),
  getNextTask: (sessionToken: string) =>
    api.get('/annotations/tasks/next', { params: { session_token: sessionToken } }),
  completeTask: (taskId: string, sessionToken: string) =>
    api.post(`/annotations/tasks/${taskId}/complete`, { session_token: sessionToken }),
};