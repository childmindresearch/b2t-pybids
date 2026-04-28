"""Demo: Custom Entities - Advanced Usage Patterns"""

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Working with Custom Entities

    ## Overview

    The bids2table compatibility layer supports custom entities just like PyBIDS,
    but simpler and more flexible. Since the underlying data is a pandas DataFrame,
    you can add custom columns and query them naturally.

    This is how **templateflow** handles custom entities like `template`, `cohort`, `resolution`.

    ## Why Custom Entities?

    Standard BIDS defines entities like `subject`, `session`, `task`. But some projects need more:

    - **templateflow**: `template`, `cohort`, `resolution`, `atlas`
    - **Processing pipelines**: `status`, `qc_grade`, `processing_date`
    - **Custom workflows**: Domain-specific labels, groupings, derived metadata

    This notebook shows three ways to add custom entities and common usage patterns.
    """)
    return


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    # Find test dataset
    repo_root = Path.cwd().parent if Path.cwd().name == 'examples' else Path.cwd()
    dataset_path = repo_root / 'datasets' / 'bids-examples' / 'ds001'

    if not dataset_path.exists():
        mo.md(f"⚠️ Dataset not found: {dataset_path}")
        mo.stop()

    mo.md(f"✅ Using dataset: `{dataset_path.name}`")
    return dataset_path, mo


@app.cell
def _(dataset_path):
    from bids2table_compat import BIDSLayout

    # Initialize layout
    layout = BIDSLayout(dataset_path, validate=False)
    return (layout,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Method 1: Direct DataFrame Manipulation

    The simplest approach - add columns directly to `layout.df`.
    """)
    return


@app.cell
def _(layout, mo):
    # Add a custom label based on file type
    layout.df['my_custom_label'] = layout.df['suffix'].apply(
        lambda x: 'anatomical' if x in ['T1w', 'T2w', 'inplaneT2']
        else 'functional' if x == 'bold'
        else 'other'
    )

    mo.md(f"""
    **Added**: `my_custom_label` column

    **Values**: `{layout.df['my_custom_label'].unique().tolist()}`

    Now we can query files using this custom entity!
    """)
    return


@app.cell
def _(layout, mo):
    # Query with custom entity
    anatomical_files = layout.get(my_custom_label='anatomical', return_type='filename')
    functional_files = layout.get(my_custom_label='functional', return_type='filename')

    mo.md(f"""
    **Query**: `my_custom_label='anatomical'` → {len(anatomical_files)} files

    **Query**: `my_custom_label='functional'` → {len(functional_files)} files
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Method 2: Using add_custom_entity() Helper

    The compat layer provides a convenience method for common patterns.
    """)
    return


@app.cell
def _(layout, mo):
    # Add constant value
    layout.add_custom_entity('processing_status', 'pending')

    # Add from dict (subject → value mapping)
    qc_grades = {'01': 'pass', '02': 'fail', '03': 'pass'}
    layout.add_custom_entity('qc_grade', qc_grades)

    mo.md("""
    **Added**:
    - `processing_status` = 'pending' (constant for all files)
    - `qc_grade` = subject-specific values from dict
    """)
    return


@app.cell
def _(layout, mo):
    # Query with both standard and custom entities
    sub01_pass = layout.get(
        subject='01',
        qc_grade='pass',
        return_type='filename'
    )

    mo.md(f"""
    **Combined query**: `subject='01'` + `qc_grade='pass'`

    **Found**: {len(sub01_pass)} files
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Method 3: Add Entity from Function

    Compute custom entities based on complex logic.
    """)
    return


@app.cell
def _(layout, mo):
    # Define function to compute entity
    def categorize_by_datatype(row):
        if row.get('datatype') == 'anat':
            return 'structural'
        elif row.get('datatype') == 'func':
            return 'functional'
        else:
            return 'other'

    layout.add_custom_entity('scan_category', categorize_by_datatype)

    mo.md(f"""
    **Added**: `scan_category` computed from datatype

    **Values**: `{layout.df['scan_category'].unique().tolist()}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Common Pattern 1: Categorize Files

    Group files into semantic categories for easier querying.
    """)
    return


@app.cell
def _(layout, mo):
    # Categorize by modality
    def categorize_modality(row):
        suffix = row.get('suffix', '')
        if suffix in ['T1w', 'T2w', 'FLAIR', 'inplaneT2']:
            return 'anatomical'
        elif suffix == 'bold':
            return 'functional'
        elif suffix == 'dwi':
            return 'diffusion'
        else:
            return 'other'

    layout.df['modality_type'] = layout.df.apply(categorize_modality, axis=1)

    # Query by category
    anat_files = layout.get(modality_type='anatomical', return_type='filename')

    mo.md(f"""
    **Pattern**: Categorize files by imaging modality

    **Anatomical files**: {len(anat_files)}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Common Pattern 2: Track Processing Status

    Mark files as they're processed for incremental workflows.
    """)
    return


@app.cell
def _(layout, mo):
    # Initialize all as unprocessed
    layout.df['processed'] = False

    # Mark some files as processed (simulated)
    processed_paths = layout.df['path'].iloc[:5].tolist()
    layout.df.loc[layout.df['path'].isin(processed_paths), 'processed'] = True

    # Query unprocessed files
    pending = layout.get(processed=False, return_type='filename')

    mo.md(f"""
    **Pattern**: Track which files have been processed

    **Processed**: {layout.df['processed'].sum()} files

    **Pending**: {len(pending)} files

    💡 **Use case**: Resume interrupted processing pipelines
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Common Pattern 3: Add Metadata-Based Entities

    Derive entities from file metadata (RepetitionTime, EchoTime, etc.)
    """)
    return


