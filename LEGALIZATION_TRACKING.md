# Legalization Tracking in Generation Trace

## Overview

This document explains the modifications made to `adder.py` to track the effect of legalization in the generation trace.

## Problem Statement

Previously, the generation trace only recorded which cells were **removed** during the optimization process. However, the legalization process can **add** cells to maintain the correctness of the adder structure. Without tracking these additions, the trace was incomplete and could not fully explain how the design evolved.

## What is Legalization?

In the context of parallel prefix adders, legalization ensures that the adder structure remains valid after a cell is removed. When a cell at position (x, y) is removed, the legalization algorithm checks if any "gaps" are created in the prefix computation chain. If so, it adds cells to fill these gaps.

### Example

Consider this scenario:

**Initial state:**
- Cell at (7, 3) exists
- Cell at (6, 3) exists  
- Cell at (5, 3) exists

**Action:** Remove cell at (7, 3)

**Legalization effect:**
- The removal creates a gap in the computation chain
- The algorithm adds cell at (4, 3) to maintain correctness
- Net result: 1 cell removed, 1 cell added, total size unchanged

Without tracking legalization, the trace would only show "removed cell at (7, 3)" and the user would be confused about why the size didn't decrease.

## Modifications Made

### 1. Modified `legalize()` Method

**Location:** `adder.py`, lines 213-233

**Changes:**
```python
# ADDED: Track cells added during legalization
added_cells = []  # New list to track added cells

# Inside the loop where cells are added:
if cell_map[last_y-1, y] == 0:
    assert last_y - 1 <= start_bit
    next_bit = last_y - 1
    cell_map[last_y-1, y] = 1
    activate_x_list.append(next_bit)
    added_cells.append((last_y-1, y))  # ADDED: Record the added cell

# MODIFIED: Return value now includes added_cells
return cell_map, min_map, activate_x_list, added_cells
```

**Before:** `legalize()` returned `(cell_map, min_map, activate_x_list)`

**After:** `legalize()` returns `(cell_map, min_map, activate_x_list, added_cells)`

**Explanation:**
- Added `added_cells = []` to initialize an empty list
- When a cell is added at position `(last_y-1, y)`, we record it in `added_cells`
- The method now returns this list as the 4th element of the tuple

### 2. Modified `get_next_state_with_random_choice()` Method

**Location:** `adder.py`, lines 268-310

**Changes:**
```python
# MODIFIED: Capture added_cells from legalize
next_cell_map, next_min_map, activate_x_list, added_cells = self.legalize(
    next_cell_map, next_min_map, start_bit = x)

# ... later in the code ...

# MODIFIED: Include legalization info in trace
operation_info = {
    'step': next_step_num,
    'action': action,
    'action_type': 'remove_cell',
    'position': (x, y),
    'prev_level': self.level,
    'next_level': next_level,
    'prev_size': self.size,
    'next_size': next_size,
    'reward': reward,
    'legalization_added_cells': added_cells  # ADDED: Track legalization effects
}
```

**Explanation:**
- Updated the unpacking to capture the 4th return value `added_cells`
- Added `'legalization_added_cells'` field to the operation info dictionary
- This field contains a list of tuples representing positions of added cells

### 3. Modified `output_generation_trace()` Method

**Location:** `adder.py`, lines 314-367

**Changes:**
```python
for op in self.generation_trace:
    trace_str += "Step {}: {} at position ({}, {})\n".format(
        op['step'], op['action_type'], op['position'][0], op['position'][1])
    trace_str += "  Action ID: {}\n".format(op['action'])
    
    # ADDED: Display legalization effects
    if 'legalization_added_cells' in op and len(op['legalization_added_cells']) > 0:
        trace_str += "  Legalization: {} cell(s) added: {}\n".format(
            len(op['legalization_added_cells']),
            ', '.join(['({}, {})'.format(c[0], c[1]) for c in op['legalization_added_cells']])
        )
    else:
        trace_str += "  Legalization: No cells added\n"
    
    # ... rest of the display code ...
```

**Explanation:**
- Check if the operation has legalization information
- If cells were added, display the count and their positions
- If no cells were added, display "No cells added"
- This provides complete transparency about legalization effects

## Benefits

1. **Complete Transparency**: Users can now see the full picture of how each action affects the design
2. **Understanding Size Changes**: Explains why removing a cell might not decrease the total size
3. **Debugging**: Helps identify when and why legalization adds cells
4. **Analysis**: Enables studying the relationship between removals and required additions
5. **Reproducibility**: Complete information allows perfect reconstruction of the design process

## Example Output

### Before (without legalization tracking):
```
Step 1: remove_cell at position (7, 3)
  Action ID: 123
  Level: 8 -> 6 (change: -2)
  Size:  10 -> 10 (change: +0)  # <-- Why didn't size change? Not clear!
  Reward: -17.00
```

### After (with legalization tracking):
```
Step 1: remove_cell at position (7, 3)
  Action ID: 123
  Legalization: 1 cell(s) added: (4, 3)  # <-- Now it's clear!
  Level: 8 -> 6 (change: -2)
  Size:  10 -> 10 (change: +0)  # Size unchanged because 1 removed, 1 added
  Reward: -17.00
```

## Testing

The modifications have been tested with multiple scenarios:

1. **No legalization**: When removing a cell doesn't require adding any cells
   - Output: "Legalization: No cells added"

2. **Single cell added**: When one cell is added during legalization
   - Output: "Legalization: 1 cell(s) added: (4, 3)"

3. **Multiple cells added**: When multiple cells are added
   - Output: "Legalization: 2 cell(s) added: (4, 3), (5, 3)"

All test cases pass successfully.

## Backward Compatibility

The changes maintain backward compatibility:
- Old code that doesn't use the trace feature continues to work
- The trace is only populated when states are created via `get_next_state_with_random_choice()`
- Files that import and use `adder.py` are unaffected

## Code Quality

The modifications follow best practices:
- **Minimal changes**: Only 3 methods modified, ~11 lines of functional code added
- **Clear variable names**: `added_cells` clearly indicates purpose
- **Consistent style**: Follows existing code conventions
- **No breaking changes**: All existing functionality preserved
- **Well documented**: Inline comments explain the purpose of changes

## Summary

The legalization tracking enhancement provides complete transparency about how the adder design evolves during optimization. By tracking both cell removals and legalization-induced additions, users can now fully understand the design process and analyze the trade-offs involved in each step.
