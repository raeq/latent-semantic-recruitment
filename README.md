# Latent Semantic Recruitment

Code and data for:

> **Orphaned Sophistication: Latent Semantic Recruitment as a Structural Signature of LLM-Generated Prose**
>
> Richard Quinn, 2026

Preprint DOI: [10.5281/zenodo.18735464](https://zenodo.org/record/18735464)

## Overview

This repository contains the detection algorithms, experiment scripts, and corpus data described in the paper. The core claim is that LLM-generated prose exhibits *orphaned sophistication*: register-elevated word choices that appear without the preparatory semantic chains human writers use to motivate them. The phenomenon is detectable by a deterministic, rule-based algorithm operating on lexical and chain-connectivity features.

## Repository structure

```
detectors/          Deterministic detection algorithms (v1-v3)
experiments/        Experiment scripts (corpus generation, cross-model
                    validation, ablation, token probing, dose-response)
data/               Result JSON files from all experiments
paper/              Manuscript drafts and supporting materials
tacl_submission/    LaTeX source and compiled PDFs (TACL and preprint)
```

## Requirements

- Python 3.10+
- API keys for experiment scripts that call external models (set as environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`)

The detection algorithms in `detectors/` have no external API dependencies.

## License

MIT. See [LICENSE](LICENSE).
