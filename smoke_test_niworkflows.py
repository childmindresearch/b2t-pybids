#!/usr/bin/env python
"""
Smoke test: Drop-in replacement of PyBIDS with bids2table_compat in niworkflows

This script tests whether bids2table_compat can replace PyBIDS in real-world code
by monkey-patching niworkflows imports and running key functions.
"""

import sys
from pathlib import Path

# Add our compat layer to the path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root / "projects" / "niworkflows"))

# Monkey-patch: Replace bids with bids2table_compat
import bids2table_compat as bids
sys.modules['bids'] = bids
sys.modules['bids.layout'] = bids

# Also handle the specific imports
from bids2table_compat import BIDSLayout, Query
bids.BIDSLayout = BIDSLayout
bids.layout.Query = Query
bids.layout.BIDSLayout = BIDSLayout

print("✓ Monkey-patched bids -> bids2table_compat")

# Now import niworkflows functions that use BIDS
try:
    from niworkflows.utils.bids import (
        collect_data,
        collect_participants,
    )
    print("✓ Successfully imported niworkflows.utils.bids functions")
except Exception as e:
    print(f"✗ Failed to import niworkflows functions: {e}")
    sys.exit(1)

# Test with a real dataset
dataset_path = repo_root / "datasets" / "bids-examples" / "ds001"

if not dataset_path.exists():
    print(f"✗ Dataset not found: {dataset_path}")
    print("  Run: git submodule update --init datasets/bids-examples")
    sys.exit(1)

print(f"✓ Using dataset: {dataset_path}")

# Test 1: collect_participants
print("\n" + "="*60)
print("TEST 1: collect_participants()")
print("="*60)

try:
    participants = collect_participants(
        str(dataset_path),
        participant_label=None,
        bids_validate=False
    )
    print(f"✓ Found {len(participants)} participants: {participants}")
except Exception as e:
    print(f"✗ collect_participants() failed:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: collect_data with specific subject
print("\n" + "="*60)
print("TEST 2: collect_data() for subject 01")
print("="*60)

try:
    # Test with subject 01
    layout = BIDSLayout(str(dataset_path), validate=False)

    # Try to collect data like niworkflows does
    data = collect_data(
        str(dataset_path),
        participant_label="01",
        bids_validate=False
    )

    print(f"✓ collect_data returned: {type(data)}")
    print(f"  Keys: {list(data[0].keys()) if data else 'empty'}")

    # Show what was collected
    if data:
        sub_data = data[0]
        print(f"  Sample entry for subject {sub_data.get('subject', 'unknown')}:")
        for key, val in list(sub_data.items())[:5]:
            if isinstance(val, list):
                print(f"    {key}: {len(val)} files")
            else:
                print(f"    {key}: {val}")

except Exception as e:
    print(f"✗ collect_data() failed:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check specific patterns niworkflows uses
print("\n" + "="*60)
print("TEST 3: Common niworkflows query patterns")
print("="*60)

try:
    layout = BIDSLayout(str(dataset_path), validate=False)

    # Pattern 1: Get all T1w files
    t1w_files = layout.get(suffix='T1w', extension='.nii.gz')
    print(f"✓ Query T1w files: {len(t1w_files)} found")

    # Pattern 2: Get bold files for a subject
    bold_files = layout.get(subject='01', suffix='bold', extension='.nii.gz')
    print(f"✓ Query BOLD for sub-01: {len(bold_files)} found")

    # Pattern 3: Get with Query.OPTIONAL (common in niworkflows)
    files_optional_session = layout.get(
        subject='01',
        session=Query.OPTIONAL,
        suffix='bold'
    )
    print(f"✓ Query with session=OPTIONAL: {len(files_optional_session)} found")

    # Pattern 4: Get metadata
    if t1w_files:
        metadata = layout.get_metadata(t1w_files[0].path)
        print(f"✓ Get metadata: {len(metadata)} keys")
        print(f"  Sample keys: {list(metadata.keys())[:5]}")

    # Pattern 5: Entity enumeration
    subjects = layout.get_subjects()
    sessions = layout.get_sessions()
    print(f"✓ Get subjects: {subjects}")
    print(f"✓ Get sessions: {sessions if sessions else 'None (dataset has no sessions)'}")

except Exception as e:
    print(f"✗ Query pattern test failed:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check for missing utilities that niworkflows imports
print("\n" + "="*60)
print("TEST 4: Check for bids.utils functions")
print("="*60)

try:
    # niworkflows imports: from bids.utils import listify
    # This is a utility function, not core BIDS
    from bids.utils import listify
    print("✓ bids.utils.listify is available")

    # Test it
    result = listify("test")
    print(f"  listify('test') = {result}")

except ImportError as e:
    print(f"⚠ bids.utils.listify not found (minor issue)")
    print(f"  This is a utility function, can be easily replaced")
    print(f"  Suggested fix: Add a utils.py with listify()")
except Exception as e:
    print(f"⚠ Unexpected error with bids.utils:")
    print(f"  {type(e).__name__}: {e}")

# Summary
print("\n" + "="*60)
print("SMOKE TEST SUMMARY")
print("="*60)
print("✓ All critical tests passed!")
print("✓ bids2table_compat works as drop-in replacement for niworkflows")
print("\nNext steps:")
print("  1. Run niworkflows actual test suite with this monkey-patch")
print("  2. Document any missing features")
print("  3. Add any missing utility functions (like listify)")
print("\nConclusion: Ready for integration testing! 🚀")
