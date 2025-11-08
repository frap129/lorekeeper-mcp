# marqo-infrastructure Specification

**Spec ID**: `marqo-infrastructure`
**Change**: `2025-11-08-replace-sqlite-with-marqo`
**Status**: Proposed

## Purpose

Define infrastructure requirements, deployment configuration, and operational procedures for running Marqo as LoreKeeper's caching and search backend.

## ADDED Requirements

### Requirement: Docker-based Marqo deployment

The system SHALL provide Docker configuration for running Marqo locally and in production.

**Rationale**: Marqo requires a separate service; Docker simplifies deployment and ensures consistent environments.

#### Scenario: Docker Compose for local development

**Given** a developer has Docker installed
**When** they run `docker-compose up -d marqo`
**Then** Marqo service starts on port 8882
**And** the service passes health checks
**And** data is persisted in a Docker volume `marqo-data`

#### Scenario: Marqo container health check

**Given** Marqo container is running
**When** Docker health check runs
**Then** `curl http://localhost:8882/health` returns 200
**And** Docker reports the container as "healthy"
**And** health checks run every 10 seconds

#### Scenario: Marqo data persistence

**Given** Marqo container is running with volume `marqo-data`
**When** documents are indexed
**And** the container is stopped and restarted
**Then** indexed documents are still available
**And** no re-indexing is required

---

### Requirement: Environment-based configuration

The system SHALL support environment-specific Marqo configuration for different deployment environments.

**Rationale**: Different environments (dev, staging, prod) require different Marqo endpoints and settings.

#### Scenario: Configure Marqo URL for production

**Given** a production environment
**When** `MARQO_URL=http://marqo-prod.internal:8882` is set
**Then** the application connects to the production Marqo instance
**And** no localhost connections are attempted

#### Scenario: Configure Marqo timeout

**Given** a high-latency environment
**When** `MARQO_TIMEOUT=60` is set
**Then** Marqo requests wait up to 60 seconds before timing out
**And** slow vector searches complete successfully

#### Scenario: Configure batch size

**Given** a resource-constrained environment
**When** `MARQO_BATCH_SIZE=50` is set
**Then** bulk indexing operations use batches of 50 documents
**And** memory usage is reduced during bulk operations

---

### Requirement: Marqo service dependencies

The system SHALL document and validate Marqo service requirements.

**Rationale**: Users need to know system requirements before deploying Marqo.

#### Scenario: Document minimum system requirements

**Given** the deployment documentation
**When** a user reads the Marqo setup section
**Then** minimum requirements are clearly stated:
- Docker 20.10+ or Podman 3.0+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space minimum
- CPU with AVX2 support (for embedding inference)

#### Scenario: Validate Docker availability

**Given** a deployment script or setup guide
**When** it checks for prerequisites
**Then** it verifies Docker/Podman is installed
**And** provides installation instructions if missing

---

### Requirement: Network configuration

The system SHALL define network requirements and port configuration for Marqo service.

**Rationale**: Clear network requirements prevent connectivity issues and security misconfigurations.

#### Scenario: Default port configuration

**Given** Marqo is deployed with default settings
**When** the service starts
**Then** Marqo listens on port 8882
**And** the LoreKeeper application connects to `localhost:8882`

#### Scenario: Custom port configuration

**Given** port 8882 is already in use
**When** Marqo is started with `MARQO_PORT=9000`
**And** `MARQO_URL=http://localhost:9000` is configured
**Then** Marqo listens on port 9000
**And** the application connects successfully

#### Scenario: Network isolation for security

**Given** a production deployment
**When** Marqo is deployed
**Then** Marqo is only accessible on a private network
**And** no external internet access to Marqo is allowed
**And** firewall rules restrict access to authorized clients only

---

### Requirement: Startup and initialization procedures

The system SHALL define startup procedures for initializing Marqo indexes on first run.

**Rationale**: Clear startup process ensures indexes are ready before serving requests.

#### Scenario: Initialize indexes on server startup

