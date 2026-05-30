; Auto-indentation rules for Vyper

; Indent after a colon (blocks: function defs, struct defs, if/for/else/elif)
[
  (function_def)
  (struct_def)
  (enum_def)
  (flag_def)
  (event_def)
  (interface_def)
  (if_statement)
  (for_statement)
] @indent

; Dedent for standalone keywords that end blocks
[
  (pass_statement)
  (break_statement)
  (continue_statement)
] @indent_end

; Dedent after return/raise in block context
(return_statement) @indent_end
(raise_statement) @indent_end
