import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { clusterApi, annotationApi } from '../services/api';
import { Cluster, ClusterImages, SplitAnnotationRequest } from '../types';

export default function AnnotationPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const navigate = useNavigate();
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [clusterImages, setClusterImages] = useState<ClusterImages | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState<'question' | 'single-person' | 'split'>('question');
  const [personName, setPersonName] = useState('');
  const [splitAnnotations, setSplitAnnotations] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clusterId) {
      loadClusterData(clusterId);
    }
  }, [clusterId]);

  const loadClusterData = async (id: string) => {
    try {
      const [clusterResponse, imagesResponse] = await Promise.all([
        clusterApi.get(id),
        clusterApi.getImages(id)
      ]);
      setCluster(clusterResponse.data);
      setClusterImages(imagesResponse.data);
    } catch (err) {
      setError('Failed to load cluster data');
    } finally {
      setLoading(false);
    }
  };

  const handleSinglePersonAnswer = (isSinglePerson: boolean) => {
    if (isSinglePerson) {
      setStep('single-person');
    } else {
      setStep('split');
    }
  };

  const handleSinglePersonSubmit = async () => {
    if (!clusterId || !personName.trim()) return;

    try {
      await clusterApi.annotate(clusterId, {
        is_single_person: true,
        person_name: personName.trim()
      });
      navigate(`/episodes/${cluster?.episode_id}`);
    } catch (err) {
      setError('Failed to save annotation');
    }
  };

  const handleSplitSubmit = async () => {
    if (!clusterId || !clusterImages) return;

    const annotations: SplitAnnotationRequest[] = Object.entries(splitAnnotations)
      .filter(([_, name]) => name.trim())
      .map(([pattern, name]) => ({
        cluster_id: clusterId,
        scene_track_pattern: pattern,
        person_name: name.trim(),
        image_paths: clusterImages.grouped_by_track[pattern] || []
      }));

    if (annotations.length === 0) {
      setError('Please assign names to at least one group');
      return;
    }

    try {
      await annotationApi.createSplit(annotations);
      navigate(`/episodes/${cluster?.episode_id}`);
    } catch (err) {
      setError('Failed to save split annotations');
    }
  };

  if (loading) {
    return <div className="loading">Loading cluster...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!cluster || !clusterImages) {
    return <div className="error">Cluster not found</div>;
  }

  return (
    <div>
      <div className="card">
        <button 
          className="button" 
          onClick={() => navigate(`/episodes/${cluster.episode_id}`)}
        >
          &larr; Back to Episode
        </button>
        <h2>Annotate {cluster.cluster_name}</h2>
        <p>{clusterImages.all_images.length} images total</p>
      </div>

      {step === 'question' && (
        <div className="card">
          <h3>Do all these faces belong to the same person?</h3>
          <div className="image-grid">
            {clusterImages.all_images.slice(0, 20).map((imagePath, index) => (
              <div key={index} className="image-item">
                <img 
                  src={`/uploads/${imagePath}`} 
                  alt={`Face ${index + 1}`}
                  onError={(e) => {
                    e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
                  }}
                />
              </div>
            ))}
          </div>
          {clusterImages.all_images.length > 20 && (
            <p>Showing first 20 of {clusterImages.all_images.length} images</p>
          )}
          <div style={{ marginTop: '20px' }}>
            <button 
              className="button" 
              onClick={() => handleSinglePersonAnswer(true)}
              style={{ marginRight: '10px' }}
            >
              Yes - Same Person
            </button>
            <button 
              className="button" 
              onClick={() => handleSinglePersonAnswer(false)}
            >
              No - Multiple People
            </button>
          </div>
        </div>
      )}

      {step === 'single-person' && (
        <div className="card">
          <h3>Who is this person?</h3>
          <input
            type="text"
            value={personName}
            onChange={(e) => setPersonName(e.target.value)}
            placeholder="Enter person name"
            style={{ 
              padding: '10px', 
              fontSize: '16px', 
              width: '300px', 
              marginRight: '10px' 
            }}
          />
          <button 
            className="button" 
            onClick={handleSinglePersonSubmit}
            disabled={!personName.trim()}
          >
            Save Annotation
          </button>
        </div>
      )}

      {step === 'split' && (
        <div className="card">
          <h3>Assign names to each group</h3>
          <p>Images have been grouped by scene and track. Assign a person name to each group:</p>
          
          {Object.entries(clusterImages.grouped_by_track).map(([pattern, images]) => (
            <div key={pattern} style={{ marginBottom: '30px', border: '1px solid #ddd', padding: '15px', borderRadius: '4px' }}>
              <h4>{pattern} ({images.length} images)</h4>
              <div className="image-grid" style={{ marginBottom: '10px' }}>
                {images.slice(0, 6).map((imagePath, index) => (
                  <div key={index} className="image-item">
                    <img 
                      src={`/uploads/${imagePath}`} 
                      alt={`${pattern} ${index + 1}`}
                      onError={(e) => {
                        e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
                      }}
                    />
                  </div>
                ))}
              </div>
              {images.length > 6 && <p>Showing 6 of {images.length} images</p>}
              <input
                type="text"
                value={splitAnnotations[pattern] || ''}
                onChange={(e) => setSplitAnnotations(prev => ({
                  ...prev,
                  [pattern]: e.target.value
                }))}
                placeholder="Enter person name"
                style={{ padding: '8px', fontSize: '14px', width: '200px' }}
              />
            </div>
          ))}
          
          <button 
            className="button" 
            onClick={handleSplitSubmit}
          >
            Save Split Annotations
          </button>
        </div>
      )}
    </div>
  );
}