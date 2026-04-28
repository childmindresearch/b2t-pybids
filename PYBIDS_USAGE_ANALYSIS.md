# PyBIDS Usage Analysis and Migration Guide

This document analyzes pybids usage patterns across major neuroimaging pipelines and provides guidance for migration to bids2table (b2t).

## Analysis Summary

Based on analysis of 6 major projects (fmriprep, smriprep, mriqc, qsiprep, fitlins, niworkflows), we identified **133 total pybids method calls** across the codebases.

## PyBIDS Methods: Usage Frequency and Migration Guide

| Method/Function | Usage Count | Projects Using | Importance | B2T Analog Exists | Migration Strategy |
|----------------|-------------|----------------|------------|-------------------|-------------------|
| **BIDSLayout()** | 44 | All 6 | **CRITICAL** | Partial | **New wrapper needed** - Core layout object with caching, validation control |
| **layout.get()** | 21 | 5/6 (not mriqc) | **CRITICAL** | Partial | **New endpoint needed** - Query interface with filtering |
| **layout.get_metadata()** | 24 | 3/6 (fmriprep, qsiprep, niworkflows) | **CRITICAL** | ✓ Yes (`load_bids_metadata`) | **Migration guide** - Direct mapping available |
| **layout.get_subjects()** | 8 | 2/6 (fmriprep, smriprep) | **HIGH** | Partial | **New endpoint needed** - Extract unique subjects from index |
| **layout.get_sessions()** | 7 | 2/6 (fmriprep, smriprep) | **HIGH** | Partial | **New endpoint needed** - Extract unique sessions from index |
| **layout.get_file().get_entities()** | 6 | 1/6 (qsiprep) | **MEDIUM** | ✓ Yes (`parse_bids_entities`) | **Migration guide** - Direct mapping available |
| **layout.get_fmapids()** | 2 | 1/6 (fmriprep) | **MEDIUM** | ✗ No | **New endpoint needed** - Complex fieldmap association logic |
| **layout.get_fieldmap()** | 1 | 1/6 (qsiprep) | **MEDIUM** | ✗ No | **New endpoint needed** - Fieldmap matching by IntendedFor |
| **layout.get_runs()** | ? | Multiple | **MEDIUM** | Partial | **New endpoint needed** - Extract unique runs from index |
| **layout.get_tasks()** | ? | Multiple | **MEDIUM** | Partial | **New endpoint needed** - Extract unique tasks from index |
| **layout.build_path()** | ? | Multiple | **LOW** | ✓ Yes (`format_bids_path`) | **Migration guide** - Direct mapping available |

## Detailed Method Analysis

### 1. BIDSLayout() - Dataset Indexing (44 occurrences)

**Importance**: CRITICAL - Core initialization for all workflows

**Common Usage Patterns**:
```python
# Standard layout with validation disabled
layout = BIDSLayout(str(bids_dir), validate=False)

# Derivatives with custom config
from niworkflows.data import load
config = load('nipreps.json')
layout = BIDSLayout(derivatives_dir, config=config, validate=False)

# With database caching
layout = BIDSLayout(str(bids_dir), database_path=db_path, validate=False)
```

**Key Parameters**:
- `validate`: bool (90% use `False` for performance)
- `config`: list/str (for derivatives)
- `database_path`: Path (for persistent caching)
- `derivatives`: bool/Path (include derivative datasets)

**B2T Analog**:
```python
# B2T approach - indexes to PyArrow table
import bids2table as b2t
tab = b2t.index_dataset(bids_dir)
df = tab.to_pandas(types_mapper=pd.ArrowDtype)
```

**Migration Strategy**: **New wrapper class needed**
- Create `BIDSLayout` wrapper around b2t index
- Cache indexed table (parquet) for performance
- Support derivatives via re-indexing
- Map validation flag to b2t schema validation

---

### 2. layout.get() - File Querying (21 occurrences)

**Importance**: CRITICAL - Primary query interface

