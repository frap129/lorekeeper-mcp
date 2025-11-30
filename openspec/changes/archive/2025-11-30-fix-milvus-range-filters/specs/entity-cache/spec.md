## ADDED Requirements

### Requirement: Range Filter Support in Filter Expressions

The cache MUST support range filter parameters (`_min` and `_max` suffixes) and convert them to appropriate comparison operators in Milvus filter expressions.

#### Scenario: Convert level_min to greater-than-or-equal filter
**Given** a filter dictionary with `{"level_min": 4}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level >= 4`
**And** only entities with level 4 or higher match the filter

#### Scenario: Convert level_max to less-than-or-equal filter
**Given** a filter dictionary with `{"level_max": 3}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level <= 3`
**And** only entities with level 3 or lower match the filter

#### Scenario: Combine range filters with semantic search
**Given** a cache containing spells at various levels
**When** calling `semantic_search("spells", "fire damage", level_min=4, level_max=6)`
**Then** the filter expression includes `level >= 4 and level <= 6`
**And** only level 4, 5, or 6 spells are searched
**And** results are ranked by semantic similarity to "fire damage"

#### Scenario: Combine range filter with exact filter
**Given** a filter dictionary with `{"level_min": 3, "school": "evocation"}`
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `level >= 3 and school == "evocation"`
**And** both conditions must be satisfied for a match

#### Scenario: Generic field minimum range support
**Given** a filter dictionary with `{"armor_class_min": 15}` for armor entities
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `armor_class >= 15`
**And** the pattern works for any indexed numeric field with `_min` suffix

#### Scenario: Generic field maximum range support
**Given** a filter dictionary with `{"challenge_rating_max": 5}` for creature entities
**When** `_build_filter_expression()` processes the filter
**Then** the resulting expression is `challenge_rating <= 5`
**And** the pattern works for any indexed numeric field with `_max` suffix
