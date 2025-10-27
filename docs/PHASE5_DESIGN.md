# Phase 5: Advanced Filtering - Design Document

## Overview

**Goal**: Enhance video filtering capabilities beyond basic duration and channel filters to provide users with fine-grained control over playlist content.

**Status**: In Progress (25% complete)

**Total Estimated Effort**: 2.5-3 hours

**Rationale**:
- Natural progression from Phase 4 channel filtering
- High user value (addresses common pain points)
- Low risk (extends existing system without architectural changes)
- Fully backward compatible
- Incremental delivery model

---

## Phase 5 Sub-phases

### Phase 5.1: Duration Range Filter ✅ COMPLETED
**Estimated**: 30 minutes | **Actual**: ~30 minutes

**Problem Solved**: Users want to filter out BOTH short videos (shorts/clips) AND long videos (lectures/streams) simultaneously.

**Implementation**:
- Added `max_duration_seconds` config field (default: `null` = unlimited)
- Extended backend validation to check `max >= min` constraint
- Updated video filtering to track "too_long" statistics
- Built UI with slider (60s-7200s) and "Unlimited" checkbox
- Config summary displays duration as range when max is set

**Use Cases Enabled**:
- "Only 5-20 minute videos" (skip shorts AND lectures)
- "Quick consumption" playlists (under 10 minutes)
- "Deep dive" playlists (30+ minutes only)
- "No lengthy content" (max 15 minutes)

**Backward Compatibility**: ✅
- Existing configs without `max_duration_seconds` work unchanged
- Default value is `null` (unlimited)
- No breaking changes

**Commit**: `8c99333 feat(filtering): add duration range filter with max duration`

---

### Phase 5.2: Date Range Filter ⏳ PLANNED
**Estimated**: 45 minutes

**Problem to Solve**: Fixed `lookback_hours` is inflexible - users want "last 7 days" or "specific date range" for curated playlists.

**Proposed Implementation**:

**Backend** (yt_sub_playlist/config/schema.py, video_filtering.py):
```python
# New config fields
DEFAULTS = {
    # ... existing fields ...
    "date_filter_mode": "lookback",      # "lookback", "days", "date_range"
    "date_filter_days": None,            # Override lookback_hours (e.g., 7, 30)
    "date_filter_start": None,           # YYYY-MM-DD
    "date_filter_end": None,             # YYYY-MM-DD
}
```

**Validation**:
- Date format: YYYY-MM-DD (ISO 8601)
- Range constraint: `start_date <= end_date`
- Days must be positive integer

**Filtering Logic**:
1. **lookback mode**: Use existing `lookback_hours` (default behavior)
2. **days mode**: Override lookback with "last N days" logic
3. **date_range mode**: Filter videos between start/end dates

**Frontend** (dashboard/config.html, config.js):
- Date filter mode dropdown (3 options)
- Conditional visibility:
  - "days" mode → number input (1-365 days)
  - "date_range" mode → start/end date pickers (HTML5 date inputs)
  - "lookback" mode → hide extra inputs (use existing lookback_hours)

**Use Cases**:
- "Last 7 days only" (rolling window)
- "Videos from October 2025" (specific month)
- "Content published this week" (date range)

---

### Phase 5.3: Keyword Filter ⏳ PLANNED
**Estimated**: 60 minutes

**Problem to Solve**: Users want to include/exclude videos based on title/description keywords (e.g., "avoid clickbait", "only tutorials").

**Proposed Implementation**:

**Backend** (yt_sub_playlist/config/schema.py, video_filtering.py):
```python
# New config fields
DEFAULTS = {
    # ... existing fields ...
    "keyword_filter_mode": "none",       # "none", "include", "exclude", "both"
    "keyword_include": None,             # List of strings or regex patterns
    "keyword_exclude": None,             # List of strings or regex patterns
    "keyword_match_type": "any",         # "any", "all" (OR vs AND logic)
    "keyword_case_sensitive": False,
    "keyword_search_description": False, # Search in description (default: title only)
}
```

**Validation**:
- Lists must be arrays of strings
- Regex patterns must be valid (compile test)
- Mode validation: must be one of allowed values

