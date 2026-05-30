; Tree-sitter highlight queries for Vyper
; Uses named node captures only (anonymous token matching is unreliable across tree-sitter versions)

; ===== COMMENTS =====
(comment) @comment

; ===== KEYWORDS (via named statement nodes) =====
(import_statement) @keyword.import
(from_import) @keyword.import

[
  (return_statement)
  (raise_statement)
  (assert_statement)
  (pass_statement)
  (break_statement)
  (continue_statement)
  (if_statement)
  (for_statement)
] @keyword

; ===== TYPE DEFINITION KEYWORDS =====
[
  (struct_def)
  (enum_def)
  (flag_def)
  (event_def)
  (interface_def)
] @keyword.type

; ===== DECORATORS =====
(decorator) @attribute

; ===== FUNCTION DEFINITIONS =====
(function_def
  name: (identifier) @function)

(function_def
  name: (identifier) @constructor
  (#eq? @constructor "__init__"))

(function_def
  name: (identifier) @constructor
  (#eq? @constructor "__default__"))

; ===== FUNCTION CALLS =====
(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (attribute
    attribute: (identifier) @function.call))

; ===== TYPES =====
(base_type) @type

(type_parameterized) @type

(type_bounded) @type

; ===== VARIABLES =====
(variable_def
  name: (identifier) @variable)

(variable_def
  name: (attribute) @variable)

; ===== CONSTANTS =====
(constant_def
  name: (identifier) @constant)

; ===== PARAMETERS =====
(parameter
  name: (identifier) @parameter)

; ===== SPECIAL VARIABLES (self, msg, block, tx) =====
((identifier) @variable.builtin
  (#eq? @variable.builtin "self"))

((identifier) @variable.builtin
  (#eq? @variable.builtin "msg"))

((identifier) @variable.builtin
  (#eq? @variable.builtin "block"))

((identifier) @variable.builtin
  (#eq? @variable.builtin "tx"))

; ===== LITERALS =====
(integer) @number
(float) @number

(string) @string

(boolean) @boolean

(none) @constant.builtin

; ===== ATTRIBUTE ACCESS =====
(attribute
  attribute: (identifier) @variable.member)

; ===== PUNCTUATION =====
[
  "."
  ","
  ":"
  "("
  ")"
  "["
  "]"
  "="
] @punctuation
