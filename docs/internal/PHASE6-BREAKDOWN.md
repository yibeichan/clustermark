# Phase 6 Breakdown: Polish & Edge Cases

**Created**: 2025-11-01
**Branch**: `feature/phase6-polish-edge-cases`
**Goal**: Address Phase 5 code review feedback with incremental, reviewable PRs

---

## Overall Strategy

**Best Practices Applied**:
- ✅ Break into sub-phases (<500 lines per PR)
- ✅ Each PR is independently testable
- ✅ Apply lessons from Phases 1-5
- ✅ Test thoroughly before requesting review
- ✅ One theme per PR (no mixing concerns)

**Phase 6 Goals** (from implementation plan):
1. Extract inline styles to CSS classes
2. Add backend API for fetching outliers
3. Split AnnotationPage into sub-components
4. Add error boundaries and loading skeletons
5. Optional: localStorage persistence

---

## Sub-Phase Breakdown

### **Phase 6a: CSS Extraction & Styling** ← START HERE

**Goal**: Extract all inline styles to CSS classes

**Scope**:
- Create `frontend/src/styles/AnnotationPage.css`
- Extract ~15 CSS classes from inline styles
- Update AnnotationPage.tsx to use className instead of style prop
- Test: Visual regression (UI should look identical)

**Files Modified**: 2 files
- `frontend/src/styles/AnnotationPage.css` (new, ~150 lines)
- `frontend/src/pages/AnnotationPage.tsx` (replace inline styles)

**Estimated Lines**: ~200 lines (+150 CSS, -50 inline styles)

**Why First**: 
- Standalone change (no logic changes)
- Makes subsequent refactors cleaner
- Easiest to review (visual diff)
- Low risk

**Testing Checklist**:
- [ ] All 4 workflow steps render correctly
- [ ] Outlier selection visual feedback works (red border)
- [ ] Button states (hover, disabled) work
- [ ] Page controls layout unchanged
- [ ] Responsive grid still works

---

### **Phase 6b: Backend Outlier Fetch API**

**Goal**: Add endpoint to retrieve outlier images for resume workflow

**Scope**:
- Add `GET /clusters/{id}/outliers` endpoint
- Add schema for response
- Add service method
- Write 3 tests (success, empty, not found)

**Files Modified**: 3 files
- `backend/app/routers/clusters.py` (+15 lines)
- `backend/app/models/schemas.py` (+8 lines)
- `backend/tests/test_cluster_service.py` (+40 lines)

**Estimated Lines**: ~65 lines

**Why Second**:
- Small, focused backend change
- Enables frontend work in 6c
- Independently testable
- No breaking changes

**Testing Checklist**:
- [ ] Returns outliers for cluster with outliers
- [ ] Returns empty array for cluster without outliers
- [ ] Returns 404 for non-existent cluster
- [ ] Test with multiple outliers
- [ ] Verify annotation_status filter works

---

### **Phase 6c: Frontend Outlier Fetch Integration**

**Goal**: Load existing outliers on page mount

**Scope**:
- Add `getOutliers` API client method
- Add useEffect to load outliers on mount
- Merge with local state
- Test with pre-existing outliers

**Files Modified**: 2 files
- `frontend/src/services/api.ts` (+6 lines)
- `frontend/src/pages/AnnotationPage.tsx` (+20 lines)

**Estimated Lines**: ~30 lines

**Why Third**:
- Depends on 6b (backend API)
- Small frontend change
- Fixes data loss bug from Phase 5
- Easy to verify

**Testing Checklist**:
- [ ] Loads existing outliers on mount
- [ ] Merges with user selections
- [ ] Handles empty outliers (no error)
- [ ] Handles API errors gracefully
- [ ] Counter shows correct count

---

### **Phase 6d: Error Boundary & Skeleton Loader**

**Goal**: Improve UX with error handling and loading states

**Scope**:
- Create ErrorBoundary component
- Create ImageGridSkeleton component
- Wrap AnnotationPage in ErrorBoundary
- Replace "Loading..." with skeleton

**Files Modified**: 4 files
- `frontend/src/components/ErrorBoundary.tsx` (new, ~45 lines)
- `frontend/src/components/ImageGridSkeleton.tsx` (new, ~25 lines)
- `frontend/src/App.tsx` (+5 lines)
- `frontend/src/pages/AnnotationPage.tsx` (+3 lines for skeleton)

**Estimated Lines**: ~80 lines

**Why Fourth**:
- Standalone UX improvement
- No dependencies on other work
- Easy to test
- Low risk

**Testing Checklist**:
- [ ] ErrorBoundary catches render errors
- [ ] ErrorBoundary shows fallback UI
- [ ] Skeleton shows during loading
- [ ] Skeleton count matches pageSize
- [ ] Skeleton animation works

---

### **Phase 6e: Component Split - Extract Sub-Components**

**Goal**: Split 500+ line AnnotationPage into focused components

**Scope**:
- Create `components/annotation/` directory
- Extract ReviewStep (image grid + pagination)
- Extract BatchLabelStep (Path A)
- Extract OutlierAnnotationStep (Path B outliers)
- Extract RemainingBatchStep (Path B remaining)
- Refactor AnnotationPage to orchestrator

**Files Modified**: 6 files
- `frontend/src/components/annotation/ReviewStep.tsx` (new, ~120 lines)
- `frontend/src/components/annotation/BatchLabelStep.tsx` (new, ~60 lines)
- `frontend/src/components/annotation/OutlierAnnotationStep.tsx` (new, ~80 lines)
- `frontend/src/components/annotation/RemainingBatchStep.tsx` (new, ~60 lines)
- `frontend/src/pages/AnnotationPage.tsx` (refactor to ~200 lines)

