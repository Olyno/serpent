; Auto-indentation rules for Vyper in Zed

; Indent after colons (blocks)
(function_def) @indent
(struct_def) @indent
(enum_def) @indent
(flag_def) @indent
(event_def) @indent
(interface_def) @indent
(if_statement) @indent
(for_statement) @indent

; Outdent for block-ending keywords
(pass_statement) @indent_end
(break_statement) @indent_end
(continue_statement) @indent_end

(return_statement) @indent_end
(raise_statement) @indent_end
