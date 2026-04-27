"""
Hancock Cybersecurity Dataset Integration Module

Integrates Hancock's cybersecurity data pipeline with PeachTree's dataset control plane.
Handles ingestion of MITRE ATT&CK, CVE, KEV, GHSA, and Atomic Red Team data into
traceable, provenance-tracked JSONL datasets for ML training.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import SourceDocument, DatasetRecord, DatasetManifest
from .builder import DatasetBuilder
from .safety import SafetyGate
from .quality import DatasetQualityScorer
from .dedup import DatasetDeduplicator
from .model_card import ModelCardGenerator
from .trainer_handoff import TrainerHandoffBuilder

logger = logging.getLogger(__name__)


@dataclass
class HancockSource:
    """Represents a Hancock data source"""
    name: str
    source_type: str  # mitre, cve, kev, ghsa, atomic
    file_path: Path
    record_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HancockIngestionConfig:
    """Configuration for Hancock data ingestion"""
    # Source paths
    hancock_data_dir: Path = Path("~/Hancock/data").expanduser()
    
    # Output paths  
    output_dir: Path = Path("data/hancock")
    
    # Quality thresholds
    min_quality_score: float = 0.70  # open-safe default
    commercial_quality_score: float = 0.80
    
    # Source filtering
    include_sources: list[str] = field(default_factory=lambda: [
        "mitre", "cve", "kev", "ghsa", "atomic", "kb", "soc-kb"
    ])
    
    # Safety options
    filter_secrets: bool = True
    require_provenance: bool = True
    allow_unknown_license: bool = False


class HancockDataIngester:
    """Ingests Hancock cybersecurity data into PeachTree datasets"""
    
    def __init__(self, config: HancockIngestionConfig | None = None):
        self.config = config or HancockIngestionConfig()
        self.sources: list[HancockSource] = []
        
    def discover_sources(self) -> list[HancockSource]:
        """Discover available Hancock data files"""
        sources = []
        data_dir = self.config.hancock_data_dir
        
        if not data_dir.exists():
            logger.warning(f"Hancock data directory not found: {data_dir}")
            return sources
        
        # Map raw files to source types
        source_mapping = {
            "raw_mitre.json": "mitre",
            "raw_cve.json": "cve",
            "raw_kev.json": "kev",
            "raw_ghsa.json": "ghsa",
            "raw_atomic.json": "atomic",
            "raw_pentest_kb.json": "kb",
            "raw_soc_kb.json": "soc-kb",
        }
        
        for filename, source_type in source_mapping.items():
            file_path = data_dir / filename
            if file_path.exists() and source_type in self.config.include_sources:
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    record_count = len(data) if isinstance(data, list) else 1
                    
                    sources.append(HancockSource(
                        name=filename.replace("raw_", "").replace(".json", ""),
                        source_type=source_type,
                        file_path=file_path,
                        record_count=record_count,
                        metadata={"ingestion_date": datetime.now().isoformat()}
                    ))
                    logger.info(f"Discovered {source_type}: {record_count} records from {filename}")
                except Exception as e:
                    logger.error(f"Failed to parse {filename}: {e}")
        
        # Check for consolidated v3 dataset
        v3_file = data_dir / "hancock_v3.jsonl"
        if v3_file.exists():
            try:
                record_count = sum(1 for _ in v3_file.read_text(encoding="utf-8").splitlines() if _.strip())
                sources.append(HancockSource(
                    name="hancock_v3",
                    source_type="consolidated",
                    file_path=v3_file,
                    record_count=record_count,
                    metadata={"format": "jsonl", "version": "3"}
                ))
                logger.info(f"Discovered consolidated v3 dataset: {record_count} records")
            except Exception as e:
                logger.error(f"Failed to parse hancock_v3.jsonl: {e}")
        
        self.sources = sources
        return sources
    
    def convert_to_source_documents(self, source: HancockSource) -> list[SourceDocument]:
        """Convert Hancock records to PeachTree SourceDocuments"""
        documents = []
        
        try:
            if source.file_path.suffix == ".jsonl":
                # Handle JSONL format (v3 consolidated dataset)
                for line in source.file_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    doc = self._hancock_record_to_source_doc(record, source)
                    if doc:
                        documents.append(doc)
            else:
                # Handle JSON format (raw data files)
                data = json.loads(source.file_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for idx, record in enumerate(data):
                        doc = self._hancock_record_to_source_doc(record, source, idx)
                        if doc:
                            documents.append(doc)
                else:
                    doc = self._hancock_record_to_source_doc(data, source, 0)
                    if doc:
                        documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to convert {source.name}: {e}")
        
        logger.info(f"Converted {len(documents)} documents from {source.name}")
        return documents
    
    def _hancock_record_to_source_doc(
        self, 
        record: dict[str, Any], 
        source: HancockSource,
        index: int = 0
    ) -> SourceDocument | None:
        """Convert a single Hancock record to SourceDocument"""
        try:
            # Extract content based on source type
            content = self._extract_content(record, source.source_type)
            if not content:
                return None
            
            # Build provenance information
            source_path = f"{source.name}/{source.source_type}/{index}"
            if "id" in record:
                source_path += f"/{record['id']}"
            elif "cve_id" in record:
                source_path += f"/{record['cve_id']}"
            elif "technique_id" in record:
                source_path += f"/{record['technique_id']}"
            
            return SourceDocument(
                content=content,
                source_repo=f"Hancock/{source.name}",
                source_path=source_path,
                license_id="MIT",  # Hancock is MIT licensed
                sha256_digest=DatasetBuilder._compute_sha256(content),
                metadata={
                    "hancock_source": source.source_type,
                    "ingestion_date": source.metadata.get("ingestion_date", ""),
                    "record_id": record.get("id", ""),
                    **self._extract_metadata(record, source.source_type)
                }
            )
        except Exception as e:
            logger.error(f"Failed to convert record {index} from {source.name}: {e}")
            return None
    
    def _extract_content(self, record: dict[str, Any], source_type: str) -> str:
        """Extract trainable content from Hancock record"""
        if source_type == "mitre":
            # MITRE ATT&CK technique
            parts = [
                f"Technique: {record.get('name', 'Unknown')}",
                f"ID: {record.get('external_references', [{}])[0].get('external_id', 'Unknown')}",
                f"Tactic: {', '.join(record.get('kill_chain_phases', [{}]))}",
                f"Description: {record.get('description', '')}",
            ]
            if record.get('x_mitre_platforms'):
                parts.append(f"Platforms: {', '.join(record['x_mitre_platforms'])}")
            if record.get('x_mitre_detection'):
                parts.append(f"Detection: {record['x_mitre_detection']}")
            return "\n\n".join(p for p in parts if p)
        
        elif source_type == "cve":
            # CVE vulnerability
            parts = [
                f"CVE ID: {record.get('id', 'Unknown')}",
                f"Published: {record.get('published', '')}",
                f"Description: {record.get('descriptions', [{}])[0].get('value', '')}",
            ]
            if record.get('metrics', {}).get('cvssMetricV31'):
                cvss = record['metrics']['cvssMetricV31'][0]['cvssData']
                parts.append(f"CVSS Score: {cvss.get('baseScore', 'N/A')} ({cvss.get('baseSeverity', 'N/A')})")
            return "\n\n".join(p for p in parts if p)
        
        elif source_type == "kev":
            # CISA KEV (Known Exploited Vulnerability)
            return f"""CVE ID: {record.get('cveID', 'Unknown')}
