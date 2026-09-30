"""Zero-shot CLIP prompts per behavior class (English: CLIP was trained on English captions)."""

from typing import Dict, List

BEHAVIOR_CLASSES = ["eating", "resting", "moving"]

PROMPTS: Dict[str, List[str]] = {
    "eating": [
        "a photo of a cow grazing with its head down",
        "a photo of a cow eating grass",
        "a photo of a cow eating hay from a feeder",
        "a photo of a cow with its muzzle on the ground eating",
    ],
    "resting": [
        "a photo of a cow lying down on the ground",
        "a photo of a cow resting on the grass",
        "a photo of a cow standing still with its head up",
        "a photo of a cow sleeping",
    ],
    "moving": [
        "a photo of a cow walking",
        "a photo of a cow running",
    ],
}