**Common Usage Patterns**:
```python
# Get T1w anatomical files
files = layout.get(
    return_type='file',  # or 'filename'
    subject='01',
    suffix='T1w',
    extension=['.nii', '.nii.gz']
)

# Get BOLD functional files with optional session
files = layout.get(
    return_type='filename',
    subject=sub_id,
    session=ses_id,  # can be None
    datatype='func',
    suffix='bold',
    task=task_name,
    extension='.nii.gz'
)

# Query with OPTIONAL session support
from bids.layout import Query
files = layout.get(
    subject='01',
    session=Query.OPTIONAL,
    suffix='T1w'
)
```

**Key Parameters**:
- `return_type`: 'file', 'filename', 'id', 'dir' (most common: 'file'/'filename')
- Entity filters: `subject`, `session`, `run`, `task`, `acquisition`, etc.
- `suffix`: data type (e.g., 'bold', 'T1w', 'dwi')
- `datatype`: BIDS datatype (e.g., 'func', 'anat', 'dwi')
- `extension`: file extensions (often `['.nii', '.nii.gz']`)
- `scope`: 'all', 'derivatives', 'raw' (controls search scope)

**B2T Analog**:
```python
# B2T approach - pandas/polars DataFrame filtering
df = tab.to_pandas()
files = df[
    (df['sub'] == '01') &
    (df['suffix'] == 'T1w') &
    (df['ext'].isin(['.nii', '.nii.gz']))
]['file_path'].tolist()
```

**Migration Strategy**: **New endpoint needed**
- Add `BIDSLayout.get()` method that wraps DataFrame filtering
- Support `return_type` parameter (default 'filename')
- Handle `Query.OPTIONAL` (allow None/NaN values)
- Map entity keys to DataFrame columns
- Return BIDSFile objects or paths based on return_type

---

### 3. layout.get_metadata() - Sidecar JSON Retrieval (24 occurrences)

**Importance**: CRITICAL - Essential for metadata-driven processing

**Common Usage Patterns**:
```python
# Get metadata for a specific file
metadata = layout.get_metadata(file_path)

# Access specific fields
pe_dir = metadata.get('PhaseEncodingDirection')
echo_time = metadata.get('EchoTime')
tr = metadata.get('RepetitionTime')

# Inherited metadata (BIDS inheritance principle)
# PyBIDS automatically inherits from parent dirs
metadata = layout.get_metadata(dwi_file)  # inherits from dataset/subject/session JSONs
```

**Common Metadata Fields Accessed**:
- `PhaseEncodingDirection` (PE direction for distortion correction)
- `EchoTime` (multi-echo sequences)
- `TotalReadoutTime` (EPI distortion)
- `EffectiveEchoSpacing` (EPI distortion)
- `B0FieldSource` (fieldmap associations)
- `IntendedFor` (fieldmap targets)
- `RepetitionTime` (fMRI timing)
- `SliceTiming` (slice timing correction)

**B2T Analog**:
```python
# B2T has direct equivalent!
from bids2table import load_bids_metadata

metadata = load_bids_metadata(file_path, dataset_path)
```

**Migration Strategy**: **Migration guide sufficient**
- Direct mapping: `layout.get_metadata(path)` → `load_bids_metadata(path, dataset_root)`
- B2T respects BIDS inheritance principle
- Document that dataset_path is required for inheritance

---

### 4. layout.get_subjects() - Subject Enumeration (8 occurrences)

**Importance**: HIGH - Participant-level iteration

**Common Usage Patterns**:
```python
# Get all subjects in dataset
subjects = layout.get_subjects()  # Returns ['01', '02', '03', ...]

# Filter subjects by having specific data
subjects = layout.get_subjects(suffix='bold', task='rest')

# Validate participant labels
if participant_label not in layout.get_subjects():
    raise ValueError(f"Subject {participant_label} not found")
```

**B2T Analog**:
```python
# B2T approach - extract unique subjects from index
df = tab.to_pandas()
subjects = df['sub'].dropna().unique().tolist()

# With filtering
subjects = df[df['suffix'] == 'bold']['sub'].unique().tolist()
```

**Migration Strategy**: **New endpoint needed**
- Add `BIDSLayout.get_subjects(**filters)` method
- Extract unique values from 'sub' column
- Support entity filters (e.g., `suffix='bold'`)
- Return sorted list of subject IDs (without 'sub-' prefix)

