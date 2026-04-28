"""Migration Guide: PyBIDS → bids2table (4 Approaches)"""

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # PyBIDS → bids2table Migration Guide

    ## Four Ways to Work with BIDS Data

    This notebook demonstrates **the same operations** in four different approaches:

    1. **PyBIDS** - What you know and love (but slow)
    2. **bids2table_compat** - Drop-in replacement (20x faster, same API)
    3. **bids2table + pandas** - Native DataFrame approach (fastest, Pythonic)
    4. **bids2table + polars** - Native with Polars (fastest + lowest memory)

    Choose your migration path based on your priorities:
    - **Minimal changes?** → Use `bids2table_compat`
    - **Best performance?** → Use `polars`
    - **Most familiar?** → Use `pandas`
    - **Not ready to migrate?** → Keep using PyBIDS (but it's slower)

    ---
    """)
    return


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import warnings
    warnings.filterwarnings('ignore')

    # Find test dataset
    repo_root = Path.cwd().parent if Path.cwd().name == 'examples' else Path.cwd()
    dataset_path = repo_root / 'datasets' / 'bids-examples' / 'ds114'

    if not dataset_path.exists():
        raise RuntimeError(f"⚠️ Dataset not found: {dataset_path}")

    mo.md(f"✅ Using dataset: `{dataset_path.name}` (128 files, 16 subjects)")
    return dataset_path, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 1. Initialization & Indexing

    How to load and index a BIDS dataset.
    """)
    return


@app.cell
def _(dataset_path, mo):
    import time
    from bids import BIDSLayout as PyBIDSLayout

    mo.md("### Approach 1: PyBIDS (Traditional)")

    # PyBIDS - slow but familiar
    _start = time.time()
    pybids_layout = PyBIDSLayout(str(dataset_path), validate=False)
    pybids_time = time.time() - _start
    mo.md(f"""
    ```python
    from bids import BIDSLayout
    layout = BIDSLayout('/path/to/dataset', validate=False)
    ```
    ⏱️ **Indexing time**: {pybids_time:.3f}s
    """)
    return pybids_layout, pybids_time, time


@app.cell
def _(dataset_path, mo, time):
    mo.md("### Approach 2: bids2table_compat (Drop-in Replacement)")

    # bids2table_compat - fast, same API
    _start = time.time()
    from bids2table_compat import BIDSLayout as CompatLayout
    compat_layout = CompatLayout(str(dataset_path), validate=False)
    compat_time = time.time() - _start

    mo.md(f"""
    ```python
    from bids2table_compat import BIDSLayout  # Just change the import!
    layout = BIDSLayout('/path/to/dataset', validate=False)
    ```
    ⏱️ **Indexing time**: {compat_time:.3f}s
    """)
    return compat_layout, compat_time


@app.cell
def _(dataset_path, mo, time):
    import bids2table as b2t
    import pandas as pd

    mo.md("### Approach 3: bids2table + pandas (Native)")

    # bids2table + pandas - fast, DataFrame native
    _start = time.time()
    pandas_tab = b2t.index_dataset(str(dataset_path))
    pandas_df = pandas_tab.to_pandas(types_mapper=pd.ArrowDtype)
    pandas_time = time.time() - _start

    mo.md(f"""
    ```python
    import bids2table as b2t
    import pandas as pd

    tab = b2t.index_dataset('/path/to/dataset')
    df = tab.to_pandas(types_mapper=pd.ArrowDtype)
    ```
    ⏱️ **Indexing time**: {pandas_time:.3f}s
    """)
    return b2t, pandas_df, pandas_time


@app.cell
def _(b2t, dataset_path, mo, time):
    import polars as pl

    mo.md("### Approach 4: bids2table + polars (Native + Fast)")

    # bids2table + polars - fastest, lowest memory
    _start = time.time()
    polars_tab = b2t.index_dataset(str(dataset_path))
    polars_df = pl.from_arrow(polars_tab)
    polars_time = time.time() - _start

    mo.md(f"""
    ```python
    import bids2table as b2t
    import polars as pl

    tab = b2t.index_dataset('/path/to/dataset')
    ```
    ⏱️ **Indexing time**: {polars_time:.3f}s
    """)
    return pl, polars_df, polars_time


