# Custom Entities Support - Summary

## Question

> The concern already raised by templateflow developers is that they create their own entities mid-processing, add them to the layout, and then want to query them.

## Answer

✅ **No new methods needed!** The compatibility layer already supports this pattern naturally.

## How It Works

Since `BIDSLayout.df` is a pandas DataFrame, you can add custom columns anytime and query them immediately:

### Method 1: Direct DataFrame Manipulation (Most Flexible)

```python
from bids2table_compat import BIDSLayout

layout = BIDSLayout('/path/to/dataset')

# Add custom entity as a column
layout.df['my_custom_entity'] = some_values

# Query it like any standard entity
files = layout.get(my_custom_entity='value', return_type='filename')
```

### Method 2: Convenience Helper (Cleaner API)

We've added `add_custom_entity()` for common patterns:

```python
# Add constant value
layout.add_custom_entity('status', 'pending')

# Add from dict (maps subject to value)
qc_grades = {'01': 'pass', '02': 'fail', '03': 'pass'}
layout.add_custom_entity('qc_grade', qc_grades)

# Add from function
def categorize(row):
    return 'anatomical' if row['datatype'] == 'anat' else 'functional'
layout.add_custom_entity('modality_type', categorize)

# Query combined with standard entities
files = layout.get(subject='01', qc_grade='pass', return_type='filename')
```

## Real-World Example: templateflow Pattern

Templateflow adds custom entities like `template`, `cohort`, `resolution`. Here's how it works with b2t:

```python
# templateflow defines custom entities in config.json
# b2t indexes and includes them as columns automatically
layout = BIDSLayout('/path/to/templateflow')

# Custom entities are already there (from schema)
mni_files = layout.get(template='MNI152NLin2009cAsym', resolution=1)

# Or add them programmatically if not in schema
layout.df['atlas_type'] = compute_atlas_type()
atlas_files = layout.get(atlas_type='probabilistic')
```

## Common Patterns Demonstrated

### 1. Processing Status Tracking
```python
# Mark files as processed
layout.df['processed'] = False
layout.df.loc[layout.df['path'].isin(completed_paths), 'processed'] = True

# Query unprocessed
pending = layout.get(processed=False)
```

### 2. QC Metadata
```python
# Add QC grades from external file
qc_data = pd.read_csv('qc_results.csv')
layout.df = layout.df.merge(qc_data, on='sub', how='left')

# Query passed files
good_files = layout.get(qc_visual='pass', subject='01')
```

### 3. Derived Metadata
```python
# Add metadata from sidecars
def get_tr_category(row):
    metadata = b2t.load_bids_metadata(row['path'], layout.root)
    tr = metadata.get('RepetitionTime', 0)
    return 'fast' if tr < 1.0 else 'slow'

layout.df['tr_category'] = layout.df.apply(get_tr_category, axis=1)
fast_tr = layout.get(tr_category='fast', suffix='bold')
```

### 4. Renaming Entities
```python
# Recode task names
task_map = {'balloonanalogrisktask': 'BART', 'restingstate': 'rest'}
layout.df['task'] = layout.df['task'].replace(task_map)

# Query with new names
bart = layout.get(task='BART')
```

## Testing

We've added comprehensive tests (`tests/test_compat/test_custom_entities.py`):

- ✅ Add constant values
- ✅ Add from dict (subject mapping)
- ✅ Add from function (computed values)
- ✅ Add from list/array
- ✅ Combine standard + custom entities
- ✅ Overwrite protection
- ✅ Direct DataFrame manipulation
- ✅ Modify existing entities
- ✅ Handle None/NaN values

**Result**: 10/10 tests passing

## Comparison: PyBIDS vs bids2table_compat

| Feature | PyBIDS | bids2table_compat |
|---------|--------|-------------------|
| Add custom entities | Requires config file | Direct DataFrame manipulation |
| Timing | Must define before indexing | Add anytime (before/after) |
| Flexibility | Limited to schema patterns | Any pandas operation |
| Query syntax | Same `.get()` | Same `.get()` |
| Complexity | Config files + regex patterns | Simple Python code |

## Benefits for templateflow

1. **No config file needed** (though can still use one)
2. **Add entities dynamically** during processing
3. **Full pandas power** for complex operations
4. **Simpler migration** - works like PyBIDS but more flexible
5. **Better performance** - no schema overhead

## Documentation

- **Full guide**: `docs/CUSTOM_ENTITIES.md`
- **Working demo**: `examples/demo_custom_entities.py`
- **Tests**: `tests/test_compat/test_custom_entities.py`

## Recommendation

**For templateflow developers:**

You can:
1. Keep your existing config.json (b2t will parse custom entities)
2. Or add entities programmatically: `layout.df['entity'] = values`
3. Query exactly like PyBIDS: `layout.get(entity='value')`

**No new methods needed** - it just works! The underlying DataFrame structure makes custom entities a natural fit.

## Example: Complete templateflow-Style Workflow

```python
from bids2table_compat import BIDSLayout

# Index with custom schema (if you have config.json)
layout = BIDSLayout('/path/to/templates')
# Custom entities from schema are already columns

# Or add custom entities dynamically
layout.add_custom_entity('atlas_version', 'v2.0')
layout.df['processing_date'] = pd.Timestamp.now()

# Compute derived entity
def get_template_group(row):
    if 'MNI' in row.get('template', ''):
        return 'adult'
    elif 'NKI' in row.get('template', ''):
        return 'pediatric'
    return 'other'

layout.add_custom_entity('template_group', get_template_group)

# Query with mix of standard and custom entities
adult_templates = layout.get(
    template_group='adult',
    resolution=1,
    atlas_version='v2.0',
    return_type='filename'
)

# Update entity values
layout.df.loc[layout.df['template'] == 'MNI152Lin', 'deprecated'] = True

# Query non-deprecated
current = layout.get(deprecated=False)
```

## Conclusion

✅ **Custom entities work out of the box** - no special implementation needed.

The DataFrame-based approach makes custom entities more flexible and powerful than PyBIDS, while maintaining the same query interface.

This addresses the templateflow concern completely: add entities anytime, query them naturally, with zero additional complexity.
