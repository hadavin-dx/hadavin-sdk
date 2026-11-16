"""Model input and output (design 8.1, amendments A-01).

INPUT: all variable text goes in ONE user message (`PART_A + PART_B`); the system prompt is a fixed constant under a
hash test, so nothing can hide there and a retry has the same shape on every route (no assistant turns, no
tool_use/tool_result pairing). PART_A is the rendered prompt (rules, `as_of`, catalog, glossary, exemplars);
PART_B is the question and, on a retry, the previous SQL and the fixed hint.

OUTPUT: the core forces a tool named `submit_answer` from `output_schema`. Parse order: exactly one such tool call,
else (cut off or no tool call) the first JSON object in the text; a failure at any step is a `SchemaViolation`.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from askdata.policy import ABSTAIN_REASONS
from askdata.safe_text import clean
from hadavin_sdk.llm.common import ANSWER_TOOL, json_in_text
from hadavin_sdk.models import Reply

SYSTEM = (
    "You write one read-only PostgreSQL SELECT for the user's question, or abstain. "
    "Follow the instructions in the user message."
)
MAX_SQL_CHARS = 4000
SCHEMA_HINT = "schema: answer by calling submit_answer with the required fields"


class SchemaViolation(ValueError):
    """The model's answer is not a usable `GenerateOutput`. The message is fixed text, never the model's words."""


class GenerateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["answer", "abstain"]
    abstain_reason: (
        Literal[
            "out_of_scope", "ambiguous", "write_request", "restricted_data", "insufficient_schema"
        ]
        | None
    ) = None
    clarifying_question: str | None = None
    sql: str | None = None
    assumptions: list[str] = []
    tables_used: list[str] = []

    @model_validator(mode="after")
    def _shape(self) -> GenerateOutput:
        if self.decision == "answer":
            if not self.sql or not self.sql.strip() or self.abstain_reason is not None:
                raise ValueError("an answer needs sql and no abstain_reason")
        elif self.abstain_reason is None or self.sql is not None:
            raise ValueError("an abstain needs an abstain_reason and no sql")
        return self


GENERATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decision"],
    "properties": {
        "decision": {"type": "string", "enum": ["answer", "abstain"]},
        "abstain_reason": {"type": ["string", "null"], "enum": [*ABSTAIN_REASONS, None]},
        "clarifying_question": {"type": ["string", "null"]},
        "sql": {
            "type": ["string", "null"],
            "description": "one SELECT over the exposed views, schema-qualified",
        },
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "tables_used": {"type": "array", "items": {"type": "string"}},
    },
}


def part_b(question: str, previous_sql: str | None = None, hint: str | None = None) -> str:
    text = f"## Question\n{clean(question)}"
    if previous_sql is not None:
        text += f"\n\n## Previous attempt\n{clean(previous_sql)}"
    if hint is not None:
        text += f"\n\n## Rejected by\n{clean(hint)}"
    return text


def build_messages(
    part_a: str, question: str, previous_sql: str | None = None, hint: str | None = None
) -> list[dict[str, Any]]:
    """Always exactly one user message."""
    return [{"role": "user", "content": part_a + "\n\n" + part_b(question, previous_sql, hint)}]


def parse_reply(reply: Reply) -> GenerateOutput:
    payload: Any
    if len(reply.tool_calls) == 1 and reply.tool_calls[0].name == ANSWER_TOOL:
        payload = reply.tool_calls[0].input
    elif (
        not reply.tool_calls
    ):  # cut off (the core drops tool calls then) or a model that answered in text
        payload = json_in_text(reply.text)
    else:
        raise SchemaViolation("unexpected tool calls")
    if payload is None:
        raise SchemaViolation("no structured answer")
    try:
        out = GenerateOutput.model_validate(payload)
    except ValidationError:
        raise SchemaViolation("the answer does not match the schema") from None
    if out.sql is not None and len(out.sql) > MAX_SQL_CHARS:
        raise SchemaViolation("sql too long")
    return out
