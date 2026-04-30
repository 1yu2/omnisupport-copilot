"""Week8 index build reporting."""

from __future__ import annotations

import json
from pathlib import Path

from pipelines.indexing.index_manifest import IndexManifest


def write_index_build_outputs(manifest: IndexManifest, report_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_id = manifest.index_release_id.replace("/", "_")
    md_path = out_dir / f"index_build_report_{safe_id}.md"
    json_path = out_dir / f"index_manifest_{safe_id}.json"

    warnings = "\n".join(f"- {item}" for item in manifest.warnings) or "- none"
    md_path.write_text(
        "\n".join(
            [
                "# Week8 Index Build Report",
                "",
                f"- index_release_id: `{manifest.index_release_id}`",
                f"- data_release_id: `{manifest.data_release_id}`",
                f"- chunk_strategy_version: `{manifest.chunk_strategy_version}`",
                f"- provider: `{manifest.provider}`",
                f"- embedding_model: `{manifest.embedding_model}`",
                f"- embedding_dim: `{manifest.embedding_dim}`",
                f"- source_table: `{manifest.source_table}`",
                f"- total_chunks: `{manifest.total_chunks}`",
                f"- embedded_chunks: `{manifest.embedded_chunks}`",
                f"- skipped_chunks: `{manifest.skipped_chunks}`",
                f"- error_count: `{manifest.error_count}`",
                f"- quality_gate: `{manifest.quality_gate}`",
                f"- elapsed_sec: `{manifest.elapsed_sec}`",
                "",
                "## Warnings",
                "",
                warnings,
                "",
                "## Notes",
                "",
                manifest.notes,
                "",
            ]
        ),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path
