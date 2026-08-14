from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.collectors.run import collect_all
from app.config import settings
from app.db import get_session, init_db
from app.models import CollectorRun, Item
from app.pipeline.enrich import enrich_items
from app.pipeline.ingest import ingest_raw_items

log = logging.getLogger(__name__)


async def collect_cycle() -> dict:
    init_db()
    session = get_session()
    run = CollectorRun(status="running")
    session.add(run)
    session.commit()
    session.refresh(run)
    detail: dict[str, int] = {}
    try:
        batches = await collect_all()
        for name, items in batches.items():
            detail[name] = len(items)
        created = ingest_raw_items(session, batches)
        top = (
            session.query(Item)
            .filter(Item.intro == "")
            .order_by(Item.score.desc())
            .limit(settings.enrich_top_n)
            .all()
        )
        enriched = await enrich_items(session, top, deep=False)
        run.new_items = len(created)
        run.status = "ok"
        run.detail_json = json.dumps({"fetched": detail, "enriched": enriched}, ensure_ascii=False)
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        log.info("cycle ok new=%s fetched=%s", len(created), detail)
        return {"new_items": len(created), "fetched": detail, "enriched": enriched}
    except Exception as exc:
        run.status = "error"
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        log.exception("cycle failed")
        raise
    finally:
        session.close()


async def worker_loop() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    init_db()
    log.info("frontier worker started, interval=%ss", settings.collect_interval_seconds)
    while True:
        try:
            await collect_cycle()
        except Exception:
            log.exception("collect cycle crashed; will retry")
        await asyncio.sleep(max(60, settings.collect_interval_seconds))


def main() -> None:
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
