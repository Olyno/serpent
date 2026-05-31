; Zed auto-indentation for Vyper
; Uses @start.X captures (matching Python's pattern) with
; increase_indent_pattern / decrease_indent_patterns in config.toml
;
; @start.X suffix is matched against valid_after in decrease_indent_patterns
; to determine where elif/else should outdent.

(_
  "["
  "]" @end) @indent

(_
  "("
  ")" @end) @indent

(function_definition) @start.def
(struct_definition) @start.class
(event_definition) @start.class
(enum_definition) @start.class
(interface_definition) @start.class
(if_statement) @start.if
(for_statement) @start.for
