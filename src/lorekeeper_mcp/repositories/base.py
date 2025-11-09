"""Repository base protocol and abstractions."""

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    """Protocol for repository implementations.

    Repositories provide a generic interface for accessing entities from
    various sources (APIs, cache, database) with consistent methods for
    retrieval and search.

    Type Parameters:
        T: The entity type this repository manages.
    """

    async def get_all(self) -> list[T]:
        """Retrieve all entities.

        Returns:
            A list of all entities of type T.
        """
        ...

    async def search(self, **filters: Any) -> list[T]:
        """Search for entities matching the given filters.

        Args:
            **filters: Arbitrary keyword arguments specifying search criteria.
                The specific filters supported depend on the entity type.

        Returns:
            A list of entities matching the filter criteria.
        """
        ...
