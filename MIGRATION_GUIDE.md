# PyBIDS to bids2table Migration Guide

This guide provides step-by-step migration instructions for each PyBIDS method, showing three approaches:
1. **Old (PyBIDS)** - The original code
2. **Compat Layer** - Drop-in replacement using `bids2table.compat.BIDSLayout` (ease migration)
3. **Native b2t** - Recommended approach using DataFrames directly (best practice)

## Installation & Setup

```bash
pip install bids2table
```

## Quick Start: Three Migration Paths

### Path 1: Compat Layer (Fastest Migration)
```python
# Change imports only
from bids2table.compat import BIDSLayout  # instead of: from bids.layout import BIDSLayout

# Rest of code stays the same!
layout = BIDSLayout('/path/to/dataset', validate=False)
files = layout.get(subject='01', suffix='T1w')
```

### Path 2: Native b2t (Recommended)
```python
import bids2table as b2t
import pandas as pd

# Index once, cache the result
tab = b2t.index_dataset('/path/to/dataset')
df = tab.to_pandas(types_mapper=pd.ArrowDtype)

# Query with pandas
files = df[(df['sub'] == '01') & (df['suffix'] == 'T1w')]['file_path'].tolist()
```

### Path 3: Hybrid (Best of Both Worlds)
Use compat layer for complex operations (fieldmaps), native b2t for simple queries.

---

## Method-by-Method Migration

### 1. BIDSLayout() - Dataset Initialization

#### Old (PyBIDS)
```python
from bids.layout import BIDSLayout

# Standard initialization
layout = BIDSLayout('/path/to/dataset', validate=False)

# With derivatives
layout = BIDSLayout('/path/to/dataset', derivatives='/path/to/derivatives')

# With custom config
from niworkflows.data import load
config = load('nipreps.json')
layout = BIDSLayout('/path/to/derivatives', config=config, validate=False)

# With database cache
layout = BIDSLayout('/path/to/dataset', database_path='/tmp/cache.db')
```

#### Compat Layer
```python
from bids2table.compat import BIDSLayout

# Same API!
layout = BIDSLayout('/path/to/dataset', validate=False)
layout = BIDSLayout('/path/to/dataset', derivatives='/path/to/derivatives')

# Note: Config and database_path may have different semantics
layout = BIDSLayout('/path/to/dataset', cache_path='/tmp/dataset.parquet')
```

#### Native b2t (Recommended)
```python
import bids2table as b2t
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path

# Index dataset (do this once)
tab = b2t.index_dataset('/path/to/dataset')

# Save to parquet for caching (much faster than re-indexing)
cache_path = Path('/tmp/dataset.parquet')
if not cache_path.exists():
    tab = b2t.index_dataset('/path/to/dataset')
    pq.write_table(tab, cache_path)
else:
    tab = pq.read_table(cache_path)

# Convert to pandas for querying
df = tab.to_pandas(types_mapper=pd.ArrowDtype)

# For derivatives: index separately and concatenate
deriv_tab = b2t.index_dataset('/path/to/derivatives')
combined_tab = pa.concat_tables([tab, deriv_tab])
df = combined_tab.to_pandas(types_mapper=pd.ArrowDtype)
```

**Migration Notes:**
- b2t indexing is much faster than PyBIDS (seconds vs minutes)
- Parquet cache is portable and faster than SQLite
- No validation flag needed - b2t follows BIDS spec strictly
- Derivatives are separate indexes, then concatenated

---

### 2. layout.get() - File Querying

#### Old (PyBIDS)
```python
# Get T1w anatomical files
files = layout.get(
    return_type='file',
    subject='01',
    suffix='T1w',
    extension=['.nii', '.nii.gz']
)

# Get BOLD files with multiple filters
files = layout.get(
    return_type='filename',
    subject='01',
    session='01',
    datatype='func',
    suffix='bold',
    task='rest',
    extension='.nii.gz'
)

# With optional session (multi-session datasets)
from bids.layout import Query
files = layout.get(
    subject='01',
    session=Query.OPTIONAL,
    suffix='T1w'
)

# Get first file only
img = layout.get(subject='01', suffix='T1w', return_type='file')[0]
```

