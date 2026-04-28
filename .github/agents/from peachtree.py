from peachtree.hancock_integration import hancock_ingestion_workflow
from pathlib import Path

summary = hancock_ingestion_workflow(
    hancock_data_dir=Path("~/Hancock/data"),
    output_dir=Path("data/hancock"),
    min_quality_score=0.70
)
print(f"✅ Ingested {summary['total_records']} records")