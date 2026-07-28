import threading
from pathlib import Path
from unittest.mock import ANY

import numpy as np
import pytest
import torch
from PIL import Image

from core import outside_text_processor
from core.config import MangaTranslatorConfig, OutsideTextConfig
from core.image import inpainting
from core.validation import validate_config
from ui.ui_models import UIConfigState, map_ui_to_backend_config
from utils.exceptions import ValidationError
from utils.model_metadata import flux_valid_backend


class _FakeModelManager:
    def __init__(self):
        self.connections = []
        self.flux_inference_lock = threading.Lock()

    def connect_flux_sdcpp_server(self, remote_url, model_key, verbose=False):
        self.connections.append((remote_url, model_key, verbose))
        return {"url": remote_url, "model_key": model_key, "remote": True}

    def ensure_flux_sdcpp_server(self, *_args, **_kwargs):
        pytest.fail("remote mode requested managed sd.cpp assets")

    def shutdown_sdcpp_server(self, *_args, **_kwargs):
        pytest.fail("remote mode attempted to stop the external server")

    def unload_flux_klein_models(self):
        pytest.fail("remote mode attempted to unload local Klein models")


class _RecordingCache:
    def __init__(self):
        self.cache_params = None

    def should_use_inpaint_cache(self, _seed):
        return True

    def get_inpaint_cache_key(self, *_args):
        self.cache_params = _args[-1]
        return "cache-key"

    def get_inpainted_image(self, _key):
        return None

    def set_inpainted_image(self, _key, _image):
        return None


def test_remote_backend_is_valid_for_all_flux_models():
    for method in ("flux_klein_4b", "flux_klein_9b", "flux_kontext"):
        assert flux_valid_backend(method, "sdcpp_remote") == "sdcpp_remote"


def test_ui_state_round_trips_remote_url(tmp_path):
    state = UIConfigState.from_dict(
        {
            "outside_text_inpainting_method": "flux_klein_4b",
            "outside_text_flux_backend": "sdcpp_remote",
            "outside_text_flux_sdcpp_remote_url": "http://127.0.0.1:1234",
        }
    )

    assert state.to_save_dict()["outside_text_flux_sdcpp_remote_url"] == (
        "http://127.0.0.1:1234"
    )
    config = map_ui_to_backend_config(state, Path(tmp_path), torch.device("cpu"))
    assert config.outside_text.flux_backend == "sdcpp_remote"
    assert config.outside_text.flux_sdcpp_remote_url == "http://127.0.0.1:1234"
    validate_config(config)


def test_remote_backend_requires_valid_url():
    config = MangaTranslatorConfig(
        yolo_model_path="model.pt",
        outside_text=OutsideTextConfig(
            inpainting_method="flux_kontext",
            flux_backend="sdcpp_remote",
            flux_sdcpp_remote_url="",
        ),
    )

    with pytest.raises(ValidationError, match="URL is required"):
        validate_config(config)


@pytest.mark.parametrize(
    ("inpainter_factory", "model_key"),
    [
        (
            lambda: inpainting.FluxKleinInpainter(
                variant="4b",
                device=torch.device("cpu"),
                backend="sdcpp_remote",
                sdcpp_remote_url="http://127.0.0.1:1234/",
            ),
            "flux_klein_4b",
        ),
        (
            lambda: inpainting.FluxKontextInpainter(
                device=torch.device("cpu"),
                backend="sdcpp_remote",
                sdcpp_remote_url="http://127.0.0.1:1234/",
            ),
            "flux_kontext",
        ),
    ],
)
def test_remote_inpainter_connects_without_owning_lifecycle(
    inpainter_factory, model_key, monkeypatch
):
    manager = _FakeModelManager()
    monkeypatch.setattr(inpainting, "get_model_manager", lambda: manager)
    monkeypatch.setattr(inpainting, "get_cache", lambda: object())

    inpainter = inpainter_factory()
    inpainter.load_models()
    inpainter.unload_models()

    assert manager.connections == [
        ("http://127.0.0.1:1234", model_key, ANY)
    ]


