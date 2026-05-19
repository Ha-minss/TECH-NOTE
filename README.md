# TECH-NOTE

Data science and machine learning project notes by Dongha Park.

This repository keeps portfolio-ready notebooks, derived result tables, and reproducible figures for each project. Raw data files are excluded when they are large or not suitable for public upload.

## Projects

| Project | Topic | Main Methods |
|---|---|---|
| [xente-credit-feature-adoption](./xente-credit-feature-adoption) | Credit scoring, feature adoption, model validation | EDA, grouped validation, LR-WOE, LightGBM, SHAP |
| [dominicks-price-elasticity-iv-dml](./dominicks-price-elasticity-iv-dml) | Price elasticity, causal inference | FE-IV, dynamic IV, FD-PLIV-DML |

## How to Read

Open each project folder and follow the numbered notebooks in order. Each project has its own `README.md`, `requirements.txt`, `data/README.md`, and `outputs/` directory.

## Repository Policy

- Keep raw data out of Git when it is large or restricted.
- Keep final notebooks executed before pushing.
- Keep portfolio explanations concise in README files, with deeper interpretation inside notebooks or the personal website note.
