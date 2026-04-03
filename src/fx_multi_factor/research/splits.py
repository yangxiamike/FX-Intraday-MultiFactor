from __future__ import annotations

from fx_multi_factor.data.contracts import FXBar1m


def build_walk_forward_splits(
    bars: list[FXBar1m],
    train_size: int = 120,
    validation_size: int = 60,
    test_size: int = 60,
    step_size: int = 60,
) -> list[dict[str, object]]:
    total_window = train_size + validation_size + test_size
    if train_size <= 0 or validation_size <= 0 or test_size <= 0 or step_size <= 0:
        raise ValueError("walk-forward split sizes must all be positive")
    if len(bars) < total_window:
        return []

    splits: list[dict[str, object]] = []
    split_id = 1
    for start in range(0, len(bars) - total_window + 1, step_size):
        train_end = start + train_size
        validation_end = train_end + validation_size
        test_end = validation_end + test_size
        train_slice = bars[start:train_end]
        validation_slice = bars[train_end:validation_end]
        test_slice = bars[validation_end:test_end]
        if not train_slice or not validation_slice or not test_slice:
            continue
        splits.append(
            {
                "split_id": split_id,
                "train_start": train_slice[0].ts,
                "train_end": train_slice[-1].ts,
                "validation_start": validation_slice[0].ts,
                "validation_end": validation_slice[-1].ts,
                "test_start": test_slice[0].ts,
                "test_end": test_slice[-1].ts,
                "train_count": len(train_slice),
                "validation_count": len(validation_slice),
                "test_count": len(test_slice),
            }
        )
        split_id += 1
    return splits
