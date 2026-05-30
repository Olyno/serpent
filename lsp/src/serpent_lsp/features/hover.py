     1|"""
     2|Information au survol (hover) pour le Vyper Language Server.
     3|
     4|Affiche la documentation et les signatures des symbols
     5|au survol de la souris.
     6|"""
     7|
     8|import logging
     9|from typing import Optional
    10|
    11|from lsprotocol import types
    12|from pygls.workspace import TextDocument
    13|
    14|from serpent_lsp import utils
    15|from serpent_lsp.ast import nodes
    16|from serpent_lsp.ast.nodes import BaseNode
    17|from serpent_lsp.features.resolve import resolve_symbol_for_word
    18|from serpent_lsp.parser import Module
    19|
    20|logger = logging.getLogger("serpent_lsp")
    21|
    22|
    23|def _get_node_documentation(node: BaseNode) -> str:
    24|    """
    25|    Generate a documentation string for an AST node.
    26|
    27|    Args:
    28|        node: The AST node.
    29|
    30|    Returns:
    31|        Formatted documentation string.
    32|    """
    33|    if isinstance(node, nodes.FunctionDef):
    34|        return _format_function_doc(node)
    35|    elif isinstance(node, nodes.VariableDecl):
    36|        return _format_variable_doc(node)
    37|    elif isinstance(node, nodes.EventDef):
    38|        return f"**Event** `{node.name}`"
    39|    elif isinstance(node, nodes.StructDef):
    40|        return f"**Structure** `{node.name}`"
    41|    elif isinstance(node, nodes.FlagDef):
    42|        return f"**Flag** `{node.name}`"
    43|    elif isinstance(node, nodes.InterfaceDef):
    44|        return f"**Interface** `{node.name}`"
    45|    else:
    46|        return f"`{getattr(node, 'name', 'symbol')}`"
    47|
    48|
    49|def _format_function_doc(func: nodes.FunctionDef) -> str:
    50|    """Format the documentation for a function."""
    51|    name = func.name or "unknown"
    52|
    53|    # Signature
    54|    args_parts = []
    55|    if func.args and func.args.args:
    56|        for arg in func.args.args:
    57|            arg_name = arg.arg
    58|            if arg.annotation:
    59|                if isinstance(arg.annotation, nodes.Name):
    60|                    args_parts.append(f"{arg_name}: {arg.annotation.id}")
    61|                else:
    62|                    args_parts.append(arg_name)
    63|            else:
    64|                args_parts.append(arg_name)
    65|
    66|    returns_str = ""
    67|    if func.returns:
    68|        if isinstance(func.returns, nodes.Name):
    69|            returns_str = f" → {func.returns.id}"
    70|
    71|    # Visibility
    72|    visibility = "interne"
    73|    for decorator in func.decorator_list:
    74|        if isinstance(decorator, nodes.Name):
    75|            if decorator.id in ("external", "public"):
    76|                visibility = decorator.id
    77|        elif isinstance(decorator, nodes.Call):
    78|            if isinstance(decorator.func, nodes.Name):
    79|                if decorator.func.id in ("external", "public"):
    80|                    visibility = decorator.func.id
    81|
    82|    doc = f"```vyper\n{visibility} def {name}({', '.join(args_parts)}){returns_str}\n```"
    83|
    84|    # Docstring
    85|    if func.doc_string and isinstance(func.doc_string, nodes.DocStr):
    86|        doc += f"\n\n{func.doc_string.value}"
    87|
    88|    return doc
    89|
    90|
    91|def _format_variable_doc(var: nodes.VariableDecl) -> str:
    92|    """Formate la documentation d'une variable d'état."""
    93|    name = var.target.id if var.target else "unknown"
    94|
    95|    modifiers = []
    96|    if var.is_constant:
    97|        modifiers.append("constant")
    98|    if var.is_immutable:
    99|        modifiers.append("immutable")
   100|    if var.is_public:
   101|        modifiers.append("public")
   102|    if var.is_transient:
   103|        modifiers.append("transient")
   104|
   105|    type_str = ""
   106|    if var.annotation:
   107|        if isinstance(var.annotation, nodes.Name):
   108|            type_str = f": {var.annotation.id}"
   109|        elif isinstance(var.annotation, nodes.Subscript):
   110|            if isinstance(var.annotation.value, nodes.Name):
   111|                type_str = f": {var.annotation.value.id}[...]"
   112|
   113|    modifier_str = f"({', '.join(modifiers)}) " if modifiers else ""
   114|    doc = f"```vyper\n{modifier_str}{name}{type_str}\n```"
   115|
   116|    return doc
   117|
   118|
   119|def get_hover_info(
   120|    get_module_func,
   121|    workspace,
   122|    doc: TextDocument,
   123|    module: Module,
   124|    position: types.Position,
   125|) -> Optional[types.Hover]:
   126|    """
   127|    Get hover information for the symbol at the given position.
   128|
   129|    Args:
   130|        get_module_func: Fonction pour obtenir un module.
   131|        workspace: Le workspace LSP.
   132|        doc: Le document courant.
   133|        module: Le module courant.
   134|        position: Position du curseur.
   135|
   136|    Returns:
   137|        Un objet Hover, ou None.
   138|    """
   139|    attribute_word = utils.get_attribute_word(doc, position)
   140|    if not attribute_word:
   141|        return None
   142|
   143|    resolved = resolve_symbol_for_word(
   144|        get_module_func, workspace, doc, module, attribute_word, position
   145|    )
   146|    if not resolved:
   147|        return None
   148|
   149|    node = resolved.node
   150|    if node is None:
   151|        return None
   152|
   153|    documentation = _get_node_documentation(node)
   154|
   155|    return types.Hover(
   156|        contents=types.MarkupContent(
   157|            kind=types.MarkupKind.Markdown,
   158|            value=documentation,
   159|        ),
   160|    )
   161|