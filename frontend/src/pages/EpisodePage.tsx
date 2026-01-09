import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { episodeApi } from '../services/api';
import { Episode, Cluster } from '../types';
import { sortClusters } from '../utils/clusterSorting';

export default function EpisodePage() {
  const { episodeId } = useParams<{ episodeId: string }>();
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (episodeId) {
      loadEpisodeData(episodeId);
    }
  }, [episodeId]);

  const loadEpisodeData = async (id: string) => {
    try {
      const [episodeResponse, clustersResponse] = await Promise.all([
        episodeApi.get(id),
        episodeApi.getClusters(id)
      ]);
      setEpisode(episodeResponse.data);

      const sortedClusters = sortClusters(clustersResponse.data);
      setClusters(sortedClusters);
    } catch (err) {
      setError('Failed to load episode data');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!episodeId) return;

    try {
      const response = await episodeApi.export(episodeId);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${episode?.name}_annotations.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export annotations');
    }
  };

  if (loading) {
    return <div className="loading">Loading episode...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!episode) {
    return <div className="error">Episode not found</div>;
  }

  return (
    <div>
      <div className="card">
        <Link to="/">&larr; Back to Episodes</Link>
        <h2 className="mt-12">{episode.name}</h2>
        <p className="mt-8">Status: {episode.status}</p>
        <p className="mb-16">Progress: {episode.annotated_clusters} / {episode.total_clusters} clusters</p>
        <button
          className="button"
          onClick={handleExport}
          disabled={episode.annotated_clusters === 0}
        >
          Export Annotations
        </button>
      </div>

      <div className="card">
        <h3>Clusters</h3>
        <div className="grid">
          {clusters
            .filter((c) => c.annotation_status === 'pending')
            .map((cluster) => (
              <div key={cluster.id} className="card">
                <h4>{cluster.cluster_name}</h4>
                <p>Status: {cluster.annotation_status}</p>
                <p>Images: {cluster.image_paths.length}</p>
                <Link
                  to={`/annotate/${cluster.id}`}
                  className="button"
                  style={{ textDecoration: 'none', display: 'inline-block', marginTop: '12px' }}
                >
                  Annotate
                </Link>
              </div>
            ))}
        </div>

        {clusters.some((c) => c.annotation_status === 'annotated') && (
          <>
            <div className="cluster-divider">
              <hr className="divider-line" />
              <h4 className="divider-text">Completed</h4>
              <hr className="divider-line" />
            </div>

            <div className="grid">
              {clusters
                .filter((c) => c.annotation_status === 'annotated')
                .map((cluster) => (
                  <div key={cluster.id} className="card">
                    <h4>{cluster.cluster_name}</h4>
                    <div className="annotated-actions mt-8">
                      <span className="status-complete">✓ Completed</span>
                      {cluster.person_name && (
                        <span className="person-label">{cluster.person_name}</span>
                      )}
                      <Link
                        to={`/annotate/${cluster.id}`}
                        className="button button-secondary"
                        style={{
                          textDecoration: 'none',
                          display: 'inline-block',
                          marginTop: '8px',
                          backgroundColor: '#6c757d',
                          color: 'white',
                          padding: '6px 12px',
                          fontSize: '13px'
                        }}
                      >
                        Edit
                      </Link>
                    </div>
                  </div>
                ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}