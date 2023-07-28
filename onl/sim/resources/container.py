from typing import TYPE_CHECKING, Union

from ..core import Environment, BoundClass
from .base import Put, Get, BaseResource

ContainerAmount = Union[int, float]


class ContainerPut(Put):
    def __init__(self, container: 'Container', amount: ContainerAmount):
        if amount <= 0:
            raise ValueError(f'amount(={amount}) must be > 0.')
        self.amount = amount
        super().__init__(container)


class ContainerGet(Get):
    def __init__(self, container: 'Container', amount: ContainerAmount):
        if amount <= 0:
            raise ValueError(f'amount(={amount}) must be > 0.')
        self.amount = amount
        super().__init__(container)


class Container(BaseResource):
    """Resource containing up to capacity of matter which may either be
    continuous (like water) or discrete (like apples). It supports requests to
    put or get matter into/from the container.

    The capacity defines the size of the container. By default, a container
    is of unlimited size. The initial amount of matter is specified by *init*
    and defaults to 0.

    """

    def __init__(
        self,
        env: Environment,
        capacity: ContainerAmount = float('inf'),
        init: ContainerAmount = 0,
    ):
        # Rasei a ValueError for invalid conditions
        if capacity <= 0:
            raise ValueError('"capacity" must be > 0.')
        if init < 0:
            raise ValueError('"init" must be >= 0.')
        if init > capacity:
            raise ValueError('"init" must be <= "capacity".')

        super().__init__(env, capacity)

        self._level = init

    @property
    def level(self) -> ContainerAmount:
        """The current amount of the matter in the container."""
        return self._level

    if TYPE_CHECKING:

        def put(  # type: ignore[override] # noqa: F821
            self, amount: ContainerAmount
        ) -> ContainerPut:
            """Request to put *amount* of matter into the container."""
            return ContainerPut(self, amount)

        def get(  # type: ignore[override] # noqa: F821
            self, amount: ContainerAmount
        ) -> ContainerGet:
            """Request to get *amount* of matter out of the container."""
            return ContainerGet(self, amount)

    else:
        put = BoundClass(ContainerPut)
        get = BoundClass(ContainerGet)

    def _do_put(self, event: ContainerPut) -> bool:
        if self._capacity - self._level >= event.amount:
            self._level += event.amount
            event.succeed()
            return True
        else:
            return False

    def _do_get(self, event: ContainerGet) -> bool:
        if self._level >= event.amount:
            self._level -= event.amount
            event.succeed()
            return True
        else:
            return False