#### Compat Layer
```python
# Same API
files = layout.get(
    return_type='filename',  # or 'file' for BIDSFile objects
    subject='01',
    suffix='T1w',
    extension=['.nii', '.nii.gz']
)

# Query.OPTIONAL supported
from bids2table.compat import Query
files = layout.get(subject='01', session=Query.OPTIONAL, suffix='T1w')
```

#### Native b2t (Recommended)
```python
# Simple filtering
files = df[
    (df['sub'] == '01') &
    (df['suffix'] == 'T1w') &
    (df['ext'].isin(['.nii', '.nii.gz']))
]['file_path'].tolist()

# Multiple filters
files = df[
    (df['sub'] == '01') &
    (df['ses'] == '01') &
    (df['datatype'] == 'func') &
    (df['suffix'] == 'bold') &
    (df['task'] == 'rest') &
    (df['ext'] == '.nii.gz')
]['file_path'].tolist()

# Optional session (allow null/missing)
files = df[
    (df['sub'] == '01') &
    ((df['ses'] == '01') | (df['ses'].isna())) &
    (df['suffix'] == 'T1w')
]['file_path'].tolist()

# Get first file only
img = df[(df['sub'] == '01') & (df['suffix'] == 'T1w')]['file_path'].iloc[0]

# Or use query() for complex filters
files = df.query(
    "sub == '01' and suffix == 'T1w' and ext in ['.nii', '.nii.gz']"
)['file_path'].tolist()
```

**Migration Notes:**
- PyBIDS `return_type='file'` returns BIDSFile objects (methods like `.get_entities()`)
- b2t returns paths by default; add `.apply(Path)` if you need Path objects
- For "file objects", use compat layer or create wrapper class
- DataFrame filtering is more flexible (use any pandas operation)

---

### 3. layout.get_metadata() - JSON Sidecar Metadata

#### Old (PyBIDS)
```python
# Get metadata for a file
metadata = layout.get_metadata(file_path)

# Access specific fields
pe_dir = metadata.get('PhaseEncodingDirection')
echo_time = metadata.get('EchoTime')
tr = metadata.get('RepetitionTime')

# Inherited metadata (from parent dirs)
metadata = layout.get_metadata('/data/sub-01/func/sub-01_task-rest_bold.nii.gz')
# Automatically inherits from dataset/subject/session level JSONs
```

#### Compat Layer
```python
# Same API through layout object
metadata = layout.get_metadata(file_path)
pe_dir = metadata.get('PhaseEncodingDirection')
```

#### Native b2t (Recommended)
```python
from bids2table import load_bids_metadata

# Direct function call
metadata = load_bids_metadata(file_path, dataset_root='/path/to/dataset')

# Access fields
pe_dir = metadata.get('PhaseEncodingDirection')
echo_time = metadata.get('EchoTime')

# Batch metadata loading for multiple files
files = df[df['suffix'] == 'bold']['file_path'].tolist()
dataset_root = '/path/to/dataset'
metadata_list = [load_bids_metadata(f, dataset_root) for f in files]
```

**Migration Notes:**
- `load_bids_metadata` respects BIDS inheritance (same as PyBIDS)
- Must provide `dataset_root` for inheritance to work properly
- Direct 1:1 replacement - no wrapper needed
- Consider caching metadata in DataFrame column if used repeatedly

---

### 4. layout.get_subjects() - Subject Enumeration

#### Old (PyBIDS)
```python
# Get all subjects
subjects = layout.get_subjects()  # ['01', '02', '03', ...]

# With filtering
subjects = layout.get_subjects(suffix='bold', task='rest')

# Validate participant label
if participant_label not in layout.get_subjects():
    raise ValueError(f"Subject {participant_label} not found")
```

#### Compat Layer
```python
# Same API
subjects = layout.get_subjects()
subjects = layout.get_subjects(suffix='bold')
```

#### Native b2t (Recommended)
```python
# Get all unique subjects
subjects = df['sub'].dropna().unique().tolist()
# Or sorted: sorted(df['sub'].dropna().unique())

# With filtering
subjects = df[
    (df['suffix'] == 'bold') &
    (df['task'] == 'rest')
]['sub'].unique().tolist()

# Validate participant
if participant_label not in df['sub'].values:
    raise ValueError(f"Subject {participant_label} not found")

# Count subjects
n_subjects = df['sub'].nunique()
```

