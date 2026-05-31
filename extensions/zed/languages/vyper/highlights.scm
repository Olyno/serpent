; Zed syntax highlighting for Vyper

; ===== COMMENTS =====
(comment) @comment

; ===== STRINGS =====
(string) @string

; ===== NUMBERS =====
(integer) @number
(float) @number

; ===== CONSTANTS =====
[
  (none)
  (true)
  (false)
] @constant

((identifier) @constant
  (#match? @constant "^(ZERO_ADDRESS|EMPTY_BYTES32|MAX_INT128|MIN_INT128|MAX_INT256|MIN_INT256|MAX_UINT256)$"))

((identifier) @constant
  (#match? @constant "^[A-Z][A-Z_0-9]*$"))

; ===== KEYWORDS =====
[
  "assert"
  "break"
  "continue"
  "def"
  "elif"
  "else"
  "for"
  "from"
  "if"
  "import"
  "pass"
  "raise"
  "return"
  "as"
  "in"
  "is"
  "not"
  "and"
  "or"
  "event"
  "struct"
  "enum"
  "interface"
  "log"
  "extcall"
  "staticcall"
] @keyword

; ===== OPERATORS =====
[
  "-"
  "-="
  "!="
  "*"
  "**"
  "**="
  "*="
  "/"
  "//"
  "//="
  "/="
  "&"
  "&="
  "%"
  "%="
  "^"
  "^="
  "+"
  "->"
  "+="
  "<"
  "<<"
  "<<="
  "<="
  "="
  "=="
  ">"
  ">="
  ">>"
  ">>="
  "|"
  "|="
  "~"
] @operator

; ===== PUNCTUATION =====
"," @punctuation.delimiter
"." @punctuation.delimiter
":" @punctuation.delimiter
"(" @punctuation.bracket
")" @punctuation.bracket
"[" @punctuation.bracket
"]" @punctuation.bracket

; ===== TYPE DEFINITIONS =====
(struct_definition name: (identifier) @type)
(event_definition name: (identifier) @type)
(enum_definition name: (identifier) @type)
(interface_definition name: (identifier) @type)

; ===== FUNCTIONS =====
(function_definition name: (identifier) @function)
((function_definition name: (identifier) @function) (#eq? @function "__init__"))

; ===== DECORATORS =====
(decorator) @attribute
((decorator (identifier) @attribute)
  (#match? @attribute "^(external|internal|public|private|view|pure|payable|nonpayable|nonreentrant|deploy)$"))

; ===== TYPES =====
(type (identifier) @type)
(generic_type (identifier) @type)

; ===== SPECIAL VARIABLES =====
((identifier) @variable
  (#match? @variable "^(self|msg|block|tx|chain)$"))

; ===== FUNCTION CALLS =====
(call function: (identifier) @function)
(call function: (attribute attribute: (identifier) @function))

((call function: (identifier) @function)
  (#match? @function "^(convert|keccak256|sha256|slice|concat|len|create_minimal_proxy_to|create_copy_of|create_from_blueprint|selfdestruct|send|raw_call|raw_log|raw_revert|raw_create|abi_decode|abi_encode|method_id|shift|empty|as_wei_value|as_unitless_number|unsafe_add|unsafe_sub|unsafe_mul|unsafe_div|uint256_addmod|uint256_mulmod|pow_mod256|sqrt|isqrt|abs|ceil|epsilon|floor|max|min|max_value|min_value|ecrecover|ecadd|ecmul|extract32|uint2str|print|clear|pop|append)$"))

; ===== ATTRIBUTE ACCESS =====
(attribute attribute: (identifier) @property)