**Filtering Logic**:
1. **include mode**: Video must match at least one include keyword
2. **exclude mode**: Video must NOT match any exclude keyword
3. **both mode**: Must match include AND not match exclude
4. **none mode**: No keyword filtering (default)

**Match Types**:
- `any`: Match if ANY keyword found (OR logic)
- `all`: Match if ALL keywords found (AND logic)

**Frontend** (dashboard/config.html, config.js):
- Mode dropdown (none/include/exclude/both)
- Textarea for include keywords (one per line)
- Textarea for exclude keywords (one per line)
- Advanced options:
  - Match type radio buttons (any/all)
  - Case sensitive checkbox
  - Search in description checkbox

**Use Cases**:
- "No spoiler videos" (exclude: ["spoiler", "ending", "finale"])
- "Tutorial content only" (include: ["tutorial", "guide", "how to"])
- "Avoid clickbait" (exclude: ["SHOCKING", "YOU WON'T BELIEVE"])
- "Specific game content" (include: ["Elden Ring"], exclude: ["spoiler"])

**Statistics**:
- Track "filtered_by_keyword_include" and "filtered_by_keyword_exclude" counts

---

### Phase 5.4: Polish & Documentation ⏳ PLANNED
**Estimated**: 30 minutes

**Tasks**:

1. **README Update**:
   - Document all Phase 5 filtering features
   - Add examples of filter combinations
   - Update configuration reference section

2. **UI Enhancements**:
   - Add inline help tooltips/info icons
   - "Reset to defaults" button for each filter section
   - Better visual grouping of filter controls

