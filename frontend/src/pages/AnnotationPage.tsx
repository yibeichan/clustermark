import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { imageApi } from '../services/api';
import { Image } from '../types';

export default function AnnotationPage() {
  const { episodeId } = useParams<{ episodeId: string }>();
  const navigate = useNavigate();

  const [currentImage, setCurrentImage] = useState<Image | null>(null);
  const [availableLabels, setAvailableLabels] = useState<string[]>([]);
  const [selectedLabel, setSelectedLabel] = useState('');
  const [customLabel, setCustomLabel] = useState('');
  const [useCustomLabel, setUseCustomLabel] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (episodeId) {
      loadLabels(episodeId);
      loadNextImage(episodeId);
    }
  }, [episodeId]);

  const loadLabels = async (id: string) => {
    try {
      const response = await imageApi.getLabels(id);
      setAvailableLabels(response.data.labels);
    } catch (err) {
      console.error('Failed to load labels', err);
    }
  };

  const loadNextImage = async (id: string) => {
    setLoading(true);
    try {
      const response = await imageApi.getNext(id);
      if (response.data.image) {
        setCurrentImage(response.data.image);
        // Pre-select initial label if it exists
        if (response.data.image.initial_label) {
          setSelectedLabel(response.data.image.initial_label);
          setUseCustomLabel(false);
        }
        setError(null);
      } else {
        setCompleted(true);
      }
    } catch (err) {
      setError('Failed to load next image');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!currentImage || !episodeId) return;

    const label = useCustomLabel ? customLabel.trim() : selectedLabel;
    if (!label) {
      setError('Please select or enter a label');
      return;
    }

    try {
      await imageApi.annotate(currentImage.id, label);
      // Load next image immediately
      await loadNextImage(episodeId);
      // Reset form
      setCustomLabel('');
      setUseCustomLabel(false);
    } catch (err) {
      setError('Failed to save annotation');
    }
  };

  const handleCorrect = async () => {
    // Quick "correct" button - uses initial label
    if (!currentImage || !currentImage.initial_label || !episodeId) return;

    try {
      await imageApi.annotate(currentImage.id, currentImage.initial_label);
      await loadNextImage(episodeId);
    } catch (err) {
      setError('Failed to save annotation');
    }
  };

  if (completed) {
    return (
      <div className="card">
        <h2>All Done!</h2>
        <p>All images have been annotated.</p>
        <button className="button" onClick={() => navigate(`/episodes/${episodeId}`)}>
          Back to Episode
        </button>
      </div>
    );
  }

  if (loading && !currentImage) {
    return <div className="loading">Loading...</div>;
  }

  if (!currentImage) {
    return <div className="error">No images to annotate</div>;
  }

  return (
    <div>
      <div className="card">
        <button className="button" onClick={() => navigate(`/episodes/${episodeId}`)}>
          &larr; Back to Episode
        </button>
        <h2>Image Annotation</h2>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Image Display */}
      <div className="card" style={{ textAlign: 'center' }}>
        <img
          src={`/uploads/${currentImage.file_path}`}
          alt={currentImage.filename}
          style={{ maxWidth: '100%', maxHeight: '600px', objectFit: 'contain' }}
        />
        <p style={{ marginTop: '10px', color: '#666' }}>{currentImage.filename}</p>
      </div>

      {/* Label Assignment */}
      <div className="card">
        <h3>Current Label: {currentImage.initial_label || 'Unlabeled'}</h3>

        {/* Quick confirm button */}
        {currentImage.initial_label && (
          <div style={{ marginBottom: '20px' }}>
            <button
              className="button"
              onClick={handleCorrect}
              style={{ backgroundColor: '#28a745', fontSize: '18px', padding: '15px 30px' }}
            >
              ✓ Correct (Keep: {currentImage.initial_label})
            </button>
          </div>
        )}

        <h4>Change Label:</h4>

        {/* Dropdown selection */}
        <div style={{ marginBottom: '15px' }}>
          <select
            value={useCustomLabel ? '' : selectedLabel}
            onChange={(e) => {
              setSelectedLabel(e.target.value);
              setUseCustomLabel(false);
            }}
            disabled={useCustomLabel}
            style={{ padding: '10px', fontSize: '16px', width: '300px' }}
          >
            <option value="">Select a label...</option>
            {availableLabels.map(label => (
              <option key={label} value={label}>{label}</option>
            ))}
          </select>
        </div>

        {/* Custom input */}
        <div style={{ marginBottom: '15px' }}>
          <label>
            <input
              type="checkbox"
              checked={useCustomLabel}
              onChange={(e) => setUseCustomLabel(e.target.checked)}
            />
            {' '}Use custom label
          </label>
        </div>

        {useCustomLabel && (
          <div style={{ marginBottom: '15px' }}>
            <input
              type="text"
              value={customLabel}
              onChange={(e) => setCustomLabel(e.target.value)}
              placeholder="Enter new label"
              style={{ padding: '10px', fontSize: '16px', width: '300px' }}
            />
          </div>
        )}

        {/* Submit button */}
        <button
          className="button"
          onClick={handleSubmit}
          disabled={!useCustomLabel && !selectedLabel}
        >
          Save & Next →
        </button>

        {/* Keyboard shortcuts hint */}
        <p style={{ marginTop: '20px', color: '#666', fontSize: '14px' }}>
          Tip: Press Enter to confirm
        </p>
      </div>
    </div>
  );
}