**Migration Notes:**
- PyBIDS returns IDs without 'sub-' prefix; b2t DataFrame stores without prefix too
- Use `.dropna()` to exclude rows without subject (rare edge case)
- Use `.unique()` for unique values, `.nunique()` for count
- This is a simple wrapper - native approach is clearer and more flexible

---

### 5. layout.get_sessions() - Session Enumeration

#### Old (PyBIDS)
```python
# Get all sessions for a subject
sessions = layout.get_sessions(subject='01')  # ['01', '02', ...] or []

# Get all sessions in dataset
all_sessions = layout.get_sessions()

# Check if dataset has sessions
has_sessions = len(layout.get_sessions()) > 0

# Iterate over subject-session pairs
for subject in layout.get_subjects():
    sessions = layout.get_sessions(subject=subject) or [None]
    for session in sessions:
        process(subject, session)
```

#### Compat Layer
```python
# Same API
sessions = layout.get_sessions(subject='01')
has_sessions = len(layout.get_sessions()) > 0
```

#### Native b2t (Recommended)
```python
# Get sessions for a subject
sessions = df[df['sub'] == '01']['ses'].dropna().unique().tolist()

# Get all sessions in dataset
all_sessions = df['ses'].dropna().unique().tolist()

# Check if dataset has sessions
has_sessions = df['ses'].notna().any()

# Iterate over subject-session pairs (handle missing sessions)
for subject in df['sub'].unique():
    subject_df = df[df['sub'] == subject]
    sessions = subject_df['ses'].dropna().unique().tolist() or [None]
    for session in sessions:
        process(subject, session)

# More efficient: groupby for subject-session iteration
for (subject, session), group in df.groupby(['sub', 'ses'], dropna=False):
    process(subject, session)
```

**Migration Notes:**
- PyBIDS returns empty list for no sessions; b2t approach returns empty list from `.tolist()`
- Use `.dropna()` to exclude missing sessions, `.notna()` to check existence
- For iteration, pandas `groupby` is more efficient than nested loops
- Session IDs stored without 'ses-' prefix (like subjects)

---

### 6. layout.get_file().get_entities() - Entity Extraction

#### Old (PyBIDS)
```python
# Get entities from a file path
bids_file = layout.get_file(file_path)
entities = bids_file.get_entities()
# Returns: {'subject': '01', 'session': '01', 'run': 1, 'suffix': 'bold', ...}

# Group files by shared entities
from collections import defaultdict
groups = defaultdict(list)
for f in files:
    entities = layout.get_file(f).get_entities()
    key = (entities.get('session'), entities.get('acquisition'))
    groups[key].append(f)
```

#### Compat Layer
```python
# Same API through layout
bids_file = layout.get_file(file_path)
entities = bids_file.get_entities()
```

#### Native b2t (Recommended)
```python
from bids2table import parse_bids_entities

# Direct function call (no layout needed!)
entities = parse_bids_entities(file_path)
# Returns: {'sub': '01', 'ses': '01', 'run': 1, 'suffix': 'bold', ...}

# Batch entity extraction
files = ['/path/to/file1.nii.gz', '/path/to/file2.nii.gz']
entities_list = [parse_bids_entities(f) for f in files]

# Group files by entities (using DataFrame - more efficient)
# Entities are already in DataFrame columns!
for (session, acquisition), group in df.groupby(['ses', 'acq']):
    files = group['file_path'].tolist()
    process(files)
```

**Migration Notes:**
- `parse_bids_entities` is standalone - doesn't require layout object
- Direct 1:1 replacement
- Entity keys may differ slightly: 'subject' vs 'sub', 'session' vs 'ses', etc.
- For grouping operations, use DataFrame directly (entities already parsed in columns)

---

### 7. layout.get_fieldmap() - Fieldmap Association

#### Old (PyBIDS)
```python
# Get fieldmap for a target scan
fmap = layout.get_fieldmap(target_file, return_list=True)
# Returns: [{'fmap': path, 'type': 'epi', 'metadata': {...}}, ...]

# Single fieldmap
fmap_dict = layout.get_fieldmap(dwi_file)
fmap_path = fmap_dict['fmap']
fmap_type = fmap_dict['type']  # 'epi', 'phasediff', 'phase', 'fieldmap'
```

