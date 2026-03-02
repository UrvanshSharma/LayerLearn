"""
Tests — Agent Memory
"""

from core.memory import AgentMemory, Turn


class TestAgentMemory:
    def test_add_user(self):
        mem = AgentMemory()
        mem.add_user("hello")
        assert len(mem.turns) == 1
        assert mem.turns[0].role == "user"
        assert mem.turns[0].content == "hello"

    def test_add_assistant(self):
        mem = AgentMemory()
        mem.add_assistant("hi there")
        assert len(mem.turns) == 1
        assert mem.turns[0].role == "assistant"

    def test_add_tool(self):
        mem = AgentMemory()
        mem.add_tool("capture_screen", "analysis result here")
        assert len(mem.turns) == 1
        assert mem.turns[0].tool_name == "capture_screen"

    def test_to_messages(self):
        mem = AgentMemory()
        mem.add_user("look at my screen")
        mem.add_tool("capture_screen", "I see code")
        mem.add_assistant("The screen shows Python code")

        msgs = mem.to_messages()
        assert len(msgs) == 3
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"  # tool results mapped to assistant
        assert "[Tool: capture_screen]" in msgs[1]["content"]
        assert msgs[2]["role"] == "assistant"

    def test_trim(self):
        mem = AgentMemory()
        for i in range(30):
            mem.add_user(f"msg {i}")
        # Default max_memory_turns is 20
        assert len(mem.turns) <= 20

    def test_clear(self):
        mem = AgentMemory()
        mem.add_user("hello")
        mem.current_task = "testing"
        mem.clear()
        assert len(mem.turns) == 0
        assert mem.current_task is None
