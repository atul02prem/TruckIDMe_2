"""The fine-tuning recipe every fine-tuned Mantis arm uses.

One copy of the constants that exp07 (`phase_a.py`) and exp08 (`round1.py`) had
each defined, with identical values, and the model constructor exp06 and exp08
shared. Fine-tuning updates every parameter of the encoder (`fine_tuning_type=
"full"`), reading out at a chosen transformer block.
"""
from __future__ import annotations

from mantis.architecture import MantisV1
from mantis.trainer import MantisTrainer

from src.config import MANTIS_CHECKPOINT

OUTPUT_TOKEN = "mean_token"   # chosen on inner validation (DECISIONS.md D13)
EPOCHS = 60                   # validation flat from ~60 (exp04 Stage 1)
BATCH_SIZE = 64
LEARNING_RATE = 1e-4          # the EEG fine-tuning paper's value


def build_model(layer: int, token: str = OUTPUT_TOKEN) -> MantisTrainer:
    """A pre-trained Mantis trainer reading out at one layer.

    Args:
        layer: transformer layer to read out; -1 is the final layer.
        token: output token; defaults to `mean_token` (exp06).

    Returns:
        The trainer, on the visible CUDA device.
    """
    network = MantisV1(device="cuda", return_transf_layer=layer,
                       output_token=token).from_pretrained(
        MANTIS_CHECKPOINT)
    return MantisTrainer(device="cuda", network=network)
