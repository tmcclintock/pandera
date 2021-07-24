"""Pandera data types."""
# pylint:disable=too-many-ancestors
import dataclasses
import inspect
from abc import ABC
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)


class DataType(ABC):
    """Base class of all Pandera data types."""

    continuous: Optional[bool] = None
    """Whether the number data type is continuous."""

    def __init__(self):
        if self.__class__ is DataType:
            raise TypeError(
                f"{self.__class__.__name__} may not be instantiated."
            )

    def coerce(self, data_container: Any):
        """Coerce data container to the data type."""
        raise NotImplementedError()

    def __call__(self, data_container: Any):
        """Coerce data container to the data type."""
        return self.coerce(data_container)

    def check(self, pandera_dtype: "DataType") -> bool:
        """Check that pandera :class:`~pandera.dtypes.DataType` are
        equivalent."""
        return self == pandera_dtype

    def __repr__(self) -> str:
        return f"DataType({str(self)})"

    def __str__(self) -> str:
        raise NotImplementedError()

    def __hash__(self) -> int:
        raise NotImplementedError()


_Dtype = TypeVar("_Dtype", bound=DataType)
_DataTypeClass = Type[_Dtype]


def immutable(
    pandera_dtype_cls: Optional[_DataTypeClass] = None, **dataclass_kwargs: Any
) -> Union[_DataTypeClass, Callable[[_DataTypeClass], _DataTypeClass]]:
    """:func:`dataclasses.dataclass` decorator with different default values:
    `frozen=True`, `init=False`, `repr=False`.

    In addition, `init=False` disables inherited `__init__` method to ensure
    the DataType's default attributes are not altered during initialization.

    :param dtype: :class:`DataType` to decorate.
    :param dataclass_kwargs: Keywords arguments forwarded to
        :func:`dataclasses.dataclass`.
    :returns: Immutable :class:`DataType`
    """
    kwargs = {"frozen": True, "init": False, "repr": False}
    kwargs.update(dataclass_kwargs)

    def _wrapper(pandera_dtype_cls: _DataTypeClass) -> _DataTypeClass:
        immutable_dtype = dataclasses.dataclass(**kwargs)(pandera_dtype_cls)
        if not kwargs["init"]:

            def __init__(self):  # pylint:disable=unused-argument
                pass

            # delattr(immutable_dtype, "__init__") doesn't work because
            # super.__init__ would still exist.
            setattr(immutable_dtype, "__init__", __init__)

        return immutable_dtype

    if pandera_dtype_cls is None:
        return _wrapper

    return _wrapper(pandera_dtype_cls)


###############################################################################
# number
###############################################################################


@immutable
class _Number(DataType):
    """Semantic representation of a numeric data type."""

    exact: Optional[bool] = None
    """Whether the data type is an exact representation of a number."""

    def check(self, pandera_dtype: "DataType") -> bool:
        if self.__class__ is _Number:
            return isinstance(pandera_dtype, _Number)
        return super().check(pandera_dtype)


@immutable
class _PhysicalNumber(_Number):
    bit_width: Optional[int] = None
    """Number of bits used by the machine representation."""
    _base_name: Optional[str] = dataclasses.field(
        default=None, init=False, repr=False
    )

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, type(self)):
            return obj.bit_width == self.bit_width
        return super().__eq__(obj)

    def __str__(self) -> str:
        return f"{self._base_name}{self.bit_width}"


###############################################################################
# boolean
###############################################################################


@immutable
class Bool(_Number):
    """Semantic representation of a boolean data type."""

    def __str__(self) -> str:
        return "bool"


###############################################################################
# signed integer
###############################################################################


@immutable(eq=False)
class Int(_PhysicalNumber):  # type: ignore
    """Semantic representation of an integer data type."""

    _base_name = "int"
    exact = True
    bit_width = 64
    signed: bool = dataclasses.field(default=True, init=False)
    """Whether the integer data type is signed."""

    def check(self, pandera_dtype: DataType) -> bool:
        return (
            isinstance(pandera_dtype, Int)
            and self.signed == pandera_dtype.signed
            and self.bit_width == pandera_dtype.bit_width
        )

    def __str__(self) -> str:
        if self.__class__ is Int:
            return "int"
        return super().__str__()


@immutable
class Int64(Int):
    """Semantic representation of an integer data type stored in 64 bits."""

    bit_width = 64


@immutable
class Int32(Int64):
    """Semantic representation of an integer data type stored in 32 bits."""

    bit_width = 32


@immutable
class Int16(Int32):
    """Semantic representation of an integer data type stored in 16 bits."""

    bit_width = 16


@immutable
class Int8(Int16):
    """Semantic representation of an integer data type stored in 8 bits."""

    bit_width = 8


###############################################################################
# unsigned integer
###############################################################################


@immutable
class UInt(Int):
    """Semantic representation of an unsigned integer data type."""

    _base_name = "uint"
    signed: bool = dataclasses.field(default=False, init=False)

    def __str__(self) -> str:
        if self.__class__ is UInt:
            return "uint"
        return super().__str__()


@immutable
class UInt64(UInt):
    """Semantic representation of an unsigned integer data type stored
    in 64 bits."""

    bit_width = 64


@immutable
class UInt32(UInt64):
    """Semantic representation of an unsigned integer data type stored
    in 32 bits."""

    bit_width = 32


