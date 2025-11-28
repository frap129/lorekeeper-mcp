# repository-infrastructure Specification Delta

## Purpose

Document removal of D&D 5e API client dependencies from repository infrastructure.

## ADDED Requirements

### Requirement: Single API Source Policy

The repository infrastructure SHALL use Open5e API exclusively for all D&D content retrieval.

#### Scenario: Repository factory creates Open5e-only repositories
- **WHEN** RepositoryFactory creates any repository instance
- **THEN** the repository uses Open5e v2 API client exclusively
- **AND** no D&D 5e API client is referenced or instantiated
- **AND** source filtering is limited to "open5e_v2" and "orcbrew" sources

#### Scenario: Source filtering excludes dnd5e_api
- **WHEN** list_documents tool is invoked with source filtering
- **THEN** "dnd5e_api" is not a valid source option
- **AND** only "open5e_v2" and "orcbrew" are accepted source values
