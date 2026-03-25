from execution_engine.llm.prompt_builder import PromptBuilder


def test_prompt_contains_ifu_and_json_instruction():
    builder = PromptBuilder()
    prompt = builder.build("Test IFU")

    assert "Test IFU" in prompt
    assert "Return JSON" in prompt


def test_prompt_includes_capability_hints():
    builder = PromptBuilder()
    prompt = builder.build("Test IFU", capability_hints={"tips": ["FCA_DiTi_200uL"]})

    assert "Capability hints" in prompt
    assert "FCA_DiTi_200uL" in prompt
