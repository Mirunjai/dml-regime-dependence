"""Locate supplied course templates without requiring a particular home path."""
from pathlib import Path
import os

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/raw/final_research_20261112'


def template(name):
    candidates=[]
    if os.environ.get('ADA_TEMPLATES_DIR'):candidates.append(Path(os.environ['ADA_TEMPLATES_DIR'])/name)
    candidates += [BASE/'artifact_templates'/name,
                   ROOT.parent/'ADA PROJECT DELIVERABLES/07_Audit_and_Reproducibility/templates'/name]
    for p in candidates:
        if p.is_file():return p
    raise FileNotFoundError(f'Provide {name} in ADA_TEMPLATES_DIR or the packaged templates folder')
