#!/usr/bin/env python
"""
Demo: Adding custom entities to BIDSLayout (like templateflow does).

This shows how to add custom columns to the layout DataFrame and then
query them just like standard BIDS entities.
"""

from pathlib import Path
from bids2table_compat import BIDSLayout

def main():
    # Find a test dataset
    repo_root = Path(__file__).parent.parent
    dataset_path = repo_root / 'datasets' / 'bids-examples' / 'ds001'

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        return

    print("="* 70)
    print("Demo: Adding Custom Entities to BIDSLayout")
    print("="* 70)
    print()

    # Initialize layout
    print("1. Create standard BIDSLayout:")
    layout = BIDSLayout(dataset_path, validate=False)
    print(f"   Initial columns: {list(layout.df.columns)[:10]}...")
    print(f"   Files: {len(layout.df)}")
    print()

    # Add custom entity as a column
    print("2. Add custom entity 'my_custom_label':")
    print("   (Simulating what templateflow does with 'template', 'cohort', etc.)")
    print()

    # Example: Add a custom label based on some logic
    # In templateflow, this might be parsed from filenames or set programmatically
    layout.df['my_custom_label'] = layout.df['suffix'].apply(
        lambda x: 'anatomical' if x in ['T1w', 'T2w', 'inplaneT2']
        else 'functional' if x == 'bold'
        else 'other'
    )

    print(f"   Added column: 'my_custom_label'")
    print(f"   Unique values: {layout.df['my_custom_label'].unique().tolist()}")
    print()

    # Query with the custom entity
    print("3. Query using the custom entity:")
    anatomical_files = layout.get(my_custom_label='anatomical', return_type='filename')
    print(f"   Files with my_custom_label='anatomical': {len(anatomical_files)}")
    if anatomical_files:
        print(f"   Example: {Path(anatomical_files[0]).name}")
    print()

    functional_files = layout.get(my_custom_label='functional', return_type='filename')
    print(f"   Files with my_custom_label='functional': {len(functional_files)}")
    if functional_files:
        print(f"   Example: {Path(functional_files[0]).name}")
    print()

    # Combine standard and custom entities
    print("4. Query with both standard and custom entities:")
    sub01_anat = layout.get(
        subject='01',
        my_custom_label='anatomical',
        return_type='filename'
    )
    print(f"   sub-01 anatomical files: {len(sub01_anat)}")
    for f in sub01_anat:
        print(f"     - {Path(f).name}")
    print()

    # More complex example: Add entity from file content/metadata
    print("5. Add entity based on file metadata:")
    # Simulate: check RepetitionTime and add 'tr_category'
    def categorize_tr(row):
        if row['suffix'] != 'bold':
            return None
        # In real case, would load metadata here
        # For demo, just use a placeholder
        return 'short_tr'  # < 2s

    layout.df['tr_category'] = layout.df.apply(categorize_tr, axis=1)

    short_tr_files = layout.get(tr_category='short_tr', return_type='filename')
    print(f"   Files with tr_category='short_tr': {len(short_tr_files)}")
    print()

    # Show how to add entities from a mapping/dictionary
    print("6. Add entity from external mapping (like a processing manifest):")
    # Simulate external metadata about files
    processing_status = {
        'sub-01': 'complete',
        'sub-02': 'complete',
        'sub-03': 'failed',
    }

    layout.df['processing_status'] = layout.df['sub'].map(processing_status)

    completed_subjects = layout.get_subjects(processing_status='complete')
    print(f"   Subjects with processing_status='complete': {completed_subjects}")
    print()

    # Advanced: Modify entity values
    print("7. Modify entity values (e.g., rename task names):")
    print(f"   Original tasks: {layout.df['task'].unique()}")

    # Create a mapping for task names
    task_mapping = {'balloonanalogrisktask': 'BART'}
    layout.df['task'] = layout.df['task'].replace(task_mapping)

    print(f"   Renamed tasks: {layout.df['task'].dropna().unique()}")
    bart_files = layout.get(task='BART', return_type='filename')
    print(f"   Files with task='BART': {len(bart_files)}")
    print()

    print("="* 70)
    print("Summary: Working with Custom Entities")
    print("="* 70)
    print()
    print("✅ You can add custom columns directly to layout.df")
    print("✅ Query them with layout.get() just like standard entities")
    print("✅ Combine custom and standard entities in queries")
    print("✅ No special methods needed - it's just pandas DataFrame operations!")
    print()
    print("Templateflow pattern:")
    print("  1. Define custom entities in config.json (for parsing)")
    print("  2. b2t indexes and includes them as columns")
    print("  3. Or add columns programmatically: layout.df['entity'] = values")
    print("  4. Query as usual: layout.get(entity='value')")
    print()
    print("="* 70)


if __name__ == '__main__':
    main()
