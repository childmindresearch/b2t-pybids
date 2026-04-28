# Working with Custom Entities in bids2table_compat

## Overview

The bids2table compatibility layer supports custom entities just like PyBIDS, but in a simpler, more flexible way. Since the underlying data structure is a pandas DataFrame, you can add custom columns and query them naturally.

This document shows how to work with custom entities, as used by advanced tools like **templateflow**.

## Why Custom Entities?

Standard BIDS defines entities like `subject`, `session`, `task`, etc. But some projects need additional metadata:

- **templateflow**: `template`, `cohort`, `resolution`, `atlas`
- **Processing pipelines**: `status`, `qc_grade`, `processing_date`
- **Custom workflows**: Domain-specific labels, groupings, or derived metadata

## Three Ways to Add Custom Entities

### 1. Via BIDS Schema (Like templateflow)

If your custom entities follow BIDS naming patterns, define them in a schema:

```json
{
  "name": "myproject",
  "entities": [
    {
      "name": "mylabel",
      "pattern": "[_/\\\\]mylabel-([a-zA-Z0-9]+)"
    }
  ]
}
```

Then b2t will automatically parse them during indexing.

**Note**: This is advanced - most users don't need custom schemas.

### 2. Add Columns Programmatically (Recommended)

Simply add columns to `layout.df` like any pandas DataFrame:

```python
from bids2table_compat import BIDSLayout

layout = BIDSLayout('/path/to/dataset')

# Add custom entity based on logic
layout.df['processing_status'] = 'pending'
layout.df.loc[layout.df['sub'].isin(['01', '02']), 'processing_status'] = 'complete'

# Query it like standard entities
completed_files = layout.get(processing_status='complete', return_type='filename')
```

### 3. Map from External Data

Load custom metadata from files or databases:

```python
import pandas as pd

# Load external metadata
qc_data = pd.read_csv('qc_results.csv')  # sub, qc_grade columns

# Merge with layout
layout.df = layout.df.merge(qc_data, on='sub', how='left')

# Query with custom entity
good_files = layout.get(qc_grade='pass', return_type='filename')
```

## Common Patterns

### Pattern 1: Categorize Files by Type

```python
def categorize_file(row):
    """Add semantic categories."""
    if row['suffix'] in ['T1w', 'T2w', 'FLAIR']:
        return 'anatomical'
    elif row['suffix'] == 'bold':
        return 'functional'
    elif row['suffix'] == 'dwi':
        return 'diffusion'
    else:
        return 'other'

layout.df['modality_category'] = layout.df.apply(categorize_file, axis=1)

# Query by category
anat_files = layout.get(modality_category='anatomical', return_type='filename')
```

### Pattern 2: Add Processing Metadata

```python
# Mark files as processed
layout.df['processed'] = False

# After processing some files
processed_paths = ['/data/sub-01_T1w.nii.gz', '/data/sub-02_T1w.nii.gz']
layout.df.loc[layout.df['path'].isin(processed_paths), 'processed'] = True

# Query unprocessed files
pending = layout.get(processed=False, return_type='filename')
```

### Pattern 3: Add Metadata from Sidecars

```python
import bids2table as b2t

def add_tr_info(row):
    """Add RepetitionTime category."""
    if row['suffix'] != 'bold':
        return None
    
    metadata = b2t.load_bids_metadata(row['path'], layout.root)
    tr = metadata.get('RepetitionTime', 0)
    
    if tr < 1.0:
        return 'fast'
    elif tr < 2.0:
        return 'medium'
    else:
        return 'slow'

layout.df['tr_category'] = layout.df.apply(add_tr_info, axis=1)

# Query by TR
fast_tr = layout.get(tr_category='fast', suffix='bold', return_type='filename')
```

### Pattern 4: Rename/Recode Entities

```python
# Recode task names to abbreviations
task_mapping = {
    'balloonanalogrisktask': 'BART',
    'restingstate': 'rest',
    'nback': 'nback'
}

layout.df['task'] = layout.df['task'].replace(task_mapping)

# Now query with short names
bart_files = layout.get(task='BART', return_type='filename')
```

### Pattern 5: Subject-Level Metadata