@app.cell
def _(layout, mo):
    import bids2table as b2t

    # Add TR category for BOLD files
    def categorize_tr(row):
        if row['suffix'] != 'bold':
            return None

        # In real use, would load metadata here
        # For demo, just use placeholder
        return 'short_tr'  # Simulated: < 2s

    layout.df['tr_category'] = layout.df.apply(categorize_tr, axis=1)

    short_tr_files = layout.get(tr_category='short_tr', return_type='filename')

    mo.md(f"""
    **Pattern**: Categorize by acquisition parameters

    **Short TR files**: {len(short_tr_files)}

    💡 **Use case**: Filter files by imaging parameters without reading full files
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Common Pattern 4: External Data Integration

    Merge custom metadata from external sources.
    """)
    return


@app.cell
def _(layout, mo):
    import pandas as pd

    # Simulate external QC data
    qc_data = pd.DataFrame({
        'sub': ['01', '02', '03'],
        'visual_qc': ['pass', 'pass', 'fail'],
        'snr_grade': ['good', 'excellent', 'poor']
    })

    # Merge with layout
    layout.df = layout.df.merge(qc_data, on='sub', how='left')

    # For demo, just show the concept
    mo.md("""
    **Pattern**: Integrate external metadata

    **Merge**: `layout.df = layout.df.merge(qc_data, on='sub', how='left')`

    **Query**: `layout.get(visual_qc='pass', snr_grade='excellent')`

    💡 **Use case**: QC results, demographic data, processing metadata

    **Merged data**:
    """)
    return


@app.cell
def _(layout):
    layout.df[['sub', 'datatype', 'suffix', 'path', 'visual_qc', 'snr_grade']].groupby('sub').first().head(5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Common Pattern 5: Rename/Recode Entities

    Simplify entity values for easier querying.
    """)
    return


@app.cell
def _(layout, mo):
    # Recode task names to abbreviations
    task_mapping = {
        'balloonanalogrisktask': 'BART',
        'restingstate': 'rest',
        'nback': 'nback'
    }

    # Apply mapping
    original_tasks = layout.df['task'].unique()
    layout.df['task'] = layout.df['task'].replace(task_mapping)
    new_tasks = layout.df['task'].dropna().unique()

    # Query with new short names
    bart_files = layout.get(task='BART', return_type='filename')

    mo.md(f"""
    **Pattern**: Rename entities for convenience

    **Original**: `{original_tasks.tolist()}`

    **Renamed**: `{new_tasks.tolist()}`

    **Query**: `task='BART'` → {len(bart_files)} files

    💡 **Use case**: Shorter names, standardize across datasets
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## How templateflow Uses Custom Entities

    templateflow defines custom entities in a BIDS schema config:

    ```json
    {
      "entities": [
        {"name": "template", "pattern": "[/\]tpl-([a-zA-Z0-9]+)"},
        {"name": "cohort", "pattern": "[_/\]cohort-(\d+)"},
        {"name": "resolution", "pattern": "[_/\]+res-0*(\d+)"}
      ]
    }
    ```

    Then b2t indexes these as columns automatically, and you can query:

    ```python
    from templateflow import api as tflow

    # Query with custom entities
    mni_files = tflow.get(template='MNI152NLin2009cAsym', resolution=1)
    infant_files = tflow.get(cohort=1)  # cohort = age group
    ```

    **You can do the same** by adding columns programmatically:

    ```python
    layout.df['template'] = ...
    layout.df['cohort'] = ...
    files = layout.get(template='MNI152', cohort=1)
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Comparison: PyBIDS vs bids2table_compat

    | Feature | PyBIDS | bids2table_compat |
    |---------|--------|-------------------|
    | Add custom entities | Config file required | Direct DataFrame access |
    | When to add | Before indexing | Anytime |
    | Flexibility | Schema patterns only | Any pandas operation |
    | Query syntax | `.get()` | Same `.get()` |
    | Complexity | Config files + regex | Simple Python code |

    **Bottom line**: Custom entities are simpler and more flexible in bids2table_compat!
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
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
    layout.custom_entities = {
        'qc_visual_rating': 'Manual QC rating (pass/fail/review)',
        'processing_batch_id': 'Batch ID from processing pipeline',
    }
    ```

    ### 3. Preserve Entity Types

    ```python
    layout.df['age'] = layout.df['age'].astype(int)
    layout.df['qc_grade'] = layout.df['qc_grade'].astype('category')
    ```

    ### 4. Handle Missing Values

    ```python
    # Be explicit
    layout.df['status'].fillna('pending', inplace=True)

    # Or filter in queries
    completed = layout.get(status='complete')  # Won't match NaN
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Summary

    ✅ **Three ways to add custom entities**:
    1. Direct DataFrame: `layout.df['entity'] = values`
    2. Helper method: `layout.add_custom_entity('entity', values)`
    3. From function: `layout.add_custom_entity('entity', compute_fn)`

    ✅ **Query like standard entities**:
    - `layout.get(custom_entity='value')`
    - Combine with standard entities
    - Use with any return_type

    ✅ **Common patterns demonstrated**:
    - File categorization
    - Processing status tracking
    - Metadata-based entities
    - External data integration
    - Entity renaming

    ✅ **templateflow pattern works seamlessly**:
    - Add custom entities as DataFrame columns
    - Query naturally with `.get()`
    - More flexible than PyBIDS config files

    ---

    💡 **No special implementation needed** - custom entities work out of the box!

    📚 **See also**: `CUSTOM_ENTITIES_SUMMARY.md` for the templateflow use case
    """)
    return


if __name__ == "__main__":
    app.run()