---

### 5. layout.get_sessions() - Session Enumeration (7 occurrences)

**Importance**: HIGH - Session-level iteration

**Common Usage Patterns**:
```python
# Get all sessions for a subject
sessions = layout.get_sessions(subject='01')  # Returns ['01', '02', ...] or []

# Check if dataset has sessions
has_sessions = len(layout.get_sessions()) > 0

# Iterate over subject-session pairs
for subject in layout.get_subjects():
    sessions = layout.get_sessions(subject=subject) or [None]
    for session in sessions:
        process(subject, session)
```

**B2T Analog**:
```python
# B2T approach
df = tab.to_pandas()
sessions = df[df['sub'] == '01']['ses'].dropna().unique().tolist()

# Check if any sessions exist
has_sessions = df['ses'].notna().any()
```

**Migration Strategy**: **New endpoint needed**
- Add `BIDSLayout.get_sessions(subject=None, **filters)` method
- If `subject` provided, filter by subject first
- Extract unique values from 'ses' column
- Return sorted list of session IDs (without 'ses-' prefix)
- Return empty list if no sessions (not None)

---

### 6. layout.get_file().get_entities() - Entity Extraction (6 occurrences)

**Importance**: MEDIUM - Entity-based grouping

**Common Usage Patterns**:
```python
# Extract entities from file path
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

**B2T Analog**:
```python
# B2T has direct equivalent!
from bids2table import parse_bids_entities

entities = parse_bids_entities(file_path)
# Returns dict with BIDS entities
```

**Migration Strategy**: **Migration guide sufficient**
- Direct mapping: `layout.get_file(path).get_entities()` → `parse_bids_entities(path)`
- Both return dictionaries with entity keys
- Document that b2t version is standalone (no layout needed)

---

### 7. layout.get_fmapids() - Fieldmap ID Retrieval (2 occurrences)

**Importance**: MEDIUM - fMRI distortion correction

**Common Usage Patterns**:
```python
# Get fieldmap IDs associated with a BOLD file
fmap_ids = layout.get_fmapids(
    subject='01',
    session='01',
    suffix='bold',
    task='rest'
)
# Returns list of fieldmap identifiers

# Used in fmriprep for SDC (susceptibility distortion correction)
```

**B2T Analog**: ✗ **No equivalent**

**Migration Strategy**: **New endpoint needed**
- Requires complex logic:
  1. Parse `B0FieldSource` from target file metadata
  2. Or use `IntendedFor` from fieldmap metadata (reverse lookup)
  3. Match fieldmap entities (PE direction, acq, etc.)
- Consider wrapping as `BIDSLayout.get_fieldmap_ids(**entities)`
- May need to implement BIDS fieldmap association rules

---

### 8. layout.get_fieldmap() - Fieldmap File Retrieval (1 occurrence)

**Importance**: MEDIUM - DWI/fMRI preprocessing

**Common Usage Patterns**:
```python
# Get fieldmap files for a given scan
fmap = layout.get_fieldmap(dwi_file, return_list=True)
# Returns dict or list of dicts with fieldmap info:
# {'fmap': path, 'type': 'epi'/'phasediff'/..., 'metadata': {...}}

# Used in qsiprep for distortion correction
```

**B2T Analog**: ✗ **No equivalent**

**Migration Strategy**: **New endpoint needed**
- Similar to `get_fmapids()` but returns actual files
- Needs BIDS fieldmap matching logic:
  - Check `IntendedFor` field in fieldmap metadata
  - Match entities (subject, session, acquisition)
  - Determine fieldmap type (phase/magnitude, epi, etc.)
- Consider `BIDSLayout.get_fieldmaps(target_file)`

---

### 9-10. layout.get_runs() / layout.get_tasks() - Entity Listing

**Importance**: MEDIUM - Iteration over runs/tasks

**Common Usage Patterns**:
```python
# Get all runs for a subject/session
runs = layout.get_runs(subject='01', session='01', suffix='bold')