3. **Optional Enhancements** (if time permits):
   - Filter preview feature (show what would be filtered without saving)
   - Export/import filter presets
   - Filter statistics on dashboard (show what's being filtered)

4. **Testing**:
   - End-to-end test with all filters enabled
   - Verify backward compatibility
   - Test filter combinations

5. **Changelog**:
   - Update CHANGELOG.md with Phase 5 features
   - Prepare for v5.0.0 release

---

## Architecture Decisions

### 1. Incremental Implementation
**Decision**: Implement Phase 5 in 4 sub-phases

**Alternative**: Implement all filters at once

**Rationale**:
- Lower risk (smaller changes per commit)
- Testable milestones
- Can pause/resume easily
- Each sub-phase delivers working features

### 2. Backward Compatibility First
**Decision**: All new fields optional with sensible defaults

**Alternative**: Breaking changes with migration

**Rationale**:
- Existing configs continue working
- No migration scripts needed
- Users can opt-in to new features

**Implementation**: All new fields default to `None` or conservative values

### 3. Simple Filter Logic (AND)
**Decision**: All filters use AND logic (must pass all)

**Alternative**: Complex boolean expressions (OR, AND, NOT)

**Rationale**:
- Simpler implementation
- Easier to understand for users
- Sufficient for 90% of use cases
- Can add complex logic in Phase 6 if needed

### 4. No API Changes Required
**Decision**: Existing REST endpoints handle new fields automatically

**Implementation**: Config PUT/GET endpoints are schema-agnostic

**Benefit**: Frontend and backend decoupled

### 5. UI-First Design
**Decision**: Design UI controls before implementing backend

**Alternative**: Backend-first approach

**Rationale**:
- Better user experience
- Catches usability issues early
- Frontend constraints inform backend design

---

## Configuration Schema (After Phase 5 Complete)

```python
DEFAULTS = {
    # Playlist settings
    "playlist_name": "Auto Playlist from Subscriptions",
    "playlist_visibility": "unlisted",
    "max_videos": 50,

    # Duration filters (Phase 5.1)
    "min_duration_seconds": 60,
    "max_duration_seconds": None,  # null = unlimited

    # Date filters (Phase 5.2)
    "lookback_hours": 24,           # Used when date_filter_mode = "lookback"
    "date_filter_mode": "lookback", # "lookback", "days", "date_range"
    "date_filter_days": None,       # Last N days (overrides lookback_hours)
    "date_filter_start": None,      # YYYY-MM-DD
    "date_filter_end": None,        # YYYY-MM-DD

    # Content type filters
    "skip_live_content": True,

    # Channel filters (Phase 4)
    "channel_filter_mode": "none",  # "none", "allowlist", "blocklist"
    "channel_allowlist": None,
    "channel_blocklist": None,

    # Keyword filters (Phase 5.3)
    "keyword_filter_mode": "none",       # "none", "include", "exclude", "both"
    "keyword_include": None,             # List[str]
    "keyword_exclude": None,             # List[str]
    "keyword_match_type": "any",         # "any", "all"
    "keyword_case_sensitive": False,
    "keyword_search_description": False,
}
```

---

## Filter Execution Order

Videos are filtered in this order (each filter can reject a video):

1. **Live content filter**: Skip if live and `skip_live_content = true`
2. **Duration filter**: Check `min_duration_seconds` and `max_duration_seconds`
3. **Date filter**: Check publish date against date filter settings
4. **Channel filter**: Check against allowlist/blocklist
5. **Keyword filter**: Check title/description against include/exclude lists

**Statistics tracked for each filter stage** to help users tune their settings.

---

## Testing Strategy

### Manual Testing (Current)
- Python validation scripts
- Browser UI testing
- Configuration save/load verification

### Automated Testing (Planned)
- pytest unit tests for filter logic
- pytest unit tests for config validation
- Integration tests for API endpoints
- UI validation tests (prevent invalid inputs)

### Test Coverage Goals
- All filter modes tested
- Edge cases (null values, empty lists, invalid dates)
- Filter combinations
- Backward compatibility scenarios

---

## UI/UX Principles

### Progressive Disclosure
- Show advanced options only when relevant mode selected
- Collapse filter sections that aren't being used
- Provide sensible defaults

### Clear Feedback
- Display current filter settings in human-readable format
- Show statistics on what's being filtered
- Validation messages explain why config is invalid

### Consistency
- All filters follow similar pattern (mode → options → save)
- Similar UI controls for similar concepts
- Consistent terminology throughout

### Safety
- Backend validation prevents invalid configs
- Frontend validation provides immediate feedback
- Changes require explicit "Save" action

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **No complex boolean logic**: Filters use AND only (can't do "duration OR keyword")
2. **No regex in UI**: Users must edit JSON for regex patterns
3. **No timezone control**: Date filters use system timezone
4. **No saved filter presets**: Can't save/load filter combinations

### Future Phase Ideas

**Phase 6: Advanced Filter Logic**
- Boolean expressions (AND, OR, NOT combinations)
- Filter groups with different logic
- Visual query builder

**Phase 7: Filter Presets**
- Save filter combinations with names
- Quick-switch between presets
- Import/export presets

**Phase 8: Smart Filters**
- ML-based content classification
- Automatic tagging
- Personalized recommendations

---

## Implementation Notes

### Files Modified (Phase 5.1)
- `yt_sub_playlist/config/schema.py` - Schema and validation
- `yt_sub_playlist/core/video_filtering.py` - Filter logic
- `dashboard/config.html` - UI controls
- `dashboard/config.js` - Frontend logic

### No New Files Created
All Phase 5 changes extend existing architecture. No new files or modules required.

### Dependencies
- No new Python dependencies
- No new JavaScript dependencies
- Uses existing Flask/HTML5/vanilla JS stack

---

## Success Metrics

### Completed (Phase 5.1)
- ✅ Backend: max_duration_seconds field added and validated
- ✅ Frontend: Max duration slider with unlimited checkbox
- ✅ Testing: Manual validation passing
- ✅ Commit: Clean git history maintained
- ✅ Backward compatibility: Existing configs work unchanged

### Pending (Phase 5.2-5.4)
- ⏳ Date filtering with 3 modes
- ⏳ Keyword filtering with include/exclude
- ⏳ Documentation updated (README, CHANGELOG)
- ⏳ UI polish (tooltips, reset buttons)
- ⏳ Automated tests added

---

## Timeline

- **Phase 5.1**: ✅ Complete (30 min)
- **Phase 5.2**: ⏳ Planned (45 min)
- **Phase 5.3**: ⏳ Planned (60 min)
- **Phase 5.4**: ⏳ Planned (30 min)

**Total Remaining**: ~2.5 hours

**Next Session**: Recommended to start with Phase 5.2 (date range filter)

---

## References

- Phase 4 Documentation: Channel filtering system
- Session Notes: `_notes/end-session-20251027-1328.md`
- Git Commit: `8c99333` (Phase 5.1 implementation)
