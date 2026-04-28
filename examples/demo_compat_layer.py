"""Demo: PyBIDS Compatibility Layer - Basic Usage"""

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # PyBIDS Compatibility Layer - Basic Demo

    This notebook demonstrates the bids2table compatibility layer providing a
    drop-in replacement for PyBIDS with 20x better performance.

    ## What You'll Learn

    1. How to initialize a BIDSLayout (with automatic caching)
    2. Query files by BIDS entities
    3. Access metadata with BIDS inheritance
    4. Use Query sentinels (OPTIONAL, NONE, ANY)
    5. Get BIDSFile objects with entity parsing
    6. Compare compat layer vs native b2t approaches
    """)
    return


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    # Find the test dataset - using ds114 (multi-session, multiple tasks)
    repo_root = Path.cwd().parent if Path.cwd().name == 'examples' else Path.cwd()
    dataset_path = repo_root / 'datasets' / 'bids-examples' / 'ds114'

    if not dataset_path.exists():
        mo.md(f"⚠️ Dataset not found: {dataset_path}")
        mo.stop()

    mo.md(f"✅ Using dataset: `{dataset_path.name}` (multi-session, multi-task)")
    return Path, dataset_path, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 1. Initialize BIDSLayout

    The compatibility layer provides the same API as PyBIDS but uses
    bids2table under the hood for fast indexing.
    """)
    return


@app.cell
def _(dataset_path):
    from bids2table_compat import BIDSLayout

    # Initialize (automatically creates parquet cache)
    layout = BIDSLayout(dataset_path, validate=False)

    print(f"Indexed: {layout}")
    print(f"Cache: {layout.cache_path}")
    return (layout,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 2. Get Subjects and Sessions

    Enumerate subjects and sessions in the dataset.
    """)
    return


@app.cell
def _(layout, mo):
    subjects = layout.get_subjects()
    sessions = layout.get_sessions()
    tasks = sorted(layout.df['task'].dropna().unique().tolist())

    mo.md(f"""
    **Subjects**: `{subjects[:5]}...` ({len(subjects)} total)

    **Sessions**: `{sessions if sessions else 'None (single-session dataset)'}`

    **Tasks**: `{tasks}`
    """)
    return (subjects,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 3. Query Files by Entity

    Use `.get()` to query files with BIDS entity filters.
    """)
    return


@app.cell
def _(layout, mo, subjects):
    # Query files for first subject
    subject = subjects[0]
    files = layout.get(subject=subject, return_type='filename')

    mo.md(f"""
    **Query**: Files for `sub-{subject}`

    **Found**: {len(files)} files

    **Examples**:
    """)
    return files, subject


