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
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      await episodeApi.upload(file);
      await loadEpisodes();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        // Duplicate detected - show options
        const detail = err.response.data.detail;
        setDuplicateInfo({
          existingId: detail.existing_id,
          hasAnnotations: detail.has_annotations,
          file: file,
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

  const handleRename = async () => {
    if (!duplicateInfo) return;

    // Create a new file with _v2 suffix
    const originalName = duplicateInfo.file.name.replace('.zip', '');
    const newName = `${originalName}_v2.zip`;
    const renamedFile = new File([duplicateInfo.file], newName, {
      type: duplicateInfo.file.type,
    });

    setUploading(true);
    setError(null);
    try {
      await episodeApi.upload(renamedFile);
      await loadEpisodes();
    } catch (err) {
      setError('Failed to upload renamed episode');
    } finally {
      setUploading(false);
      setDuplicateInfo(null);
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
      {/* Duplicate Dialog */}
      {duplicateInfo && (
        <div className="card" style={{ backgroundColor: '#fff3cd', borderColor: '#ffc107' }}>
          <h3>Episode Already Exists</h3>
          <p>
            {duplicateInfo.hasAnnotations
              ? 'This episode has annotations. What would you like to do?'
              : 'An episode with this name already exists.'}
          </p>
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button
              type="button"
              onClick={handleReplace}
              style={{ backgroundColor: '#dc3545', color: 'white' }}
            >
              Replace
            </button>
            <button type="button" onClick={handleRename}>
              Rename to _v2
            </button>
            <button type="button" onClick={() => setDuplicateInfo(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}

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
                <button
                  type="button"
                  onClick={() => handleDelete(episode)}
                  disabled={deleting === episode.id}
                  style={{
                    backgroundColor: '#dc3545',
                    color: 'white',
                    marginTop: '10px',
                    cursor: deleting === episode.id ? 'not-allowed' : 'pointer',
                  }}
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