"""CrewAI Crew for LLM Query Interpretation.

This module implements the InterpreterCrew that orchestrates
the 3-agent workflow: Interpreter → Validator → Refiner.
"""

from pathlib import Path
from typing import Any

import structlog
import yaml
from crewai import LLM, Agent, Crew, Process, Task
from pydantic import BaseModel

from src.config.config import get_settings
from src.schemas.interpreter import (
    InterpretedQuery,
    InterpreterCrewOutput,
    RefinedQuery,
    ValidationResult,
)

logger = structlog.get_logger(__name__)

# Path to config files
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
AGENTS_CONFIG_PATH = CONFIG_DIR / "agents.yaml"
TASKS_CONFIG_PATH = CONFIG_DIR / "tasks.yaml"


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        path: Path to the YAML file.

    Returns:
        Dictionary with configuration data.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        result: dict[str, Any] = yaml.safe_load(f)
        return result


def create_llm(response_format: type[BaseModel] | None = None) -> LLM:
    """Create a configured LLM instance.

    Args:
        response_format: Optional Pydantic model for structured output.

    Returns:
        Configured LLM instance.
    """
    settings = get_settings()

    llm_kwargs: dict[str, Any] = {
        "model": f"openai/{settings.openai_model}",
        "temperature": settings.openai_temperature,
        "timeout": float(settings.openai_timeout),
        "max_retries": settings.openai_max_retries,
    }

    if response_format is not None:
        llm_kwargs["response_format"] = response_format

    return LLM(**llm_kwargs)


class InterpreterCrew:
    """CrewAI Crew for interpreting natural language prompts into SQL queries.

    This crew uses a sequential process with 3 specialized agents:
    1. Interpreter: Converts natural language to structured query intent
    2. Validator: Validates security and catalog compliance
    3. Refiner: Generates and optimizes the final SQL query
    """

    def __init__(self) -> None:
        """Initialize the InterpreterCrew with configuration."""
        self._agents_config = load_yaml_config(AGENTS_CONFIG_PATH)
        self._tasks_config = load_yaml_config(TASKS_CONFIG_PATH)

        # Create agents
        self._interpreter_agent = self._create_agent("interpreter")
        self._validator_agent = self._create_agent("validator")
        self._refiner_agent = self._create_agent("refiner")

        logger.info("InterpreterCrew initialized with 3 agents")

    def _create_agent(self, agent_name: str) -> Agent:
        """Create an agent from YAML configuration.

        Args:
            agent_name: Name of the agent in the config.

        Returns:
            Configured Agent instance.
        """
        config = self._agents_config.get(agent_name, {})

        return Agent(
            role=config.get("role", agent_name),
            goal=config.get("goal", ""),
            backstory=config.get("backstory", ""),
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            llm=create_llm(),
        )

    def _create_task(
        self,
        task_name: str,
        agent: Agent,
        context_tasks: list[Task] | None = None,
        output_pydantic: type[BaseModel] | None = None,
    ) -> Task:
        """Create a task from YAML configuration.

        Args:
            task_name: Name of the task in the config.
            agent: Agent to assign the task to.
            context_tasks: Tasks that provide context for this task.
            output_pydantic: Pydantic model for structured output.

        Returns:
            Configured Task instance.
        """
        config = self._tasks_config.get(task_name, {})

        task_kwargs: dict[str, Any] = {
            "description": config.get("description", ""),
            "expected_output": config.get("expected_output", ""),
            "agent": agent,
        }

        if context_tasks:
            task_kwargs["context"] = context_tasks

        if output_pydantic is not None:
            task_kwargs["output_pydantic"] = output_pydantic

        return Task(**task_kwargs)

    def create_crew(
        self,
    ) -> Crew:
        """Create a Crew configured for query interpretation.

        Returns:
            Configured Crew instance ready to kickoff.
        """
        # Create tasks with structured outputs
        interpret_task = self._create_task(
            "interpret_task",
            self._interpreter_agent,
            output_pydantic=InterpretedQuery,
        )

        validate_task = self._create_task(
            "validate_task",
            self._validator_agent,
            context_tasks=[interpret_task],
            output_pydantic=ValidationResult,
        )

        refine_task = self._create_task(
            "refine_task",
            self._refiner_agent,
            context_tasks=[interpret_task, validate_task],
            output_pydantic=RefinedQuery,
        )

        return Crew(
            agents=[
                self._interpreter_agent,
                self._validator_agent,
                self._refiner_agent,
            ],
            tasks=[interpret_task, validate_task, refine_task],
            process=Process.sequential,
            verbose=True,
        )

    async def interpret(
        self,
        user_prompt: str,
        catalog_context: str,
    ) -> InterpreterCrewOutput:
        """Run the interpretation crew and return structured output.

        Args:
            user_prompt: The natural language prompt from the user.
            catalog_context: The catalog context markdown.

        Returns:
            InterpreterCrewOutput with interpretation, validation, and query.

        Raises:
            Exception: If the crew fails to complete.
        """
        log = logger.bind(prompt_preview=user_prompt[:100])
        log.info("Starting interpretation crew")

        # Create crew
        crew = self.create_crew()

        # Run the crew
        try:
            crew.kickoff(
                inputs={
                    "user_prompt": user_prompt,
                    "catalog_context": catalog_context,
                }
            )

            log.info("Crew completed successfully")

            # Extract structured outputs from tasks
            # Note: CrewAI returns task outputs in order
            tasks = crew.tasks

            # Get outputs and cast to proper types
            interpretation_output = (
                tasks[0].output.pydantic if tasks[0].output else None
            )
            validation_output = tasks[1].output.pydantic if tasks[1].output else None
            refined_output = tasks[2].output.pydantic if tasks[2].output else None

            # Cast to expected types (CrewAI returns BaseModel but we know the actual type)
            interpretation: InterpretedQuery | None = (
                interpretation_output
                if isinstance(interpretation_output, InterpretedQuery)
                or interpretation_output is None
                else None
            )
            validation: ValidationResult | None = (
                validation_output
                if isinstance(validation_output, ValidationResult)
                or validation_output is None
                else None
            )
            refined: RefinedQuery | None = (
                refined_output
                if isinstance(refined_output, RefinedQuery) or refined_output is None
                else None
            )

            # Determine status
            if validation and not validation.is_valid:
                status = "blocked"
            elif interpretation and validation and refined:
                status = "ready"
            else:
                status = "error"

            return InterpreterCrewOutput(
                interpretation=interpretation
                or InterpretedQuery(
                    target_tables=[],
                    natural_explanation="Erro na interpretação",
                    confidence=0.0,
                ),
                validation=validation or ValidationResult(is_valid=False),
                refined_query=refined
                or RefinedQuery(
                    sql_query="",
                    explanation="Erro na geração da query",
                ),
                status=status,
            )

        except Exception as e:
            log.error("Crew failed", error=str(e))
            raise


# Singleton instance
_crew: InterpreterCrew | None = None


def get_interpreter_crew() -> InterpreterCrew:
    """Get the InterpreterCrew singleton."""
    global _crew
    if _crew is None:
        _crew = InterpreterCrew()
    return _crew
