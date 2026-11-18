"""Prove that slicing a cached embedding equals re-embedding the channel subset.

exp05 evaluates channel subsets by taking column slices out of the cached
50-channel frozen embedding, instead of pushing the subset through Mantis again.
That is only legitimate if the two are the same numbers.

They should be, because `MantisTrainer.transform` encodes each channel
*independently* and concatenates:

    concat([self._transform(x[:, [i], :]) for i in range(x.shape[1])], axis=1)

so channel i's 256 outputs cannot depend on which other channels were present.
This script checks that claim against the actual library rather than trusting
the source reading: it embeds an 11-channel tensor from scratch with the frozen
encoder and compares the result to the matching blocks of the cached
50-channel embedding.

A non-zero but tiny difference is expected and acceptable — batching changes
floating-point reduction order on the GPU. A difference large enough to change
a classifier's input is not, and fails the check.

Run:
    python -u -m experiments.exp05_frozen_channel_subsets.verify_slice_equivalence
"""
from __future__ import annotations

import numpy as np
from mantis.trainer import MantisTrainer

from experiments.exp04_open_set_finetune.encoder import (BATCH_SIZE, DEVICE,
                                                         build_network)
from experiments.exp05_frozen_channel_subsets.run import (ACTUATED,
                                                          WINDOW_SECONDS,
                                                          subset_columns)
from src.features.build_tensors import tensor_path
from src.features.build_embeddings import embedding_path as frozen_embedding_path

# Larger than float32 round-off from a different batching order, far smaller
# than anything a standardised classifier input would notice.
TOLERANCE = 1e-3


def main() -> None:
    """Re-embed the actuated channels and compare against the cached slice."""
    windows = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    cached = np.load(frozen_embedding_path("cls_token", WINDOW_SECONDS),
                     allow_pickle=True)

    channels = [str(c) for c in windows["channels"]]
    if channels != [str(c) for c in cached["channels"]]:
        raise ValueError("tensor and embedding disagree on channel order")

    blocks = sorted(channels.index(c) for c in ACTUATED)
    subset = windows["X"][:, blocks, :]
    print(f"re-embedding {subset.shape} "
          f"({len(blocks)} channels: {[channels[b] for b in blocks]})")

    model = MantisTrainer(device=DEVICE, network=build_network(pretrained=True))
    fresh = model.transform(subset, batch_size=BATCH_SIZE)
    sliced = cached["E"][:, subset_columns(windows["channels"], ACTUATED)]

    if fresh.shape != sliced.shape:
        raise ValueError(f"shape mismatch: fresh {fresh.shape} "
                         f"vs sliced {sliced.shape}")

    difference = np.abs(fresh - sliced)
    scale = np.abs(sliced).mean()
    print(f"\nfresh  {fresh.shape}  mean |value| {np.abs(fresh).mean():.6f}")
    print(f"sliced {sliced.shape}  mean |value| {scale:.6f}")
    print(f"max  absolute difference : {difference.max():.3e}")
    print(f"mean absolute difference : {difference.mean():.3e}")
    print(f"relative to signal scale : {difference.max() / scale:.3e}")
    print(f"exactly equal elements   : "
          f"{100 * np.mean(fresh == sliced):.2f}%")

    verdict = "PASS" if difference.max() < TOLERANCE else "FAIL"
    print(f"\n{verdict}: slicing the cached embedding "
          f"{'is' if verdict == 'PASS' else 'is NOT'} equivalent to "
          f"re-embedding the subset (tolerance {TOLERANCE:g})")


if __name__ == "__main__":
    main()
