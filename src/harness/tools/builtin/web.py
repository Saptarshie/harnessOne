"""Web fetch tool."""


def register_web_tool(registry):
    def fetch_url(params: dict) -> str:
        url = params["url"]
        format_type = params.get("format", "text")

        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, headers={"User-Agent": "CognitiveHarness/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8", errors="replace")

            if format_type == "text":
                import re
                content = re.sub(r"<[^>]+>", " ", content)
                content = re.sub(r"\s+", " ", content).strip()

            return content[:20000]
        except Exception as e:
            return f"Error fetching {url}: {e}"

    registry.register(
        name="fetch_url",
        description="Fetch content from a URL",
        parameters={
            "url": {"type": "string", "description": "URL to fetch", "required": True},
            "format": {"type": "string", "description": "Output format: 'text' or 'html'", "enum": ["text", "html"]},
        },
        handler=fetch_url,
    )
