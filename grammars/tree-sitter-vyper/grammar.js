// Tree-sitter grammar for Vyper smart contract language
// Vyper is indentation-based like Python — uses external scanner for INDENT/DEDENT

const PREC = {
  ASSIGN: 1,
  LOGICAL_OR: 2,
  LOGICAL_AND: 3,
  EQUALITY: 4,
  COMPARISON: 5,
  BITWISE_OR: 6,
  BITWISE_XOR: 7,
  BITWISE_AND: 8,
  SHIFT: 9,
  ADD: 10,
  MULTIPLY: 11,
  UNARY: 12,
  EXPONENT: 13,
  CALL: 14,
  MEMBER: 15,
};

module.exports = grammar({
  name: 'vyper',

  externals: $ => [
    $._newline,
    $._indent,
    $._dedent,
  ],

  extras: $ => [
    $.comment,
    /[ \t\f\v]+/,
  ],

  word: $ => $.identifier,

  rules: {
    // ========== TOP LEVEL ==========
    source_file: $ => seq(
      optional($._statements),
    ),

    _statements: $ => seq(
      $._statement,
      repeat($._statement),
    ),

    _statement: $ => choice(
      $.import_statement,
      $.struct_def,
      $.enum_def,
      $.flag_def,
      $.event_def,
      $.interface_def,
      $.function_def,
      $.constant_def,
      $.variable_def,
      $.return_statement,
      $.raise_statement,
      $.assert_statement,
      $.if_statement,
      $.for_statement,
      $.pass_statement,
      $.break_statement,
      $.continue_statement,
      $.expression_statement,
    ),

    // ========== COMMENTS ==========
    comment: $ => token(seq('#', /.*/)),

    // ========== IMPORTS ==========
    import_statement: $ => choice(
      seq(
        choice('import', 'uses', 'implements', 'initializes', 'exports'),
        field('name', $.dotted_name),
        $._newline,
      ),
      $.from_import,
    ),

    from_import: $ => seq(
      'from',
      field('module', $.dotted_name),
      'import',
      field('name', $.dotted_name),
      repeat(seq(',', $.dotted_name)),
      $._newline,
    ),

    dotted_name: $ => choice(
      $.identifier,
      seq($.dotted_name, '.', $.identifier),
    ),

    // ========== STRUCT ==========
    struct_def: $ => seq(
      'struct',
      field('name', $.identifier),
      ':',
      $._newline,
      $._indent,
      repeat($.struct_field),
      $._dedent,
    ),

    struct_field: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.type),
      $._newline,
    ),

    // ========== ENUM ==========
    enum_def: $ => seq(
      'enum',
      field('name', $.identifier),
      ':',
      $._newline,
      $._indent,
      repeat($.enum_member),
      $._dedent,
    ),

    enum_member: $ => seq(
      field('name', $.identifier),
      $._newline,
    ),

    // ========== FLAG ==========
    flag_def: $ => seq(
      'flag',
      field('name', $.identifier),
      ':',
      $._newline,
      $._indent,
      repeat($.flag_member),
      $._dedent,
    ),

    flag_member: $ => seq(
      field('name', $.identifier),
      $._newline,
    ),

    // ========== EVENT ==========
    event_def: $ => seq(
      'event',
      field('name', $.identifier),
      ':',
      $._newline,
      $._indent,
      repeat($.event_field),
      $._dedent,
    ),

    event_field: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.event_type),
      $._newline,
    ),

    event_type: $ => choice(
      $.indexed_type,
      $.type,
    ),

    indexed_type: $ => seq(
      'indexed',
      '(',
      field('type', $.type),
      ')',
    ),

    // ========== INTERFACE ==========
    interface_def: $ => seq(
      'interface',
      field('name', $.identifier),
      ':',
      $._newline,
      $._indent,
      repeat($.interface_member),
      $._dedent,
    ),

    interface_member: $ => seq(
      'def',
      field('name', $.identifier),
      field('parameters', $.parameters),
      optional($.return_type),
      ':',
      $._newline,
    ),

    // ========== FUNCTION ==========
    function_def: $ => seq(
      repeat($.decorator),
      'def',
      field('name', $.identifier),
      field('parameters', $.parameters),
      optional($.return_type),
      ':',
      $._newline,
      $._indent,
      optional(alias($._suite, $.body)),
      $._dedent,
    ),

    _suite: $ => seq(
      $._stmt_list,
      repeat(seq($._stmt_list)),
    ),

    _stmt_list: $ => choice(
      $.simple_statement,
      $.compound_statement,
    ),

    simple_statement: $ => seq(
      choice(
        $.return_statement,
        $.raise_statement,
        $.assert_statement,
        $.pass_statement,
        $.break_statement,
        $.continue_statement,
        $.expression_statement,
        $.variable_def,
        $.constant_def,
      ),
      $._newline,
    ),

    compound_statement: $ => choice(
      $.if_statement,
      $.for_statement,
    ),

    return_type: $ => seq(
      '->',
      field('type', $.type),
    ),

    decorator: $ => seq(
      '@',
      field('name', $.identifier),
      $._newline,
    ),

    parameters: $ => seq(
      '(',
      optional($.parameter_list),
      ')',
    ),

    parameter_list: $ => seq(
      $.parameter,
      repeat(seq(',', $.parameter)),
      optional(','),
    ),

    parameter: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.type),
      optional(seq('=', field('default', $._expression))),
    ),

    // ========== CONSTANTS ==========
    constant_def: $ => seq(
      field('name', $.identifier),
      ':',
      'constant',
      '(',
      field('type', $.type),
      ')',
      '=',
      field('value', $._expression),
    ),

    // ========== VARIABLES ==========
    variable_def: $ => seq(
      field('name', choice($.identifier, $.attribute)),
      ':',
      field('type', $.type),
      optional(seq('=', field('value', $._expression))),
    ),

    // ========== TYPES ==========
    type: $ => choice(
      $.type_bounded,
      $.type_parameterized,
      $.base_type,
    ),

    base_type: $ => choice(
      'bool',
      'address',
      'decimal',
      /uint(8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)/,
      /int(8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)/,
      /bytes(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32)/,
      'String',
      'Bytes',
    ),

    type_parameterized: $ => seq(
      choice('DynArray', 'HashMap'),
      '[',
      field('key_type', $.type),
      ',',
      field('value_type', $.type),
      ']',
    ),

    type_bounded: $ => prec(1, seq(
      $.base_type,
      '[',
      field('bound', $._integer),
      ']',
    )),

    // ========== STATEMENTS ==========
    return_statement: $ => seq(
      'return',
      optional($._expression),
    ),

    raise_statement: $ => seq(
      'raise',
      optional($._expression),
    ),

    assert_statement: $ => seq(
      'assert',
      $._expression,
      optional(seq(',', $._expression)),
    ),

    pass_statement: $ => 'pass',

    break_statement: $ => 'break',

    continue_statement: $ => 'continue',

    expression_statement: $ => $._expression,

    if_statement: $ => seq(
      'if',
      field('condition', $._expression),
      ':',
      $._newline,
      $._indent,
      optional(alias($._suite, $.consequence)),
      $._dedent,
      repeat(seq(
        'elif',
        field('condition', $._expression),
        ':',
        $._newline,
        $._indent,
        optional(alias($._suite, $.consequence)),
        $._dedent,
      )),
      optional(seq(
        'else',
        ':',
        $._newline,
        $._indent,
        optional(alias($._suite, $.alternative)),
        $._dedent,
      )),
    ),

    for_statement: $ => seq(
      'for',
      field('variable', $.identifier),
      'in',
      field('iterable', $._expression),
      ':',
      $._newline,
      $._indent,
      optional(alias($._suite, $.body)),
      $._dedent,
    ),

    // ========== EXPRESSIONS ==========
    _expression: $ => $._logical_or,

    _logical_or: $ => prec.left(PREC.LOGICAL_OR, seq(
      field('left', $._logical_or),
      'or',
      field('right', $._logical_and),
    )),

    _logical_and: $ => prec.left(PREC.LOGICAL_AND, seq(
      field('left', $._logical_and),
      'and',
      field('right', $._equality),
    )),

    _equality: $ => prec.left(PREC.EQUALITY, choice(
      seq(
        field('left', $._equality),
        '==',
        field('right', $._comparison),
      ),
      seq(
        field('left', $._equality),
        '!=',
        field('right', $._comparison),
      ),
      $._comparison,
    )),

    _comparison: $ => prec.left(PREC.COMPARISON, choice(
      seq(
        field('left', $._comparison),
        choice('<', '<=', '>', '>=', 'in'),
        field('right', $._bitwise_or),
      ),
      $._bitwise_or,
    )),

    _bitwise_or: $ => prec.left(PREC.BITWISE_OR, choice(
      seq(field('left', $._bitwise_or), '|', field('right', $._bitwise_xor)),
      $._bitwise_xor,
    )),

    _bitwise_xor: $ => prec.left(PREC.BITWISE_XOR, choice(
      seq(field('left', $._bitwise_xor), '^', field('right', $._bitwise_and)),
      $._bitwise_and,
    )),

    _bitwise_and: $ => prec.left(PREC.BITWISE_AND, choice(
      seq(field('left', $._bitwise_and), '&', field('right', $._shift)),
      $._shift,
    )),

    _shift: $ => prec.left(PREC.SHIFT, choice(
      seq(field('left', $._shift), '<<', field('right', $._additive)),
      seq(field('left', $._shift), '>>', field('right', $._additive)),
      $._additive,
    )),

    _additive: $ => prec.left(PREC.ADD, choice(
      seq(field('left', $._additive), '+', field('right', $._multiplicative)),
      seq(field('left', $._additive), '-', field('right', $._multiplicative)),
      $._multiplicative,
    )),

    _multiplicative: $ => prec.left(PREC.MULTIPLY, choice(
      seq(field('left', $._multiplicative), '*', field('right', $._unary)),
      seq(field('left', $._multiplicative), '/', field('right', $._unary)),
      seq(field('left', $._multiplicative), '%', field('right', $._unary)),
      $._unary,
    )),

    _unary: $ => prec(PREC.UNARY, choice(
      seq(choice('not', '-', '~'), field('argument', $._unary)),
      $._exponent,
    )),

    _exponent: $ => prec.right(PREC.EXPONENT, choice(
      seq(
        field('argument', $._primary),
        '**',
        field('argument', $._exponent),
      ),
      $._primary,
    )),

    _primary: $ => choice(
      $.identifier,
      $._literal,
      $.attribute,
      $.subscript,
      $.call_expression,
      $.parenthesized_expression,
      $.list_expression,
      $.tuple_expression,
    ),

    // ========== LITERALS ==========
    _literal: $ => choice(
      $.integer,
      $.float,
      $.string,
      $.boolean,
      $.none,
    ),

    integer: $ => $._integer,

    _integer: $ => choice(
      $._hex_integer,
      $._decimal_integer,
    ),

    _hex_integer: $ => token(seq('0x', /[0-9a-fA-F_]+/)),

    _decimal_integer: $ => token(/[0-9][0-9_]*/),

    float: $ => token(seq(
      /[0-9][0-9_]*/,
      '.',
      /[0-9_]+/,
    )),

    string: $ => choice(
      $._single_quoted_string,
      $._double_quoted_string,
    ),

    _single_quoted_string: $ => token(seq(
      "'",
      repeat(choice(
        /[^'\\\n]/,
        /\\./,
      )),
      "'",
    )),

    _double_quoted_string: $ => token(seq(
      '"',
      repeat(choice(
        /[^"\\\n]/,
        /\\./,
      )),
      '"',
    )),

    boolean: $ => choice('True', 'False'),

    none: $ => 'None',

    // ========== COMPOUND EXPRESSIONS ==========
    attribute: $ => prec(PREC.MEMBER, seq(
      field('object', $._primary),
      '.',
      field('attribute', $.identifier),
    )),

    subscript: $ => prec(PREC.MEMBER, seq(
      field('value', $._primary),
      '[',
      field('index', $._expression),
      repeat(seq(',', field('index', $._expression))),
      ']',
    )),

    call_expression: $ => prec(PREC.CALL, seq(
      field('function', $._primary),
      field('arguments', $.arguments),
    )),

    arguments: $ => seq(
      '(',
      optional($.argument_list),
      ')',
    ),

    argument_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression)),
      optional(','),
    ),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')',
    ),

    list_expression: $ => seq(
      '[',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression)),
        optional(','),
      )),
      ']',
    ),

    tuple_expression: $ => seq(
      '(',
      $._expression,
      ',',
      repeat(seq($._expression, ',')),
      optional($._expression),
      ')',
    ),

    // ========== SPECIAL VARIABLES ==========
    // self/msg/block/tx are parsed as identifiers, chained via attribute rule.
    // Highlighting is handled via tree-sitter queries (e.g. ((identifier) @variable.builtin (#eq? @variable.builtin "self"))).
    // This avoids grammar conflicts between self_variable and the general attribute rule.

    // ========== IDENTIFIER ==========
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
  },
});
