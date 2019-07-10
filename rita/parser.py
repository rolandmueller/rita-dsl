import logging

import ply.yacc as yacc

from functools import partial

from rita.lexer import RitaLexer
from rita import macros

logger = logging.getLogger(__name__)


def stub(*args, **kwargs):
    return None


def var_wrapper(variable):
    def wrapper(*args, **kwargs):
        logger.debug("Variables: {}".format(macros.VARIABLES))
        return macros.VARIABLES[variable]

    return wrapper


class RitaParser(object):
    tokens = RitaLexer.tokens
    precedence = (
        ("nonassoc", "ARROW"),
        ("nonassoc", "COMMA"),
        ("left", "ASSIGN"),
        ("left", "RBRACKET", "LBRACKET"),
        ("left", "KEYWORD", "NAME", "LITERAL"),
        ("right", "MODIF_QMARK", "MODIF_STAR", "MODIF_PLUS"),
    )

    def p_document(self, p):
        """
        DOCUMENT : MACRO_CHAIN
                 | VARIABLE
        """
        logger.debug("Building initial document {}".format(p[1]))
        p[0] = [p[1]]

    def p_document_list(self, p):
        """
        DOCUMENT : DOCUMENT MACRO_CHAIN
                 | DOCUMENT VARIABLE
        """
        logger.debug("Extending document {}".format(p[2]))
        p[0] = p[1] + [p[2]]

    def p_macro_chain(self, p):
        " MACRO_CHAIN : MACRO ARROW MACRO "
        logger.debug("Have {0} -> {1}".format(p[1], p[3]))
        p[0] = partial(p[3], p[1])

    def p_macro_w_modif(self, p):
        """
        MACRO : MACRO MODIF_PLUS
              | MACRO MODIF_STAR
              | MACRO MODIF_QMARK
        """
        logger.debug("Adding modifier to Macro {}".format(p[1]))
        fn = p[1]
        p[0] = partial(fn, op=p[2])

    def p_macro_wo_args(self, p):
        " MACRO : KEYWORD "
        fn = getattr(macros, p[1])
        logger.debug("Parsing macro (w/o args): {}".format(p[1]))
        p[0] = fn

    def p_macro_w_args(self, p):
        " MACRO : KEYWORD LBRACKET ARGS RBRACKET "
        logger.debug("Parsing macro: {0}, args: {1}".format(p[1], p[3]))
        fn = getattr(macros, p[1])
        p[0] = partial(fn, *p[3])

    def p_variable(self, p):
        " VARIABLE_NAME : NAME "
        p[0] = var_wrapper(p[1])

    def p_variable_from_arg(self, p):
        " VARIABLE : NAME ASSIGN ARG "
        macros.ASSIGN(p[1], p[3])

    def p_arg_list(self, p):
        " ARGS : ARGS COMMA ARG "
        p[0] = p[1] + [p[3]]

    def p_args(self, p):
        " ARGS : ARG "
        p[0] = [p[1]]

    def p_arg(self, p):
        " ARG : LITERAL "
        p[0] = p[1]

    def p_arg_from_macro(self, p):
        " ARG : MACRO "
        p[0] = p[1]

    def p_arg_from_var(self, p):
        " ARG : VARIABLE_NAME "
        p[0] = p[1](context={})

    def p_error(self, p):
        logger.error("Syntax error at '{}'".format(p.value))

    def build(self, **kwargs):
        self.lexer = RitaLexer().build(**kwargs)
        self.parser = yacc.yacc(module=self, errorlog=logger, **kwargs)

    def parse(self, data):
        return self.parser.parse(data, lexer=self.lexer, debug=logger)
