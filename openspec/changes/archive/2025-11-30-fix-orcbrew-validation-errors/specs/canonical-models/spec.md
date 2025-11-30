## MODIFIED Requirements

### Requirement: OrcBrew Relaxed Models

The system SHALL provide OrcBrew-specific model variants with relaxed field requirements for incomplete data and SHALL handle OrcBrew-specific data formats through model validators.

#### Scenario: Validate OrcBrew spell with missing fields
- **GIVEN** an OrcBrew spell with only `name`, `level`, `school`, `description`
- **WHEN** validated through `OrcBrewSpell` model
- **THEN** validation succeeds
- **AND** missing fields (`casting_time`, `range`, `duration`) are `None`

#### Scenario: OrcBrew creature without ability scores
- **GIVEN** an OrcBrew creature with `name`, `type`, `size`, `challenge`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** ability scores default to `None`
- **AND** `hit_points` and `hit_dice` default to `None`

#### Scenario: Convert OrcBrew model to canonical
- **GIVEN** an `OrcBrewSpell` instance
- **WHEN** calling `to_canonical()` method
- **THEN** returns a `Spell` instance with same data
- **AND** missing fields remain `None`

#### Scenario: Normalize OrcBrew spell components from dict format
- **GIVEN** an OrcBrew spell with `components: {'verbal': True, 'somatic': True, 'material': True}`
- **WHEN** validated through `OrcBrewSpell` model
- **THEN** validation succeeds
- **AND** components is normalized to string `"V, S, M"`
- **AND** if `material-component` key exists, its value is extracted to `material` field

#### Scenario: Handle OrcBrew spell components dict with material description
- **GIVEN** an OrcBrew spell with `components: {'verbal': True, 'material': True, 'material-component': 'a sunburst pendant worth at least 100 gp'}`
- **WHEN** validated through `OrcBrewSpell` model
- **THEN** `components` field becomes `"V, M"`
- **AND** `material` field becomes `"a sunburst pendant worth at least 100 gp"`

#### Scenario: Normalize OrcBrew creature hit_points from dict format
- **GIVEN** an OrcBrew creature with `hit_points: {'die': 8, 'die-count': 10, 'modifier': 20}`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** `hit_points` is calculated as integer: `10 * (8 + 1) / 2 + 20 = 65`

#### Scenario: Handle OrcBrew creature with string speed
- **GIVEN** an OrcBrew creature with `speed: "30 ft."`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** `speed` field accepts the string value

#### Scenario: Handle OrcBrew creature with dict speed
- **GIVEN** an OrcBrew creature with `speed: {'walk': 30, 'fly': 60}`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** `speed` field accepts the dict value

#### Scenario: Handle OrcBrew creature legendary_actions metadata dict
- **GIVEN** an OrcBrew creature with `legendary_actions: {'description': 'The demon can take 3 legendary actions...'}`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** `legendary_actions` field accepts the single dict value (metadata about legendary action economy)

#### Scenario: Handle OrcBrew creature actions metadata dict
- **GIVEN** an OrcBrew creature with `actions: {'description': 'On each of its turns...'}`
- **WHEN** validated through `OrcBrewCreature` model
- **THEN** validation succeeds
- **AND** `actions` field accepts the single dict value (metadata about action economy)
