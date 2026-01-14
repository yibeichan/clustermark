import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { episodeApi } from '../services/api';
import { Episode } from '../types';

// Duplicate dialog state
interface DuplicateInfo {
  existingId: string;
  hasAnnotations: boolean;
  file: File;
}

export default function HomePage() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

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

  const handleDelete = async (episode: Episode) => {
    const hasAnnotations = episode.annotated_clusters > 0;
    const message = hasAnnotations
      ? `This episode has ${episode.annotated_clusters} annotated clusters. Delete anyway?`
      : `Delete episode "${episode.name}"?`;

    if (!window.confirm(message)) return;

    setDeleting(episode.id);
    try {
      await episodeApi.delete(episode.id);
      await loadEpisodes();
    } catch (err) {
      setError('Failed to delete episode');
    } finally {
      setDeleting(null);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    // Separate files
    const zipFile = acceptedFiles.find(f => f.name.endsWith('.zip'));
    const jsonFile = acceptedFiles.find(f => f.name.endsWith('.json'));

    if (!zipFile) {
      setError('Please upload a ZIP file.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await episodeApi.upload(zipFile, jsonFile);
      await loadEpisodes();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        // Duplicate detected - show options
        const detail = err.response.data.detail;
        setDuplicateInfo({
          existingId: detail.existing_id,
          hasAnnotations: detail.has_annotations,
          file: zipFile,
        });
      } else {
        setError('Failed to upload episode');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleReplace = async () => {
    if (!duplicateInfo) return;

    setUploading(true);
    setError(null);
    try {
      await episodeApi.replace(duplicateInfo.existingId, duplicateInfo.file);
      await loadEpisodes();
    } catch (err) {
      setError('Failed to replace episode');
    } finally {
      setUploading(false);
      setDuplicateInfo(null);
    }
  };



  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip'],
      'application/json': ['.json']
    },
    multiple: true,
    maxFiles: 2
  });

  if (loading) {
    return <div className="loading">Loading episodes...</div>;
  }

  return (
    <div>
      {/* Duplicate Dialog */}
      {duplicateInfo && (
        <div className="card card-warning">
          <h3>Episode Already Exists</h3>
          <p>
            {duplicateInfo.hasAnnotations
              ? 'This episode has annotations. What would you like to do?'
              : 'An episode with this name already exists.'}
          </p>
          <div className="button-group">
            <button
              type="button"
              className="button button-danger"
              onClick={handleReplace}
            >
              Replace
            </button>
            <button type="button" className="button button-secondary" onClick={() => setDuplicateInfo(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Upload Episode</h2>
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <p>Uploading...</p>
          ) : isDragActive ? (
            <p>Drop files here...</p>
          ) : (
            <div>
              <p>Drag and drop encoded episode (.zip)</p>
              <p className="text-secondary text-sm mt-2">Optional: Include annotations (.json) to skip labeling</p>
            </div>
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
                <button
                  type="button"
                  className="button button-danger button-sm"
                  onClick={() => handleDelete(episode)}
                  disabled={deleting === episode.id}
                >
                  {deleting === episode.id ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}