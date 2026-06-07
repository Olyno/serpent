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
((function_definition name: (identifier) @function) (#eq? @function "__default__"))

; ===== DECORATORS =====
(decorator) @attribute
((decorator (identifier) @keyword)
  (#match? @keyword "^(external|internal|public|private|view|pure|payable|nonpayable|nonreentrant|deploy|constant|immutable|transient|indexed)$"))

; ===== TYPES =====
(type (identifier) @type)
(generic_type (identifier) @type)

; ===== SPECIAL VARIABLES =====
((identifier) @variable.builtin
  (#match? @variable.builtin "^(self|msg|block|tx|chain)$"))

((identifier) @keyword
  (#match? @keyword "^(self)$"))

; ===== PARAMETERS =====
(parameters (identifier) @parameter @variable.builtin)
(typed_parameter (identifier) @parameter @variable.builtin)
(default_parameter name: (identifier) @parameter @variable.builtin)
(typed_default_parameter name: (identifier) @parameter @variable.builtin)

; ===== STORAGE MODIFIERS =====
((call
  function: (identifier) @keyword
  arguments: (argument_list (identifier) @type))
  (#match? @keyword "^(public|constant|immutable|transient)$"))

; ===== FUNCTION CALLS =====
(call function: (identifier) @function
  (#not-match? @function "^(public|constant|immutable|transient)$"))
(call function: (attribute attribute: (identifier) @function))

; Built-in functions
((call function: (identifier) @function.builtin)
  (#match? @function.builtin "^(convert|keccak256|sha256|slice|concat|len|create_minimal_proxy_to|create_copy_of|create_from_blueprint|selfdestruct|send|raw_call|raw_log|raw_revert|raw_create|abi_decode|abi_encode|method_id|shift|empty|as_wei_value|unsafe_add|unsafe_sub|unsafe_mul|unsafe_div|uint256_addmod|uint256_mulmod|pow_mod256|sqrt|isqrt|abs|ceil|epsilon|floor|max|min|max_value|min_value|ecrecover|ecadd|ecmul|extract32|uint2str|print|blockhash|blobhash|pop|append)$"))

; ===== ATTRIBUTE ACCESS =====
(attribute attribute: (identifier) @property)

; ===== TYPE PRIMITIVES =====
((identifier) @type.builtin
  (#match? @type.builtin "^(bool|address|decimal|String|Bytes|HashMap|DynArray|(u?int)(8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)|bytes([1-9]|[12][0-9]|3[0-2]))$"))
