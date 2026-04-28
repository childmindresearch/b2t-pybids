#!/usr/bin/env python
"""
Demo script showing the bids2table compatibility layer in action.

This demonstrates how the compat layer provides a drop-in replacement
for PyBIDS while using bids2table's fast indexing underneath.
"""

from pathlib import Path
from bids2table_compat import BIDSLayout, Query

def main():
    # Find a test dataset
    repo_root = Path(__file__).parent.parent
    dataset_path = repo_root / 'datasets' / 'bids-examples' / 'ds001'

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        print("Please ensure bids-examples submodule is initialized")
        return

    print("="* 60)
    print("PyBIDS Compatibility Layer Demo")
    print("="* 60)
    print()

    # Initialize layout (with caching)
    print(f"Indexing dataset: {dataset_path}")
    layout = BIDSLayout(dataset_path, validate=False)
    print(f"✓ Indexed: {layout}")
    print()

    # Get subjects
    print("1. Get all subjects:")
    subjects = layout.get_subjects()
    print(f"   Subjects: {subjects[:5]}..." if len(subjects) > 5 else f"   Subjects: {subjects}")
    print()

    # Get sessions
    print("2. Get all sessions:")
    sessions = layout.get_sessions()
    if sessions:
        print(f"   Sessions: {sessions}")
    else:
        print("   No sessions (single-session dataset)")
    print()

    # Query files
    print("3. Query files by entity:")
    if subjects:
        subject = subjects[0]
        files = layout.get(subject=subject, return_type='filename')
        print(f"   Files for sub-{subject}: {len(files)} files")
        if files:
            print(f"   Example: {Path(files[0]).name}")
    print()

    # Query with multiple filters
    print("4. Query with multiple filters:")
    anat_files = layout.get(
        subject=subjects[0] if subjects else None,
        datatype='anat',
        return_type='filename'
    )
    print(f"   Anatomical files: {len(anat_files)}")
    if anat_files:
        print(f"   Example: {Path(anat_files[0]).name}")
    print()

    # Query with special values
    print("5. Query with Query.OPTIONAL:")
    files_optional_session = layout.get(
        subject=subjects[0] if subjects else None,
        session=Query.OPTIONAL,
        return_type='filename'
    )
    print(f"   Files (any/no session): {len(files_optional_session)}")
    print()

    # Get BIDSFile objects with entities
    print("6. Get BIDSFile objects with entities:")
    bids_files = layout.get(suffix='bold', return_type='file')
    if bids_files:
        example_file = bids_files[0]
        entities = example_file.get_entities()
        print(f"   Example file: {Path(example_file.path).name}")
        print(f"   Entities: {entities}")
    else:
        print("   No BOLD files found")
    print()

    # Get metadata
    print("7. Get metadata:")
    if bids_files:
        metadata = layout.get_metadata(bids_files[0].path)
        print(f"   Metadata keys: {list(metadata.keys())[:5]}...")
        if 'RepetitionTime' in metadata:
            print(f"   RepetitionTime: {metadata['RepetitionTime']}")
    print()

    # Show cache location
    print("8. Cache info:")
    print(f"   Cache path: {layout.cache_path}")
    print(f"   Cache exists: {layout.cache_path.exists()}")
    if layout.cache_path.exists():
        cache_size = layout.cache_path.stat().st_size / 1024
        print(f"   Cache size: {cache_size:.1f} KB")
    print()

    print("="* 60)
    print("Demo complete!")
    print()
    print("Compare this to native b2t approach:")
    print()
    print("  import bids2table as b2t")
    print("  tab = b2t.index_dataset(dataset_path)")
    print("  df = tab.to_pandas()")
    print("  subjects = sorted(df['sub'].unique())")
    print("  files = df[df['sub'] == '01']['path'].tolist()")
    print()
    print("Both approaches work - compat layer for easy migration,")
    print("native DataFrames for maximum flexibility!")
    print("="* 60)


if __name__ == '__main__':
    main()
