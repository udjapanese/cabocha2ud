"""List Object based Key."""

from typing import Optional, TypeVar

T = TypeVar("T")


class ListBasedKey(list[T]):
    """List Content with str."""

    def __init__(self, /, *_: tuple, **kwargs: dict) -> None:
        """Init."""
        super().__init__()
        self.key_order: list[str] = []
        if kwargs.get("keys") and kwargs.get("objs"):
            assert isinstance(kwargs["keys"], list)
            assert isinstance(kwargs["objs"], list)
            assert len(kwargs["keys"]) == len(kwargs["objs"])
            for kkk, vvv in zip(kwargs["keys"], kwargs["objs"]):
                assert isinstance(kkk, str)
                super().append(vvv)
                self.key_order.append(kkk)
        assert len(self) == len(self.key_order)

    def __repr__(self) -> str:
        """Repr."""
        aaa = ", ".join([k + ":" + str(v) for k, v in zip(self.keys(), self)])
        return f"[{aaa}]"

    def set_item(self, key: str, obj: T) -> None:
        """Set item by key."""
        assert self.include_key(key)
        self[self.key_order.index(key)] = obj

    def append(self, _: T) -> None:
        """Append object."""
        msg = "Do not use append function"
        raise ValueError(msg)

    def __str__(self) -> str:
        """Get string."""
        return self.__repr__()

    def get_dict(self) -> dict[str, T]:
        """Get dict."""
        return dict(zip(self.keys(), self))

    def get_item(self, key: str) -> Optional[T]:
        """Get item from key."""
        if key not in self.key_order:
            return None
        return self[self.key_order.index(key)]

    def keys(self) -> list[str]:
        """Return keys."""
        return list(self.key_order)

    def append_with_key(self, key: str, obj: T) -> None:
        """Append with key."""
        self.key_order.append(key)
        super().append(obj)

    def insert_with_key(self, pos:int, key: str, obj: T) -> None:
        """Insert position with key."""
        super().insert(pos, obj)
        self.key_order.insert(pos, key)

    def include_key(self, key: str) -> bool:
        """Check including key."""
        return key in self.key_order

    def remove_obj_by_key(self, key: str) -> None:
        """Remove key."""
        assert self.include_key(key)
        self.remove(self[self.key_order.index(key)])
        self.key_order.remove(key)


def _main() -> None:
    """Do main function."""
    abc: ListBasedKey[int] = ListBasedKey()
    abc.append_with_key("a", 1)
    abc.append_with_key("b", 1)


if __name__ == "__main__":
    _main()