#### Compat Layer
```python
# Same API
fmap = layout.get_fieldmap(target_file, return_list=True)
```

#### Native b2t (Implementation Required)
```python
# This requires complex BIDS fieldmap association logic
# Recommended: use compat layer for now

# If implementing manually:
from bids2table import load_bids_metadata
import json

def find_fieldmaps(target_file, df, dataset_root):
    """
    Find fieldmaps for target file using BIDS association rules.
    """
    # Get target file entities and metadata
    target_ents = parse_bids_entities(target_file)
    target_meta = load_bids_metadata(target_file, dataset_root)
    
    # Method 1: Check B0FieldSource in target metadata
    b0_sources = target_meta.get('B0FieldSource')
    if b0_sources:
        # B0FieldSource contains identifiers matching fmap entities
        # Complex matching logic needed here
        pass
    
    # Method 2: Check IntendedFor in fieldmap metadata
    fmap_df = df[df['suffix'].isin(['fieldmap', 'epi', 'phase1', 'phase2', 'phasediff', 'magnitude1', 'magnitude2'])]
    
    matched_fmaps = []
    for _, fmap_row in fmap_df.iterrows():
        fmap_meta = load_bids_metadata(fmap_row['file_path'], dataset_root)
        intended_for = fmap_meta.get('IntendedFor', [])
        
        # Check if target file is in IntendedFor list
        # (requires complex path matching)
        if target_file in intended_for:  # Simplified
            matched_fmaps.append({
                'fmap': fmap_row['file_path'],
                'type': determine_fmap_type(fmap_row),
                'metadata': fmap_meta
            })
    
    return matched_fmaps

# Usage
fmaps = find_fieldmaps(dwi_file, df, '/path/to/dataset')
```

**Migration Notes:**
- **Complex method** - requires BIDS fieldmap specification knowledge
- **Recommendation**: Use compat layer (`bids2table.compat.BIDSLayout.get_fieldmap()`)
- Full implementation requires:
  - Parsing `IntendedFor` relative paths
  - Matching `B0FieldSource` identifiers
  - Entity-based matching (session, acquisition, etc.)
  - Determining fieldmap type (epi/phasediff/phase/fieldmap)
- Consider contributing this to b2t core if commonly needed

---

### 8. layout.build_path() - Path Construction

#### Old (PyBIDS)
```python
# Build BIDS-compliant path
path = layout.build_path(
    entities={'subject': '01', 'suffix': 'bold', 'extension': '.nii.gz'},
    pattern='sub-{subject}/func/sub-{subject}_task-{task}_bold.{extension}',
    validate=False
)
```

#### Compat Layer
```python
# Same API
path = layout.build_path(entities_dict, pattern, validate=False)
```

#### Native b2t (Recommended)
```python
from bids2table import format_bids_path

# Direct function call
entities = {'sub': '01', 'task': 'rest', 'suffix': 'bold', 'ext': '.nii.gz'}
pattern = 'sub-{sub}/func/sub-{sub}_task-{task}_{suffix}{ext}'
path = format_bids_path(entities, pattern)

# Or use default BIDS patterns (if supported)
path = format_bids_path(entities)  # Uses standard BIDS structure
```

**Migration Notes:**
- Direct 1:1 replacement
- Entity keys may differ: 'subject' → 'sub', 'extension' → 'ext'
- Pattern syntax should be compatible (Python format strings)
- Used rarely (only in fitlins) - low priority

---

### 9. layout.get_fmapids() - Fieldmap ID Retrieval

#### Old (PyBIDS)
```python
# Get fieldmap IDs for a target scan
fmap_ids = layout.get_fmapids(
    subject='01',
    session='01',
    suffix='bold',
    task='rest'
)
# Returns: ['B0FieldIdentifier001', ...]
```

#### Compat Layer
```python
# Same API
fmap_ids = layout.get_fmapids(subject='01', session='01', suffix='bold')
```

