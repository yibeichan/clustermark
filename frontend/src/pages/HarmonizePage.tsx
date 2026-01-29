import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { consolidationApi, episodeApi } from '../services/api'; // Added episodeApi
import { Pile } from '../types';
import LabelDropdown from '../components/LabelDropdown';

export default function HarmonizePage() {
    const { episodeId } = useParams<{ episodeId: string }>();
    const navigate = useNavigate();
    const [piles, setPiles] = useState<Pile[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedPiles, setSelectedPiles] = useState<Set<string>>(new Set());
    const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
    const [expandedPileId, setExpandedPileId] = useState<string | null>(null);
    const [combineLabel, setCombineLabel] = useState<string>('');
    const [speakers, setSpeakers] = useState<string[]>([]); // For LabelDropdown

    // Ref for auto-scrolling inspector
    const inspectorRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to top when inspector opens or changes pile
    useEffect(() => {
        if (expandedPileId && inspectorRef.current) {
            inspectorRef.current.scrollTop = 0;
        }
    }, [expandedPileId]);

    // Define bucket URL base
    const BUCKET_URL = '/uploads';

    useEffect(() => {
        if (episodeId) {
            loadData();
        }
    }, [episodeId]);

    const loadData = async () => {
        if (!episodeId) return;
        try {
            const [pilesRes, speakersRes] = await Promise.all([
                consolidationApi.getPiles(episodeId),
                episodeApi.getSpeakers(episodeId)
            ]);
            setPiles(pilesRes.data);
            setSpeakers(speakersRes.data.speakers);
        } catch (err) {
            setError('Failed to load harmonization data');
        } finally {
            setLoading(false);
        }
    };

    const togglePileSelection = (pileId: string) => {
        const newSelected = new Set(selectedPiles);
        if (newSelected.has(pileId)) {
            newSelected.delete(pileId);
        } else {
            newSelected.add(pileId);
        }
        setSelectedPiles(newSelected);
    };

    const toggleImageSelection = (imageId: string) => {
        const newSelected = new Set(selectedImages);
        if (newSelected.has(imageId)) {
            newSelected.delete(imageId);
        } else {
            newSelected.add(imageId);
        }
        setSelectedImages(newSelected);
    };

    const handleCombinePiles = () => {
        if (selectedPiles.size < 2 || !combineLabel) return;

        const sourcePiles = piles.filter(p => selectedPiles.has(p.id));
        const allImages = sourcePiles.flatMap(p => p.images);

        // Create new merged pile
        const newPile: Pile = {
            id: crypto.randomUUID(),
            name: combineLabel,
            isOutlier: combineLabel.toLowerCase().startsWith('dk'),
            images: allImages
        };

        // Remove source piles and add new one
        const remainingPiles = piles.filter(p => !selectedPiles.has(p.id));
        setPiles([newPile, ...remainingPiles].sort((a, b) => b.images.length - a.images.length));

        // Reset selection
        setSelectedPiles(new Set());
        setCombineLabel('');
    };

    const handleMoveImages = (targetPileId: string) => {
        if (selectedImages.size === 0) return;

        // Find source images and remove them from their current piles
        const newPiles = piles.map(pile => {
            // Filter out moving images from this pile
            const remainingImages = pile.images.filter(img => !selectedImages.has(img.id));

            // If this is the target pile, add the moving images
            if (pile.id === targetPileId) {
                // Find the actual image objects from current state (inefficient but safe)
                const movingImages = piles.flatMap(p => p.images).filter(img => selectedImages.has(img.id));
                // Remove duplicates if any (shouldn't be, but good practice)
                const uniqueIds = new Set(remainingImages.map(i => i.id));
                const newImagesToAdd = movingImages.filter(i => !uniqueIds.has(i.id));
                return { ...pile, images: [...remainingImages, ...newImagesToAdd] };
            }

            return { ...pile, images: remainingImages };
        }).filter(p => p.images.length > 0); // Remove empty piles

        setPiles(newPiles);
        setSelectedImages(new Set());
    };

    const handleSave = async () => {
        if (!episodeId) return;
        try {
            setIsSaving(true);
            await consolidationApi.saveHarmonization(episodeId, piles);
            navigate(`/episodes/${episodeId}`);
        } catch (err) {
            setError('Failed to save harmonization');
            setIsSaving(false);
        }
    };

    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="harmonize-page">
            <div className="card sticky-header">
                <div className="flex justify-between items-center">
                    <h2>Harmonize: {piles.length} Piles</h2>
                    <div className="button-group">
                        <button className="button button-secondary" onClick={() => navigate(`/episodes/${episodeId}`)}>
                            Cancel
                        </button>
                        <button
                            className="button"
                            onClick={handleSave}
                            disabled={isSaving}
                        >
                            {isSaving ? 'Saving...' : 'Save & Finish'}
                        </button>
                    </div>
                </div>
            </div>

            <div className="harmonize-content mt-4">
                {/* Inspection View - Full Screen Images Only */}
                {expandedPileId ? (
                    <div ref={inspectorRef} className="card inspector-panel">
                        {(() => {
                            const pile = piles.find(p => p.id === expandedPileId);
                            if (!pile) return null;

                            return (
                                <>
                                    <div className="flex justify-between items-center mb-4">
                                        <div className="flex items-center gap-4">
                                            <button
                                                className="button button-secondary"
                                                onClick={() => setExpandedPileId(null)}
                                            >
                                                ← Back to Piles
                                            </button>
                                            <h3>
                                                <span className={`badge ${pile.isOutlier ? 'badge-warning' : 'badge-primary'}`}>
                                                    {pile.name}
                                                </span>
                                                <span className="text-secondary ml-2">({pile.images.length} images)</span>
                                            </h3>
                                        </div>

                                        {selectedImages.size > 0 && (
                                            <div className="flex items-center gap-2">
                                                <span>Move {selectedImages.size} images to:</span>
                                                <select
                                                    className="form-select"
                                                    onChange={(e) => {
                                                        if (e.target.value) handleMoveImages(e.target.value);
                                                    }}
                                                    value=""
                                                >
                                                    <option value="">Select pile...</option>
                                                    {piles.filter(p => p.id !== pile.id).map(p => (
                                                        <option key={p.id} value={p.id}>{p.name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-fill-100 gap-2">
                                        {pile.images.map(img => (
                                            <div
                                                key={img.id}
                                                className={`relative cursor-pointer ${selectedImages.has(img.id) ? 'ring-2 ring-primary' : ''}`}
                                                onClick={() => toggleImageSelection(img.id)}
                                            >
                                                <img
                                                    src={`${BUCKET_URL}/${img.file_path}`}
                                                    className="w-full h-24 object-cover rounded"
                                                    alt={pile.name}
                                                />
                                                {/* Selection indicator overlay */}
                                                {selectedImages.has(img.id) && (
                                                    <div className="absolute top-1 right-1 bg-primary text-white rounded-full w-4 h-4 flex items-center justify-center text-xs">
                                                        ✓
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </>
                            );
                        })()}
                    </div>
                ) : (
                    /* Pile List View */
                    <>
                        {/* Combine Controls */}
                        {selectedPiles.size > 1 && (
                            <div className="card card-action mb-4">
                                <h3>Combine {selectedPiles.size} Piles</h3>

                                <div className="info-box naming-help-box my-3">
                                    <ul className="info-box-list text-xs text-secondary">
                                        <li>For "Others", use descriptive names (e.g. <code>woman1</code>, <code>man_in_red</code>).</li>
                                        <li>Do NOT reuse names unless they are the same person.</li>
                                    </ul>
                                </div>

                                <div className="flex items-center gap-4 mt-2">
                                    <LabelDropdown
                                        value={combineLabel}
                                        onChange={(label) => {
                                            setCombineLabel(label);
                                        }}
                                        speakers={speakers}
                                        placeholder="Select new label for combined pile..."
                                    />
                                    <button
                                        className="button"
                                        disabled={!combineLabel}
                                        onClick={handleCombinePiles}
                                    >
                                        Combine
                                    </button>
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-fill-200 gap-4">
                            {piles.map(pile => (
                                <div
                                    key={pile.id}
                                    className={`card pile-card ${selectedPiles.has(pile.id) ? 'selected' : ''}`}
                                    onClick={() => togglePileSelection(pile.id)}
                                >
                                    <div className="pile-header flex justify-between">
                                        <span className={`badge ${pile.isOutlier ? 'badge-warning' : 'badge-primary'}`}>
                                            {pile.name}
                                        </span>
                                        <span className="text-secondary">{pile.images.length}</span>
                                    </div>

                                    <div className="pile-preview mt-2 grid grid-cols-2 gap-1 pointer-events-none">
                                        {pile.images.slice(0, 4).map(img => (
                                            <img
                                                key={img.id}
                                                src={`${BUCKET_URL}/${img.file_path}`}
                                                className="w-full h-16 object-cover rounded"
                                                alt=""
                                            />
                                        ))}
                                    </div>

                                    <div className="mt-2 text-center">
                                        <button
                                            className="button button-sm button-secondary w-full"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setExpandedPileId(pile.id);
                                            }}
                                        >
                                            Inspect
                                        </button>
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
