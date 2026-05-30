"""
Nœuds AST pour le Vyper Language Server.

Dataclasses représentant chaque type de nœud dans l'AST Vyper,
avec informations de position (ligne, colonne) pour le LSP.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass(eq=False)
class BaseNode:
    """Nœud de base pour l'AST Vyper avec informations de position."""

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
    """Nœud de haut niveau avec un nom et un corps."""

    name: Optional[str] = None
    body: List[Any] = field(default_factory=list)
    doc_string: Optional[Any] = None


@dataclass(eq=False)
class Module(TopLevel):
    """Nœud racine représentant un module/fichier Vyper."""

    path: Optional[str] = None
    body: List[Any] = field(default_factory=list)
    resolved_path: Optional[str] = None
    source_id: Optional[int] = None
    is_interface: Optional[bool] = None
    settings: Optional[Any] = None
    source_sha256sum: Optional[str] = None


@dataclass(eq=False)
class FunctionDef(TopLevel):
    """Définition de fonction Vyper."""

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
    """Arguments d'une fonction."""

    args: List[Any] = field(default_factory=list)
    defaults: List[Any] = field(default_factory=list)
    default: Optional[Any] = None


@dataclass(eq=False)
class arg(BaseNode):
    """Un argument de fonction."""

    arg: str = ""
    annotation: Optional[Any] = None


@dataclass(eq=False)
class Return(BaseNode):
    """Instruction return."""

    value: Optional[Any] = None


@dataclass(eq=False)
class Expr(BaseNode):
    """Expression wrapper."""

    value: Any = None


@dataclass(eq=False)
class NamedExpr(BaseNode):
    """Expression nommée (walrus)."""

    target: Any = None
    value: Any = None


@dataclass(eq=False)
class Log(BaseNode):
    """Instruction log."""

    value: Any = None


@dataclass(eq=False)
class FlagDef(TopLevel):
    """Définition de flag (enum)."""

    pass


@dataclass(eq=False)
class EventDef(TopLevel):
    """Définition d'événement."""

    pass


@dataclass(eq=False)
class InterfaceDef(TopLevel):
    """Définition d'interface."""

    pass


@dataclass(eq=False)
class StructDef(TopLevel):
    """Définition de structure."""

    pass


@dataclass(eq=False)
class ExprNode(BaseNode):
    """Nœud d'expression de base."""

    pass


@dataclass(eq=False)
class Constant(ExprNode):
    """Valeur constante."""

    value: Any = None


@dataclass(eq=False)
class Num(Constant):
    """Nombre générique."""

    pass


@dataclass(eq=False)
class Int(Num):
    """Entier."""

    pass


@dataclass(eq=False)
class Decimal(Num):
    """Nombre décimal."""

    pass


@dataclass(eq=False)
class Hex(Constant):
    """Valeur hexadécimale."""

    value: str = ""


@dataclass(eq=False)
class Str(Constant):
    """Chaîne de caractères."""

    value: str = ""


@dataclass(eq=False)
class Bytes(Constant):
    """Bytes."""

    value: bytes = b""


@dataclass(eq=False)
class HexBytes(BaseNode):
    """Bytes hexadécimaux."""

    value: Optional[bytes] = None


@dataclass(eq=False)
class ListNode(BaseNode):
    """Liste (évite le conflit avec built-in list)."""

    elements: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class TupleNode(BaseNode):
    """Tuple (évite le conflit avec built-in tuple)."""

    elements: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class NameConstant(BaseNode):
    """Constante nommée (True, False, None)."""

    value: Any = None


@dataclass(eq=False)
class Ellipsis(BaseNode):
    """Ellipsis (...)."""

    value: Optional[Any] = None


@dataclass(eq=False)
class DictNode(BaseNode):
    """Dictionnaire (évite le conflit avec built-in Dict)."""

    keys: List[Any] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class Name(BaseNode):
    """Référence à un identifiant."""

    id: str = ""


@dataclass(eq=False)
class UnaryOp(BaseNode):
    """Opération unaire."""

    op: Any = None
    operand: Any = None


@dataclass(eq=False)
class Operator(BaseNode):
    """Opérateur."""

    pass


