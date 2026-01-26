import json
import os
from typing import Any, Dict, List

from braintrust import api_conn, load_prompt, login, projects


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


PROMPTS: List[Dict[str, Any]] = [
    # Example:
    # {
    #     "project_name": "rev-langgraph-demo",
    #     "prompt_slug": "legal-deposition-assistant",
    #     "prompt_name": "Legal Deposition Assistant",
    #     "prompt_text": "You are a legal deposition assistant...",
    #     "model": "gpt-4o-mini",
    #     "environment_slug": "prod",
    # }
]


def _load_prompt_configs() -> List[Dict[str, Any]]:
    raw = os.environ.get("BRAINTRUST_PROMPT_CONFIG_JSON")
    if raw:
        return json.loads(raw)
    return PROMPTS


def _require_field(config: Dict[str, Any], name: str) -> Any:
    value = config.get(name)
    if not value:
        raise RuntimeError(f"Missing required field: {name}")
    return value


def main() -> None:
    api_key = require_env("BRAINTRUST_API_KEY")
    org_name = os.environ.get("BRAINTRUST_ORG_NAME")
    app_url = os.environ.get("BRAINTRUST_APP_URL")
    default_project = os.environ.get("BRAINTRUST_PROJECT_NAME")

    login(api_key=api_key, org_name=org_name, app_url=app_url)

    for config in _load_prompt_configs():
        project_name = config.get("project_name") or default_project
        if not project_name:
            raise RuntimeError("Missing project_name (set BRAINTRUST_PROJECT_NAME)")

        prompt_slug = _require_field(config, "prompt_slug")
        prompt_name = _require_field(config, "prompt_name")
        prompt_text = _require_field(config, "prompt_text")
        model = _require_field(config, "model")
        environment_slug = config.get("environment_slug")

        project = projects.create(project_name)
        project.prompts.create(
            name=prompt_name,
            slug=prompt_slug,
            prompt=prompt_text,
            model=model,
            if_exists="replace",
        )
        project.publish()

        if environment_slug:
            prompt = load_prompt(
                project=project_name,
                slug=prompt_slug,
                api_key=api_key,
                org_name=org_name,
                app_url=app_url,
            )
            api_conn().post_json(
                f"environment-object/prompt/{prompt.id}",
                {
                    "object_version": prompt.version,
                    "environment_slug": environment_slug,
                    "org_name": org_name,
                },
            )


if __name__ == "__main__":
    main()
