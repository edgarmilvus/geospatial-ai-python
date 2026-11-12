"""A scripted chat model that calls tools, for harnesses of function-calling agents.

`FakeListChatModel` returns text, which is what a ReAct parser wants. A tool-calling
agent wants something else: an assistant message whose `tool_calls` name a tool and
carry its arguments, followed by an assistant message with the final answer. This
model returns exactly those messages, in order, so the harness drives the same
executor the listing builds without a key and without a network.

    model = ScriptedToolCallingModel([
        ("count_buildings", {"damage_class": "Destroyed"}),
        ("total_area", {"damage_class": "Destroyed"}),
    ], final="Four buildings, 920 square metres.")
    executor = module.build_executor(model)
"""
from __future__ import annotations

import itertools
import uuid

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedToolCallingModel(BaseChatModel):
    """Return one tool call per step, then the final answer."""

    calls: list = []
    final: str = "done"
    _index: object = None

    def __init__(self, calls, final="done", **kwargs):
        super().__init__(**kwargs)
        self.calls = list(calls)
        self.final = final
        self._index = itertools.count()

    @property
    def _llm_type(self) -> str:
        return "scripted-tool-calling"

    def bind_tools(self, tools, **kwargs):
        # The real model needs the tool schemas; the script does not, but the
        # agent builder calls this, so it has to return something callable.
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        step = next(self._index)
        if step < len(self.calls):
            name, args = self.calls[step]
            message = AIMessage(
                content="",
                tool_calls=[{"name": name, "args": args,
                             "id": "call_%s" % uuid.uuid4().hex[:8]}],
            )
        else:
            message = AIMessage(content=self.final)
        return ChatResult(generations=[ChatGeneration(message=message)])
