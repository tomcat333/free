from tests.conftest import add_item

from app.dispatch import build_run_pack


def test_run_pack_for_github_repo(session):
    item = add_item(
        session,
        kind="repo",
        title="acme/world-model",
        url="https://github.com/acme/world-model",
        extra_json='{"clone_url": "https://github.com/acme/world-model.git"}',
    )
    pack = build_run_pack(item)
    assert pack["event"] == "frontier.dispatch"
    assert "git clone" in pack["suggested_commands"][0]
    assert "最小复现" in pack["agent_prompt"]
    assert pack["clone_url"].endswith(".git")
