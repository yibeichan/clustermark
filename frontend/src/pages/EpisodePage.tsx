import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { episodeApi } from '../services/api';
import { Episode, Cluster } from '../types';

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
      setClusters(clustersResponse.data);
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
        <h2>{episode.name}</h2>
        <p>Status: {episode.status}</p>
        <p>Progress: {episode.annotated_clusters} / {episode.total_clusters} images</p>

        <div style={{ marginTop: '20px', marginBottom: '20px' }}>
          <Link
            to={`/episodes/${episode.id}/annotate`}
            className="button"
            style={{
              fontSize: '18px',
              padding: '15px 30px',
              textDecoration: 'none',
              display: 'inline-block',
              marginRight: '10px'
            }}
          >
            Start Annotating
          </Link>
          <button
            className="button"
            onClick={handleExport}
            disabled={episode.annotated_clusters === 0}
          >
            Export Annotations
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Clusters</h3>
        <div className="grid">
          {clusters.map((cluster) => (
            <div key={cluster.id} className="card">
              <h4>{cluster.cluster_name}</h4>
              <p>Status: {cluster.annotation_status}</p>
              <p>Images: {cluster.image_paths.length}</p>
              {cluster.person_name && (
                <p>Person: {cluster.person_name}</p>
              )}
              {cluster.annotation_status === 'pending' ? (
                <Link 
                  to={`/annotate/${cluster.id}`}
                  className="button"
                  style={{ textDecoration: 'none', display: 'inline-block' }}
                >
                  Annotate
                </Link>
              ) : (
                <span style={{ color: '#28a745' }}>✓ Completed</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}