@immutable
class UInt16(UInt32):
    """Semantic representation of an unsigned integer data type stored
    in 16 bits."""

    bit_width = 16


@immutable
class UInt8(UInt16):
    """Semantic representation of an unsigned integer data type stored
    in 8 bits."""

    bit_width = 8


###############################################################################
# float
###############################################################################


@immutable(eq=False)
class Float(_PhysicalNumber):  # type: ignore
    """Semantic representation of a floating data type."""

    _base_name = "float"
    continuous = True
    exact = False
    bit_width = 64

    def check(self, pandera_dtype: DataType) -> bool:
        return (
            isinstance(pandera_dtype, Float)
            and self.bit_width == pandera_dtype.bit_width
        )

    def __str__(self) -> str:
        if self.__class__ is Float:
            return "float"
        return super().__str__()


@immutable
class Float128(Float):
    """Semantic representation of a floating data type stored in 128 bits."""

    bit_width = 128


@immutable
class Float64(Float128):
    """Semantic representation of a floating data type stored in 64 bits."""

    bit_width = 64


@immutable
class Float32(Float64):
    """Semantic representation of a floating data type stored in 32 bits."""

    bit_width = 32


@immutable
class Float16(Float32):
    """Semantic representation of a floating data type stored in 16 bits."""

    bit_width = 16


###############################################################################
# complex
###############################################################################


@immutable(eq=False)
class Complex(_PhysicalNumber):  # type: ignore
    """Semantic representation of a complex number data type."""

    _base_name = "complex"
    bit_width = 128

    def check(self, pandera_dtype: DataType) -> bool:
        return (
            isinstance(pandera_dtype, Complex)
            and self.bit_width == pandera_dtype.bit_width
        )

    def __str__(self) -> str:
        if self.__class__ is Complex:
            return "complex"
        return super().__str__()


@immutable
class Complex256(Complex):
    """Semantic representation of a complex number data type stored
    in 256 bits."""

    bit_width = 256


@immutable
class Complex128(Complex):
    """Semantic representation of a complex number data type stored
    in 128 bits."""

    bit_width = 128


@immutable
class Complex64(Complex128):
    """Semantic representation of a complex number data type stored
    in 64 bits."""

    bit_width = 64


###############################################################################
# nominal
###############################################################################


@immutable(init=True)
class Category(DataType):  # type: ignore
    """Semantic representation of a categorical data type."""

    categories: Optional[Tuple[Any]] = None  # tuple to ensure safe hash
    ordered: bool = False

    def __init__(
        self, categories: Optional[Iterable[Any]] = None, ordered: bool = False
    ):
        # Define __init__ to avoid exposing pylint errors to end users.
        super().__init__()
        if categories is not None:
            object.__setattr__(self, "categories", tuple(categories))
        object.__setattr__(self, "ordered", ordered)

    def check(self, pandera_dtype: "DataType") -> bool:
        if isinstance(pandera_dtype, Category) and (
            self.categories is None or pandera_dtype.categories is None
        ):
            # Category without categories is a superset of any Category
            # Allow end-users to not list categories when validating.
            return True

        return super().check(pandera_dtype)

    def __str__(self) -> str:
        return "category"


@immutable
class String(DataType):
    """Semantic representation of a string data type."""

    def __str__(self) -> str:
        return "string"


###############################################################################
# time
###############################################################################


@immutable
class Date(DataType):
    """Semantic representation of a date data type."""

    def __str__(self) -> str:
        return "date"


@immutable
class Timestamp(Date):
    """Semantic representation of a timestamp data type."""

    def __str__(self) -> str:
        return "timestamp"


DateTime = Timestamp


@immutable
class Timedelta(DataType):
    """Semantic representation of a delta time data type."""

    def __str__(self) -> str:
        return "timedelta"


###############################################################################
# Utilities
###############################################################################


def is_subdtype(
    arg1: Union[DataType, Type[DataType]],
    arg2: Union[DataType, Type[DataType]],
) -> bool:
    """Returns True if first argument is lower/equal in DataType hierarchy."""
    arg1_cls = arg1 if inspect.isclass(arg1) else arg1.__class__
    arg2_cls = arg2 if inspect.isclass(arg2) else arg2.__class__
    return issubclass(arg1_cls, arg2_cls)  # type: ignore


def is_int(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is an integer."""
    return is_subdtype(pandera_dtype, Int)


def is_uint(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is
    an unsigned integer."""
    return is_subdtype(pandera_dtype, UInt)


def is_float(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a float."""
    return is_subdtype(pandera_dtype, Float)


def is_complex(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a complex number."""
    return is_subdtype(pandera_dtype, Complex)


def is_numeric(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a complex number."""
    return is_subdtype(pandera_dtype, _Number)


def is_bool(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a boolean."""
    return is_subdtype(pandera_dtype, Bool)


def is_string(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a string."""
    return is_subdtype(pandera_dtype, String)


def is_category(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a category."""
    return is_subdtype(pandera_dtype, Category)


def is_datetime(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a datetime."""
    return is_subdtype(pandera_dtype, DateTime)


def is_timedelta(pandera_dtype: Union[DataType, Type[DataType]]) -> bool:
    """Return True if :class:`pandera.dtypes.DataType` is a timedelta."""
    return is_subdtype(pandera_dtype, Timedelta)
