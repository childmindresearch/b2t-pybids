# b2t PyBIDS Compatibility Layer - Implementation Plan

## Project Goal

Create an optional compatibility layer (`bids2table.compat`) that provides a PyBIDS-like API as a drop-in replacement, enabling easy migration while teaching users the superior DataFrame-based approach.

## Design Principles

1. **Optional, not core** - Compat layer is separate submodule, not part of main b2t API
2. **Thin wrapper** - All methods delegate to native b2t or DataFrame operations
3. **Educational** - Migration guide shows both compat and native approaches
4. **Performance-conscious** - Minimize overhead, leverage b2t's speed advantages
5. **Deprecation path** - Can sunset compat layer once pybids is retired

## Architecture

```
bids2table/
├── __init__.py              (existing - core b2t API)
├── _indexing.py             (existing)
├── _entities.py             (existing)
├── _metadata.py             (existing)
└── compat/                  (NEW - compatibility layer)
    ├── __init__.py          (exports BIDSLayout, Query, BIDSFile)
    ├── layout.py            (BIDSLayout class)
    ├── query.py             (Query helpers)
    └── bidsfile.py          (BIDSFile wrapper)
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Priority: CRITICAL** - Enables basic migration for all projects

#### 1.1 BIDSLayout Class
- **File**: `bids2table/compat/layout.py`
- **Methods**:
  - `__init__(root, validate, derivatives, cache_path, **kwargs)`
  - Internal: `_load_or_create_index()` - handle parquet caching
  - Internal: `_index_derivatives()` - handle derivatives concatenation

**Implementation notes**:
- Store PyArrow table and DataFrame internally
- Support parquet caching (default: `{root}/.bids2table_cache.parquet`)
- `validate` parameter: log warning but don't enforce (b2t always validates)
- `derivatives`: can be str, Path, List[Path]

**Test cases**:
- Load dataset with/without cache
- Load with derivatives
- Cache invalidation on dataset changes

#### 1.2 layout.get() - File Querying
- **File**: `bids2table/compat/layout.py` (method of BIDSLayout)
- **Signature**: `get(return_type='file', **entities) -> List[Union[str, BIDSFile]]`

**Implementation notes**:
- Filter DataFrame by entity kwargs
- Handle `Query.OPTIONAL` sentinel value
- Handle list values (e.g., `extension=['.nii', '.nii.gz']`)
- Map `return_type`:
  - `'filename'` → list of path strings
  - `'file'` → list of BIDSFile objects
  - `'id'` → list of file IDs (row indices)
  - `'dir'` → list of unique directories

**Edge cases**:
- Unknown entities: ignore or warn?
- Empty results: return [] (not None)
- Invalid return_type: raise ValueError

**Test cases**:
- Single entity filter
- Multiple entity filters
- List values (extensions)
- Query.OPTIONAL
- All return_type options

#### 1.3 layout.get_metadata()
- **File**: `bids2table/compat/layout.py` (method of BIDSLayout)
- **Signature**: `get_metadata(path: str) -> Dict[str, Any]`

**Implementation**:
```python
def get_metadata(self, path: str) -> Dict[str, Any]:
    return b2t.load_bids_metadata(path, str(self.root))
```

**Test cases**:
- Load metadata with inheritance
- Missing sidecar (should return {})
- Relative vs absolute paths

### Phase 2: Entity Access (Week 1-2)

**Priority: HIGH** - Used by multiple projects

#### 2.1 BIDSFile Class
- **File**: `bids2table/compat/bidsfile.py`
- **Attributes**:
  - `path` (str)
  - `_entities` (cached dict)
- **Methods**:
  - `get_entities() -> Dict[str, Any]`
  - `__str__()`, `__repr__()`

**Implementation notes**:
- Lazy loading: entities parsed on first `get_entities()` call
- Delegate to `b2t.parse_bids_entities()`

**Test cases**:
- Parse entities from various file types
- Caching works (only parse once)
- String representation

#### 2.2 layout.get_subjects()
- **File**: `bids2table/compat/layout.py`
- **Signature**: `get_subjects(**filters) -> List[str]`

**Implementation**:
```python
def get_subjects(self, **filters) -> List[str]:
    df = self.df.copy()
    for key, value in filters.items():
        if key in df.columns:
            df = df[df[key] == value]
    return sorted(df['sub'].dropna().unique().tolist())