**Given** the LoreKeeper server is starting
**When** the `lifespan` startup function runs
**Then** `init_indexes()` is called
**And** all entity type indexes are created (if they don't exist)
**And** the server waits for index creation to complete
**And** the server is marked as ready

#### Scenario: Skip initialization if indexes exist

**Given** Marqo already has indexes for all entity types
**When** the server starts
**Then** `init_indexes()` detects existing indexes
**And** no duplicate indexes are created
**And** startup completes quickly (<5 seconds)

#### Scenario: Startup fails gracefully if Marqo unavailable

**Given** Marqo service is not running
**When** the server attempts to start
**Then** a warning is logged: "Marqo unavailable - cache will fallback to API"
**And** the server still starts successfully
**And** health check reports Marqo as unhealthy
**And** queries fall back to direct API calls

---

### Requirement: Monitoring and observability

The system SHALL provide monitoring capabilities for Marqo service health and performance.

**Rationale**: Operators need visibility into Marqo status, performance, and issues.

#### Scenario: Health check endpoint

**Given** the LoreKeeper server is running
**When** a health check is requested
**Then** the response includes Marqo health status:
```json
{
  "status": "healthy",
  "marqo": {
    "available": true,
    "url": "http://localhost:8882",
    "indexes": 11,
    "response_time_ms": 15
  }
}
```

#### Scenario: Log Marqo connection status

**Given** the server is starting
**When** Marqo connection is established
**Then** an INFO log is written: "Marqo client connected to http://localhost:8882"
**And** index count is logged: "Found 11 Marqo indexes"

#### Scenario: Log Marqo errors

**Given** a Marqo request fails
**When** the error is caught
**Then** a WARNING log is written with error details
**And** the error includes the failed operation (search, index, get)
**And** the error includes suggested remediation steps

---

### Requirement: Backup and disaster recovery

The system SHALL document backup procedures for Marqo data.

**Rationale**: Operators need to protect against data loss and recover from failures.

#### Scenario: Document backup procedures

**Given** the operational documentation
**When** an operator reads the backup section
**Then** backup procedures are documented:
- Marqo data location: `/opt/marqo/data` (in container)
- Backup method: Docker volume backup or filesystem snapshot
- Restore procedure: Stop container, restore volume, restart

#### Scenario: Rebuild from source APIs

**Given** Marqo data is lost or corrupted
**When** the operator runs the migration script
**Then** all entities are re-fetched from Open5e APIs
**And** all indexes are rebuilt
**And** the system returns to full functionality
**And** no permanent data loss occurs (APIs are source of truth)

---

### Requirement: Resource management

The system SHALL define resource limits and scaling considerations for Marqo.

**Rationale**: Prevent resource exhaustion and guide capacity planning.

#### Scenario: Document resource recommendations

**Given** deployment documentation
**When** sizing Marqo infrastructure
**Then** recommended resources are provided:
- 8GB RAM for < 10,000 documents
- 16GB RAM for < 50,000 documents
- 2-4 CPU cores for production
- 20-50GB disk space depending on entity count

#### Scenario: Memory limits in Docker

**Given** Docker Compose configuration
**When** Marqo service is defined
**Then** memory limits are set appropriately:
```yaml
services:
  marqo:
    mem_limit: 8g
    mem_reservation: 4g
```

---

### Requirement: Security configuration

The system SHALL define security requirements for Marqo deployment.

**Rationale**: Protect Marqo from unauthorized access and secure data in transit.

#### Scenario: Network isolation

**Given** a production deployment
**When** Marqo is configured
**Then** Marqo only accepts connections from LoreKeeper application
**And** Marqo is not exposed to the public internet
**And** firewall rules enforce network isolation

#### Scenario: No authentication required for local development

**Given** a local development environment
**When** Marqo runs on localhost
**Then** no authentication is required
**And** connections are over HTTP (not HTTPS)
**And** this is documented as development-only

#### Scenario: Production security recommendations

**Given** production deployment documentation
**When** an operator reads security guidelines
**Then** recommendations include:
- Run Marqo on private network
- Use VPN or bastion host for admin access
- Consider TLS/SSL for production (if available in Marqo)
- Restrict port 8882 to application subnet only

---

### Requirement: Upgrade and maintenance procedures

The system SHALL document procedures for upgrading Marqo and performing maintenance.

**Rationale**: Operators need safe procedures for upgrades without data loss or downtime.

#### Scenario: Document upgrade procedure

**Given** a new Marqo version is available
**When** an operator follows the upgrade guide
**Then** the procedure includes:
1. Backup current Marqo data
2. Stop LoreKeeper application
3. Stop Marqo container
4. Pull new Marqo image
5. Start Marqo with same volume
6. Verify index health
7. Start LoreKeeper application

#### Scenario: Rolling restart

**Given** Marqo needs to be restarted
**When** the operator restarts the container
**Then** data persists in Docker volume
**And** indexes are immediately available after restart
**And** no re-indexing is required
**And** downtime is < 30 seconds

---

## MODIFIED Requirements

None - Infrastructure is new for Marqo.

---

## REMOVED Requirements

### Requirement: SQLite file location

**Removed**: No SQLite database file to manage.

**Migration**: SQLite database file (`data/cache.db`) can be archived or deleted after Marqo migration is complete.

---

## Cross-References

- Related Spec: `marqo-cache-implementation` - Defines how to use deployed Marqo service
- Related Spec: `marqo-semantic-search` - Semantic search depends on healthy Marqo service

---

## Notes

- Marqo requires Docker/Podman - no native installation option
- Marqo data is stored in `/opt/marqo/data` inside container
- Default Marqo image: `marqoai/marqo:latest` (can pin specific version)
- Marqo supports GPU acceleration (optional, requires CUDA setup)
- For large deployments, consider Marqo Cloud or managed hosting
- Marqo does not support authentication/authorization natively