@dataclass(eq=False)
class USub(BaseNode):
    """Opérateur moins unaire."""

    pass


@dataclass(eq=False)
class Not(BaseNode):
    """Opérateur not."""

    pass


@dataclass(eq=False)
class Invert(BaseNode):
    """Opérateur inversion."""

    pass


@dataclass(eq=False)
class BinOp(BaseNode):
    """Opération binaire."""

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
    """Opération booléenne."""

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
    """Comparaison."""

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
    """Appel de fonction."""

    func: Any = None
    args: List[Any] = field(default_factory=list)
    keywords: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class ExtCall(BaseNode):
    """Appel externe."""

    value: Any = None


@dataclass(eq=False)
class StaticCall(BaseNode):
    """Appel statique."""

    value: Any = None


@dataclass(eq=False)
class keyword(BaseNode):
    """Argument nommé (keyword)."""

    arg: Optional[str] = None
    value: Any = None


@dataclass(eq=False)
class Attribute(BaseNode):
    """Accès à un attribut (ex: self.foo)."""

    value: Any = None
    attr: str = ""


@dataclass(eq=False)
class Subscript(BaseNode):
    """Accès par index (ex: arr[0])."""

    value: Any = None
    slice: Any = None


@dataclass(eq=False)
class Assign(BaseNode):
    """Assignation simple."""

    target: Any = None
    value: Any = None


@dataclass(eq=False)
class AnnAssign(BaseNode):
    """Assignation annotée (avec type)."""

    target: Any = None
    annotation: Any = None
    value: Optional[Any] = None


@dataclass(eq=False)
class VariableDecl(BaseNode):
    """Déclaration de variable d'état Vyper."""

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
    """Assignation augmentée (+=, -=, etc.)."""

    op: Any = None
    target: Any = None
    value: Any = None


@dataclass(eq=False)
class Raise(BaseNode):
    """Instruction raise."""

    exc: Any = None


@dataclass(eq=False)
class Assert(BaseNode):
    """Instruction assert."""

    test: Any = None
    msg: Any = None


@dataclass(eq=False)
class Pass(BaseNode):
    """Instruction pass."""

    pass


@dataclass(eq=False)
class Import(BaseNode):
    """Instruction import simple."""

    name: Optional[str] = None
    alias: Optional[str] = None
    import_info: Optional[Dict] = None


@dataclass(eq=False)
class ImportFrom(BaseNode):
    """Instruction import from ... ."""

    name: Optional[str] = None
    alias: Optional[str] = None
    level: Optional[int] = None
    module: Optional[str] = None
    import_info: Optional[Dict] = None


@dataclass(eq=False)
class ImplementsDecl(BaseNode):
    """Déclaration implements."""

    annotation: Any = None


@dataclass(eq=False)
class UsesDecl(BaseNode):
    """Déclaration uses."""

    annotation: Any = None


@dataclass(eq=False)
class InitializesDecl(BaseNode):
    """Déclaration initializes."""

    annotation: Any = None


@dataclass(eq=False)
class ExportsDecl(BaseNode):
    """Déclaration exports."""

    annotation: Any = None


@dataclass(eq=False)
class If(BaseNode):
    """Instruction conditionnelle if."""

    test: Any = None
    body: List[Any] = field(default_factory=list)
    orelse: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class IfExp(BaseNode):
    """Expression conditionnelle (ternaire)."""

    test: Any = None
    body: Any = None
    orelse: Any = None


@dataclass(eq=False)
class For(BaseNode):
    """Boucle for."""

    target: Any = None
    iter: Any = None
    body: List[Any] = field(default_factory=list)


@dataclass(eq=False)
class Break(BaseNode):
    """Instruction break."""

    pass


@dataclass(eq=False)
class Continue(BaseNode):
    """Instruction continue."""

    pass


# Mapping des types AST pour la conversion JSON → dataclasses
AST_CLASS_MAP: Dict[str, Type[BaseNode]] = {
    cls.__name__: cls
    for cls in list(globals().values())
    if isinstance(cls, type) and issubclass(cls, BaseNode)
}