```

**Test cases**:
- No filters (all subjects)
- With filters (e.g., suffix='bold')
- Empty result

#### 2.3 layout.get_sessions()
- **File**: `bids2table/compat/layout.py`
- **Signature**: `get_sessions(subject=None, **filters) -> List[str]`

**Implementation**:
```python
def get_sessions(self, subject: Optional[str] = None, **filters) -> List[str]:
    df = self.df.copy()
    if subject:
        df = df[df['sub'] == subject]
    for key, value in filters.items():
        if key in df.columns:
            df = df[df[key] == value]
    return sorted(df['ses'].dropna().unique().tolist())
```

**Test cases**:
- All sessions in dataset
- Sessions for specific subject
- Dataset without sessions (return [])
- With additional filters

#### 2.4 Query Helpers
- **File**: `bids2table/compat/query.py`
- **Classes**:
  - `Query` with `OPTIONAL` class attribute

**Implementation**:
```python
class Query:
    """Special query values for filtering."""
    OPTIONAL = object()  # Sentinel for optional entities
    # Future: NONE, ANY, etc.
```

### Phase 3: Specialized Features (Week 2-3)

**Priority: MEDIUM** - Used by specific projects only

#### 3.1 layout.get_file()
- **File**: `bids2table/compat/layout.py`
- **Signature**: `get_file(path: str) -> BIDSFile`

**Implementation**:
```python
def get_file(self, path: str) -> BIDSFile:
    return BIDSFile(path)
```

**Note**: Simple wrapper, doesn't validate path exists

#### 3.2 layout.build_path()
- **File**: `bids2table/compat/layout.py`
- **Signature**: `build_path(entities: Dict, pattern: Optional[str] = None, validate: bool = True) -> str`

**Implementation**:
```python
def build_path(self, entities: Dict, pattern: Optional[str] = None, **kwargs) -> str:
    return b2t.format_bids_path(entities, pattern)
```

**Test cases**:
- With custom pattern
- With default pattern
- Entity key mapping (subject→sub, extension→ext)

#### 3.3 layout.get_fieldmap()
- **File**: `bids2table/compat/fieldmaps.py` (separate module - complex logic)
- **Signature**: `get_fieldmap(target: str, return_list: bool = False) -> Union[Dict, List[Dict]]`

**Implementation strategy**:
1. Parse target file entities and metadata
2. Find candidate fieldmap files (suffix in ['fieldmap', 'epi', 'phasediff', ...])
3. Match using BIDS association rules:
   - Check `B0FieldSource` in target metadata
   - Check `IntendedFor` in fieldmap metadata
   - Match entities (subject, session, acquisition)
4. Determine fieldmap type and return dict

**Algorithm**:
```python
def get_fieldmap(self, target: str, return_list: bool = False):
    # 1. Get target metadata
    target_meta = self.get_metadata(target)
    target_ents = b2t.parse_bids_entities(target)
    
    # 2. Method A: B0FieldSource in target
    b0_sources = target_meta.get('B0FieldSource')
    if b0_sources:
        # Find fmaps with matching B0FieldIdentifier
        fmaps = self._find_fmaps_by_b0field(b0_sources, target_ents)
        if fmaps:
            return fmaps if return_list else fmaps[0]
    
    # 3. Method B: IntendedFor in fieldmaps
    fmaps = self._find_fmaps_by_intendedfor(target, target_ents)
    if fmaps:
        return fmaps if return_list else fmaps[0]
    
    # 4. Method C: Entity-based matching (fallback)
    fmaps = self._find_fmaps_by_entities(target_ents)
    return fmaps if return_list else (fmaps[0] if fmaps else None)
```

**Helper methods**:
- `_find_fmaps_by_b0field()` - Match B0FieldIdentifier
- `_find_fmaps_by_intendedfor()` - Parse IntendedFor paths
- `_find_fmaps_by_entities()` - Entity-based heuristics
- `_determine_fmap_type()` - Classify fmap type (epi/phasediff/etc)

**Test cases** (use bids-examples):
- Dataset with `IntendedFor` fieldmaps
- Dataset with `B0FieldSource` fieldmaps
- Multi-echo fieldmaps
- No matching fieldmap (return None)

**References**:
- BIDS Specification: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html#fieldmap-data
- PyBIDS implementation: https://github.com/bids-standard/pybids/blob/master/bids/layout/layout.py#L812

#### 3.4 layout.get_fmapids()
- **File**: `bids2table/compat/fieldmaps.py`
- **Signature**: `get_fmapids(**entities) -> List[str]`

**Implementation**:
```python
def get_fmapids(self, **entities) -> List[str]:
    # Find files matching entities
    files = self.get(return_type='filename', **entities)
    if not files:
        return []
    
    # Get B0FieldSource from metadata
    target_meta = self.get_metadata(files[0])
    return target_meta.get('B0FieldSource', [])
