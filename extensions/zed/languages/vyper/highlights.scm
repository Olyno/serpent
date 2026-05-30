; Zed highlight queries for Vyper
; Order: general captures first, specific overrides last

; ===== COMMENTS =====
(comment) @comment

; ===== PUNCTUATION =====
"," @punctuation.delimiter
"." @punctuation.delimiter
":" @punctuation.delimiter
"=" @operator
"->" @operator
"+" @operator
"-" @operator
"*" @operator
"/" @operator
"%" @operator
"**" @operator
"<" @operator
"<=" @operator
">" @operator
">=" @operator
"==" @operator
"!=" @operator
"&" @operator
"|" @operator
"^" @operator
"<<" @operator
">>" @operator
"~" @operator
"(" @punctuation.bracket
")" @punctuation.bracket
"[" @punctuation.bracket
"]" @punctuation.bracket

; ===== KEYWORDS (single-token — node IS the token) =====
(pass_statement) @keyword
(break_statement) @keyword
(continue_statement) @keyword

; ===== KEYWORDS (compound — imperfect but visible) =====
(return_statement) @keyword
(raise_statement) @keyword
(assert_statement) @keyword
(if_statement) @keyword
(for_statement) @keyword

; ===== TYPE DEFINITIONS =====
(struct_def) @keyword.type
(enum_def) @keyword.type
(flag_def) @keyword.type
(event_def) @keyword.type
(interface_def) @keyword.type

; ===== IMPORTS =====
(import_statement) @keyword.import
(from_import) @keyword.import

; ===== FUNCTIONS =====
(function_def name: (identifier) @function)
(function_def name: (identifier) @constructor (#eq? @constructor "__init__"))

; ===== DECORATORS =====
(decorator) @attribute

; ===== TYPES (in annotations: x: uint256, y: HashMap[K,V]) =====
(base_type) @type
(type_parameterized) @type
(type_bounded) @type

; ===== PARAMETERS =====
(parameter name: (identifier) @parameter)

; ===== VARIABLES =====
(variable_def name: (identifier) @variable)
(constant_def name: (identifier) @constant)

; ===== LITERALS =====
(integer) @number
(float) @number.float
(string) @string
(boolean) @boolean
(none) @constant.builtin

; ===== SPECIAL VARIABLES (self, msg, block, tx, chain) =====
; Uses #match? on identifiers to avoid grammar conflicts
((identifier) @variable.builtin
  (#match? @variable.builtin "^(self|msg|block|tx|chain)$"))

; ===== FUNCTION CALLS (general) =====
(call_expression function: (identifier) @function)

; ===== BUILT-IN FUNCTIONS (override general @function for these) =====
(call_expression function: (identifier) @function.builtin
  (#match? @function.builtin "^(convert|keccak256|sha256|slice|concat|len|create_minimal_proxy_to|create_copy_of|create_from_blueprint|selfdestruct|send|raw_call|raw_log|raw_revert|raw_create|abi_decode|abi_encode|method_id|shift|empty|as_wei_value|as_unitless_number|unsafe_add|unsafe_sub|unsafe_mul|unsafe_div|uint256_addmod|uint256_mulmod|pow_mod256|sqrt|isqrt|abs|ceil|epsilon|floor|max|min|max_value|min_value|ecrecover|ecadd|ecmul|extract32|uint2str|print|clear|pop|append)$"))

; ===== ATTRIBUTE ACCESS (.member) =====
(attribute attribute: (identifier) @property)