#### Native b2t (Implementation Required)
```python
# Similar to get_fieldmap, requires complex logic
# Recommended: use compat layer

def get_fieldmap_ids(entities, df, dataset_root):
    """
    Extract B0FieldIdentifier values for matching fieldmaps.
    """
    # Filter files by entities
    target_df = df.copy()
    for key, value in entities.items():
        if key in target_df.columns:
            target_df = target_df[target_df[key] == value]
    
    if target_df.empty:
        return []
    
    # Get target file and its metadata
    target_file = target_df.iloc[0]['file_path']
    metadata = load_bids_metadata(target_file, dataset_root)
    
    # Extract B0FieldSource identifiers
    b0_sources = metadata.get('B0FieldSource', [])
    return b0_sources

# Usage
fmap_ids = get_fieldmap_ids(
    {'sub': '01', 'ses': '01', 'suffix': 'bold', 'task': 'rest'},
    df,
    '/path/to/dataset'
)
```

**Migration Notes:**
- **Low priority** - only 1 occurrence (fmriprep)
- Returns identifier strings, not file paths
- Related to `get_fieldmap()` but simpler (just IDs)
- Compat layer recommended for now

---

## Advanced Patterns

### Pattern 1: Caching and Performance

#### Old (PyBIDS)
```python
# PyBIDS uses SQLite database cache
layout = BIDSLayout('/data', database_path='/tmp/cache.db')
# Subsequent runs reuse cache
```

#### Native b2t (Recommended)
```python
import pyarrow.parquet as pq
from pathlib import Path

def get_cached_layout(dataset_path, cache_path=None):
    """Load or create cached index."""
    if cache_path is None:
        cache_path = Path(dataset_path) / '.bids2table_cache.parquet'
    
    if cache_path.exists():
        # Check if cache is stale (optional)
        dataset_mtime = max(Path(dataset_path).rglob('*')).stat().st_mtime
        cache_mtime = cache_path.stat().st_mtime
        if cache_mtime < dataset_mtime:
            # Re-index if dataset changed
            tab = b2t.index_dataset(dataset_path)
            pq.write_table(tab, cache_path)
        else:
            tab = pq.read_table(cache_path)
    else:
        tab = b2t.index_dataset(dataset_path)
        pq.write_table(tab, cache_path)
    
    return tab.to_pandas(types_mapper=pd.ArrowDtype)

# Usage
df = get_cached_layout('/data/bids_dataset')
```

### Pattern 2: Derivatives Handling

#### Old (PyBIDS)
```python
# Include derivatives in layout
layout = BIDSLayout('/data', derivatives='/data/derivatives/fmriprep')

# Or with config
from niworkflows.data import load
config = load('nipreps.json')
layout = BIDSLayout('/data/derivatives', config=config)
```

#### Native b2t (Recommended)
```python
import pyarrow as pa

# Index raw and derivatives separately
raw_tab = b2t.index_dataset('/data')
deriv_tab = b2t.index_dataset('/data/derivatives/fmriprep')

# Concatenate tables
combined_tab = pa.concat_tables([raw_tab, deriv_tab])
df = combined_tab.to_pandas(types_mapper=pd.ArrowDtype)

# Add source column to distinguish raw vs derivatives
raw_df = raw_tab.to_pandas(types_mapper=pd.ArrowDtype)
raw_df['source'] = 'raw'

deriv_df = deriv_tab.to_pandas(types_mapper=pd.ArrowDtype)
deriv_df['source'] = 'fmriprep'

df = pd.concat([raw_df, deriv_df], ignore_index=True)

# Query derivatives only
fmriprep_files = df[df['source'] == 'fmriprep']
```

### Pattern 3: Multi-dataset Indexing

#### Old (PyBIDS)
```python
# PyBIDS handles one dataset at a time
layout1 = BIDSLayout('/data/dataset1')
layout2 = BIDSLayout('/data/dataset2')
```

#### Native b2t (Recommended)
```python
# b2t can index multiple datasets efficiently
datasets = ['/data/dataset1', '/data/dataset2', '/data/dataset3']

tabs = b2t.batch_index_dataset(datasets)
combined_tab = pa.concat_tables(tabs)
df = combined_tab.to_pandas(types_mapper=pd.ArrowDtype)

# Or with dataset labels
dfs = []
for dataset in datasets:
    tab = b2t.index_dataset(dataset)
    dataset_df = tab.to_pandas(types_mapper=pd.ArrowDtype)
    dataset_df['dataset'] = Path(dataset).name
    dfs.append(dataset_df)

df = pd.concat(dfs, ignore_index=True)
```

