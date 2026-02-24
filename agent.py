"""
Simple AI Agent using Anthropic Claude
Supports multi-turn conversation with built-in tools.
"""

import os
import json
import yaml
import anthropic
from datetime import datetime


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ── Built-in tools ────────────────────────────────────────────────────────────

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def search_memory(query: str, memory: list[dict]) -> str:
    """Rudimentary keyword search over conversation history."""
    hits = [
        m["content"] for m in memory
        if isinstance(m.get("content"), str) and query.lower() in m["content"].lower()
    ]
    return "\n".join(hits) if hits else "No relevant memory found."


TOOLS = [
    {
        "name": "get_current_time",
        "description": "Returns the current date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "calculate",
        "description": "Evaluates a safe mathematical expression and returns the result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python-style math expression, e.g. '2 ** 10 + 5'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "search_memory",
        "description": "Searches the conversation history for relevant past messages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or phrase to search for"}
            },
            "required": ["query"],
        },
    },
]


def dispatch_tool(name: str, inputs: dict, memory: list[dict]) -> str:
    if name == "get_current_time":
        return get_current_time()
    elif name == "calculate":
        return calculate(inputs["expression"])
    elif name == "search_memory":
        return search_memory(inputs["query"], memory)
    return f"Unknown tool: {name}"


# ── Agent loop ────────────────────────────────────────────────────────────────

class Agent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY") or self.config.get("api_key", "")
        )
        self.model = self.config["model"]
        self.max_tokens = self.config["max_tokens"]
        self.system_prompt = self.config["system_prompt"]
        self.memory: list[dict] = []

    def _run_turn(self, user_message: str) -> str:
        self.memory.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=TOOLS,
                messages=self.memory,
            )

            # Collect assistant content blocks
            assistant_content = response.content
            self.memory.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason == "end_turn":
                # Extract text from content blocks
                texts = [b.text for b in assistant_content if hasattr(b, "text")]
                return "\n".join(texts)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        result = dispatch_tool(block.name, block.input, self.memory)
                        print(f"  [tool] {block.name}({block.input}) → {result}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                self.memory.append({"role": "user", "content": tool_results})
                # loop again so Claude can continue
            else:
                # Unexpected stop reason — return whatever text we have
                texts = [b.text for b in assistant_content if hasattr(b, "text")]
                return "\n".join(texts) or f"[stopped: {response.stop_reason}]"

    def chat(self):
        cfg = self.config
        print(f"\n{'='*50}")
        print(f"  {cfg['agent_name']} — {cfg['description']}")
        print(f"  Model : {self.model}")
        print(f"  Tools : {', '.join(t['name'] for t in TOOLS)}")
        print(f"{'='*50}")
        print("Type 'exit' or 'quit' to stop.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            response = self._run_turn(user_input)
            print(f"\nAgent: {response}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = Agent()
    agent.chat()