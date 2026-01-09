import { Cluster } from '../types';

/**
 * Sorts clusters: pending first, then annotated.
 * Within the same status, sorts alphabetically by cluster name.
 */
export const sortClusters = (clusters: Cluster[]): Cluster[] => {
    return [...clusters].sort((a, b) => {
        // Pending clusters first
        if (a.annotation_status === 'pending' && b.annotation_status !== 'pending') {
            return -1;
        }
        if (a.annotation_status !== 'pending' && b.annotation_status === 'pending') {
            return 1;
        }
        // Within same status, sort by cluster name
        return a.cluster_name.localeCompare(b.cluster_name, undefined, { numeric: true });
    });
};
