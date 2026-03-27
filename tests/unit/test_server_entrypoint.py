"""Unit tests for the negentropy-perceives server entrypoint."""

from types import SimpleNamespace

import negentropy.perceives.server as server_module


class TestServerMain:
    """测试服务启动入口打印与参数透传。"""

    def test_main_prints_resolved_settings(self, capsys, monkeypatch):
        mock_settings = SimpleNamespace(
            server_name="negentropy-perceives",
            server_version="0.1.6.1",
            transport_mode="http",
            enable_javascript=False,
            use_random_user_agent=True,
            use_proxy=False,
            http_host="127.0.0.1",
            http_port=8082,
            http_path="/mcp",
            http_cors_origins="*",
        )

        app_calls = []

        def fake_run(**kwargs):
            app_calls.append(kwargs)

        monkeypatch.setattr(server_module, "settings", mock_settings)
        monkeypatch.setattr(server_module.app, "run", fake_run)
        monkeypatch.setattr(server_module.sys, "argv", ["negentropy-perceives"])

        server_module.main()

        output = capsys.readouterr().out
        assert "CLI entrypoint: negentropy-perceives" in output
        assert "Resolved settings: server_name=negentropy-perceives" in output
        assert "port=8082" in output
        assert app_calls == [
            {
                "transport": "http",
                "host": "127.0.0.1",
                "port": 8082,
                "path": "/mcp",
            }
        ]
