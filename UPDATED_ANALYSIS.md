# Updated PyBIDS Usage Analysis - With nibabies, neurosynth, templateflow

## Summary of Changes

After adding three new repositories (nibabies, neurosynth, templateflow), we discovered:

### New Repositories Analysis

| Repository | Uses PyBIDS? | Notable Findings |
|------------|--------------|------------------|
| **nibabies** | ✅ Yes | Similar to fmriprep (nipreps family), adds `parse_file_entities`, uses `Query.NONE`, `Query.ANY` |
| **neurosynth** | ❌ No | No PyBIDS usage found |
| **templateflow** | ✅ Yes | **Advanced usage**: subclasses BIDSLayout, uses `add_config_paths()`, custom entity types |

### New Methods Discovered

| Method | Count | Projects | Description | Migration Priority |
|--------|-------|----------|-------------|-------------------|
| **parse_file_entities()** | 2 | nibabies | Standalone entity parser (no layout needed) | **Migration guide** - Same as `get_entities()` |
| **BIDSLayoutIndexer** | 2 | nibabies, templateflow | Low-level indexing control | **Low** - Internal API, rarely used |
| **add_config_paths()** | 1 | templateflow | Register custom BIDS configs | **Medium** - Needed for extensions |
| **Query.NONE** | 1 | nibabies | Filter for explicitly missing entities | **Medium** - Add to Query class |
| **Query.ANY** | 2 | nibabies, templateflow | Filter allowing any value | **Medium** - Add to Query class |
| **Custom Layout subclass** | 1 | templateflow | Extend BIDSLayout with custom methods | **Low** - Advanced feature |
| **scope parameter** | 2 | nibabies | Filter by 'raw' vs 'derivatives' | **Low** - Can use DataFrame filtering |

## Updated Method Frequency Table

| Method/Function | Old Count | New Count | Change | Projects Using |
|----------------|-----------|-----------|--------|----------------|
| **BIDSLayout()** | 44 | **51** | +7 | All 7 (added nibabies, templateflow) |
| **layout.get()** | 21 | **34** | +13 | 6/8 (added nibabies, templateflow) |
| **layout.get_metadata()** | 29 | **35** | +6 | 4/8 (added nibabies) |
| **layout.get_sessions()** | 7 | **8** | +1 | 3/8 (added nibabies) |
| **layout.get_subjects()** | 6 | **7** | +1 | 5/8 (added nibabies) |
| **layout.get_file().get_entities()** | 6 | **6** | 0 | 1/8 (qsiprep only) |
| **parse_file_entities()** | 0 | **2** | NEW | 1/8 (nibabies) |
| **layout.get_fieldmap()** | 4 | **4** | 0 | 1/8 (qsiprep) |
| **layout.build_path()** | 2 | **2** | 0 | 1/8 (fitlins) |
| **layout.get_fmapids()** | 1 | **1** | 0 | 1/8 (fmriprep) |
| **BIDSLayoutIndexer()** | 0 | **2** | NEW | 2/8 (nibabies, templateflow) |
| **add_config_paths()** | 0 | **1** | NEW | 1/8 (templateflow) |
| **Query.NONE** | 0 | **1** | NEW | 1/8 (nibabies) |
| **Query.ANY** | 0 | **2** | NEW | 2/8 (nibabies, templateflow) |

## Impact on Migration Plan

### ✅ No Major Changes Required

The new repositories confirm our approach:

1. **Core methods remain dominant**: `.get()`, `.get_metadata()`, `get_subjects/sessions()` still account for most usage
2. **New methods are minor**: `parse_file_entities` is equivalent to `get_entities()`, Query enums are simple additions
3. **Advanced features are rare**: Only templateflow subclasses BIDSLayout (1/8 projects)

### 📝 Minor Additions Needed

#### 1. parse_file_entities() - Standalone Entity Parser

**Old (PyBIDS)**:
```python
from bids.layout import parse_file_entities

entities = parse_file_entities(file_path)
# Returns: {'sub': '01', 'ses': '01', 'task': 'rest', ...}
```

**Migration**:
```python
from bids2table import parse_bids_entities

entities = parse_bids_entities(file_path)
# IDENTICAL - just different import!
```

**Priority**: Migration guide only (direct 1:1 mapping)

#### 2. Query.NONE and Query.ANY - Extended Query Types

**Old (PyBIDS)**:
```python
from bids.layout import Query

# Get files explicitly WITHOUT sessions (session=null)
files = layout.get(subject='01', session=Query.NONE)

# Get files with ANY value for task (including missing)
files = layout.get(subject='01', task=Query.ANY)
```

