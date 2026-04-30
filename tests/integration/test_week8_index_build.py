from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.indexing.index_manifest import build_manifest
from pipelines.indexing.reporting import write_index_build_outputs


def test_week8_index_report_outputs(tmp_path: Path):
    manifest = build_manifest(
        index_release_id="index-week08-dev",
        data_release_id="data-week08-dev",
        chunk_strategy_version="section_aware_v1",
        embedding_model="dry_run",
        embedding_dim=1536,
        provider="dry_run",
        source_table="knowledge_section",
        total_chunks=3,
        embedded_chunks=0,
        skipped_chunks=3,
        error_count=0,
        warnings=["dry_run=true; embeddings were not generated"],
        elapsed_sec=0.01,
    )

    md_path, json_path = write_index_build_outputs(manifest, tmp_path)

    assert md_path.exists()
    assert json_path.exists()
    assert "index-week08-dev" in md_path.read_text()
    assert '"quality_gate": "warn"' in json_path.read_text()