```python
# Add demographics or QC at subject level
subject_metadata = {
    '01': {'age_group': 'adult', 'qc_status': 'pass'},
    '02': {'age_group': 'adult', 'qc_status': 'fail'},
    '03': {'age_group': 'child', 'qc_status': 'pass'},
}

# Add as columns
for sub_id, meta in subject_metadata.items():
    for key, value in meta.items():
        layout.df.loc[layout.df['sub'] == sub_id, key] = value

# Query by demographics and QC
adult_pass = layout.get(age_group='adult', qc_status='pass', return_type='filename')
```

## How templateflow Does It

Templateflow uses custom entities extensively:

```python
# templateflow has entities like: template, cohort, resolution, atlas, density
# These are defined in their config.json and parsed by b2t at index time

from templateflow import api as tflow

# Query with custom entities
mni_files = tflow.get(template='MNI152NLin2009cAsym', resolution=1)
infant_files = tflow.get(cohort=1)  # cohort = age group
```

Under the hood, templateflow's Layout is just:
1. A custom BIDS schema defining `template`, `cohort`, etc.
2. b2t indexes with that schema
3. Standard `.get()` queries work automatically

You can do the same without a custom schema by adding columns!

## Advanced: Computed Entities

For expensive computations, consider lazy evaluation:

```python
class LazyBIDSLayout(BIDSLayout):
    """Layout with on-demand computed entities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._computed = {}
    
    def add_computed_entity(self, name, compute_fn):
        """Register a function to compute entity on first access."""
        self._computed[name] = compute_fn
    
    def get(self, **entities):
        # Compute any lazy entities that are being queried
        for key in entities:
            if key in self._computed and key not in self.df.columns:
                print(f"Computing {key}...")
                self.df[key] = self.df.apply(self._computed[key], axis=1)
        
        return super().get(**entities)

# Usage
layout = LazyBIDSLayout('/path/to/dataset')

def compute_file_size(row):
    """Expensive: stat the file."""
    from pathlib import Path
    return Path(row['path']).stat().st_size

# Register but don't compute yet
layout.add_computed_entity('file_size', compute_file_size)

# First query computes it
large_files = layout.get(file_size=lambda x: x > 100_000_000)
```

## Comparison: PyBIDS vs bids2table_compat

### PyBIDS Approach
```python
from bids.layout import BIDSLayout, add_config_paths

# Must define schema upfront
add_config_paths(myproject='config.json')

layout = BIDSLayout('/data', config='myproject')
# Custom entities are now available
```

**Limitations**:
- Requires config file for each custom entity
- Hard to add entities dynamically
- Schema must be written before indexing

### bids2table_compat Approach
```python
from bids2table_compat import BIDSLayout

layout = BIDSLayout('/data')

# Add entities anytime, no config needed
layout.df['my_entity'] = compute_values()

# Query immediately
files = layout.get(my_entity='value')
```

**Benefits**:
- ✅ No config files needed
- ✅ Add entities anytime (before or after indexing)
- ✅ Full pandas flexibility
- ✅ Works with any computation or external data

## Best Practices

### 1. Name Entities Clearly
```python
# Good
layout.df['qc_visual_rating'] = ratings
layout.df['processing_batch_id'] = batch

# Avoid
layout.df['x'] = values  # What is x?
layout.df['status'] = status  # Status of what?
```

### 2. Document Custom Entities
```python
# Add to layout metadata
layout.custom_entities = {
    'qc_visual_rating': 'Manual QC rating (pass/fail/review)',
    'processing_batch_id': 'Batch ID from processing pipeline',
    'derived_snr': 'Signal-to-noise ratio computed from data'
}
```

### 3. Preserve Entity Types
```python
# Keep consistent types
layout.df['age'] = layout.df['age'].astype(int)
layout.df['qc_grade'] = layout.df['qc_grade'].astype('category')
```

### 4. Handle Missing Values
```python
# Be explicit about missing values
layout.df['processing_status'] = layout.df['processing_status'].fillna('pending')

# Or filter them out in queries
completed = layout.get(processing_status='complete')  # Won't match NaN
```

## Summary

**Adding custom entities is simple**:
1. Add column to `layout.df` using pandas operations
2. Query it with `layout.get(my_entity='value')`
3. That's it!

**No special methods needed** - it's just DataFrames all the way down.

This gives you all the power of PyBIDS's custom entities (like templateflow uses), plus:
- More flexibility (add/modify anytime)
- Simpler (no config files)
- More powerful (full pandas/polars capabilities)

See `examples/demo_custom_entities.py` for working code.
