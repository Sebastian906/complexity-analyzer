"""
Parser de Pseudocódigo

Implementa el parser principal usando Lark para convertir pseudocódigo
en un Abstract Syntax Tree (AST).
"""

from pathlib import Path
from typing import Optional

from lark import Lark, Tree, Token
from lark.exceptions import (
    LarkError,
    ParseError,
    UnexpectedCharacters,
    UnexpectedToken,
)

from app.core.config import settings
from app.core.exceptions import (
    ParserException,
    SyntaxErrorException,
    TokenizationException,
)
from app.core.parser.ast_builder import ASTBuilder
from app.core.parser.ast_nodes import ProgramNode
from app.utils.logger import setup_logger, LoggerContextManager

logger = setup_logger(__name__)

class PseudocodeParser:
    """
    Parser principal de pseudocódigo.

    Utiliza Lark para el parsing y un ASTBuilder para construir el AST.

    Attributes:
        parser: Instancia de Lark parser
        ast_builder: Constructor de AST

    Example:
        >>> parser = PseudocodeParser()
        >>> ast = parser.parse(code)
        >>> print(ast.algorithm.name)
    """

    def __init__(self):
        """Inicializa el parser cargando la gramática"""
        self.grammar_path = Path(__file__).parent / "grammar" / "pseudocode.lark"

        if not self.grammar_path.exists():
            raise FileNotFoundError(
                f"Archivo de gramática no encontrado: {self.grammar_path}"
            )

        logger.info(f"Cargando gramática desde: {self.grammar_path}")

        try:
            # Cargar gramática y crear parser
            with open(self.grammar_path, 'r', encoding='utf-8') as f:
                grammar = f.read()

            self.parser = Lark(
                grammar,
                start='start',
                parser='lalr',  # LALR es más rápido que Earley
                propagate_positions=True,  # Mantener info de línea/columna
                maybe_placeholders=False,
                cache=True  # Cachear la gramática compilada
            )

            logger.info("Parser inicializado correctamente")

        except Exception as e:
            logger.error(f"Error al cargar gramática: {e}")
            raise ParserException(
                message="Error al inicializar el parser",
                details={"error": str(e)}
            )

        # Inicializar constructor de AST
        self.ast_builder = ASTBuilder()

    def parse(
        self,
        code: str,
        validate: bool = True,
        timeout: Optional[int] = None
    ) -> ProgramNode:
        """
        Parsea código pseudocódigo y retorna el AST.

        Args:
            code: Código pseudocódigo a parsear
            validate: Si True, valida el código antes de parsear
            timeout: Timeout en segundos (usa settings.PARSER_TIMEOUT si None)

        Returns:
            ProgramNode: Raíz del AST

        Raises:
            SyntaxErrorException: Si hay errores de sintaxis
            TokenizationException: Si hay errores de tokenización
            ParserException: Otros errores de parsing

        Example:
            >>> parser = PseudocodeParser()
            >>> code = '''
            ... algorithm test(n)
            ... begin
            ...     for i ← 1 to n do
            ...         x ← x + 1
            ... end
            ... '''
            >>> ast = parser.parse(code)
        """
        timeout = timeout or settings.PARSER_TIMEOUT

        with LoggerContextManager("parse_algorithm", code_length=len(code)):
            # Validación previa
            if validate:
                self._validate_code(code)

            try:
                # Parsear con Lark
                logger.debug("Iniciando parsing con Lark")
                parse_tree = self.parser.parse(code)

                logger.debug(f"Parse tree generado: {parse_tree.data}")

                # Construir AST desde parse tree
                logger.debug("Construyendo AST")
                ast = self.ast_builder.transform(parse_tree)

                logger.info(f"Parsing completado: {ast.algorithm.name if ast.algorithm else 'N/A'}")

                return ast

            except UnexpectedCharacters as e:
                logger.error(f"Caracter inesperado en línea {e.line}, columna {e.column}")
                raise TokenizationException(
                    message=f"Caracter inesperado: '{e.char}'",
                    position=e.pos_in_stream
                )

            except UnexpectedToken as e:
                expected = ", ".join(str(t) for t in e.expected)
                logger.error(f"Token inesperado en línea {e.line}, columna {e.column}")
                raise SyntaxErrorException(
                    message=f"Token inesperado: '{e.token}'",
                    line=e.line,
                    column=e.column,
                    expected=expected,
                    got=str(e.token)
                )

            except ParseError as e:
                logger.error(f"Error de parsing: {e}")
                raise SyntaxErrorException(
                    message="Error de sintaxis en el código",
                    line=getattr(e, 'line', None),
                    column=getattr(e, 'column', None)
                )

            except LarkError as e:
                logger.error(f"Error de Lark: {e}")
                raise ParserException(
                    message="Error durante el parsing",
                    details={"error": str(e)}
                )

            except Exception as e:
                logger.exception(f"Error inesperado durante parsing: {e}")
                raise ParserException(
                    message="Error inesperado durante el parsing",
                    details={"error": str(e)}
                )

    def _validate_code(self, code: str) -> None:
        """
        Valida el código antes de parsear.

        Args:
            code: Código a validar

        Raises:
            ValidationException: Si el código no pasa las validaciones
        """
        from app.core.exceptions import AlgorithmTooLargeException

        # Validar longitud
        if len(code) > settings.MAX_ALGORITHM_SIZE_KB * 1024:
            raise AlgorithmTooLargeException(
                size=len(code),
                max_size=settings.MAX_ALGORITHM_SIZE_KB * 1024
            )

        # Validar número de líneas
        lines = code.count('\n') + 1
        if lines > settings.MAX_ALGORITHM_LINES:
            raise AlgorithmTooLargeException(
                size=lines,
                max_size=settings.MAX_ALGORITHM_LINES
            )

        # Validar que no esté vacío
        if not code.strip():
            raise ParserException(
                message="El código está vacío",
                error_code="EMPTY_CODE"
            )

        logger.debug(f"Código validado: {lines} líneas, {len(code)} caracteres")

    def parse_from_file(self, file_path: str) -> ProgramNode:
        """
        Parsea código desde un archivo.

        Args:
            file_path: Ruta al archivo

        Returns:
            ProgramNode: AST del código
        """
        logger.info(f"Parseando archivo: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            return self.parse(code)

        except FileNotFoundError:
            raise ParserException(
                message=f"Archivo no encontrado: {file_path}",
                error_code="FILE_NOT_FOUND"
            )
        except UnicodeDecodeError as e:
            raise ParserException(
                message=f"Error de codificación al leer archivo: {e}",
                error_code="ENCODING_ERROR"
            )

    def get_parse_tree(self, code: str) -> Tree:
        """
        Obtiene el parse tree de Lark sin construir AST.

        Útil para debugging y testing.

        Args:
            code: Código a parsear

        Returns:
            Tree: Parse tree de Lark
        """
        try:
            return self.parser.parse(code)
        except LarkError as e:
            raise ParserException(
                message="Error obteniendo parse tree",
                details={"error": str(e)}
            )

    def pretty_print_tree(self, code: str) -> str:
        """
        Retorna representación bonita del parse tree.

        Args:
            code: Código a parsear

        Returns:
            str: Parse tree formateado
        """
        tree = self.get_parse_tree(code)
        return tree.pretty()

# Función Helper para uso directo

def parse_pseudocode(code: str) -> ProgramNode:
    """
    Helper function para parsear pseudocódigo rápidamente.

    Args:
        code: Código pseudocódigo

    Returns:
        ProgramNode: AST del código

    Example:
        >>> from app.core.parser import parse_pseudocode
        >>> ast = parse_pseudocode("algorithm test(n)\\nbegin\\n  x ← 1\\nend")
    """
    parser = PseudocodeParser()
    return parser.parse(code)