Vendor/Project: {record.get('vendorProject', '')}
Product: {record.get('product', '')}
Vulnerability: {record.get('vulnerabilityName', '')}
Date Added: {record.get('dateAdded', '')}
Short Description: {record.get('shortDescription', '')}
Required Action: {record.get('requiredAction', '')}
Due Date: {record.get('dueDate', '')}"""
        
        elif source_type == "ghsa":
            # GitHub Security Advisory
            parts = [
                f"Advisory ID: {record.get('ghsa_id', 'Unknown')}",
                f"Severity: {record.get('severity', 'Unknown')}",
                f"Summary: {record.get('summary', '')}",
            ]
            if record.get('description'):
                parts.append(f"Description: {record['description']}")
            if record.get('vulnerabilities'):
                vuln = record['vulnerabilities'][0]
                parts.append(f"Package: {vuln.get('package', {}).get('name', 'Unknown')}")
                parts.append(f"Ecosystem: {vuln.get('package', {}).get('ecosystem', 'Unknown')}")
            return "\n\n".join(p for p in parts if p)
        
        elif source_type == "atomic":
            # Atomic Red Team test
            parts = [
                f"Technique: {record.get('attack_technique', 'Unknown')}",
                f"Test Name: {record.get('name', 'Unknown')}",
                f"Description: {record.get('description', '')}",
            ]
            if record.get('executor', {}).get('command'):
                parts.append(f"Command:\n{record['executor']['command']}")
            return "\n\n".join(p for p in parts if p)
        
        elif source_type in ("kb", "soc-kb"):
            # Knowledge base Q&A
            return f"""Question: {record.get('question', '')}