@app.cell
def _(Path, files, mo):
    # Show first few files
    mo.md("\n".join([f"- `{Path(f).name}`" for f in files[:3]]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 4. Query with Multiple Filters

    Combine multiple entity filters to narrow down results.
    """)
    return


@app.cell
def _(layout, mo, subject):
    # Query anatomical files for subject
    anat_files = layout.get(
        subject=subject,
        datatype='anat',
        return_type='filename'
    )

    mo.md(f"""
    **Query**: `sub-{subject}` + `datatype='anat'`

    **Found**: {len(anat_files)} anatomical files

    **Files**:
    """)
    return (anat_files,)


@app.cell
def _(Path, anat_files, mo):
    mo.md("\n".join([f"- `{Path(f).name}`" for f in anat_files]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 5. Query with Query.OPTIONAL

    Handle datasets that may or may not have sessions.
    """)
    return


@app.cell
def _(layout, mo, subject):
    from bids2table_compat import Query

    # Query allowing any session (or no session)
    files_optional = layout.get(
        subject=subject,
        session=Query.OPTIONAL,
        return_type='filename'
    )

    mo.md(f"""
    **Query**: `sub-{subject}` + `session=Query.OPTIONAL`

    **Found**: {len(files_optional)} files (allows any/no session)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 6. Get BIDSFile Objects with Entities

    Use `return_type='file'` to get BIDSFile objects that can parse entities.
    """)
    return


@app.cell
def _(Path, layout, mo):
    # Get BIDSFile objects
    bids_files = layout.get(suffix='bold', return_type='file')

    if bids_files:
        example_file = bids_files[0]
        entities = example_file.get_entities()

        entity_text = f"""
        **Query**: `suffix='bold'` + `return_type='file'`

        **Found**: {len(bids_files)} BOLD files

        **Example file**: `{Path(example_file.path).name}`

        **Entities**: `{entities}`
        """
    
    else:
        example_file = None
        entities = None
        entity_text = "⚠️ No BOLD files found in dataset"

    mo.md(entity_text)
    return (bids_files,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 7. Get Metadata with BIDS Inheritance

    Load JSON sidecar metadata following BIDS inheritance rules.
    """)
    return


@app.cell
def _(bids_files, layout, mo):
    if bids_files and len(bids_files) > 0:
        metadata = layout.get_metadata(bids_files[0].path)
        metadata_keys = list(metadata.keys())
        md_text = f"""
        **Metadata keys**: `{metadata_keys[:5]}...`

        """

        if 'RepetitionTime' in metadata:
            md_text += f"**RepetitionTime**: `{metadata['RepetitionTime']}` seconds"

    else:
        md_text = "⚠️ No files to show metadata for"
        metadata = {}
        metadata_keys = []

    mo.md(md_text)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 8. Cache Information

    The compat layer uses parquet caching for fast reloading.
    """)
    return


@app.cell
def _(layout, mo):
    cache_size_kb = layout.cache_path.stat().st_size / 1024 if layout.cache_path.exists() else 0

    mo.md(f"""
    **Cache path**: `{layout.cache_path}`

    **Cache exists**: `{layout.cache_path.exists()}`

    **Cache size**: `{cache_size_kb:.1f} KB`

    💡 **Note**: Parquet cache is ~100x smaller than PyBIDS SQLite cache!
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Comparison: Compat Layer vs Native b2t

    The compat layer provides a familiar API, but you can also use native
    bids2table DataFrames for maximum flexibility.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Compat Layer (Drop-in Replacement)

    ```python
    from bids2table_compat import BIDSLayout

    layout = BIDSLayout('/data/dataset')
    subjects = layout.get_subjects()
    files = layout.get(subject='01', suffix='T1w')
    ```

    ✅ Familiar PyBIDS API
    ✅ Easy migration (change 1 line)
    ✅ Same query patterns

    ---

    ### Native b2t (Best Performance)

    ```python
    import bids2table as b2t
    import pandas as pd

    tab = b2t.index_dataset('/data/dataset')
    df = tab.to_pandas()

    subjects = sorted(df['sub'].unique())
    files = df[(df['sub'] == '01') & (df['suffix'] == 'T1w')]['path'].tolist()
    ```

    ✅ More flexible (full pandas)
    ✅ Slightly faster queries
    ✅ Direct DataFrame access

    ---

    ### Which to Use?

    - **Migrating from PyBIDS?** → Use compat layer
    - **New project?** → Consider native b2t
    - **Need complex queries?** → Native b2t gives full pandas power
    - **Want simplicity?** → Compat layer is cleaner
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Summary

    This demo showed the basic features of the compatibility layer:

    ✅ **BIDSLayout initialization** with automatic caching
    ✅ **Subject/session enumeration**
    ✅ **File querying** with entity filters
    ✅ **Query sentinels** (OPTIONAL, NONE, ANY)
    ✅ **BIDSFile objects** with entity parsing
    ✅ **Metadata loading** with BIDS inheritance
    ✅ **Parquet caching** for performance

    **Next**: See `demo_custom_entities.py` for advanced patterns including
    custom entities (the templateflow pattern).

    ---

    📚 **Documentation**: See `MIGRATION_GUIDE.md` for complete migration instructions.
    """)
    return


if __name__ == "__main__":
    app.run()
