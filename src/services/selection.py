"""Pure selection algorithms used by training and examinations."""
from __future__ import annotations

import random
from collections.abc import Sequence
from src.models import Sound


def training_choice(sounds: Sequence[Sound], success_rates: dict[int, float], prioritize_difficult: bool,
                    rng: random.Random | None = None) -> Sound:
    if not sounds:
        raise ValueError("At least one enabled sound is required.")
    randomizer = rng or random
    if not prioritize_difficult:
        return randomizer.choice(list(sounds))
    weights = [max(0.15, 1.15 - success_rates.get(sound.id, 0.5)) for sound in sounds]
    return randomizer.choices(list(sounds), weights=weights, k=1)[0]


def exam_questions(sounds: Sequence[Sound], count: int, allow_repeats: bool,
                   rng: random.Random | None = None) -> list[Sound]:
    if count < 1:
        raise ValueError("Question count must be positive.")
    if not sounds:
        raise ValueError("Add and enable at least one sound first.")
    if not allow_repeats and count > len(sounds):
        raise ValueError(f"{count} questions require repeats: only {len(sounds)} enabled sounds are available.")
    randomizer = rng or random
    return randomizer.choices(list(sounds), k=count) if allow_repeats else randomizer.sample(list(sounds), count)


def multiple_choice_options(current: Sound, sounds: Sequence[Sound], rng: random.Random | None = None) -> list[Sound]:
    alternatives = [sound for sound in sounds if sound.id != current.id]
    if len(alternatives) < 4:
        raise ValueError("Level 1 requires at least five enabled sounds.")
    randomizer = rng or random
    result = [current, *randomizer.sample(alternatives, 4)]
    randomizer.shuffle(result)
    return result
