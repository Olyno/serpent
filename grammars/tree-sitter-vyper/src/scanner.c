// External scanner for Vyper — handles INDENT/DEDENT/NEWLINE
// Based on tree-sitter-python's scanner approach

#include "tree_sitter/alloc.h"
#include "tree_sitter/array.h"
#include "tree_sitter/parser.h"

#include <assert.h>
#include <string.h>
#include <stdbool.h>

// Token types
enum TokenType {
  NEWLINE,
  INDENT,
  DEDENT,
};

// Scanner state — tracks indentation levels
typedef struct {
  Array(uint16_t) indent_length_stack;
} Scanner;

// ===== Helper: determine if a character ends an identifier =====
static bool is_identifier_end(char c) {
  return !((c >= 'a' && c <= 'z') ||
           (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9') ||
           c == '_');
}

// ===== Init scanner =====
static void advance_scanner(Scanner *scanner) {
  array_push(&scanner->indent_length_stack, 0);
}

// ===== Get the latest indent level =====
static unsigned current_indent(Scanner *scanner) {
  size_t size = scanner->indent_length_stack.size;
  return size > 0
    ? *array_get(&scanner->indent_length_stack, size - 1)
    : 0;
}

// ===== Pop indentation stack =====
static void pop_indent(Scanner *scanner) {
  if (scanner->indent_length_stack.size > 0) {
    scanner->indent_length_stack.size--;
  }
}

// ===== Push new indent level =====
static void push_indent(Scanner *scanner, uint16_t length) {
  array_push(&scanner->indent_length_stack, length);
}

// ===== Advance past a newline =====
static void skip_newline(TSLexer *lexer) {
  if (lexer->lookahead == '\r') {
    lexer->advance(lexer, true);
    if (lexer->lookahead == '\n') {
      lexer->advance(lexer, true);
    }
  } else if (lexer->lookahead == '\n') {
    lexer->advance(lexer, true);
  }
}

// ===== Skip whitespace (spaces and tabs), return number of columns =====
static unsigned skip_whitespace(TSLexer *lexer) {
  unsigned columns = 0;
  for (;;) {
    if (lexer->lookahead == ' ') {
      lexer->advance(lexer, true);
      columns++;
    } else if (lexer->lookahead == '\t') {
      lexer->advance(lexer, true);
      columns += 8;
    } else {
      break;
    }
  }
  return columns;
}

// ===== Skip a comment line =====
static bool skip_comment(TSLexer *lexer) {
  if (lexer->lookahead == '#') {
    while (lexer->lookahead != 0 && lexer->lookahead != '\n') {
      lexer->advance(lexer, false);
    }
    return true;
  }
  return false;
}

// ===== Core scan logic =====
static bool scan(Scanner *scanner, TSLexer *lexer, const bool *valid_symbols) {
  // Only process newline/indent/dedent when valid
  bool has_newline = valid_symbols[NEWLINE];
  bool has_indent = valid_symbols[INDENT];
  bool has_dedent = valid_symbols[DEDENT];

  // If no indentation tokens are requested, do nothing
  if (!has_newline && !has_indent && !has_dedent) {
    return false;
  }

  // Handle explicit newlines in the parse stack
  bool found_newline = false;

  // Handle pending dedents (from previous scan)
  if (has_dedent && scanner->indent_length_stack.size > 1) {
    // The tree-sitter parser may request dedent tokens
    // Pop one level when dedent is expected
    pop_indent(scanner);
    lexer->result_symbol = DEDENT;
    return true;
  }

  // Check for newline characters
  if (lexer->lookahead == '\n' || lexer->lookahead == '\r') {
    skip_newline(lexer);
    found_newline = true;
  }

  // Determine the indentation level of the next non-empty, non-comment line
  unsigned next_indent_length = 0;

  // If we just consumed a newline, check the indentation of the next line
  if (found_newline) {
    // Count leading whitespace
    next_indent_length = skip_whitespace(lexer);

    // Skip empty lines and comment lines
    while (
      lexer->lookahead == '\n' ||
      lexer->lookahead == '\r' ||
      lexer->lookahead == '#'
    ) {
      if (lexer->lookahead == '\n' || lexer->lookahead == '\r') {
        next_indent_length = 0;
        skip_newline(lexer);
        next_indent_length = skip_whitespace(lexer);
      } else if (lexer->lookahead == '#') {
        skip_comment(lexer);
        if (lexer->lookahead == '\n' || lexer->lookahead == '\r') {
          skip_newline(lexer);
          next_indent_length = skip_whitespace(lexer);
        } else {
          // Comment at end of file
          break;
        }
      }
    }

    // End of file: emit dedents
    if (lexer->lookahead == 0) {
      if (has_dedent) {
        pop_indent(scanner);
        lexer->result_symbol = DEDENT;
        return true;
      }
      // If no dedent needed but EOF, emit NEWLINE if requested
      if (has_newline) {
        lexer->result_symbol = NEWLINE;
        return true;
      }
      return false;
    }

    unsigned current = current_indent(scanner);

    if (next_indent_length > current) {
      // Indent level increased
      if (has_indent) {
        push_indent(scanner, next_indent_length);
        lexer->result_symbol = INDENT;
        return true;
      }
      // Otherwise, emit NEWLINE
      if (has_newline) {
        lexer->result_symbol = NEWLINE;
        return true;
      }
    } else if (next_indent_length < current) {
      // Indent level decreased — emit DEDENT and adjust stack
      if (has_dedent) {
        pop_indent(scanner);
        lexer->result_symbol = DEDENT;
        return true;
      }
      if (has_newline) {
        lexer->result_symbol = NEWLINE;
        return true;
      }
    } else {
      // Same indent level — emit NEWLINE
      if (has_newline) {
        lexer->result_symbol = NEWLINE;
        return true;
      }
    }
  }

  return false;
}

// ===== Allocation =====
void *tree_sitter_vyper_external_scanner_create(void) {
  Scanner *scanner = ts_calloc(1, sizeof(Scanner));
  array_init(&scanner->indent_length_stack);
  array_push(&scanner->indent_length_stack, 0);
  return scanner;
}

// ===== Deallocation =====
void tree_sitter_vyper_external_scanner_destroy(void *payload) {
  Scanner *scanner = (Scanner *)payload;
  array_delete(&scanner->indent_length_stack);
  ts_free(scanner);
}

// ===== Serialization =====
unsigned tree_sitter_vyper_external_scanner_serialize(
  void *payload, char *buffer
) {
  Scanner *scanner = (Scanner *)payload;
  size_t size = scanner->indent_length_stack.size;

  if (size * sizeof(uint16_t) > TREE_SITTER_SERIALIZATION_BUFFER_SIZE) {
    return 0;
  }

  memcpy(buffer, scanner->indent_length_stack.contents, size * sizeof(uint16_t));
  return size * sizeof(uint16_t);
}

// ===== Deserialization =====
void tree_sitter_vyper_external_scanner_deserialize(
  void *payload, const char *buffer, unsigned length
) {
  Scanner *scanner = (Scanner *)payload;
  size_t size = length / sizeof(uint16_t);

  array_delete(&scanner->indent_length_stack);
  array_init(&scanner->indent_length_stack);

  for (size_t i = 0; i < size; i++) {
    uint16_t level;
    memcpy(&level, buffer + i * sizeof(uint16_t), sizeof(uint16_t));
    array_push(&scanner->indent_length_stack, level);
  }
}

// ===== Main scan entry point =====
bool tree_sitter_vyper_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  return scan((Scanner *)payload, lexer, valid_symbols);
}
