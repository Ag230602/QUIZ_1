from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptExample:
    baseline_prompt: str
    structured_prompt: str
    negative_prompt: str


class PromptBuilder:
    def __init__(self, config: Dict):
        self.prompt_cfg = config["prompting"]
        self.control_cfg = config["control"]

    def build_structured_prompt(self, row: Dict) -> str:
        title = row["title"]
        color = row["color"]
        material = row["material"]
        style = row["style"]
        attributes = row["attributes"]
        target_view = row["target_view"]
        environment = row["environment"]
        lighting = self.prompt_cfg["lighting"]
        composition = self.prompt_cfg["composition"]
        lens = self.prompt_cfg["lens"]

        return (
            f"Commercial e-commerce product photo of {title}, {color}, made of {material}, "
            f"{style} style. Key attributes: {attributes}. View: {target_view}. "
            f"Scene: {environment}. {lighting}. {lens}. {composition}. "
            f"Single product only, photorealistic, crisp edges, catalog-ready."
        )

    def build_negative_prompt(self) -> str:
        return self.control_cfg.get("negative_prompt", "")

    def build(self, row: Dict) -> PromptExample:
        return PromptExample(
            baseline_prompt=row["baseline_prompt"],
            structured_prompt=self.build_structured_prompt(row),
            negative_prompt=self.build_negative_prompt(),
        )