**Compat Layer**:
```python
from bids2table.compat import Query

# Same API
files = layout.get(subject='01', session=Query.NONE)
files = layout.get(subject='01', task=Query.ANY)
```

**Native b2t**:
```python
# Query.NONE - explicit nulls
files = df[(df['sub'] == '01') & (df['ses'].isna())]['file_path'].tolist()

# Query.ANY - don't filter on task (allow any/missing)
files = df[df['sub'] == '01']['file_path'].tolist()
```

**Implementation**:
```python
# bids2table/compat/query.py
class Query:
    OPTIONAL = object()  # Already planned
    NONE = object()      # NEW - matches explicit null
    ANY = object()       # NEW - matches any value (don't filter)
```

**Priority**: Low (only 3 total uses)

#### 3. add_config_paths() - Custom BIDS Configs

**Old (PyBIDS)**:
```python
from bids.layout import add_config_paths

# Register custom BIDS entities/configs
add_config_paths(templateflow='/path/to/config.json')

# Now BIDSLayout understands custom entities
layout = BIDSLayout('/path/to/templates')
templates = layout.get_templates()  # Custom method from config
```

**Migration Strategy**: **Complex - may not need full support**

Templateflow uses this to extend BIDS with custom entity types (e.g., `template`, `cohort`, `res`) that aren't in standard BIDS. This is an advanced feature.

**Options**:
1. **Compat layer approach**: Implement in `bids2table.compat` with custom config loading
2. **Native b2t approach**: Templateflow could define custom schema in b2t format
3. **Defer**: Templateflow is unique case, handle separately if needed

**Priority**: Low (only 1 project uses it)

#### 4. BIDSLayoutIndexer - Low-level Indexing Control

**Old (PyBIDS)**:
```python
from bids.layout.index import BIDSLayoutIndexer

indexer = BIDSLayoutIndexer(validate=False, index_metadata=True)
layout = BIDSLayout('/path', indexer=indexer)
```

**Migration**: Not needed - internal implementation detail

b2t indexing is controlled via `index_dataset()` parameters. This is more of an internal PyBIDS API.