@app.cell
def _(compat_time, mo, pandas_time, polars_time, pybids_time):
    mo.md("### Performance Comparison")

    if pybids_time:
        speedup_compat = pybids_time / compat_time
        speedup_pandas = pybids_time / pandas_time
        speedup_polars = pybids_time / polars_time

        bmark = f"""
        | Approach | Time | Speedup vs PyBIDS |
        |----------|------|-------------------|
        | PyBIDS | {pybids_time:.3f}s | 1x (baseline) |
        | bids2table_compat | {compat_time:.3f}s | **{speedup_compat:.1f}x faster** ⚡ |
        | bids2table + pandas | {pandas_time:.3f}s | **{speedup_pandas:.1f}x faster** ⚡ |
        | bids2table + polars | {polars_time:.3f}s | **{speedup_polars:.1f}x faster** ⚡ |
        """
    else:
        bmark = f"""
        | Approach | Time |
        |----------|------|
        | bids2table_compat | {compat_time:.3f}s |
        | bids2table + pandas | {pandas_time:.3f}s |
        | bids2table + polars | {polars_time:.3f}s |

        *PyBIDS not installed for comparison*
        """
    mo.md(bmark)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 2. Basic Query: Get T1w Files

    Most common operation: find files by entity values.
    """)
    return


@app.cell
def _(mo, pybids_layout):
    mo.md("### Approach 1: PyBIDS")

    pybids_t1w = pybids_layout.get(suffix='T1w', extension='.nii.gz', return_type='filename')
    mo.md(f"""
    ```python
    files = layout.get(suffix='T1w', extension='.nii.gz', return_type='filename')
    ```
    **Found**: {len(pybids_t1w)} files
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("### Approach 2: bids2table_compat")

    compat_t1w = compat_layout.get(suffix='T1w', extension='.nii.gz', return_type='filename')

    mo.md(f"""
    ```python
    files = layout.get(suffix='T1w', extension='.nii.gz', return_type='filename')
    ```
    **Found**: {len(compat_t1w)} files

    ✅ **Same API as PyBIDS!** No code changes needed.
    """)
    return (compat_t1w,)


@app.cell
def _(mo, pandas_df):
    mo.md("### Approach 3: bids2table + pandas")

    pandas_t1w = pandas_df[
        (pandas_df['suffix'] == 'T1w') &
        (pandas_df['ext'] == '.nii.gz')
    ]['path'].tolist()

    mo.md(f"""
    ```python
    files = df[
        (df['suffix'] == 'T1w') &
        (df['ext'] == '.nii.gz')
    ]['path'].tolist()
    ```
    **Found**: {len(pandas_t1w)} files

    💡 **Native pandas** - familiar boolean indexing
    """)
    return


@app.cell
def _(mo, pl, polars_df):
    mo.md("### Approach 4: bids2table + polars")

    polars_t1w = polars_df.filter(
        (pl.col('suffix') == 'T1w') &
        (pl.col('ext') == '.nii.gz')
    )['path'].to_list()

    mo.md(f"""
    ```python
    files = df.filter(
        (pl.col('suffix') == 'T1w') &
        (pl.col('ext') == '.nii.gz')
    )['path'].to_list()
    ```
    **Found**: {len(polars_t1w)} files

    💡 **Native polars** - lazy evaluation, fastest queries
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 3. Query with Multiple Entities

    Find BOLD files for a specific subject and task.
    """)
    return


