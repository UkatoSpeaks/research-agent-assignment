from app.tools.page_fetcher import PageFetcherTool


def test_page_fetcher():
    tool = PageFetcherTool()

    result = tool.run(
        "https://example.com"
    )

    assert result.success is True
    assert result.output is not None
    assert result.tool_name == "page_fetcher"
    assert result.output["status_code"] == 200
    assert result.output["text"]


def test_page_fetcher_empty_url():
    tool = PageFetcherTool()

    result = tool.run("")

    assert result.success is False
    assert result.error is not None