**Priority**: None (don't implement - internal API)

#### 5. scope Parameter - Filter Raw vs Derivatives

**Old (PyBIDS)**:
```python
# Get subjects from raw data only
subjects = layout.get_subjects(scope='raw')

# Get subjects from derivatives
subjects = layout.get_subjects(scope='derivatives')
```

**Native b2t**:
```python
# Add 'source' column when combining raw + derivatives
raw_df['source'] = 'raw'
deriv_df['source'] = 'derivatives'
combined_df = pd.concat([raw_df, deriv_df])

# Filter by source
raw_subjects = combined_df[combined_df['source'] == 'raw']['sub'].unique()
```

**Priority**: Low (can handle with DataFrame column)

### 🔍 Interesting Pattern: Templateflow's Custom Layout

Templateflow demonstrates an **advanced PyBIDS pattern** - subclassing BIDSLayout:

```python
class Layout(BIDSLayout):
    def __repr__(self):
        return f"TemplateFlow Layout - Templates: {self.get_templates()}"
```

**Implications for b2t compat layer**:
- Compat `BIDSLayout` must be subclassable
- Custom methods (like `get_templates()`) come from config files
- This is rare (1/8 projects) but important for extensibility

**Design decision**: Make `BIDSLayout` in compat layer easy to subclass, but don't implement full config system (too complex, too rare).

## Updated Implementation Plan Changes

### Phase 1 (Core) - No changes
- BIDSLayout, .get(), .get_metadata(), .get_subjects(), .get_sessions()
- Still the critical path

### Phase 2 (Entity Access) - Minor addition
- Add `parse_file_entities()` alias → Already exists as `parse_bids_entities()`
- Just add to compat layer imports

### Phase 3 (Query Enums) - Small addition
- Add `Query.NONE` and `Query.ANY` to Query class
- Implement filtering logic in `.get()` method
- ~20 lines of code

### Phase 4 (Advanced) - Defer
- `add_config_paths()`: Defer to separate templateflow integration (if needed)
- Custom Layout subclassing: Ensure BIDSLayout is subclassable, but don't implement config system
- `BIDSLayoutIndexer`: Don't implement (internal API)

## Validation: Does Our Approach Still Work?

### ✅ Yes - Core strategy remains sound

**Evidence**:
1. **Method distribution unchanged**: 95% of usage is still the core 5-6 methods
2. **New methods are simple**: Query enums are trivial additions, `parse_file_entities` already exists
3. **Advanced features are rare**: Only 1/8 projects does anything exotic (templateflow)
4. **Compat layer is still right approach**: New repos would benefit from drop-in replacement

### 📊 Updated Statistics (8 projects total)

| Category | Methods | Total Uses | % of Total |
|----------|---------|------------|------------|
| **Critical** (Phase 1) | BIDSLayout, .get(), .get_metadata() | 120 / 145 | **83%** |
| **High-value** (Phase 2) | .get_subjects(), .get_sessions(), .get_entities() | 21 / 145 | **14%** |
| **Specialized** (Phase 3) | Fieldmaps, build_path, Query enums | 4 / 145 | **3%** |

**Interpretation**: Focus on Phase 1-2 (97% of usage), Phase 3 is optional for niche cases.

## Updated Priority Ranking

### Phase 1: Critical (Required) - **Week 1**
1. **BIDSLayout()** - 51 uses, all projects
2. **layout.get()** - 34 uses, 75% of projects
3. **layout.get_metadata()** - 35 uses, 50% of projects (direct mapping)

### Phase 2: High-Value - **Week 1-2**
4. **layout.get_subjects()** - 7 uses
5. **layout.get_sessions()** - 8 uses
6. **layout.get_entities()** / **parse_file_entities()** - 8 uses (direct mapping)

### Phase 3: Query Enums - **Week 2** (New!)
7. **Query.OPTIONAL** - Already planned (from original analysis)
8. **Query.NONE** - 1 use (nibabies)
9. **Query.ANY** - 2 uses (nibabies, templateflow)

### Phase 4: Specialized - **Week 2-3**
10. **layout.get_fieldmap()** - 4 uses (qsiprep)
11. **layout.build_path()** - 2 uses (fitlins)
12. **layout.get_fmapids()** - 1 use (fmriprep)

### Phase 5: Advanced/Optional - **Future** (Defer)
13. **add_config_paths()** - 1 use (templateflow) - Complex, rare
14. **Custom Layout subclass** - 1 use (templateflow) - Just ensure subclassable
15. **scope parameter** - 2 uses (nibabies) - Can handle with DataFrame
16. **BIDSLayoutIndexer** - 2 uses - Internal API, don't implement

## Testing Updates

### Additional Test Cases Needed

#### Query Enum Tests
```python
def test_query_none():
    """Test Query.NONE matches explicit null."""
    layout = BIDSLayout('dataset')
    # Dataset has some files with session, some without
    files = layout.get(subject='01', session=Query.NONE)
    assert all('ses' not in f for f in files)

def test_query_any():
    """Test Query.ANY allows any value."""
    layout = BIDSLayout('dataset')
    files = layout.get(subject='01', task=Query.ANY)
    # Should return files regardless of task value
    assert len(files) > 0
```

#### Subclassing Test
```python
def test_layout_subclassing():
    """Test that BIDSLayout can be subclassed."""
    class CustomLayout(BIDSLayout):
        def custom_method(self):
            return "custom"
    
    layout = CustomLayout('dataset')
    assert layout.custom_method() == "custom"
    assert layout.get_subjects()  # Base methods still work
```

## Recommendations

### 1. Proceed with Original Plan ✅
- Core strategy validated by new repos
- Only minor additions needed (Query enums)

### 2. Add Query Enums to Phase 2 📝
- Simple to implement (~20 lines)
- Used by 3 files across 2 projects
- Natural extension of existing Query.OPTIONAL

### 3. Defer Advanced Features ⏸️
- `add_config_paths()`: Too complex, only 1 user
- `BIDSLayoutIndexer`: Internal API, not needed
- Templateflow can be handled as special case if needed

### 4. Ensure Subclassability 🏗️
- Make `BIDSLayout` easy to subclass
- Don't override `__init__()` in a way that breaks subclassing
- Document how to extend (for power users like templateflow)

## Conclusion

**The new repos validate our approach with only minor adjustments needed:**

✅ **No major architectural changes**  
✅ **Core methods confirmed as 97% of usage**  
✅ **Compat layer strategy still optimal**  
📝 **Small addition: Query.NONE and Query.ANY**  
⏸️ **Defer: Advanced features (config system)**

**Recommendation**: Proceed with implementation as planned, adding Query enums to Phase 2.
