"""
PeachTree Advanced Export Formats

Additional export formats for ML frameworks including Llama, Gemini, Claude,
and cybersecurity-specific formats for Hancock workflows.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class ExportResult:
    """Result of export operation"""
    source_dataset: str
    output_path: str
    export_format: str
    records_exported: int
    metadata: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dataset": self.source_dataset,
            "output_path": self.output_path,
            "export_format": self.export_format,
            "records_exported": self.records_exported,
            "metadata": self.metadata,
        }


class AdvancedExporters:
    """Advanced export formats for various ML frameworks"""
    
    @staticmethod
    def export_llama3(
        dataset_path: Path | str,
        output_path: Path | str,
        system_prompt: str = "You are a helpful AI assistant.",
    ) -> ExportResult:
        """
        Export to Llama 3 format
        
        Format: {"messages": [{"role": "system", "content": "..."}, ...]}
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Llama 3 format
                llama_record = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ]
                }
                
                # Add provenance as metadata
                if "source_repo" in record or "source_path" in record:
                    llama_record["metadata"] = {
                        "source_repo": record.get("source_repo"),
                        "source_path": record.get("source_path"),
                    }
                
                f_out.write(json.dumps(llama_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="llama3",
            records_exported=count,
            metadata={"system_prompt": system_prompt},
        )
    
    @staticmethod
    def export_gemini(
        dataset_path: Path | str,
        output_path: Path | str,
    ) -> ExportResult:
        """
        Export to Google Gemini format
        
        Format: {"contents": [{"role": "user", "parts": [{"text": "..."}]}]}
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Gemini format
                gemini_record = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": content}]
                        }
                    ]
                }
                
                f_out.write(json.dumps(gemini_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="gemini",
            records_exported=count,
            metadata={},
        )
    
    @staticmethod
    def export_claude(
        dataset_path: Path | str,
        output_path: Path | str,
        system_prompt: str = "You are Claude, an AI assistant created by Anthropic.",
    ) -> ExportResult:
        """
        Export to Claude format (Anthropic Messages API)
        
        Format: {"system": "...", "messages": [{"role": "user", "content": "..."}]}
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Claude format
                claude_record = {
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": content}
                    ]
                }
                
                f_out.write(json.dumps(claude_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="claude",
            records_exported=count,
            metadata={"system_prompt": system_prompt},
        )
    
    @staticmethod
    def export_hancock_cybersecurity(
        dataset_path: Path | str,
        output_path: Path | str,
    ) -> ExportResult:
        """
        Export to Hancock cybersecurity format
        
        Format optimized for security analysis with IOCs, TTPs, and MITRE ATT&CK
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Hancock cybersecurity format
                hancock_record = {
                    "task": "cybersecurity_analysis",
                    "input": content,
                    "metadata": {
                        "source_repo": record.get("source_repo"),
                        "source_path": record.get("source_path"),
                        "digest": record.get("digest"),
                    },
                    "security_context": {
                        "iocs_present": False,
                        "mitre_tactics": [],
                        "severity": "unknown",
                    }
                }
                
                f_out.write(json.dumps(hancock_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="hancock_cybersecurity",
            records_exported=count,
            metadata={"specialized": "cybersecurity"},
        )
    
    @staticmethod
    def export_mistral(
        dataset_path: Path | str,
        output_path: Path | str,
    ) -> ExportResult:
        """
        Export to Mistral AI format
        
        Format: {"messages": [{"role": "user", "content": "..."}]}
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Mistral format
                mistral_record = {
                    "messages": [
                        {"role": "user", "content": content}
                    ]
                }
                
                f_out.write(json.dumps(mistral_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="mistral",
            records_exported=count,
            metadata={},
        )
    
    @staticmethod
    def export_qwen(
        dataset_path: Path | str,
        output_path: Path | str,
        system_prompt: str = "You are Qwen, a helpful AI assistant.",
    ) -> ExportResult:
        """
        Export to Qwen format (Alibaba Cloud)
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Qwen format
                qwen_record = {
                    "conversations": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ]
                }
                
                f_out.write(json.dumps(qwen_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="qwen",
            records_exported=count,
            metadata={"system_prompt": system_prompt},
        )
    
    @staticmethod
    def export_unsloth(
        dataset_path: Path | str,
        output_path: Path | str,
    ) -> ExportResult:
        """
        Export to Unsloth training format (optimized for LoRA)
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Unsloth LoRA format
                unsloth_record = {
                    "text": content,
                    "metadata": {
                        "source_repo": record.get("source_repo"),
                        "provenance": record.get("digest"),
                    }
                }
                
                f_out.write(json.dumps(unsloth_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="unsloth",
            records_exported=count,
            metadata={"training_type": "lora"},
        )
    
    @staticmethod
    def export_jsonl_with_conversation(
        dataset_path: Path | str,
        output_path: Path | str,
        conversation_field: str = "conversation",
    ) -> ExportResult:
        """
        Export with conversation structure (multi-turn dialogs)
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        with open(dataset_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                content = record.get("content", "")
                
                # Multi-turn conversation format
                conv_record = {
                    "id": record.get("id"),
                    conversation_field: [
                        {"role": "user", "content": content},
                    ],
                    "metadata": {
                        "source_repo": record.get("source_repo"),
                        "source_path": record.get("source_path"),
                    }
                }
                
                f_out.write(json.dumps(conv_record) + "\n")
                count += 1
        
        return ExportResult(
            source_dataset=str(dataset_path),
            output_path=str(output_path),
            export_format="jsonl_conversation",
            records_exported=count,
            metadata={"conversation_field": conversation_field},
        )


def get_advanced_format_names() -> list[str]:
    """Get list of available advanced format names"""
    return [
        "llama3",
        "gemini",
        "claude",
        "hancock_cybersecurity",
        "mistral",
        "qwen",
        "unsloth",
        "jsonl_conversation",
    ]
