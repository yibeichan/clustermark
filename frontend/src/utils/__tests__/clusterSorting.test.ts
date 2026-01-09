import { describe, it, expect } from 'vitest';
import { sortClusters } from '../clusterSorting';
import { Cluster } from '../../types';

describe('sortClusters', () => {
    it('should put pending clusters before annotated ones', () => {
        const mockClusters = [
            { id: '1', cluster_name: 'Cluster 1', annotation_status: 'annotated' },
            { id: '2', cluster_name: 'Cluster 2', annotation_status: 'pending' },
            { id: '3', cluster_name: 'Cluster 3', annotation_status: 'annotated' },
        ] as Cluster[];

        const sorted = sortClusters(mockClusters);

        expect(sorted[0].id).toBe('2');
        expect(sorted[1].annotation_status).toBe('annotated');
        expect(sorted[2].annotation_status).toBe('annotated');
    });

    it('should sort by cluster name within the same status', () => {
        const mockClusters = [
            { id: '1', cluster_name: 'Cluster 10', annotation_status: 'pending' },
            { id: '2', cluster_name: 'Cluster 2', annotation_status: 'pending' },
        ] as Cluster[];

        const sorted = sortClusters(mockClusters);

        // Numeric sort should ensure Cluster 2 comes before Cluster 10
        expect(sorted[0].cluster_name).toBe('Cluster 2');
        expect(sorted[1].cluster_name).toBe('Cluster 10');
    });

    it('should maintain original clusters when sorting (pure function)', () => {
        const mockClusters = [
            { id: '1', cluster_name: 'Cluster 1', annotation_status: 'annotated' },
            { id: '2', cluster_name: 'Cluster 2', annotation_status: 'pending' },
        ] as Cluster[];

        const originalOrder = [...mockClusters];
        sortClusters(mockClusters);

        expect(mockClusters).toEqual(originalOrder);
    });
});