@app.cell
def _(mo, pybids_layout):
    mo.md("### Approach 1: PyBIDS")

    pybids_bold = pybids_layout.get(
        subject='01',
        task='linebisection',
        suffix='bold',
        return_type='filename'
    )
    mo.md(f"""
    ```python
    files = layout.get(
        subject='01',
        task='linebisection',
        suffix='bold',
        return_type='filename'
    )
    ```
    **Found**: {len(pybids_bold)} files
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("### Approach 2: bids2table_compat")

    compat_bold = compat_layout.get(
        subject='01',
        task='linebisection',
        suffix='bold',
        return_type='filename'
    )

    mo.md(f"""
    ```python
    files = layout.get(
        subject='01',
        task='linebisection',
        suffix='bold',
        return_type='filename'
    )
    ```
    **Found**: {len(compat_bold)} files

    ✅ **Exact same syntax**
    """)
    return


@app.cell
def _(mo, pandas_df):
    mo.md("### Approach 3: bids2table + pandas")

    pandas_bold = pandas_df[
        (pandas_df['sub'] == '01') &
        (pandas_df['task'] == 'linebisection') &
        (pandas_df['suffix'] == 'bold')
    ]['path'].tolist()

    mo.md(f"""
    ```python
    files = df[
        (df['sub'] == '01') &
        (df['task'] == 'linebisection') &
        (df['suffix'] == 'bold')
    ]['path'].tolist()
    ```
    **Found**: {len(pandas_bold)} files

    💡 Chain conditions with `&`
    """)
    return


@app.cell
def _(mo, pl, polars_df):
    mo.md("### Approach 4: bids2table + polars")

    polars_bold = polars_df.filter(
        (pl.col('sub') == '01') &
        (pl.col('task') == 'linebisection') &
        (pl.col('suffix') == 'bold')
    )['path'].to_list()

    mo.md(f"""
    ```python
    files = df.filter(
        (pl.col('sub') == '01') &
        (pl.col('task') == 'linebisection') &
        (pl.col('suffix') == 'bold')
    )['path'].to_list()
    ```
    **Found**: {len(polars_bold)} files

    💡 Use `.filter()` instead of boolean indexing
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 4. Entity Enumeration

    Get unique values for entities (subjects, sessions, tasks, etc.)
    """)
    return


@app.cell
def _(mo, pybids_layout):
    mo.md("### Approach 1: PyBIDS")

    pybids_subjects = pybids_layout.get_subjects()
    pybids_tasks = pybids_layout.get_tasks()
    mo.md(f"""
    ```python
    subjects = layout.get_subjects()
    tasks = layout.get_tasks()
    ```
    **Subjects**: {len(pybids_subjects)} → `{pybids_subjects[:5]}...`
    **Tasks**: {pybids_tasks}
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("### Approach 2: bids2table_compat")

    compat_subjects = compat_layout.get_subjects()
    compat_tasks = compat_layout.get_entities()['task']

    mo.md(f"""
    ```python
    subjects = layout.get_subjects()
    tasks = layout.get_entities()['task']
    ```
    **Subjects**: {len(compat_subjects)} → `{compat_subjects[:5]}...`
    **Tasks**: {compat_tasks}

    ✅ **Same helper methods**
    """)
    return


@app.cell
def _(mo, pandas_df):
    mo.md("### Approach 3: bids2table + pandas")

    pandas_subjects = pandas_df['sub'].dropna().unique().tolist()
    pandas_tasks = pandas_df['task'].dropna().unique().tolist()

    mo.md(f"""
    ```python
    subjects = df['sub'].dropna().unique().tolist()
    tasks = df['task'].dropna().unique().tolist()
    ```
    **Subjects**: {len(pandas_subjects)} → `{pandas_subjects[:5]}...`
    **Tasks**: {pandas_tasks}

    💡 **Standard pandas operations** - `.unique()` on any column
    """)
    return


@app.cell
def _(mo, polars_df):
    mo.md("### Approach 4: bids2table + polars")

    polars_subjects = polars_df['sub'].drop_nulls().unique().to_list()
    polars_tasks = polars_df['task'].drop_nulls().unique().to_list()

    mo.md(f"""
    ```python
    subjects = df['sub'].drop_nulls().unique().to_list()
    tasks = df['task'].drop_nulls().unique().to_list()
    ```
    **Subjects**: {len(polars_subjects)} → `{polars_subjects[:5]}...`
    **Tasks**: {polars_tasks}

    💡 **Polars syntax** - similar to pandas but optimized
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 5. Metadata Access

    Load JSON sidecar metadata for a file (with BIDS inheritance).
    """)
    return


@app.cell
def _(compat_t1w, mo, pybids_layout):
    mo.md("### Approach 1: PyBIDS")

    pybids_meta = pybids_layout.get_metadata(compat_t1w[0])
    mo.md(f"""
    ```python
    metadata = layout.get_metadata(file_path)
    ```
    **Keys**: {list(pybids_meta.keys())[:5] if pybids_meta else 'None'}...
    """)
    return


@app.cell
def _(compat_layout, compat_t1w, mo):
    mo.md("### Approach 2: bids2table_compat")

    compat_meta = compat_layout.get_metadata(compat_t1w[0])

    mo.md(f"""
    ```python
    metadata = layout.get_metadata(file_path)
    ```
    **Keys**: {list(compat_meta.keys())[:5] if compat_meta else 'None'}...

    ✅ **Same method, handles BIDS inheritance**
    """)
    return


@app.cell
def _(b2t, compat_t1w, dataset_path, mo):
    mo.md("### Approach 3: bids2table + pandas")

    pandas_meta = b2t.load_bids_metadata(compat_t1w[0], str(dataset_path))

    mo.md(f"""
    ```python
    import bids2table as b2t
    metadata = b2t.load_bids_metadata(file_path, dataset_root)
    ```
    **Keys**: {list(pandas_meta.keys())[:5] if pandas_meta else 'None'}...

    💡 **Direct function call** - no layout needed
    """)
    return


@app.cell
def _(b2t, compat_t1w, dataset_path, mo):
    mo.md("### Approach 4: bids2table + polars")

    polars_meta = b2t.load_bids_metadata(compat_t1w[0], str(dataset_path))

    mo.md(f"""
    ```python
    import bids2table as b2t
    metadata = b2t.load_bids_metadata(file_path, dataset_root)
    ```
    **Keys**: {list(polars_meta.keys())[:5] if polars_meta else 'None'}...

    💡 **Same function** - metadata loading is DataFrame-agnostic
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 6. Advanced: Query with OPTIONAL

    Find files where an entity may or may not be present.
    """)
    return


@app.cell
def _(mo, pybids_layout):
    mo.md("### Approach 1: PyBIDS")

    from bids.layout import Query as PyQuery
    pybids_optional = pybids_layout.get(
        subject='01',
        session=PyQuery.OPTIONAL,
        suffix='bold',
        return_type='filename'
    )
    mo.md(f"""
    ```python
    from bids.layout import Query
    files = layout.get(
        subject='01',
        session=Query.OPTIONAL,  # Match files with or without session
        suffix='bold',
        return_type='filename'
    )
    ```
    **Found**: {len(pybids_optional)} files
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("### Approach 2: bids2table_compat")

    from bids2table_compat import Query as CompatQuery
    compat_optional = compat_layout.get(
        subject='01',
        session=CompatQuery.OPTIONAL,
        suffix='bold',
        return_type='filename'
    )

    mo.md(f"""
    ```python
    from bids2table_compat import Query
    files = layout.get(
        subject='01',
        session=Query.OPTIONAL,  # Match files with or without session
        suffix='bold',
        return_type='filename'
    )
    ```
    **Found**: {len(compat_optional)} files

    ✅ **Query sentinels work!**
    """)
    return


@app.cell
def _(mo, pandas_df):
    mo.md("### Approach 3: bids2table + pandas")

    # In pandas, "optional" means: match if null OR any value
    pandas_optional = pandas_df[
        (pandas_df['sub'] == '01') &
        (pandas_df['suffix'] == 'bold')
        # No session filter = all sessions (including null) match
    ]['path'].tolist()

    mo.md(f"""
    ```python
    # Don't filter on session = matches all (including null)
    files = df[
        (df['sub'] == '01') &
        (df['suffix'] == 'bold')
        # No session condition = optional!
    ]['path'].tolist()
    ```
    **Found**: {len(pandas_optional)} files

    💡 **Just omit the filter** - simpler than Query.OPTIONAL!
    """)
    return


@app.cell
def _(mo, pl, polars_df):
    mo.md("### Approach 4: bids2table + polars")

    polars_optional = polars_df.filter(
        (pl.col('sub') == '01') &
        (pl.col('suffix') == 'bold')
        # No session filter = all sessions match
    )['path'].to_list()

    mo.md(f"""
    ```python
    # Don't filter on session = matches all (including null)
    files = df.filter(
        (pl.col('sub') == '01') &
        (pl.col('suffix') == 'bold')
        # No session condition = optional!
    )['path'].to_list()
    ```
    **Found**: {len(polars_optional)} files

    💡 **Omit the filter** - natural in DataFrame queries
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 7. Custom Entities

    Add custom metadata columns for filtering (QC grades, processing status, etc.)
    """)
    return


@app.cell
def _(mo):
    mo.md("### Approach 1: PyBIDS")

    # PyBIDS doesn't have a built-in method for custom entities
    # You'd need to extend BIDSLayout or use external tracking
    mo.md("""
    ```python
    # No native support for custom entities in PyBIDS
    # Would need to track separately or extend BIDSLayout
    ```
    ⚠️ **No analog in PyBIDS** - custom entity tracking must be done separately
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("### Approach 2: bids2table_compat")

    # Add custom entity
    qc_grades = {str(i).zfill(2): 'pass' if int(i) % 2 == 1 else 'fail'
                 for i in range(1, 17)}
    compat_layout.add_custom_entity('qc_grade', qc_grades)

    compat_qc_pass = compat_layout.get(qc_grade='pass', suffix='T1w', return_type='filename')

    mo.md(f"""
    ```python
    # Add custom entity via helper
    qc_grades = {{'01': 'pass', '02': 'fail', ...}}
    layout.add_custom_entity('qc_grade', qc_grades)

    # Query with custom entity
    files = layout.get(qc_grade='pass', suffix='T1w', return_type='filename')
    ```
    **Found**: {len(compat_qc_pass)} T1w files with QC grade 'pass'

    ✅ **Helper method for custom entities**
    """)
    return (qc_grades,)


@app.cell
def _(mo, pandas_df, qc_grades):
    mo.md("### Approach 3: bids2table + pandas")

    # Add custom column directly
    pandas_df_custom = pandas_df.copy()
    pandas_df_custom['qc_grade'] = pandas_df_custom['sub'].map(qc_grades)

    pandas_qc_pass = pandas_df_custom[
        (pandas_df_custom['qc_grade'] == 'pass') &
        (pandas_df_custom['suffix'] == 'T1w')
    ]['path'].tolist()

    mo.md(f"""
    ```python
    # Add custom column with pandas
    df['qc_grade'] = df['sub'].map(qc_grades)

    # Query with custom column
    files = df[
        (df['qc_grade'] == 'pass') &
        (df['suffix'] == 'T1w')
    ]['path'].tolist()
    ```
    **Found**: {len(pandas_qc_pass)} T1w files with QC grade 'pass'

    💡 **Native pandas column operations** - very flexible!
    """)
    return


@app.cell
def _(mo, pl, polars_df, qc_grades):
    mo.md("### Approach 4: bids2table + polars")

    # Add custom column with polars
    polars_df_custom = polars_df.with_columns(
        pl.col('sub').replace(qc_grades).alias('qc_grade')
    )

    polars_qc_pass = polars_df_custom.filter(
        (pl.col('qc_grade') == 'pass') & 
        (pl.col('suffix') == 'T1w')
    )['path'].to_list()

    mo.md(f"""
    ```python
    # Add custom column with polars
    df = df.with_columns(
        pl.col('sub').replace(qc_grades).alias('qc_grade')
    )

    # Query with custom column
    files = df.filter(
        (pl.col('qc_grade') == 'pass') &
        (pl.col('suffix') == 'T1w')
    )['path'].to_list()
    ```
    **Found**: {len(polars_qc_pass)} T1w files with QC grade 'pass'

    💡 **Polars `.with_columns()`** - immutable, efficient transformations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 8. DataFrame Inspection

    What does the underlying data actually look like?
    """)
    return


@app.cell
def _(mo):
    mo.md("### Approach 1: PyBIDS")

    mo.md("""
    ```python
    # PyBIDS uses a SQLite database internally, not DataFrames
    # No direct DataFrame access available
    ```
    ⚠️ **No DataFrame analog in PyBIDS** - uses SQLite database backend instead
    """)
    return


@app.cell
def _(compat_layout, mo):
    mo.md("""
    ### Approach 2: bids2table_compat

    The compat layer wraps a pandas DataFrame:
    """)

    compat_layout.df.head(3)
    return


@app.cell
def _(mo, pandas_df):
    mo.md("""
    ### Approach 3: bids2table + pandas

    Direct access to the full DataFrame:
    """)

    pandas_df.head(3)
    return


@app.cell
def _(mo, polars_df):
    mo.md("""
    ### Approach 4: bids2table + polars

    Polars DataFrame with lazy evaluation:
    """)

    polars_df.head(3)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Summary: Which Approach Should You Use?

    ### 🎯 Decision Matrix

    | Your Priority | Recommended Approach | Why |
    |---------------|---------------------|-----|
    | **Minimal code changes** | `bids2table_compat` | Change only the import, everything else stays the same |
    | **Best performance** | `bids2table + polars` | Fastest queries, lowest memory usage, lazy evaluation |
    | **Most familiar syntax** | `bids2table + pandas` | If you already know pandas, this is natural |
    | **Large datasets (>10k files)** | `bids2table + polars` | Memory-efficient, handles big data better |
    | **Integration with existing pandas code** | `bids2table + pandas` | Fits naturally into pandas workflows |
    | **Just want it to work** | `bids2table_compat` | Drop-in replacement, no learning curve |

    ### 🚀 Migration Paths

    **Path 1: Fast (1 minute)**
    ```python
    # Change this:
    from bids.layout import BIDSLayout

    # To this:
    from bids2table_compat import BIDSLayout

    # Done! 20x faster, no other changes needed
    ```

    **Path 2: Gradual (over time)**
    1. Start with `bids2table_compat` (minimal changes)
    2. Gradually replace `.get()` calls with DataFrame operations
    3. Eventually drop the compat layer entirely

    **Path 3: All-in (1-2 hours)**
    1. Replace `BIDSLayout` with `b2t.index_dataset()`
    2. Convert `.get()` calls to DataFrame filters
    3. Use native pandas/polars throughout

    ### 📊 Performance Summary

    All three modern approaches are **~20x faster** than PyBIDS for indexing.

    For queries:
    - **bids2table_compat**: Fast (wraps pandas)
    - **pandas**: Fast (native DataFrame)
    - **polars**: Fastest (optimized, lazy evaluation)

    ### 💡 Best Practice

    Start with **`bids2table_compat`** for immediate gains, then migrate to native DataFrames when you have time.

    ---

    ## Need Help?

    - **Documentation**: See `MIGRATION_GUIDE.md` in the repo
    - **Examples**: Check other marimo notebooks in `examples/`
    - **Issues**: https://github.com/nipreps/b2t-api-expand/issues

    **Happy migrating! 🎉**
    """)
    return


if __name__ == "__main__":
    app.run()
