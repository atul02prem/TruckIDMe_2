"""Encoder construction and training hyperparameters for exp04.

Defined here rather than imported from `src.models.finetune_mantis`, so this
experiment depends only on `src.config` and the `src.models` libraries, and not
on an earlier training driver with dependencies exp04 never uses.

The values below are copied from `finetune_mantis` verbatim and verified equal to
it, so the two produce identical networks and identical optimisation. They are
restated rather than referenced for the same reason `EPOCHS` is pinned in
`run.py`: a configuration recorded in one module and read from another is how SPN
2979 ended up inside a tensor the decision record said excluded it.
"""
from __future__ import annotations

from mantis.architecture import MantisV1

from src.config import MANTIS_CHECKPOINT, MANTIS_LAYER, MANTIS_OUTPUT_TOKEN

DEVICE = "cuda"
BATCH_SIZE = 64
LEARNING_RATE = 1e-4          # as used for the published EEG fine-tuning
SEED = 42

# No channel adapter. `MantisTrainer.transform` ignores any adapter passed to
# `fit`, and every read-out here is built on `transform`'s embeddings, so an
# adapted encoder would need custom embedding code. Recorded in DECISIONS.md B3
# (narrowed: `predict_proba` does apply an adapter in `adapter_head` mode).
ADAPTER_CHANNELS = None


def build_network(pretrained: bool) -> MantisV1:
    """Create the encoder, optionally loading pre-trained weights.

    Args:
        pretrained: load the published checkpoint if True, else random init,
            which is the only difference between the `full` and `scratch` arms.

    Returns:
        A MantisV1 network configured for the recommended read-out.
    """
    network = MantisV1(device=DEVICE, return_transf_layer=MANTIS_LAYER,
                       output_token=MANTIS_OUTPUT_TOKEN)
    if pretrained:
        network = network.from_pretrained(MANTIS_CHECKPOINT)
    return network
