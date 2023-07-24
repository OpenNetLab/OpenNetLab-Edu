from heapq import heappush, heappop
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    NamedTuple,
    Union,
)

from ..core import BoundClass, Environment
from ..resources import base


class StorePut(base.Put):
    """Request to put item into the store. The request is triggered once
    there is space for the item in the store.

    """

    def __init__(self, store: 'Store', item: Any):
        self.item = item
        """The item to put into the store."""
        super().__init__(store)


class StoreGet(base.Get):
    """Request to get an item from the store. The request is triggered
    once there is an item available in the store.

    """


class FilterStoreGet(StoreGet):
    """Request to get an item from the store matching the filter. The request
    is triggered once there is such an item available in the store.

    """

    def __init__(
        self,
        resource: 'FilterStore',
        filter: Callable[[Any], bool] = lambda item: True,
    ):
        self.filter = filter
        """The filter function to filter items in the store."""
        super().__init__(resource)


class Store(base.BaseResource):
    """Resource with capacity slots for storing arbitrary objects. By
    default, the capacity is unlimited and objects are put and retrieved from
    the store in a first-in first-out order.

    """

    def __init__(
        self, env: Environment, capacity: Union[float, int] = float('inf')
    ):
        if capacity <= 0:
            raise ValueError('"capacity" must be > 0.')

        super().__init__(env, capacity)

        self.items: List[Any] = []
        """List of the items available in the store."""

    if TYPE_CHECKING:

        def put(  # type: ignore[override] # noqa: F821
            self, item: Any
        ) -> StorePut:
            """Request to put *item* into the store."""
            return StorePut(self, item)

        def get(self) -> StoreGet:  # type: ignore[override] # noqa: F821
            """Request to get an *item* out of the store."""
            return StoreGet(self)

    else:
        put = BoundClass(StorePut)
        get = BoundClass(StoreGet)

    def _do_put(self, event: StorePut) -> bool:
        if len(self.items) < self._capacity:
            self.items.append(event.item)
            event.succeed()
            return True
        else:
            return False

    def _do_get(self, event: StoreGet) -> bool:
        if self.items:
            event.succeed(self.items.pop(0))
            return True
        else:
            return False


class PriorityItem(NamedTuple):
    """Wrap an arbitrary item with an orderable priority."""

    priority: Any
    item: Any

    def __lt__(self, other: 'PriorityItem') -> bool:
        return self.priority < other.priority


class PriorityStore(Store):
    """Use heap and PriorityItem to maintain order of the item list """

    def _do_put(self, event: StorePut) -> bool:
        if len(self.items) < self._capacity:
            heappush(self.items, event.item)
            event.succeed()
            return True
        else:
            return False

    def _do_get(self, event: StoreGet) -> bool:
        if self.items:
            event.succeed(heappop(self.items))
            return True
        else:
            return False


class FilterStore(Store):
    """Use filter function to get from store"""

    if TYPE_CHECKING:

        def get(self, filter: Callable[[Any], bool] = lambda item: True) -> FilterStoreGet:
            return FilterStoreGet(self, filter)

    else:
        get = BoundClass(FilterStoreGet)

    def _do_get(self, event: FilterStoreGet) -> bool:
        for item in self.items:
            if event.filter(item):
                self.items.remove(item)
                event.succeed(item)
                break
        return True