@pytest.mark.parametrize("model", ["klein", "kontext"])
def test_remote_inpainter_preserves_sdcpp_payload(model, monkeypatch):
    manager = _FakeModelManager()
    monkeypatch.setattr(inpainting, "get_model_manager", lambda: manager)
    monkeypatch.setattr(inpainting, "get_cache", lambda: object())

    if model == "klein":
        inpainter = inpainting.FluxKleinInpainter(
            variant="4b",
            device=torch.device("cpu"),
            backend="sdcpp_remote",
            sdcpp_remote_url="http://127.0.0.1:1234",
            num_inference_steps=4,
        )
        expected_prompt = inpainter.KLEIN_PROMPT
        expected_guidance = inpainter.KLEIN_GUIDANCE_SCALE
    else:
        inpainter = inpainting.FluxKontextInpainter(
            device=torch.device("cpu"),
            backend="sdcpp_remote",
            sdcpp_remote_url="http://127.0.0.1:1234",
            num_inference_steps=8,
        )
        expected_prompt = inpainter.prompt
        expected_guidance = inpainter.guidance_scale

    inpainter.sdcpp_assets = {
        "url": "http://127.0.0.1:1234",
        "remote": True,
    }
    recorded = {}
    expected_image = Image.new("RGB", (64, 80), "black")

    def fake_run_image_job(server, payload, **kwargs):
        recorded.update(server=server, payload=payload, kwargs=kwargs)
        return expected_image

    monkeypatch.setattr(inpainting, "run_image_job", fake_run_image_job)
    source_image = Image.new("RGB", (64, 80), "white")

    result = inpainter._run_sdcpp_inference(
        source_image,
        width=64,
        height=80,
        seed=17,
        verbose=True,
    )

    assert result is expected_image
    assert recorded == {
        "server": inpainter.sdcpp_assets,
        "payload": {
            "prompt": expected_prompt,
            "negative_prompt": "",
            "width": 64,
            "height": 80,
            "seed": 17,
            "batch_count": 1,
            "ref_images": [inpainting.pil_to_base64_png(source_image)],
            "sample_params": {
                "sample_method": "euler",
                "sample_steps": inpainter.num_inference_steps,
                "guidance": {
                    "txt_cfg": 1.0,
                    "img_cfg": 1.0,
                    "distilled_guidance": float(expected_guidance),
                },
            },
            "output_format": "png",
            "output_compression": 100,
        },
        "kwargs": {"verbose": True, "timeout_sec": 900},
    }


def test_remote_url_participates_in_inpaint_cache_key(monkeypatch):
    recorded_urls = []

    for remote_url in ("http://server-a:1234", "http://server-b:1234"):
        manager = _FakeModelManager()
        cache = _RecordingCache()
        monkeypatch.setattr(
            inpainting, "get_model_manager", lambda manager=manager: manager
        )
        monkeypatch.setattr(inpainting, "get_cache", lambda cache=cache: cache)
        monkeypatch.setattr(
            inpainting,
            "run_image_job",
            lambda _server, _payload, **_kwargs: Image.new("RGB", (64, 64), "white"),
        )

        inpainter = inpainting.FluxKleinInpainter(
            variant="4b",
            device=torch.device("cpu"),
            backend="sdcpp_remote",
            sdcpp_remote_url=remote_url,
            luminance_correction=False,
            upscale_small_crops=False,
        )
        monkeypatch.setattr(
            inpainter,
            "_prepare_image_for_inference",
            lambda image, verbose=False: (image, 1.0, False),
        )
        mask = np.zeros((64, 64), dtype=bool)
        mask[20:40, 20:40] = True
        inpainter.inpaint_mask(Image.new("RGB", (64, 64), "white"), mask, seed=1)
        recorded_urls.append(cache.cache_params["sdcpp_remote_url"])

    assert recorded_urls == ["http://server-a:1234", "http://server-b:1234"]


def test_failed_remote_job_uses_logged_opencv_fallback(monkeypatch):
    logs = []

    class FailingRemoteInpainter:
        def __init__(self, **kwargs):
            assert kwargs["backend"] == "sdcpp_remote"
            assert kwargs["sdcpp_remote_url"] == "http://127.0.0.1:1234"

        def inpaint_mask(self, *_args, **_kwargs):
            raise RuntimeError("remote job failed")

        def unload_models(self):
            return None

    monkeypatch.setattr(
        outside_text_processor, "FluxKleinInpainter", FailingRemoteInpainter
    )
    monkeypatch.setattr(
        outside_text_processor,
        "log_message",
        lambda message, **_kwargs: logs.append(message),
    )

    checkerboard = np.indices((64, 64)).sum(axis=0) % 2
    image_array = np.where(checkerboard[..., None] == 0, 30, 220).astype(np.uint8)
    image = Image.fromarray(np.repeat(image_array, 3, axis=2))
    mask = np.zeros((64, 64), dtype=bool)
    mask[20:40, 20:40] = True
    config = MangaTranslatorConfig(
        yolo_model_path="model.pt",
        device=torch.device("cpu"),
        outside_text=OutsideTextConfig(
            inpainting_method="flux_klein_4b",
            flux_backend="sdcpp_remote",
            flux_sdcpp_remote_url="http://127.0.0.1:1234",
            flux_upscale_small_crops=False,
        ),
    )
    work = outside_text_processor.OutsideTextWork(
        pil_image=image,
        config=config,
        image_path=Path("image.png"),
        image_format="PNG",
        verbose=True,
        outside_text_results=[((20, 20, 40, 40), 1.0)],
        raw_outside_text_results=[((20, 20, 40, 40), 1.0)],
        original_text_colors={},
        total_bubble_mask=np.zeros((64, 64), dtype=bool),
        outside_detector=None,
        mask_groups=[
            {
                "combined_mask": mask,
                "mask_indices": [0],
                "original_bbox": {"x": 20, "y": 20, "width": 20, "height": 20},
            }
        ],
        img_w=64,
        img_h=64,
        mime_type="image/png",
        cv2_ext=".png",
    )

    result, _outside_text_data = outside_text_processor.finish_outside_text_work(work)

    assert np.array(result)[30, 30].tolist() == [255, 255, 255]
    assert any(
        "remote job failed" in message and "falling back to CV2 fill" in message
        for message in logs
    )