# Get all tasks in dataset
tasks = layout.get_tasks()
```

**B2T Analog**: Partial (DataFrame filtering)

**Migration Strategy**: **New endpoint needed**
- Similar to `get_subjects()` and `get_sessions()`
- Add `BIDSLayout.get_<entity>(**filters)` methods
- Generic implementation for any entity column

---

### 11. layout.build_path() - Path Construction

**Importance**: LOW - Output path generation

**Common Usage Patterns**:
```python
# Build BIDS-compliant path from entities
path = layout.build_path(
    entities={'subject': '01', 'suffix': 'bold', 'extension': '.nii.gz'},
    pattern='sub-{subject}/func/sub-{subject}_task-{task}_bold.{extension}'
)
```

**B2T Analog**:
```python
# B2T has direct equivalent!
from bids2table import format_bids_path

path = format_bids_path(entities_dict, pattern)
```

**Migration Strategy**: **Migration guide sufficient**
- Direct mapping exists
- Document pattern syntax differences (if any)

---

## Priority Ranking for Implementation

### Phase 1: Critical Core (Blocking most workflows)
1. **BIDSLayout wrapper class** - Core infrastructure
2. **layout.get()** - Primary query interface  
3. **layout.get_metadata()** - Metadata access (migration guide only)

### Phase 2: High-Value Utilities
4. **layout.get_subjects()** - Subject iteration
5. **layout.get_sessions()** - Session iteration
6. **layout.get_entities()** - Entity extraction (migration guide only)

### Phase 3: Specialized Features
7. **layout.get_fieldmap() / get_fmapids()** - Fieldmap association
8. **layout.get_runs() / get_tasks()** - Generic entity listing
9. **layout.build_path()** - Path construction (migration guide only)

## Project-Specific Usage Notes

### fmriprep (27 calls)
- Heavy fieldmap logic (`get_fmapids`)
- Derivative caching for reusing outputs
- EchoTime sorting for multi-echo

### qsiprep (44 calls - highest usage!)
- Most intensive metadata user
- DWI-specific: fieldmap matching, PE direction grouping
- `MultipartID` for grouping related scans

### niworkflows (21 calls)
- Provides reusable `collect_data()` function
- Used by fmriprep, smriprep, others
- **High-priority target** - fixing here fixes all downstream

### fitlins (23 calls)
- BIDS-Stats model file queries
- Derivatives-heavy (analyzes preprocessed data)

### smriprep (10 calls)
- Transform file caching
- Spatial normalization queries

### mriqc (8 calls - lowest usage)
- Basic layout initialization only
- Easiest migration target

## Common Parameter Patterns

- **validate=False**: 90% of instantiations (performance critical)
- **return_type='file' vs 'filename'**: File objects vs strings
- **extension=['.nii', '.nii.gz']**: NIfTI filtering ubiquitous
- **session=Query.OPTIONAL**: Handle single/multi-session datasets
- **scope='derivatives'**: Distinguish raw vs processed data

## Metadata Fields by Use Case

### Distortion Correction (SDC)
- `PhaseEncodingDirection`
- `TotalReadoutTime`
- `EffectiveEchoSpacing`
- `B0FieldSource`
- `IntendedFor`

### Timing Information
- `RepetitionTime`
- `EchoTime`
- `SliceTiming`
- `DelayTime`

### Grouping/Association
- `MultipartID` (qsiprep)
- `IntendedFor` (fieldmaps)
- `B0FieldSource` (reverse fieldmap lookup)

## Recommendations

1. **Start with niworkflows**: Fixing `collect_data()` impacts all pipelines
2. **Prioritize caching**: PyBIDS performance relies on SQLite cache; b2t needs parquet cache
3. **Fieldmap logic is complex**: Consider external library or detailed BIDS spec implementation
4. **Test with derivatives**: Derivatives config is heavily used
5. **Validate parameter coverage**: Entity filters are extensive (20+ entity types)

## Next Steps

1. Create `BIDSLayout` wrapper class skeleton
2. Implement `.get()` method with DataFrame filtering
3. Write migration guide for direct mappings (`get_metadata`, `parse_entities`, `format_path`)
4. Build test suite using bids-examples datasets
5. Profile performance vs PyBIDS (especially with caching)
6. Gather user feedback from pipeline maintainers