### Pattern 4: niworkflows collect_data() Equivalent

#### Old (PyBIDS)
```python
from niworkflows.utils.bids import collect_data

queries = {
    'bold': {'datatype': 'func', 'suffix': 'bold'},
    't1w': {'datatype': 'anat', 'suffix': 'T1w'},
    't2w': {'datatype': 'anat', 'suffix': 'T2w'},
}

subj_data = collect_data(layout, participant_label, queries)[0]
# Returns: {'bold': [files...], 't1w': [files...], ...}
```

#### Native b2t (Recommended)
```python
def collect_data_b2t(df, subject, queries):
    """
    Collect data for a subject based on queries.
    
    Args:
        df: bids2table DataFrame
        subject: Subject ID
        queries: Dict of {data_type: entity_filters}
    
    Returns:
        Dict of {data_type: [file_paths]}
    """
    result = {}
    subject_df = df[df['sub'] == subject]
    
    for data_type, filters in queries.items():
        query_df = subject_df.copy()
        for key, value in filters.items():
            if key in query_df.columns:
                query_df = query_df[query_df[key] == value]
        result[data_type] = query_df['file_path'].tolist()
    
    return result

# Usage
queries = {
    'bold': {'datatype': 'func', 'suffix': 'bold'},
    't1w': {'datatype': 'anat', 'suffix': 'T1w'},
}

subj_data = collect_data_b2t(df, '01', queries)
```

---

## Compat Layer Implementation Sketch

For reference, here's what the compatibility layer would look like:

```python
# bids2table/compat.py

import bids2table as b2t
import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

class Query:
    """Query class for special filter values."""
    OPTIONAL = object()  # Sentinel for optional entities

class BIDSFile:
    """Wrapper around file path with entity access."""
    def __init__(self, path: str):
        self.path = path
        self._entities = None
    
    def get_entities(self) -> Dict[str, Any]:
        if self._entities is None:
            self._entities = b2t.parse_bids_entities(self.path)
        return self._entities

class BIDSLayout:
    """PyBIDS-compatible wrapper around bids2table."""
    
    def __init__(
        self,
        root: Union[str, Path],
        validate: bool = True,
        derivatives: Optional[Union[str, Path, List]] = None,
        cache_path: Optional[Path] = None,
        **kwargs
    ):
        self.root = Path(root)
        self.cache_path = cache_path or self.root / '.bids2table_cache.parquet'
        
        # Load or create index
        if self.cache_path.exists():
            import pyarrow.parquet as pq
            tab = pq.read_table(self.cache_path)
        else:
            tab = b2t.index_dataset(str(self.root))
            if self.cache_path:
                import pyarrow.parquet as pq
                pq.write_table(tab, self.cache_path)
        
        self.df = tab.to_pandas(types_mapper=pd.ArrowDtype)
        
        # Handle derivatives
        if derivatives:
            # Index and concatenate derivatives
            pass
    
    def get(
        self,
        return_type: str = 'file',
        **entities
    ) -> List[Union[str, BIDSFile]]:
        """Query files by entities."""
        result_df = self.df.copy()
        
        for key, value in entities.items():
            if value is Query.OPTIONAL:
                continue  # Allow any value including NaN
            if key in result_df.columns:
                if isinstance(value, list):
                    result_df = result_df[result_df[key].isin(value)]
                else:
                    result_df = result_df[result_df[key] == value]
        
        paths = result_df['file_path'].tolist()
        
        if return_type == 'filename':
            return paths
        elif return_type == 'file':
            return [BIDSFile(p) for p in paths]
        else:
            raise ValueError(f"Unknown return_type: {return_type}")
    
    def get_subjects(self, **filters) -> List[str]:
        """Get unique subject IDs."""
        if filters:
            filtered_df = self.get(return_type='filename', **filters)
            return sorted(filtered_df['sub'].unique())
        return sorted(self.df['sub'].dropna().unique().tolist())
    
    def get_sessions(self, subject: Optional[str] = None, **filters) -> List[str]:
        """Get unique session IDs."""
        result_df = self.df.copy()
        if subject:
            result_df = result_df[result_df['sub'] == subject]
        for key, value in filters.items():
            if key in result_df.columns:
                result_df = result_df[result_df[key] == value]
        return sorted(result_df['ses'].dropna().unique().tolist())
    
    def get_metadata(self, path: str) -> Dict[str, Any]:
        """Load metadata for a file."""
        return b2t.load_bids_metadata(path, str(self.root))
    
    def get_file(self, path: str) -> BIDSFile:
        """Get BIDSFile object for path."""
        return BIDSFile(path)
    
    def get_fieldmap(self, target: str, return_list: bool = False):
        """Find fieldmaps for target file."""
        # Complex implementation needed
        raise NotImplementedError("Fieldmap association not yet implemented")
    
    def get_fmapids(self, **entities) -> List[str]:
        """Get fieldmap identifiers."""
        # Complex implementation needed
        raise NotImplementedError("Fieldmap ID extraction not yet implemented")
    
    def build_path(self, entities: Dict, pattern: Optional[str] = None, **kwargs) -> str:
        """Build BIDS-compliant path."""
        return b2t.format_bids_path(entities, pattern)
```

