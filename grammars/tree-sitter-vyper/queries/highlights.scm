; Tree-sitter highlight queries for Vyper
; Captures: @keyword, @type, @function, @string, @comment, @variable, @constant,
;           @operator, @punctuation, @attribute, @number, @boolean, @parameter,
;           @namespace, @constructor, @variable.builtin, @function.builtin

; ===== KEYWORDS =====
[
  "def"
  "return"
  "raise"
  "assert"
  "if"
  "elif"
  "else"
  "for"
  "in"
  "pass"
  "break"
  "continue"
  "not"
  "and"
  "or"
] @keyword

; ===== MODULE KEYWORDS (import system) =====
[
  "import"
  "from"
  "uses"
  "implements"
  "initializes"
  "exports"
] @keyword.import

; ===== TYPE DEFINITION KEYWORDS =====
[
  "struct"
  "enum"
  "flag"
  "event"
  "interface"
  "constant"
  "indexed"
] @keyword.type

; ===== DECORATORS =====
(decorator) @attribute

; ===== BUILTIN FUNCTIONS =====
((identifier) @function.builtin
  (#match? @function.builtin
    "^(send|raw_call|raw_log|raw_revert|keccak256|sha256|create_from_blueprint|create_copy_of|create_minimal_proxy_to|convert|slice|concat|empty|as_wei_value|as_unitless_number|ceil|floor|max|min|max_value|min_value|pow_mod256|sqrt|isqrt|epsilon|extract32|unsafe_add|unsafe_sub|unsafe_mul|unsafe_div|abi_decode|abi_encode|_abi_encode|method_id|print|log|clear|pop|append|len|range)$"))

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

; ===== TYPES (base types like uint256, bool, etc.) =====
(base_type) @type

; ===== PARAMETERIZED TYPES (DynArray, HashMap) =====
(type_parameterized
  [
    "DynArray"
    "HashMap"
  ] @type)

; ===== BOUNDED TYPES (String[32], Bytes[64]) =====
(type_bounded
  [
    "String"
    "Bytes"
  ] @type)

; ===== VARIABLE DEFINITIONS =====
(variable_def
  name: (identifier) @variable)

(variable_def
  name: (attribute) @variable)

; ===== CONSTANT DEFINITIONS =====
(constant_def
  name: (identifier) @constant)

; ===== FUNCTION PARAMETERS =====
(parameter
  name: (identifier) @parameter)

; ===== SPECIAL VARIABLES (self, msg, block, tx) =====
(special_variable) @variable.builtin

(self_variable
  (identifier) @variable.builtin)

(msg_variable
  (identifier) @variable.builtin)

(block_variable
  (identifier) @variable.builtin)

(tx_variable
  (identifier) @variable.builtin)

; ===== LITERALS =====
(integer) @number

(float) @number.float

(string) @string

(boolean) @boolean

(none) @constant.builtin

; ===== COMMENTS =====
(comment) @comment

; ===== OPERATORS =====
[
  "+"
  "-"
  "*"
  "/"
  "%"
  "**"
  "="
  "+="
  "-="
  "*="
  "/="
  "%="
  "**="
  "&="
  "|="
  "^="
  "<<="
  ">>="
  "=="
  "!="
  "<"
  "<="
  ">"
  ">="
  "&"
  "|"
  "^"
  "~"
  "<<"
  ">>"
  "->"
] @operator

; ===== PUNCTUATION =====
[
  "("
  ")"
  "["
  "]"
  ","
  ":"
  "."
  "@"
] @punctuation

; ===== ATTRIBUTE ACCESS (obj.attr) =====
(attribute
  attribute: (identifier) @attribute)

; ===== STRUCT/EVENT/INTERFACE/ENUM/FLAG NAMES =====
(struct_def
  name: (identifier) @type)

(enum_def
  name: (identifier) @type)

(flag_def
  name: (identifier) @type)

(event_def
  name: (identifier) @type)

(interface_def
  name: (identifier) @type)

; ===== STRUCT/EVENT FIELDS =====
(struct_field
  name: (identifier) @variable.member)

(event_field
  name: (identifier) @variable.member)

; ===== IMPORT NAMES =====
(import_statement
  name: (dotted_name) @namespace)

(from_import
  module: (dotted_name) @namespace)

(from_import
  name: (dotted_name) @namespace)