Answer: {record.get('answer', '')}
Category: {record.get('category', 'Unknown')}"""
        
        else:
            # Fallback: JSON dump
            return json.dumps(record, indent=2)
    
    def _extract_metadata(self, record: dict[str, Any], source_type: str) -> dict[str, Any]:
        """Extract metadata fields from Hancock record"""
        metadata = {"source_type": source_type}
        
        if source_type == "mitre":
            metadata.update({
                "technique_id": record.get("external_references", [{}])[0].get("external_id", ""),
                "tactic": ",".join(kc.get("phase_name", "") for kc in record.get("kill_chain_phases", [])),
                "platforms": ",".join(record.get("x_mitre_platforms", [])),
            })
        elif source_type == "cve":
            metadata.update({
                "cve_id": record.get("id", ""),
                "published": record.get("published", ""),
                "severity": record.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseSeverity", ""),
            })
        elif source_type == "kev":
            metadata.update({
                "cve_id": record.get("cveID", ""),
                "vendor": record.get("vendorProject", ""),
                "product": record.get("product", ""),
                "date_added": record.get("dateAdded", ""),
            })
        elif source_type == "ghsa":
            metadata.update({
                "ghsa_id": record.get("ghsa_id", ""),
                "severity": record.get("severity", ""),
                "ecosystem": record.get("vulnerabilities", [{}])[0].get("package", {}).get("ecosystem", ""),
            })
        elif source_type == "atomic":
            metadata.update({
                "technique_id": record.get("attack_technique", ""),
                "test_name": record.get("name", ""),
                "executor": record.get("executor", {}).get("name", ""),
            })
        elif source_type in ("kb", "soc-kb"):
            metadata.update({
                "category": record.get("category", ""),
                "difficulty": record.get("difficulty", ""),
            })
        
        return metadata
    
    def ingest_all(self) -> tuple[list[SourceDocument], DatasetManifest]:
        """Ingest all discovered Hancock sources into PeachTree dataset"""
        # Discover sources
        sources = self.discover_sources()
        if not sources:
            raise ValueError("No Hancock data sources found")
        
        # Convert to source documents
        all_documents = []
        for source in sources:
            docs = self.convert_to_source_documents(source)
            all_documents.extend(docs)
        
        logger.info(f"Total documents converted: {len(all_documents)}")
        
        # Build dataset with safety gates
        safety_gate = SafetyGate(allow_unknown_license=self.config.allow_unknown_license)
        builder = DatasetBuilder(domain="cybersecurity", safety_gate=safety_gate)
        records = builder.records_from_documents(all_documents)
        
        # Write JSONL output
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dataset_path = output_dir / "hancock_security_dataset.jsonl"
        manifest_path = output_dir / "hancock_manifest.json"
        
        manifest = builder.write_jsonl(records, dataset_path, manifest_path, all_documents)
        
        logger.info(f"Dataset written to: {dataset_path}")
        logger.info(f"Manifest written to: {manifest_path}")
        
        return all_documents, manifest
    
    def generate_training_handoff(self, manifest: DatasetManifest) -> dict[str, Any]:
        """Generate trainer handoff package for Hancock dataset"""
        handoff_builder = TrainerHandoffBuilder()
        
        handoff = handoff_builder.create_handoff(
            manifest=manifest,
            model_type="cybersecurity-llm",
            base_model="meta-llama/Llama-3.2-3B",
            task_description="Cybersecurity question answering and threat analysis",
            recommended_epochs=3,
            notes=[
                "Dataset combines MITRE ATT&CK, CVE, CISA KEV, GHSA, and Atomic Red Team data",
                "Suitable for security operations and penetration testing use cases",
                "Contains real-world vulnerability and exploit documentation",
                "Recommend additional filtering for production deployment"
            ]
        )
        
        # Write handoff manifest
        handoff_path = self.config.output_dir / "hancock_trainer_handoff.json"
        handoff_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
        
        logger.info(f"Trainer handoff written to: {handoff_path}")
        return handoff


def hancock_ingestion_workflow(
    hancock_data_dir: Path | None = None,
    output_dir: Path | None = None,
    min_quality_score: float = 0.70,
    generate_handoff: bool = True
) -> dict[str, Any]:
    """
    Complete Hancock ingestion workflow
    
    Returns:
        Summary dictionary with paths and statistics
    """
    config = HancockIngestionConfig(
        hancock_data_dir=hancock_data_dir or Path("~/Hancock/data").expanduser(),
        output_dir=output_dir or Path("data/hancock"),
        min_quality_score=min_quality_score
    )
    
    ingester = HancockDataIngester(config)
    
    # Ingest all sources
    documents, manifest = ingester.ingest_all()
    
    # Quality scoring
    scorer = DatasetQualityScorer()
    quality_report = scorer.score_dataset(config.output_dir / "hancock_security_dataset.jsonl")
    
    # Deduplication
    deduplicator = DatasetDeduplicator()
    dedup_stats = deduplicator.deduplicate_dataset(
        config.output_dir / "hancock_security_dataset.jsonl",
        config.output_dir / "hancock_security_dataset_deduped.jsonl"
    )
    
    # Generate trainer handoff if requested
    handoff = None
    if generate_handoff:
        handoff = ingester.generate_training_handoff(manifest)
    
    summary = {
        "sources_ingested": len(ingester.sources),
        "total_documents": len(documents),
        "total_records": len(manifest.records),
        "quality_score": quality_report.get("overall_quality_score", 0.0),
        "deduplication": dedup_stats,
        "dataset_path": str(config.output_dir / "hancock_security_dataset_deduped.jsonl"),
        "manifest_path": str(config.output_dir / "hancock_manifest.json"),
        "handoff_path": str(config.output_dir / "hancock_trainer_handoff.json") if handoff else None,
        "ready_for_training": quality_report.get("overall_quality_score", 0.0) >= config.min_quality_score
    }
    
    return summary
