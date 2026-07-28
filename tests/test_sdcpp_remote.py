import base64
import io

import pytest
from PIL import Image

from core.ml import sdcpp_server
from utils.exceptions import ModelError


def _encoded_image() -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" http://127.0.0.1:1234/ ", "http://127.0.0.1:1234"),
        ("https://example.test/sd///", "https://example.test/sd"),
    ],
)
def test_normalize_sdcpp_server_url(value, expected):
    assert sdcpp_server.normalize_sdcpp_server_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "127.0.0.1:1234",
        "ftp://example.test",
        "http://user:secret@example.test",
        "http://example.test?token=secret",
        "http://example.test:invalid",
    ],
)
def test_normalize_sdcpp_server_url_rejects_invalid_values(value):
    with pytest.raises(ModelError):
        sdcpp_server.normalize_sdcpp_server_url(value)


def test_connect_remote_server_is_non_owning(tmp_path, monkeypatch):
    manager = sdcpp_server.SDCppServerManager(tmp_path)
    monkeypatch.setattr(manager, "_server_ready", lambda _url: True)
    monkeypatch.setattr(
        sdcpp_server.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("remote mode started a process"),
    )

    server = manager.connect_remote_server(
        "http://127.0.0.1:1234/", "flux_klein_4b"
    )

    assert server == {
        "url": "http://127.0.0.1:1234",
        "model_key": "flux_klein_4b",
        "remote": True,
    }
    assert manager._servers == {}


def test_connect_remote_server_rejects_failed_preflight(tmp_path, monkeypatch):
    manager = sdcpp_server.SDCppServerManager(tmp_path)
    monkeypatch.setattr(manager, "_server_ready", lambda _url: False)

    with pytest.raises(ModelError, match="not reachable"):
        manager.connect_remote_server("http://127.0.0.1:1234", "flux_kontext")


def test_run_image_job_accepts_synchronous_result(monkeypatch):
    calls = []

    def fake_json_request(url, payload=None, timeout=None):
        calls.append((url, payload, timeout))
        return {"status": "completed", "images": [{"b64_json": _encoded_image()}]}

    monkeypatch.setattr(sdcpp_server, "_json_request", fake_json_request)
    payload = {"prompt": "Remove all text."}

    image = sdcpp_server.run_image_job(
        {"url": "http://example.test/base/", "remote": True}, payload
    )

    assert image.size == (2, 2)
    assert calls == [
        ("http://example.test/base/sdcpp/v1/img_gen", payload, 30)
    ]


def test_run_image_job_polls_queued_result(monkeypatch):
    calls = []
    responses = iter(
        [
            {"id": "job-1"},
            {"status": "running"},
            {
                "status": "completed",
                "result": {"images": [{"b64_json": _encoded_image()}]},
            },
        ]
    )

    def fake_json_request(url, payload=None, timeout=None):
        calls.append((url, payload, timeout))
        return next(responses)

    monkeypatch.setattr(sdcpp_server, "_json_request", fake_json_request)
    monkeypatch.setattr(sdcpp_server.time, "sleep", lambda _seconds: None)

    image = sdcpp_server.run_image_job(
        {"url": "http://example.test", "remote": True}, {"prompt": "edit"}
    )

    assert image.size == (2, 2)
    assert [call[0] for call in calls] == [
        "http://example.test/sdcpp/v1/img_gen",
        "http://example.test/sdcpp/v1/jobs/job-1",
        "http://example.test/sdcpp/v1/jobs/job-1",
    ]
