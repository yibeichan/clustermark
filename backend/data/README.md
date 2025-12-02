# Backend Reference Data

This directory contains static reference data used by the ClusterMark application.

## Files

### `friends_speakers.tsv`

**Purpose**: Episode-specific speaker data for Friends TV show annotation workflow.

**Format**: Tab-separated values with 3 columns:
- `episode`: Episode identifier (format: `s01e01`, `s02e15`, etc.)
- `speaker`: Character/speaker name (lowercase)
- `utterances`: Number of utterances in that episode (integer)

**Example**:
```
episode	speaker	utterances
s01e01	monica	73
s01e01	rachel	48
s01e01	ross	47
```

**Usage**: 
- Loaded into database on initialization to populate `episode_speakers` table
- Used to show episode-specific dropdown options when annotating face clusters
- Utterance counts used for sorting (most frequent speakers shown first)

**Episode Suffix Handling**:
- Episodes with suffixes (e.g., `S01E05a`, `S01E05b`, `S01E05c`) all map to base episode (`s01e05`)
- Ensures consistent speaker lists across multi-part episode annotations

**Case Normalization**:
- TSV contains lowercase names (e.g., `rachel`, `mrs. geller`)
- Application normalizes to title case on import (e.g., `Rachel`, `Mrs. Geller`)
- Case-insensitive matching used for annotation comparisons

## Adding New Reference Data

To add new reference data:
1. Place file in `backend/data/`
2. Add documentation to this README
3. Create import script in `backend/scripts/` if database loading is required
4. Update `.gitignore` if file should NOT be tracked (this directory IS tracked by default)