```

**Test cases**:
- Files with B0FieldSource
- Files without B0FieldSource (return [])

### Phase 4: Testing & Documentation (Week 3-4)

#### 4.1 Unit Tests
- **File**: `tests/compat/test_layout.py`
- **Coverage targets**:
  - BIDSLayout initialization (raw, derivatives, caching)
  - All query methods (.get, .get_subjects, .get_sessions)
  - Metadata access
  - Entity extraction
  - Fieldmap association

**Test datasets**:
- Use `datasets/bids-examples/*` (already have as submodule)
- Focus on: ds000001 (simple), ds000117 (multi-echo), asl* (complex)

#### 4.2 Integration Tests
- **File**: `tests/compat/test_migration.py`
- **Goal**: Compare PyBIDS and compat outputs for identical operations
- **Strategy**:
  ```python
  def test_pybids_compat_equivalence():
      # If PyBIDS installed
      from bids.layout import BIDSLayout as PyBIDSLayout
      pybids_layout = PyBIDSLayout('datasets/bids-examples/ds000001')
      
      from bids2table.compat import BIDSLayout
      compat_layout = BIDSLayout('datasets/bids-examples/ds000001')
      
      # Compare results
      assert set(pybids_layout.get_subjects()) == set(compat_layout.get_subjects())
      # ... more comparisons
  ```

#### 4.3 Documentation
- **File**: `docs/compat.md`
- **Sections**:
  - Why use compat layer?
  - Installation & imports
  - API reference (auto-generated)
  - Differences from PyBIDS
  - Performance characteristics
  - When to use compat vs native

#### 4.4 Migration Guide (already done!)
- Review and update based on implementation

### Phase 5: Performance Optimization (Week 4)

#### 5.1 Caching Improvements
- Benchmark cache load times (parquet vs SQLite)
- Consider compression options (snappy, gzip, zstd)
- Cache invalidation strategy (mtime checking)

#### 5.2 Query Optimization
- Profile `.get()` with complex filters
- Consider indexing DataFrame (set_index on common entities)
- Lazy evaluation where possible

#### 5.3 Memory Optimization
- Consider using PyArrow directly (avoid conversion to pandas)
- Lazy loading of metadata (only load when accessed)
- Option to load subset of columns

## Testing Strategy

### Unit Tests
- Each method in isolation
- Edge cases (empty results, missing data, malformed inputs)
- All parameters and return types

### Integration Tests
- Full workflows (e.g., niworkflows.collect_data equivalent)
- Multi-dataset scenarios
- Derivatives handling

### Comparison Tests
- PyBIDS vs compat layer (if PyBIDS available)
- Verify identical results for identical queries

### Performance Tests
- Indexing time: b2t vs PyBIDS
- Query time: compat vs native DataFrame
- Memory usage: large datasets (>10k files)

### Real-world Tests
- Run on actual pipelines (fmriprep, qsiprep)
- Monkey-patch imports: `bids.layout.BIDSLayout = bids2table.compat.BIDSLayout`
- Verify outputs match

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] BIDSLayout class with basic initialization
- [ ] `.get()` method with entity filtering
- [ ] `.get_subjects()` and `.get_sessions()`
- [ ] `.get_metadata()` wrapper
- [ ] Query.OPTIONAL support
- [ ] Parquet caching works
- [ ] Unit tests pass (>80% coverage)
- [ ] Documentation written

### Full Feature Parity
- [ ] All Phase 1-3 features implemented
- [ ] Fieldmap association works (get_fieldmap, get_fmapids)
- [ ] Integration tests pass
- [ ] Performance benchmarks show >10x speedup over PyBIDS
- [ ] Migration guide tested on real projects

### Production Ready
- [ ] All tests pass (>90% coverage)
- [ ] Performance profiled and optimized
- [ ] Documentation complete
- [ ] At least one real pipeline (e.g., niworkflows) successfully migrated
- [ ] PyPI package published (bids2table[compat] optional extra)

## Non-Goals (Out of Scope)

1. **Full PyBIDS feature parity** - Only implement methods actually used in real projects
2. **PyBIDS bugs/quirks** - Don't replicate known issues, use sensible behavior
3. **SQL backend** - Use parquet only (simpler, faster, more portable)
4. **Config files** - Derivatives handled by concatenation, not complex configs
5. **Writing BIDS datasets** - b2t is read-only (like PyBIDS Layout)

## Dependencies

### Required
- `bids2table` (core library)
- `pandas` (already required by b2t)
- `pyarrow` (already required by b2t)

### Optional
- `pybids` (for comparison tests only, not runtime dependency)

### Development
- `pytest` (testing)
- `pytest-cov` (coverage)
- `pytest-benchmark` (performance)

## Installation

```bash
# Core b2t (no compat layer)
pip install bids2table

# With compatibility layer
pip install bids2table[compat]

# Development
git clone https://github.com/childmindresearch/bids2table.git
cd bids2table
pip install -e ".[compat,dev]"
```

## File Structure (Proposed Changes)

```
bids2table/
├── setup.py                 (add 'compat' extra)
├── README.md               (mention compat layer)
├── bids2table/
│   ├── __init__.py         (unchanged)
│   ├── compat/             (NEW)
│   │   ├── __init__.py     (export BIDSLayout, Query, BIDSFile)
│   │   ├── layout.py       (~300 lines)
│   │   ├── query.py        (~20 lines)
│   │   ├── bidsfile.py     (~50 lines)
│   │   └── fieldmaps.py    (~200 lines, complex)
│   └── ...                 (existing files)
├── tests/
│   ├── compat/             (NEW)
│   │   ├── test_layout.py
│   │   ├── test_query.py
│   │   ├── test_bidsfile.py
│   │   ├── test_fieldmaps.py
│   │   └── test_migration.py
│   └── ...
└── docs/
    ├── compat.md           (NEW)
    └── migration.md        (NEW - from MIGRATION_GUIDE.md)
```

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Fieldmap logic too complex | High | Medium | Start with simple cases, expand incrementally |
| Performance overhead from compat layer | Medium | Medium | Profile and optimize, provide native alternative |
| API differences cause bugs | Medium | High | Comprehensive comparison tests with PyBIDS |
| Parquet cache invalidation issues | Low | High | Conservative mtime checking, manual override |
| Entity key mapping inconsistencies | Medium | Medium | Document differences, provide migration notes |

### Project Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| b2t core API changes | Medium | High | Version pinning, maintain compatibility |
| PyBIDS evolves differently | Low | Low | We're targeting existing usage, not future |
| Low adoption (users prefer native) | Low | Low | That's fine! Native is better anyway |
| Maintenance burden | Medium | Medium | Keep compat layer thin, minimize custom logic |

## Timeline

### Week 1: Core Infrastructure
- Days 1-2: BIDSLayout class, caching, basic .get()
- Days 3-4: get_subjects(), get_sessions(), Query.OPTIONAL
- Day 5: Unit tests, basic documentation

### Week 2: Entity Access & Testing
- Days 1-2: BIDSFile class, get_entities(), get_file()
- Days 3-4: build_path(), integration tests
- Day 5: Comparison tests with PyBIDS

### Week 3: Fieldmaps
- Days 1-3: Fieldmap association logic (complex!)
- Day 4: Fieldmap tests
- Day 5: Performance profiling

### Week 4: Polish & Release
- Days 1-2: Documentation, migration guide refinement
- Days 3-4: Real-world testing (niworkflows, fmriprep)
- Day 5: Package, release, announce

**Total: 4 weeks for full implementation**
**MVP: 1 week** (Phase 1 only)

## Next Steps (Immediate)

1. ✅ Add more repos to analysis (nibabies, neurosynth, templateflow)
2. ✅ Re-run usage analysis to validate approach
3. Get feedback on plan from b2t maintainers
4. Create feature branch: `feat/pybids-compat`
5. Start with MVP (Phase 1)
6. Iterate based on feedback

## Questions for b2t Maintainers

1. Is a compat layer acceptable in the repo? Or separate package?
2. Preferred location: `bids2table.compat` or `bids2table.pybids_compat`?
3. Should fieldmap logic be in core b2t or only in compat?
4. Caching strategy: convention for cache location?
5. Testing: can we add pybids as optional test dependency?

## References

- PyBIDS: https://github.com/bids-standard/pybids
- BIDS Specification: https://bids-specification.readthedocs.io/
- b2t: https://github.com/childmindresearch/bids2table
- Usage Analysis: `PYBIDS_USAGE_ANALYSIS.md`
- Migration Guide: `MIGRATION_GUIDE.md`
