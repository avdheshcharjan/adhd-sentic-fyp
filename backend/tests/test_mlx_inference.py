"""Tests for MLX inference service.

Since mlx_lm may not be fully importable in all environments (e.g., missing
native dependencies or version mismatches), we pre-populate sys.modules with a
mock mlx_lm before the service module is imported.  This guarantees tests run
anywhere without needing actual model files.
"""

import sys
from unittest.mock import MagicMock, patch

# ── Pre-mock mlx_lm so services.mlx_inference can be imported ──────────
_mock_mlx_lm = MagicMock()
_mock_sample_utils = MagicMock()
_mock_sample_utils.make_sampler.return_value = lambda x: x

sys.modules.setdefault("mlx_lm", _mock_mlx_lm)
sys.modules.setdefault("mlx_lm.sample_utils", _mock_sample_utils)

from services.mlx_inference import MLXInference  # noqa: E402


class TestMLXInferenceLifecycle:
    """Test model load/unload lifecycle without actual model files."""

    def test_initial_state_is_unloaded(self):
        inference = MLXInference()
        assert inference.model is None
        assert inference.tokenizer is None
        assert inference.current_model_key is None

    def test_unload_when_already_unloaded_is_safe(self):
        inference = MLXInference()
        inference._unload()
        assert inference.model is None

    def test_maybe_unload_when_no_model_is_noop(self):
        inference = MLXInference()
        inference.maybe_unload_if_idle()
        assert inference.model is None

    @patch("mlx_lm.load")
    def test_load_model_sets_state(self, mock_load):
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)

        inference = MLXInference()
        inference._load_model("primary")

        assert inference.model is mock_model
        assert inference.tokenizer is mock_tokenizer
        assert inference.current_model_key == "primary"
        assert inference.last_used is not None

    @patch("mlx_lm.load")
    def test_load_same_model_twice_is_noop(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")
        inference._load_model("primary")

        mock_load.assert_called_once()

    @patch("mlx_lm.load")
    def test_unload_frees_model(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")
        inference._unload()

        assert inference.model is None
        assert inference.tokenizer is None
        assert inference.current_model_key is None

    @patch("mlx_lm.load")
    def test_maybe_unload_respects_ttl(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")

        # Model was just loaded so it should NOT be unloaded
        inference.maybe_unload_if_idle()
        assert inference.model is not None

    @patch("mlx_lm.sample_utils.make_sampler", return_value=lambda x: x)
    @patch("mlx_lm.generate", return_value="I hear you.")
    @patch("mlx_lm.load")
    def test_generate_loads_model_on_demand(self, mock_load, mock_generate, mock_sampler):
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "formatted prompt"
        mock_load.return_value = (mock_model, mock_tokenizer)

        inference = MLXInference()
        result = inference.generate_coaching_response(
            system_prompt="You are a coach.",
            user_message="I feel overwhelmed.",
        )

        assert result == "I hear you."
        assert inference.model is not None
