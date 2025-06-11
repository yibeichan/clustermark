import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { episodeApi } from '../services/api';
import { Episode } from '../types';

export default function HomePage() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEpisodes();
  }, []);

  const loadEpisodes = async () => {
    try {
      const response = await episodeApi.list();
      setEpisodes(response.data);
    } catch (err) {
      setError('Failed to load episodes');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      await episodeApi.upload(file);
      await loadEpisodes();
    } catch (err) {
      setError('Failed to upload episode');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip']
    },
    multiple: false
  });

  if (loading) {
    return <div className="loading">Loading episodes...</div>;
  }

  return (
    <div>
      <div className="card">
        <h2>Upload Episode</h2>
        <div
          {...getRootProps()}
          style={{
            border: '2px dashed #ccc',
            padding: '40px',
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? '#f0f0f0' : 'white'
          }}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <p>Uploading...</p>
          ) : isDragActive ? (
            <p>Drop the ZIP file here...</p>
          ) : (
            <p>Drag and drop a ZIP file here, or click to select</p>
          )}
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="card">
        <h2>Episodes</h2>
        {episodes.length === 0 ? (
          <p>No episodes uploaded yet.</p>
        ) : (
          <div className="grid">
            {episodes.map((episode) => (
              <div key={episode.id} className="card">
                <h3>
                  <Link to={`/episodes/${episode.id}`}>{episode.name}</Link>
                </h3>
                <p>Status: {episode.status}</p>
                <p>
                  Progress: {episode.annotated_clusters} / {episode.total_clusters} clusters
                </p>
                <p>Uploaded: {new Date(episode.upload_timestamp).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}