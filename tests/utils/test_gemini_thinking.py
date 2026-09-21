from unittest.mock import MagicMock

from google.genai import types

import conf.models as models
from utils.gemini_client import configure_thinking_for_model, generate_content_with_retry


def test_is_mini_model():
    assert models.is_mini_model(models.gemini_mini()) is True
    assert models.is_mini_model("gemini-3.5-flash-lite") is True
    assert models.is_mini_model("custom-model-mini") is True
    assert models.is_mini_model(models.gemini_standard()) is False
    assert models.is_mini_model("gemini-3.8-flash") is False
    assert models.is_mini_model("") is False


def test_configure_thinking_for_standard_model():
    cfg = configure_thinking_for_model(models.gemini_standard(), None)
    assert cfg is None

    orig_cfg = types.GenerateContentConfig(temperature=0.5)
    cfg2 = configure_thinking_for_model(models.gemini_standard(), orig_cfg)
    assert cfg2.thinking_config is None


def test_configure_thinking_for_mini_model_none_config():
    cfg = configure_thinking_for_model(models.gemini_mini(), None)
    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.thinking_config is not None
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW


def test_configure_thinking_for_mini_model_existing_config():
    orig_cfg = types.GenerateContentConfig(temperature=0.7)
    cfg = configure_thinking_for_model(models.gemini_mini(), orig_cfg)
    assert cfg.thinking_config is not None
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert cfg.temperature == 0.7


def test_configure_thinking_preserves_existing_thinking_config():
    existing = types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH)
    orig_cfg = types.GenerateContentConfig(thinking_config=existing)
    cfg = configure_thinking_for_model(models.gemini_mini(), orig_cfg)
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.HIGH


def test_generate_content_with_retry_applies_thinking_for_mini():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    res = generate_content_with_retry(
        client=mock_client,
        model=models.gemini_mini(),
        contents="test prompt",
    )
    assert res == mock_resp
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    passed_config = call_kwargs["config"]
    assert passed_config is not None
    assert passed_config.thinking_config is not None
    assert passed_config.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert passed_config.automatic_function_calling is not None
    assert passed_config.automatic_function_calling.disable is True


def test_configure_afc_none_config():
    from utils.gemini_client import configure_afc

    cfg = configure_afc(None)
    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.automatic_function_calling is not None
    assert cfg.automatic_function_calling.disable is True


def test_configure_afc_existing_config():
    from utils.gemini_client import configure_afc

    orig = types.GenerateContentConfig(temperature=0.3)
    cfg = configure_afc(orig)
    assert cfg.automatic_function_calling is not None
    assert cfg.automatic_function_calling.disable is True
    assert cfg.temperature == 0.3


def test_configure_model_config_sets_both():
    from utils.gemini_client import configure_model_config

    cfg = configure_model_config(models.gemini_mini(), None)
    assert isinstance(cfg, types.GenerateContentConfig)
    assert cfg.thinking_config is not None
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert cfg.automatic_function_calling is not None
    assert cfg.automatic_function_calling.disable is True
