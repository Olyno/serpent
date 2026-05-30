; Zed highlight queries for Vyper
; Standard Zed captures: @keyword, @type, @function, @string, @comment,
;   @variable, @constant, @operator, @punctuation, @attribute, @number,
;   @boolean, @namespace

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
  "import"
  "from"
  "uses"
  "implements"
  "initializes"
  "exports"
  "struct"
  "enum"
  "flag"
  "event"
  "interface"
  "constant"
  "indexed"
] @keyword

; ===== DECORATORS =====
(decorator) @attribute

; ===== BUILTIN FUNCTIONS =====
((identifier) @function
  (#match? @function
    "^(send|raw_call|raw_log|raw_revert|keccak256|sha256|create_from_blueprint|create_copy_of|create_minimal_proxy_to|convert|slice|concat|empty|as_wei_value|as_unitless_number|ceil|floor|max|min|max_value|min_value|pow_mod256|sqrt|isqrt|epsilon|extract32|unsafe_add|unsafe_sub|unsafe_mul|unsafe_div|abi_decode|abi_encode|_abi_encode|method_id|print|log|clear|pop|append|len|range)$"))

; ===== FUNCTION DEFINITIONS =====
(function_def
  name: (identifier) @function)

(function_def
  name: (identifier) @function
  (#eq? @function "__init__"))

(function_def
  name: (identifier) @function
  (#eq? @function "__default__"))

; ===== FUNCTION CALLS =====
(call_expression
  function: (identifier) @function)

(call_expression
  function: (attribute
    attribute: (identifier) @function))

; ===== TYPES =====
(base_type) @type

(type_parameterized
  [
    "DynArray"
    "HashMap"
  ] @type)

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
  name: (identifier) @variable)

; ===== SPECIAL VARIABLES (self, msg, block, tx) =====
(special_variable) @variable

(self_variable
  (identifier) @variable)

(msg_variable
  (identifier) @variable)

(block_variable
  (identifier) @variable)

(tx_variable
  (identifier) @variable)

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
  name: (identifier) @variable)

(event_field
  name: (identifier) @variable)

; ===== LITERALS =====
(integer) @number

(float) @number

(string) @string

(boolean) @boolean

(none) @constant

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

; ===== IMPORT NAMES =====
(import_statement
  name: (dotted_name) @namespace)

(from_import
  module: (dotted_name) @namespace)

(from_import
  name: (dotted_name) @namespace)
