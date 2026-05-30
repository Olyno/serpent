"""
AST nodes for the Vyper Language Server.

Dataclasses representing each node type in the Vyper AST,
with position information (line, column) for LSP.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass(eq=False)
class BaseNode:
    """Base node for the Vyper AST with position information."""

    ast_type: str
    src: Optional[str] = None
    lineno: int = 0
    col_offset: int = 0
    end_lineno: int = 0
    end_col_offset: int = 0
    node_id: Optional[int] = None
    parent: Optional["BaseNode"] = field(default=None, repr=False, compare=False)

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseNode):
            return NotImplemented
        return self.node_id == other.node_id


@dataclass(eq=False)
class TopLevel(BaseNode):
    """Top-level node with a name and a body."""

    name: Optional[str] = None
    body: List[Any] = field(default_factory=list)
    doc_string: Optional[Any] = None


@dataclass(eq=False)
class Module(TopLevel):
    """Root node representing a Vyper module/file."""

    path: Optional[str] = None
    body: List[Any] = field(default_factory=list)
    resolved_path: Optional[str] = None
    source_id: Optional[int] = None
    is_interface: Optional[bool] = None
    settings: Optional[Any] = None
    source_sha256sum: Optional[str] = None


@dataclass(eq=False)
class FunctionDef(TopLevel):
    """Vyper function definition."""

    args: Optional[Any] = None
    returns: Optional[Any] = None
    decorator_list: List[Any] = field(default_factory=list)
    pos: Optional[Any] = None


@dataclass(eq=False)
class DocStr(BaseNode):
    """Docstring."""

    value: str = ""


@dataclass(eq=False)
class arguments(BaseNode):
    """Function arguments."""

    args: List[Any] = field(default_factory=list)
    defaults: List[Any] = field(default_factory=list)
    default: Optional[Any] = None


@dataclass(eq=False)
class arg(BaseNode):
    """A function argument."""

    arg: str = ""
    annotation: Optional[Any] = None


@dataclass(eq=False)
class Return(BaseNode):
    """Return statement."""

    value: Optional[Any] = None


@dataclass(eq=False)
class Expr(BaseNode):
    """Expression wrapper."""

    value: Any = None


@dataclass(eq=False)
class NamedExpr(BaseNode):
    """Named expression (walrus)."""

    target: Any = None
    value: Any = None


@dataclass(eq=False)
class Log(BaseNode):
    """Log statement."""

    value: Any = None


@dataclass(eq=False)
class FlagDef(TopLevel):
    """Flag definition (enum)."""

    pass


@dataclass(eq=False)
class EventDef(TopLevel):
    """Event definition."""

    pass


@dataclass(eq=False)
class InterfaceDef(TopLevel):
    """Interface definition."""

    pass


@dataclass(eq=False)
class StructDef(TopLevel):
    """Struct definition."""

    pass


@dataclass(eq=False)
class ExprNode(BaseNode):
    """Base expression node."""

    pass


@dataclass(eq=False)
class Constant(ExprNode):
    """Constant value."""

    value: Any = None


@dataclass(eq=False)
class Num(Constant):
    """Generic number."""

    pass


@dataclass(eq=False)
class Int(Num):
    """Integer."""

    pass


@dataclass(eq=False)
class Decimal(Num):
    """Decimal number."""

    pass


@dataclass(eq=False)
class Hex(Constant):
    """Hexadecimal value."""

    value: str = ""


@dataclass(eq=False)
class Str(Constant):
    """String."""

    value: str = ""


@dataclass(eq=False)
class Bytes(Constant):
    """Bytes."""

    value: bytes = b""


@dataclass(eq=False)
class HexBytes(BaseNode):
    """Hexadecimal bytes."""

    value: Optional[bytes] = None


@dataclass(eq=False)
class ListNode(BaseNode):
    """List (avoids conflict with built-in list)."""

    elements: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class TupleNode(BaseNode):
    """Tuple (avoids conflict with built-in tuple)."""

    elements: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class NameConstant(BaseNode):
    """Named constant (True, False, None)."""

    value: Any = None


@dataclass(eq=False)
class Ellipsis(BaseNode):
    """Ellipsis (...)."""

    value: Optional[Any] = None


@dataclass(eq=False)
class DictNode(BaseNode):
    """Dictionary (avoids conflict with built-in Dict)."""

    keys: List[Any] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class Name(BaseNode):
    """Reference to an identifier."""

    id: str = ""


@dataclass(eq=False)
class UnaryOp(BaseNode):
    """Unary operation."""

    op: Any = None
    operand: Any = None


@dataclass(eq=False)
class Operator(BaseNode):
    """Operator."""

    pass


@dataclass(eq=False)
class USub(BaseNode):
    """Unary minus operator."""

    pass


@dataclass(eq=False)
class Not(BaseNode):
    """Not operator."""

    pass


@dataclass(eq=False)
class Invert(BaseNode):
    """Invert operator."""

    pass


@dataclass(eq=False)
class BinOp(BaseNode):
    """Binary operation."""

    left: Any = None
    op: Any = None
    right: Any = None


@dataclass(eq=False)
class Add(BaseNode):
    pass


@dataclass(eq=False)
class Sub(BaseNode):
    pass


@dataclass(eq=False)
class Mult(BaseNode):
    pass


@dataclass(eq=False)
class Div(BaseNode):
    pass


@dataclass(eq=False)
class FloorDiv(BaseNode):
    pass


@dataclass(eq=False)
class Mod(BaseNode):
    pass


@dataclass(eq=False)
class Pow(BaseNode):
    pass


@dataclass(eq=False)
class BitAnd(BaseNode):
    pass


@dataclass(eq=False)
class BitOr(BaseNode):
    pass


@dataclass(eq=False)
class BitXor(BaseNode):
    pass


@dataclass(eq=False)
class LShift(BaseNode):
    pass


@dataclass(eq=False)
class RShift(BaseNode):
    pass


@dataclass(eq=False)
class BoolOp(BaseNode):
    """Boolean operation."""

    op: Any = None
    values: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class And(BaseNode):
    pass


@dataclass(eq=False)
class Or(BaseNode):
    pass


@dataclass(eq=False)
class Compare(BaseNode):
    """Comparison."""

    left: Any = None
    op: Any = None
    right: Any = None


@dataclass(eq=False)
class Eq(BaseNode):
    pass


@dataclass(eq=False)
class NotEq(BaseNode):
    pass


@dataclass(eq=False)
class Lt(BaseNode):
    pass


@dataclass(eq=False)
class LtE(BaseNode):
    pass


@dataclass(eq=False)
class Gt(BaseNode):
    pass


@dataclass(eq=False)
class GtE(BaseNode):
    pass


@dataclass(eq=False)
class In(BaseNode):
    pass


@dataclass(eq=False)
class NotIn(BaseNode):
    pass


@dataclass(eq=False)
class Call(BaseNode):
    """Function call."""

    func: Any = None
    args: List[Any] = field(default_factory=list)
    keywords: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class ExtCall(BaseNode):
    """External call."""

    value: Any = None


@dataclass(eq=False)
class StaticCall(BaseNode):
    """Static call."""

    value: Any = None


@dataclass(eq=False)
class keyword(BaseNode):
    """Named argument (keyword)."""

    arg: Optional[str] = None
    value: Any = None


@dataclass(eq=False)
class Attribute(BaseNode):
    """Attribute access (e.g. self.foo)."""

    value: Any = None
    attr: str = ""


@dataclass(eq=False)
class Subscript(BaseNode):
    """Index access (e.g. arr[0])."""

    value: Any = None
    slice: Any = None


@dataclass(eq=False)
class Assign(BaseNode):
    """Simple assignment."""

    target: Any = None
    value: Any = None


@dataclass(eq=False)
class AnnAssign(BaseNode):
    """Annotated assignment (with type)."""

    target: Any = None
    annotation: Any = None
    value: Optional[Any] = None


@dataclass(eq=False)
class VariableDecl(BaseNode):
    """Vyper state variable declaration."""

    target: Any = None
    annotation: Any = None
    value: Optional[Any] = None
    is_constant: Optional[bool] = None
    is_public: Optional[bool] = None
    is_immutable: Optional[bool] = None
    is_transient: Optional[bool] = None
    is_reentrant: Optional[bool] = None


@dataclass(eq=False)
class AugAssign(BaseNode):
    """Augmented assignment (+=, -=, etc.)."""

    op: Any = None
    target: Any = None
    value: Any = None


@dataclass(eq=False)
class Raise(BaseNode):
    """Raise statement."""

    exc: Any = None


@dataclass(eq=False)
class Assert(BaseNode):
    """Assert statement."""

    test: Any = None
    msg: Any = None


@dataclass(eq=False)
class Pass(BaseNode):
    """Pass statement."""

    pass


@dataclass(eq=False)
class Import(BaseNode):
    """Simple import statement."""

    name: Optional[str] = None
    alias: Optional[str] = None
    import_info: Optional[Dict] = None


@dataclass(eq=False)
class ImportFrom(BaseNode):
    """Import from ... statement."""

    name: Optional[str] = None
    alias: Optional[str] = None
    level: Optional[int] = None
    module: Optional[str] = None
    import_info: Optional[Dict] = None


@dataclass(eq=False)
class ImplementsDecl(BaseNode):
    """Implements declaration."""

    annotation: Any = None


@dataclass(eq=False)
class UsesDecl(BaseNode):
    """Uses declaration."""

    annotation: Any = None


@dataclass(eq=False)
class InitializesDecl(BaseNode):
    """Initializes declaration."""

    annotation: Any = None


@dataclass(eq=False)
class ExportsDecl(BaseNode):
    """Exports declaration."""

    annotation: Any = None


@dataclass(eq=False)
class If(BaseNode):
    """If conditional statement."""

    test: Any = None
    body: List[Any] = field(default_factory=list)
    orelse: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class IfExp(BaseNode):
    """Conditional expression (ternary)."""

    test: Any = None
    body: Any = None
    orelse: Any = None


@dataclass(eq=False)
class For(BaseNode):
    """For loop."""

    target: Any = None
    iter: Any = None
    body: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class Break(BaseNode):
    """Break statement."""

    pass


@dataclass(eq=False)
class Continue(BaseNode):
    """Continue statement."""

    pass


# Mapping of AST types for JSON → dataclass conversion
AST_CLASS_MAP: Dict[str, Type[BaseNode]] = {
    cls.__name__: cls
    for cls in list(globals().values())
    if isinstance(cls, type) and issubclass(cls, BaseNode)
}
