from heapq import heappush, heappop
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Union,
    List,
    Optional,
    NamedTuple
)
from ..core import (
    Environment,
    BoundClass
)

from .base import Put, Get, BaseResource


class StorePut(Put):
    def __init__(self, store: 'Store', item: Any):
        self.item = item
        super().__init__(store)


class StoreGet(Get):
    pass


class Store(BaseResource):
    def __init__(self,
                 env: Environment,
                 capacity: Union[float, int]):
        super().__init__(env, capacity)
        # the items availabe in this store
        self.items: List[Any] = []

    if TYPE_CHECKING:
        def put(self, item) -> StorePut:
            return StorePut(self, item)

        def get(self, item) -> StoreGet:
            return StoreGet(self)
    else:
        put = BoundClass(StorePut)
        get = BoundClass(StoreGet)

    def _do_put(self, event: StorePut) -> Optional[bool]:
        if len(self.items) < self._capacity:
            self.items.append(event)
            event.succeed()
            return True
        return None

    def _do_get(self, event: StoreGet):
        if self.items:
            event.succeed(self.items.pop(0))
            return True
        return None


class PriorityItem(NamedTuple):
    priority: Any
    item: Any

    def __lt__(self, other: 'PriorityItem') -> bool:
        return self.priority < other.priority


class PriorityStore(Store):
    def __init__(self,
                 env: Environment,
                 capacity: Union[float, int]):
        super().__init__(env, capacity)
        # the items availabe in this store
        self.items: List[Any] = []

    def _do_put(self, event: StorePut) -> Optional[bool]:
        if len(self.items) < self._capacity:
            heappush(self.items, event.item)
            return True
        return None

    def _do_get(self, event: StoreGet):
        if self.items:
            event.succeed(heappop(self.items))
            return True
        return None


class FilterStoreGet(Get):
    def __init__(self,
                 store: 'FilterStore',
                 filter: Callable[[Any], bool] = lambda item: True):
        self.filter = filter
        super().__init__(store)


class FilterStore(Store):
    if TYPE_CHECKING:
        def get(self,
                filter: Callable[[Any], bool] = lambda item: True) -> FilterStoreGet:
            return FilterStoreGet(self, filter)
    else:
        get = BoundClass(FilterStoreGet)

    def _do_get(self, event: FilterStoreGet) -> Optional[bool]:
        for item in self.items:
            if event.filter(item):
                self.items.remove(item)
                event.succeed()
                break
        return True
