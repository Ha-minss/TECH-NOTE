# LLM Integration

The optional LLM path augments the deterministic StoreOps workflow with four bounded components: case parsing, evidence planning, clarification question generation, and merchant response drafting.

The checklist extractor is a bounded LLM component: it reads retrieved SOP excerpts, extracts operational checks, and maps them only to allowed `data_need` values from the tool catalog. It does not diagnose root cause, output expected state, invent tools, or bypass the deterministic executor.

The LLM does not execute tools directly. It selects allowed data needs, and the workflow maps those needs to known read-only tools. Evidence records, deterministic reasoners, safety gates, and operator review still control the final case state.

## Local Configuration

The repository is provider-agnostic. Live calls use a generic JSON chat-completions adapter configured through `LIVE_LLM_*` environment variables or `config/live.local.json`. Do not commit local credentials.

## Scripted Demo

The scripted provider is deterministic and safe for CI.

```powershell
$env:PYTHONPATH = "src"
py -X utf8 -m storeops.apps.demo S5 --provider scripted-demo
```

## Optional Live Demo

```powershell
Copy-Item config/live.local.example.json config/live.local.json
# fill api_key, model_name, and base_url locally
py -X utf8 -m storeops.apps.demo S5 --provider live --config config/live.local.json
```

The live provider is for local demonstration only. The evaluation baseline uses `python -m storeops.evals.llm_runner --provider scripted`, so CI never calls an external LLM service.
