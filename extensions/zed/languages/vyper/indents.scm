; Zed auto-indentation for Vyper
; Only @indent and @end are valid captures.
; pass/break/continue/return indentation is handled by the tree-sitter parser.

(function_definition) @indent
(struct_definition) @indent
(event_definition) @indent
(enum_definition) @indent
(interface_definition) @indent
(if_statement) @indent
(for_statement) @indent
(import_from_statement) @indent
