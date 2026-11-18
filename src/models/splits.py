"""Split helpers shared by every evaluation stage.

Two rules hold everywhere:

1. **Chronological within a driver.** Train on early windows, discard a gap,
   test on late ones — so adjacent, nearly identical windows never straddle the
   split and the model must fingerprint behaviour rather than position in the drive.
2. **Stratified by awareness group** when choosing known/unknown drivers, so no
   partition accidentally holds out most of G3 (the group earlier work found
   hardest to classify).
"""

import numpy as np

TRAIN_END = 0.70     # first 70% of a driver's windows
TEST_START = 0.75    # last 25%; the 5% between is discarded as a gap


def driver_group(driver_id: str) -> str:
    """Awareness group of a driver.

    Args:
        driver_id: canonical id, e.g. 'G2S07'.

    Returns:
        'G1' (control), 'G2' (aware) or 'G3' (aware + protocol).
    """
    return driver_id[:2]


def chronological_split(start_times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split one driver's windows into an early train part and a late test part.

    Args:
        start_times: window start times for a single driver.

    Returns:
        (train_positions, test_positions) as index arrays into start_times,
        with a discarded gap between them.
    """
    order = np.argsort(start_times)
    n = len(order)
    return order[:int(TRAIN_END * n)], order[int(TEST_START * n):]


def split_by_driver(drivers: np.ndarray, start_times: np.ndarray
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Apply the chronological split to every driver.

    Args:
        drivers: driver id per window.
        start_times: window start time per window.

    Returns:
        (train_index, test_index) into the full window arrays.
    """
    train, test = [], []
    for driver in np.unique(drivers):
        positions = np.flatnonzero(drivers == driver)
        local_train, local_test = chronological_split(start_times[positions])
        train.append(positions[local_train])
        test.append(positions[local_test])
    return np.concatenate(train), np.concatenate(test)


def known_unknown_partitions(drivers: np.ndarray, n_unknown: int, n_partitions: int,
                             seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Draw repeated known/unknown driver partitions, stratified by group.

    Args:
        drivers: driver id per window (duplicates fine).
        n_unknown: how many drivers to hold out as never-enrolled.
        n_partitions: how many independent partitions to draw.
        seed: base random seed.

    Returns:
        A list of (known_driver_ids, unknown_driver_ids) arrays.
    """
    unique = np.unique(drivers)
    groups = {g: unique[[driver_group(d) == g for d in unique]]
              for g in sorted({driver_group(d) for d in unique})}
    # hold out proportionally from each group, largest groups first
    quota = {g: int(round(n_unknown * len(members) / len(unique)))
             for g, members in groups.items()}
    while sum(quota.values()) != n_unknown:
        target = max(quota, key=lambda g: len(groups[g]) - quota[g]) \
            if sum(quota.values()) < n_unknown else max(quota, key=quota.get)
        quota[target] += 1 if sum(quota.values()) < n_unknown else -1

    partitions = []
    for index in range(n_partitions):
        rng = np.random.default_rng(seed + index)
        unknown = np.concatenate([rng.choice(groups[g], size=quota[g], replace=False)
                                  for g in groups])
        known = np.setdiff1d(unique, unknown)
        partitions.append((known, unknown))
    return partitions


def eta_squared(values: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Between-group variance as a fraction of total, per column.

    The same model-independent statistic used for the raw-signal leakage audit:
    1.0 means a column separates the groups perfectly, 0.0 means not at all.

    Args:
        values: (n_samples, n_features).
        labels: group label per sample.

    Returns:
        eta-squared per feature, shape (n_features,).
    """
    grand_mean = values.mean(axis=0)
    total = ((values - grand_mean) ** 2).sum(axis=0)
    between = np.zeros(values.shape[1])
    for label in np.unique(labels):
        member = values[labels == label]
        between += len(member) * (member.mean(axis=0) - grand_mean) ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(total > 0, between / total, 0.0)


def known_train_index(drivers: np.ndarray, starts: np.ndarray,
                      known: np.ndarray) -> np.ndarray:
    """Training window positions for one partition's known drivers.

    The same chronological split `evaluate_partition` applies, computed here so
    the encoder is fitted on exactly the windows that will later be used to build
    prototypes — and on nothing else.

    Args:
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.

    Returns:
        Positions into the full window arrays.
    """
    positions = np.flatnonzero(np.isin(drivers, known))
    train_local, _ = split_by_driver(drivers[positions], starts[positions])
    return positions[train_local]


def inner_train_index(drivers: np.ndarray, starts: np.ndarray,
                      known: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split the known drivers' training windows into inner-train and the rest.

    Args:
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.

    Returns:
        (inner_train positions, known_train positions), both into the full
        window arrays. The encoder is fitted on the first; read-outs are later
        scored on the inner-validation part of the second.
    """
    known_train = known_train_index(drivers, starts, known)
    local, _ = split_by_driver(drivers[known_train], starts[known_train])
    return known_train[local], known_train
