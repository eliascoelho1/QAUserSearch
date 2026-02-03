"""Suggestion Service for error messages and fuzzy matching.

This module provides intelligent suggestions when users encounter errors,
helping them understand what terms are available in the catalog and
suggesting corrections for unrecognized terms.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.catalog import CatalogRepository

logger = structlog.get_logger(__name__)


@dataclass
class SimilarTerm:
    """A term found similar to user input."""

    term: str
    term_type: str  # "table", "column", "value"
    similarity_score: float
    context: str | None = None  # e.g., table name for columns


@dataclass
class SuggestionResult:
    """Result of suggestion generation."""

    original_term: str
    similar_terms: list[SimilarTerm]
    suggestions: list[str]  # Human-readable suggestions
    has_matches: bool


class SuggestionService:
    """Generates suggestions for error recovery and term correction."""

    # Minimum similarity threshold for considering a match
    MIN_SIMILARITY_THRESHOLD = 0.4

    # Common business term mappings to technical terms
    BUSINESS_TERM_MAPPINGS: dict[str, list[str]] = {
        # Status-related terms
        "ativo": ["active", "enabled", "open"],
        "inativo": ["inactive", "disabled", "closed"],
        "bloqueado": ["blocked", "locked", "suspended"],
        "cancelado": ["cancelled", "canceled", "closed"],
        "vencido": ["overdue", "expired", "past_due"],
        "pago": ["paid", "settled", "completed"],
        "pendente": ["pending", "waiting", "processing"],
        # Entity-related terms
        "usuario": ["user", "customer", "client", "account"],
        "usuário": ["user", "customer", "client", "account"],
        "cartao": ["card", "credit_card", "debit_card"],
        "cartão": ["card", "credit_card", "debit_card"],
        "fatura": ["invoice", "bill", "statement"],
        "conta": ["account", "balance", "statement"],
        # Time-related terms
        "hoje": ["today", "current_date"],
        "ontem": ["yesterday"],
        "semana": ["week", "weekly"],
        "mes": ["month", "monthly"],
        "mês": ["month", "monthly"],
        "ano": ["year", "yearly"],
        # Type-related terms
        "credito": ["credit", "credit_card"],
        "crédito": ["credit", "credit_card"],
        "debito": ["debit", "debit_card"],
        "débito": ["debit", "debit_card"],
    }

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the suggestion service.

        Args:
            session: Database session for catalog queries.
        """
        self._session = session
        self._repository = CatalogRepository(session)
        self._catalog_cache: dict[str, Any] | None = None

    async def _load_catalog_cache(self) -> dict[str, Any]:
        """Load and cache catalog data for faster lookups.

        Returns:
            Dictionary with tables and columns information.
        """
        if self._catalog_cache is not None:
            return self._catalog_cache

        tables: dict[str, dict[str, Any]] = {}
        all_columns: list[dict[str, Any]] = []
        all_values: list[dict[str, Any]] = []

        sources = await self._repository.list_sources(limit=100)

        for source in sources:
            full_name = f"{source.db_name}.{source.table_name}"
            columns = await self._repository.get_columns(source.id, limit=1000)

            tables[full_name] = {
                "db_name": source.db_name,
                "table_name": source.table_name,
                "document_count": source.document_count,
                "columns": [col.column_name for col in columns],
            }

            for col in columns:
                all_columns.append(
                    {
                        "name": col.column_name,
                        "table": full_name,
                        "type": col.inferred_type,
                    }
                )

                # Collect enumerable values
                if col.is_enumerable and col.unique_values:
                    for val in col.unique_values:
                        all_values.append(
                            {
                                "value": str(val),
                                "column": col.column_name,
                                "table": full_name,
                            }
                        )

        self._catalog_cache = {
            "tables": tables,
            "columns": all_columns,
            "values": all_values,
        }

        return self._catalog_cache

    def _calculate_similarity(self, term1: str, term2: str) -> float:
        """Calculate similarity ratio between two terms.

        Uses SequenceMatcher for fuzzy string matching.

        Args:
            term1: First term.
            term2: Second term.

        Returns:
            Similarity ratio between 0.0 and 1.0.
        """
        return SequenceMatcher(None, term1.lower(), term2.lower()).ratio()

    def _find_business_term_matches(self, term: str) -> list[str]:
        """Find technical terms that match a business term.

        Args:
            term: The business term to look up.

        Returns:
            List of potential technical terms.
        """
        term_lower = term.lower()
        matches: list[str] = []

        # Direct mapping lookup
        if term_lower in self.BUSINESS_TERM_MAPPINGS:
            matches.extend(self.BUSINESS_TERM_MAPPINGS[term_lower])

        # Partial match lookup
        for business_term, tech_terms in self.BUSINESS_TERM_MAPPINGS.items():
            if business_term in term_lower or term_lower in business_term:
                matches.extend(tech_terms)

        return list(set(matches))

    async def find_similar_tables(
        self, term: str, max_results: int = 5
    ) -> list[SimilarTerm]:
        """Find tables similar to a given term.

        Args:
            term: The term to find matches for.
            max_results: Maximum number of results to return.

        Returns:
            List of similar table names with scores.
        """
        catalog = await self._load_catalog_cache()
        similar: list[SimilarTerm] = []

        # Check business term mappings first
        tech_terms = self._find_business_term_matches(term)

        for table_name in catalog["tables"]:
            # Calculate base similarity
            score = self._calculate_similarity(term, table_name)

            # Boost score if tech term matches
            for tech_term in tech_terms:
                if tech_term.lower() in table_name.lower():
                    score = max(score, 0.7)

            if score >= self.MIN_SIMILARITY_THRESHOLD:
                similar.append(
                    SimilarTerm(
                        term=table_name,
                        term_type="table",
                        similarity_score=score,
                    )
                )

        # Sort by similarity score descending
        similar.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar[:max_results]

    async def find_similar_columns(
        self, term: str, table_filter: str | None = None, max_results: int = 5
    ) -> list[SimilarTerm]:
        """Find columns similar to a given term.

        Args:
            term: The term to find matches for.
            table_filter: Optional table name to filter columns.
            max_results: Maximum number of results to return.

        Returns:
            List of similar column names with scores.
        """
        catalog = await self._load_catalog_cache()
        similar: list[SimilarTerm] = []

        # Check business term mappings
        tech_terms = self._find_business_term_matches(term)

        for col in catalog["columns"]:
            # Filter by table if specified
            if table_filter and col["table"] != table_filter:
                continue

            # Calculate similarity
            score = self._calculate_similarity(term, col["name"])

            # Boost score for tech term matches
            for tech_term in tech_terms:
                if tech_term.lower() in col["name"].lower():
                    score = max(score, 0.7)

            if score >= self.MIN_SIMILARITY_THRESHOLD:
                similar.append(
                    SimilarTerm(
                        term=col["name"],
                        term_type="column",
                        similarity_score=score,
                        context=col["table"],
                    )
                )

        # Sort by similarity score descending
        similar.sort(key=lambda x: x.similarity_score, reverse=True)
        return similar[:max_results]

    async def find_similar_values(
        self, term: str, column_filter: str | None = None, max_results: int = 5
    ) -> list[SimilarTerm]:
        """Find enumerable values similar to a given term.

        Args:
            term: The term to find matches for.
            column_filter: Optional column name to filter values.
            max_results: Maximum number of results to return.

        Returns:
            List of similar values with scores.
        """
        catalog = await self._load_catalog_cache()
        similar: list[SimilarTerm] = []

        # Check business term mappings
        tech_terms = self._find_business_term_matches(term)

        for val in catalog["values"]:
            # Filter by column if specified
            if column_filter and val["column"] != column_filter:
                continue

            # Calculate similarity
            score = self._calculate_similarity(term, val["value"])

            # Boost score for tech term matches
            for tech_term in tech_terms:
                if tech_term.lower() == val["value"].lower():
                    score = 1.0
                elif tech_term.lower() in val["value"].lower():
                    score = max(score, 0.8)

            if score >= self.MIN_SIMILARITY_THRESHOLD:
                similar.append(
                    SimilarTerm(
                        term=val["value"],
                        term_type="value",
                        similarity_score=score,
                        context=f"{val['table']}.{val['column']}",
                    )
                )

        # Sort by similarity score descending and deduplicate
        similar.sort(key=lambda x: x.similarity_score, reverse=True)

        # Remove duplicates keeping highest score
        seen_terms: set[str] = set()
        unique_similar: list[SimilarTerm] = []
        for item in similar:
            if item.term not in seen_terms:
                seen_terms.add(item.term)
                unique_similar.append(item)

        return unique_similar[:max_results]

    async def generate_suggestions_for_term(
        self, term: str, max_suggestions: int = 5
    ) -> SuggestionResult:
        """Generate suggestions for an unrecognized term.

        Args:
            term: The unrecognized term from user input.
            max_suggestions: Maximum number of suggestions to generate.

        Returns:
            SuggestionResult with similar terms and human-readable suggestions.
        """
        log = logger.bind(term=term)
        log.info("Generating suggestions for unrecognized term")

        all_similar: list[SimilarTerm] = []

        # Find similar tables
        similar_tables = await self.find_similar_tables(term, max_results=3)
        all_similar.extend(similar_tables)

        # Find similar columns
        similar_columns = await self.find_similar_columns(term, max_results=3)
        all_similar.extend(similar_columns)

        # Find similar values
        similar_values = await self.find_similar_values(term, max_results=3)
        all_similar.extend(similar_values)

        # Sort all by similarity score
        all_similar.sort(key=lambda x: x.similarity_score, reverse=True)
        top_similar = all_similar[:max_suggestions]

        # Generate human-readable suggestions
        suggestions = self._generate_human_suggestions(term, top_similar)

        has_matches = len(top_similar) > 0

        if not has_matches:
            # Provide generic suggestions if no matches found
            suggestions = [
                f"O termo '{term}' não foi encontrado no catálogo.",
                "Verifique a ortografia ou use termos mais comuns.",
                "Consulte o catálogo para ver as tabelas e colunas disponíveis.",
            ]

        log.info(
            "Suggestions generated",
            term=term,
            num_similar=len(top_similar),
            has_matches=has_matches,
        )

        return SuggestionResult(
            original_term=term,
            similar_terms=top_similar,
            suggestions=suggestions,
            has_matches=has_matches,
        )

    def _generate_human_suggestions(
        self, _term: str, similar_terms: list[SimilarTerm]
    ) -> list[str]:
        """Generate human-readable suggestions from similar terms.

        Args:
            _term: The original term (unused, kept for potential future use).
            similar_terms: List of similar terms found.

        Returns:
            List of suggestion strings in Portuguese.
        """
        suggestions: list[str] = []

        if not similar_terms:
            return suggestions

        # Group by type
        tables = [s for s in similar_terms if s.term_type == "table"]
        columns = [s for s in similar_terms if s.term_type == "column"]
        values = [s for s in similar_terms if s.term_type == "value"]

        if tables:
            table_names = ", ".join(f"'{t.term}'" for t in tables[:3])
            suggestions.append(f"Você quis dizer uma destas tabelas? {table_names}")

        if columns:
            col_info = [
                f"'{c.term}' (em {c.context})" if c.context else f"'{c.term}'"
                for c in columns[:3]
            ]
            suggestions.append(f"Colunas similares encontradas: {', '.join(col_info)}")

        if values:
            val_info = [
                f"'{v.term}' ({v.context})" if v.context else f"'{v.term}'"
                for v in values[:3]
            ]
            suggestions.append(f"Valores similares: {', '.join(val_info)}")

        return suggestions

    async def generate_no_results_suggestions(
        self, interpreted_tables: list[str], interpreted_filters: list[dict[str, Any]]
    ) -> list[str]:
        """Generate suggestions when a query returns no results.

        Args:
            interpreted_tables: Tables that were queried.
            interpreted_filters: Filters that were applied.

        Returns:
            List of suggestions for broadening the search.
        """
        suggestions: list[str] = []

        suggestions.append(
            "A consulta não retornou resultados. Tente as seguintes alternativas:"
        )

        # Suggest removing filters
        if interpreted_filters:
            suggestions.append(
                "- Remova alguns filtros para ampliar a busca. "
                f"Você aplicou {len(interpreted_filters)} filtro(s)."
            )

            # Suggest specific filter removals
            for f in interpreted_filters[:3]:
                field = f.get("field", f.get("column", "campo"))
                value = f.get("value", "")
                suggestions.append(f"- Tente sem o filtro '{field} = {value}'.")

        # Suggest checking the data
        if interpreted_tables:
            table_list = ", ".join(interpreted_tables)
            suggestions.append(
                f"- Verifique se existem dados nas tabelas: {table_list}"
            )

        # Generic suggestions
        suggestions.append("- Use termos mais genéricos na sua busca.")
        suggestions.append(
            "- Verifique se os valores dos filtros existem no banco de dados."
        )

        return suggestions

    async def generate_error_suggestions(
        self, error_code: str, context: dict[str, Any] | None = None
    ) -> list[str]:
        """Generate suggestions based on error code.

        Args:
            error_code: The error code from the system.
            context: Additional context about the error.

        Returns:
            List of actionable suggestions.
        """
        suggestions: list[str] = []
        context = context or {}

        error_suggestions: dict[str, list[str]] = {
            "INVALID_PROMPT": [
                "Descreva o tipo de dados que você precisa buscar.",
                "Use termos de negócio como 'usuários', 'faturas', 'cartões'.",
                "Especifique filtros como 'ativos', 'bloqueados', 'vencidos'.",
            ],
            "PROMPT_TOO_LONG": [
                "Reduza o tamanho do prompt para menos de 2000 caracteres.",
                "Divida sua busca em consultas menores.",
                "Remova detalhes desnecessários.",
            ],
            "SQL_COMMAND_BLOCKED": [
                "Reformule seu pedido para buscar dados em vez de modificá-los.",
                "Use termos como 'buscar', 'encontrar', 'listar'.",
                "Apenas consultas de leitura (SELECT) são permitidas.",
            ],
            "LLM_TIMEOUT": [
                "Simplifique seu prompt.",
                "Divida em buscas menores.",
                "Tente novamente em alguns segundos.",
            ],
            "NO_TABLES_FOUND": [
                "Verifique se as tabelas mencionadas existem no catálogo.",
                "Use nomes de tabelas do catálogo disponível.",
            ],
            "NO_COLUMNS_FOUND": [
                "Verifique se as colunas mencionadas existem na tabela.",
                "Consulte o esquema da tabela para ver as colunas disponíveis.",
            ],
            "AMBIGUOUS_PROMPT": [
                "Seja mais específico sobre qual tipo de dados você busca.",
                "Escolha entre os significados possíveis do termo.",
            ],
            "INTERPRETATION_ERROR": [
                "Tente reformular o prompt.",
                "Verifique se os termos usados existem no catálogo.",
                "Use termos mais simples e diretos.",
            ],
        }

        if error_code in error_suggestions:
            suggestions.extend(error_suggestions[error_code])
        else:
            # Generic suggestions for unknown errors
            suggestions.extend(
                [
                    "Tente reformular sua consulta.",
                    "Verifique se os termos usados estão corretos.",
                    "Se o problema persistir, entre em contato com o suporte.",
                ]
            )

        # Add context-specific suggestions
        if context.get("unrecognized_term"):
            term = context["unrecognized_term"]
            result = await self.generate_suggestions_for_term(term)
            suggestions.extend(result.suggestions)

        return suggestions


# Dependency injection helper
def get_suggestion_service(session: AsyncSession) -> SuggestionService:
    """Create a SuggestionService with the given session."""
    return SuggestionService(session)
