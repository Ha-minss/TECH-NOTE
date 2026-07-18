# Data

Original CSV files are not copied into this repository. Pass the external data directory at runtime:

```bash
python scripts/run_ab_analysis.py --data-dir "C:\dev\Codex\gamelytics_data" --bootstrap-iterations 5000 --seed 42
python scripts/run_retention_analysis.py --data-dir "C:\dev\Codex\gamelytics_data"
```

The source CSV delimiter is semicolon (`;`).
