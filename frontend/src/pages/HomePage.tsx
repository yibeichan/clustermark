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

  const [pendingZip, setPendingZip] = useState<File | null>(null);
  const [pendingJson, setPendingJson] = useState<File | null>(null);

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

  const onDrop = (acceptedFiles: File[]) => {
    // Separate files
    const zipFile = acceptedFiles.find(f => f.name.endsWith('.zip'));
    const jsonFile = acceptedFiles.find(f => f.name.endsWith('.json'));

    if (zipFile) {
      setPendingZip(zipFile);
      setError(null);
    }
    if (jsonFile) {
      setPendingJson(jsonFile);
    }
  };

  const handleUpload = async () => {
    if (!pendingZip) {
      setError('Please upload a ZIP file.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await episodeApi.upload(pendingZip, pendingJson || undefined);
      // Clear pending files on success
      setPendingZip(null);
      setPendingJson(null);
      await loadEpisodes();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        // Duplicate detected - show options
        const detail = err.response.data.detail;
        setDuplicateInfo({
          existingId: detail.existing_id,
          hasAnnotations: detail.has_annotations,
          file: pendingZip,  // Use pending zip
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
      // Clear pending files after replace
      setPendingZip(null);
      setPendingJson(null);
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

  const getNameMatchStatus = () => {
    if (!pendingZip || !pendingJson) return null;
    const zipName = pendingZip.name.replace('.zip', '');
    const jsonName = pendingJson.name;
    // Simple check: does json contain the zip basename?
    // User requirement: "episode name should appear on both files"
    if (jsonName.includes(zipName)) {
      return { match: true, message: 'Filenames match' };
    }
    return {
      match: false,
      message: `Warning: Annotation filename doesn't contain episode name "${zipName}"`
    };
  };

  const matchStatus = getNameMatchStatus();

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

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''} mb-6`}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop files here...</p>
          ) : (
            <div>
              <p>Drag and drop encoded episode (.zip)</p>
              <p className="text-secondary text-sm mt-2">
                And optionally drop an annotations (.json) file.
              </p>
            </div>
          )}
        </div>

        {/* Selected Files Staging Area */}
        {(pendingZip || pendingJson) && (
          <div className="mb-6 border rounded p-4 bg-gray-50">
            <h4 className="mb-4">Selected Files:</h4>

            {/* Zip File Row */}
            <div className="flex items-center justify-between mb-2 p-2 bg-white rounded shadow-sm">
              <div className="flex items-center gap-2">
                <span className="font-bold text-primary">ZIP</span>
                {pendingZip ? (
                  <span>{pendingZip.name} ({(pendingZip.size / 1024 / 1024).toFixed(2)} MB)</span>
                ) : (
                  <span className="text-gray-400 italic">No episode file selected</span>
                )}
              </div>
              {pendingZip && (
                <button
                  onClick={() => setPendingZip(null)}
                  className="text-red-500 hover:underline text-sm"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Json File Row */}
            <div className="flex items-center justify-between mb-2 p-2 bg-white rounded shadow-sm">
              <div className="flex items-center gap-2">
                <span className="font-bold text-secondary">JSON</span>
                {pendingJson ? (
                  <span>{pendingJson.name}</span>
                ) : (
                  <span className="text-gray-400 italic">No annotations file selected (Optional)</span>
                )}
              </div>
              {pendingJson && (
                <button
                  onClick={() => setPendingJson(null)}
                  className="text-red-500 hover:underline text-sm"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Validation Message */}
            {matchStatus && (
              <div className={`text-sm mt-2 ${matchStatus.match ? 'text-green-600' : 'text-orange-500'}`}>
                {matchStatus.match ? '✓ ' : '⚠️ '} {matchStatus.message}
              </div>
            )}
          </div>
        )}

        {/* Upload Action */}
        <div className="flex gap-4 items-center">
          <button
            className="button button-primary"
            onClick={handleUpload}
            disabled={!pendingZip || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Episode'}
          </button>
          {error && <span className="error my-0">{error}</span>}
        </div>
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