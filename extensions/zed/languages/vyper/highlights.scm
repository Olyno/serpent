; Zed highlight queries for Vyper — using named node captures only

; ===== COMMENTS =====
(comment) @comment

; ===== KEYWORDS =====
[
  (return_statement)
  (raise_statement)
  (assert_statement)
  (pass_statement)
  (break_statement)
  (continue_statement)
  (if_statement)
  (for_statement)
  (import_statement)
  (from_import)
] @keyword

; ===== TYPE DEFINITIONS =====
[
  (struct_def)
  (enum_def)
  (flag_def)
  (event_def)
  (interface_def)
] @keyword

; ===== FUNCTIONS =====
(function_def
  name: (identifier) @function)

(function_def
  name: (identifier) @constructor
  (#eq? @constructor "__init__"))

; ===== FUNCTION CALLS =====
(call_expression
  function: (identifier) @function)

(call_expression
  function: (attribute
    attribute: (identifier) @function))

; ===== TYPES =====
(base_type) @type
(type_parameterized) @type
(type_bounded) @type

; ===== VARIABLES =====
(variable_def
  name: (identifier) @variable)

(variable_def
  name: (attribute) @variable)

(constant_def
  name: (identifier) @constant)

(parameter
  name: (identifier) @parameter)

; ===== SPECIAL (self, msg, block, tx) =====
((identifier) @variable
  (#eq? @variable "self"))

((identifier) @variable
  (#eq? @variable "msg"))

((identifier) @variable
  (#eq? @variable "block"))

((identifier) @variable
  (#eq? @variable "tx"))

; ===== LITERALS =====
(integer) @number
(float) @number
(string) @string
(boolean) @boolean
(none) @constant

; ===== ATTRIBUTES =====
(attribute
  attribute: (identifier) @property)

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