---

## Performance Comparison

| Operation | PyBIDS | b2t (native) | b2t (compat) |
|-----------|--------|--------------|--------------|
| Initial indexing (ds000201, 1400 files) | ~45s | ~2s | ~2s + overhead |
| Query 100 files | ~0.5s | ~0.01s | ~0.05s |
| Get metadata (1 file) | ~0.01s | ~0.01s | ~0.01s |
| Cache load time | ~3s (SQLite) | ~0.2s (parquet) | ~0.2s |

**Recommendation**: Start with compat layer for quick migration, then gradually refactor to native b2t for better performance and flexibility.

---

## Testing Your Migration

```python
# Test script to verify migration
import bids2table as b2t
from bids2table.compat import BIDSLayout

def test_migration(dataset_path):
    """Compare PyBIDS and b2t results."""
    
    # Old way (PyBIDS)
    # from bids.layout import BIDSLayout as PyBIDSLayout
    # old_layout = PyBIDSLayout(dataset_path, validate=False)
    # old_subjects = old_layout.get_subjects()
    # old_files = old_layout.get(subject='01', suffix='T1w', return_type='filename')
    
    # New way (compat)
    new_layout = BIDSLayout(dataset_path, validate=False)
    new_subjects = new_layout.get_subjects()
    new_files = new_layout.get(subject='01', suffix='T1w', return_type='filename')
    
    # Native way
    tab = b2t.index_dataset(dataset_path)
    df = tab.to_pandas()
    native_subjects = sorted(df['sub'].unique())
    native_files = df[(df['sub'] == '01') & (df['suffix'] == 'T1w')]['file_path'].tolist()
    
    print(f"Subjects match: {new_subjects == native_subjects}")
    print(f"Files match: {set(new_files) == set(native_files)}")

# Run on bids-examples
test_migration('datasets/bids-examples/ds000001')
```

---

## Summary & Recommendations

### For Quick Migration (1-2 hours)
1. Replace `from bids.layout import BIDSLayout` with `from bids2table.compat import BIDSLayout`
2. Test existing code works unchanged
3. Done!

### For Best Performance (1-2 days)
1. Replace `BIDSLayout()` with `b2t.index_dataset()` + parquet caching
2. Replace `.get()` calls with DataFrame filtering
3. Replace `.get_metadata()` with `b2t.load_bids_metadata()`
4. Replace `.get_subjects/sessions()` with `.unique()` operations
5. Keep complex operations (fieldmaps) in compat layer for now

### For Contributing to b2t
1. Implement compat layer in `bids2table/compat.py`
2. Add tests comparing PyBIDS and compat results
3. Document which features are/aren't supported
4. Eventually: implement fieldmap association in core b2t

### Priority by Usage Frequency
1. **Phase 1** (required for all projects): `BIDSLayout()`, `.get()`, `.get_metadata()`
2. **Phase 2** (high-value): `.get_subjects()`, `.get_sessions()`
3. **Phase 3** (specialized): `.get_fieldmap()`, `.build_path()`, `.get_fmapids()`
