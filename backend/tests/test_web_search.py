from app.tools.web_search import WebSearchTool


def test_web_search():
    tool = WebSearchTool()

    result = tool.run(
        "official GitHub Copilot pricing"
    )

    assert result.success is True
    assert result.output is not None
    assert result.tool_name == "web_search"