**Estimated Lines**: ~520 lines (net +200 after refactor)

**Why Fifth**:
- Most complex refactor
- Depends on 6a (CSS classes in place)
- Benefits from 6d (components can use ErrorBoundary)
- High risk of regression

**Testing Checklist**:
- [ ] All 4 workflow steps work identically
- [ ] Props correctly passed to sub-components
- [ ] State management unchanged
- [ ] No visual regressions
- [ ] Complete annotation workflow works end-to-end

**Anti-Pattern Watch**:
- ❌ Don't change logic during refactor (pure extraction)
- ❌ Don't mix styling changes with component split
- ❌ Don't add new features in this PR

---

### **Phase 6f: localStorage Persistence (Optional)**

**Goal**: Backup outlier selections to localStorage

**Scope**:
- Save selections to localStorage on change
- Load on mount (merge with backend)
- Clear on successful submission

**Files Modified**: 1 file
- `frontend/src/pages/AnnotationPage.tsx` (+25 lines)

**Estimated Lines**: ~25 lines

**Why Last**:
- Optional enhancement
- Backend API (6b-6c) is primary solution
- Low priority
- Can skip if time-constrained

**Testing Checklist**:
- [ ] Selections persist across refresh
- [ ] Merges with backend outliers
- [ ] Clears on submission
- [ ] Handles JSON parse errors
- [ ] Works across browser sessions

---

## PR Strategy

### PR Sizing Goals
- **Target**: <300 lines per PR
- **Maximum**: <500 lines per PR
- **Files**: 2-6 files per PR

### Review Approach
- Request AI code review (Gemini, Codex, Copilot)
- Address ALL feedback (100% response rate)
- Run tests after every fix
- Use incremental commits (one theme per commit)

### Merge Order
1. Phase 6a (CSS) → Independent, can merge first
2. Phase 6b (Backend API) → Independent, can merge first
3. Phase 6c (Frontend integration) → Depends on 6b
4. Phase 6d (Error boundary) → Independent, can merge anytime
5. Phase 6e (Component split) → Depends on 6a, benefits from 6d
6. Phase 6f (localStorage) → Optional, can skip

**Parallel Work Opportunities**:
- 6a + 6b can be done in parallel (different stacks)
- 6d can be done in parallel with 6a/6b/6c

---

## Risk Assessment

### Low Risk
- ✅ Phase 6a (CSS extraction) - visual only
- ✅ Phase 6b (Backend API) - new endpoint, no changes to existing
- ✅ Phase 6c (Frontend fetch) - additive change
- ✅ Phase 6d (Error boundary) - wrapper component

### Medium Risk
- ⚠️ Phase 6e (Component split) - large refactor, regression potential

### High Risk
- ❌ None (good breakdown!)

### Mitigation Strategies
- **6e Component Split**: 
  - Test after every file extraction
  - Keep commits small (one component per commit)
  - Don't change logic, only structure
  - Use TypeScript to catch prop errors

---

## Success Criteria

**Code Quality**:
- [ ] No inline styles in AnnotationPage
- [ ] All components <150 lines
- [ ] Type safety maintained
- [ ] No new ESLint warnings

**Functionality**:
- [ ] Complete annotation workflow unchanged
- [ ] Outlier resume workflow works
- [ ] Error states handled gracefully
- [ ] Loading states use skeletons

**Testing**:
- [ ] All existing tests pass
- [ ] New tests for backend API
- [ ] Manual testing of all 4 workflow steps
- [ ] Visual regression testing

**Review**:
- [ ] AI code review passes
- [ ] All feedback addressed
- [ ] No regressions introduced

---

## Anti-Patterns to Avoid

Based on lessons from Phases 1-5:

### From Phase 2 (Security)
- ❌ Don't skip sanitization (N/A for Phase 6)
- ✅ Apply: Test edge cases (empty outliers, API errors)

### From Phase 3 (Ownership)
- ❌ Don't allow cross-cluster access
- ✅ Apply: Verify cluster_id in outlier endpoint

### From Phase 4 (Type Safety)
- ❌ Don't use `any` assertions
- ✅ Apply: Proper typing for new components

### From Phase 5 (Race Conditions)
- ❌ Don't leave async operations without cleanup
- ✅ Apply: Add cleanup to outlier fetch useEffect
- ❌ Don't allow interactions during submission
- ✅ Apply: Pass `disabled` prop to all sub-components

### General Best Practices
- ❌ Don't mix concerns in one PR
- ❌ Don't change logic during refactoring
- ❌ Don't commit without testing
- ✅ One theme per commit
- ✅ Test after every change
- ✅ Address all review feedback

---

## Estimated Timeline

- **Phase 6a**: 2-3 hours (CSS extraction + testing)
- **Phase 6b**: 1-2 hours (Backend API + tests)
- **Phase 6c**: 1 hour (Frontend integration)
- **Phase 6d**: 2 hours (ErrorBoundary + Skeleton)
- **Phase 6e**: 4-5 hours (Component split + testing)
- **Phase 6f**: 1 hour (localStorage - optional)

**Total**: 11-14 hours of work across 5-6 PRs

**Review overhead**: +2-3 hours per PR (AI review + fixes)

**Grand total**: ~20-30 hours (Phase 6 complete)

---

## Next Steps

1. ✅ Create feature branch: `feature/phase6-polish-edge-cases`
2. Start with Phase 6a (CSS extraction)
3. Test thoroughly
4. Commit with clear message
5. Push and prepare for AI code review
6. Address feedback
7. Merge to main
8. Repeat for 6b, 6c, 6d, 6e, 6f

**Current Status**: Ready to start Phase 6a ✅
