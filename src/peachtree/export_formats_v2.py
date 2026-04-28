"""
PeachTree Export Formats V2

Additional ML framework export formats: PyTorch, TensorFlow, HuggingFace, Alpaca, ShareGPT.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class ExportFormatResult:
    """Result of export format operation"""
    source_path: str
    output_path: str
    format_name: str
    records_exported: int
    output_size_bytes: int
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "format_name": self.format_name,
            "records_exported": self.records_exported,
            "output_size_bytes": self.output_size_bytes,
        }


class ExportFormatsV2:
    """Export datasets to additional ML framework formats"""
    
    def __init__(self):
        """Initialize export formats engine"""
        self.supported_formats = [
            "pytorch",
            "tensorflow",
            "huggingface",
            "alpaca",
            "sharegpt",
            "openai-finetune",
        ]
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats"""
        return self.supported_formats.copy()
    
    def export_pytorch(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> ExportFormatResult:
        """
        Export to PyTorch Dataset format
        
        Format: JSONL with {"text": ..., "label": ...} structure
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to PyTorch format
                    pytorch_record = {
                        "text": record.get("content", ""),
                        "label": record.get("label", ""),
                        "metadata": record.get("metadata", {}),
                    }
                    
                    f_out.write(json.dumps(pytorch_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="pytorch",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_tensorflow(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> ExportFormatResult:
        """
        Export to TensorFlow Dataset format
        
        Format: JSONL with {"features": {...}, "label": ...} structure
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to TensorFlow format
                    tf_record = {
                        "features": {
                            "text": record.get("content", ""),
                            "quality_score": record.get("quality_score", 0.0),
                        },
                        "label": record.get("label", ""),
                    }
                    
                    f_out.write(json.dumps(tf_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="tensorflow",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_huggingface(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> ExportFormatResult:
        """
        Export to HuggingFace datasets format
        
        Format: JSONL with {"text": ..., "meta": {...}} structure
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to HuggingFace format
                    hf_record = {
                        "text": record.get("content", ""),
                        "meta": {
                            "id": record.get("id", ""),
                            "quality_score": record.get("quality_score", 0.0),
                            "source": record.get("source_document", {}),
                        },
                    }
                    
                    f_out.write(json.dumps(hf_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="huggingface",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_alpaca(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> ExportFormatResult:
        """
        Export to Alpaca format
        
        Format: JSONL with {"instruction": ..., "input": ..., "output": ...}
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to Alpaca format
                    alpaca_record = {
                        "instruction": record.get("instruction", record.get("content", "")[:100]),
                        "input": record.get("input", ""),
                        "output": record.get("output", record.get("content", "")),
                    }
                    
                    f_out.write(json.dumps(alpaca_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="alpaca",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_sharegpt(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> ExportFormatResult:
        """
        Export to ShareGPT format
        
        Format: JSONL with {"conversations": [{"from": "human", "value": ...}, {"from": "gpt", "value": ...}]}
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to ShareGPT format
                    conversations = []
                    
                    # Check if already has conversation structure
                    if "conversations" in record:
                        conversations = record["conversations"]
                    elif "prompt" in record and "response" in record:
                        conversations = [
                            {"from": "human", "value": record["prompt"]},
                            {"from": "gpt", "value": record["response"]},
                        ]
                    else:
                        # Default: treat content as response
                        conversations = [
                            {"from": "human", "value": "Please provide information."},
                            {"from": "gpt", "value": record.get("content", "")},
                        ]
                    
                    sharegpt_record = {
                        "conversations": conversations,
                        "id": record.get("id", f"sharegpt_{record_count}"),
                    }
                    
                    f_out.write(json.dumps(sharegpt_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="sharegpt",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_openai_finetune(
        self,
        source_path: Path | str,
        output_path: Path | str,
        system_prompt: str = "You are a helpful AI assistant.",
    ) -> ExportFormatResult:
        """
        Export to OpenAI fine-tuning format
        
        Format: JSONL with {"messages": [{"role": "system", "content": ...}, {"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
            system_prompt: System prompt for OpenAI format
        
        Returns:
            ExportFormatResult
        """
        source_path = Path(source_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        record_count = 0
        
        with open(source_path) as f_in, open(output_path, 'w') as f_out:
            for line in f_in:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Convert to OpenAI format
                    messages = []
                    
                    # Add system message
                    messages.append({
                        "role": "system",
                        "content": system_prompt,
                    })
                    
                    # Check for existing messages structure
                    if "messages" in record:
                        messages.extend(record["messages"])
                    elif "prompt" in record and "response" in record:
                        messages.append({"role": "user", "content": record["prompt"]})
                        messages.append({"role": "assistant", "content": record["response"]})
                    else:
                        # Default: treat content as assistant response
                        messages.append({"role": "user", "content": "Please provide information."})
                        messages.append({"role": "assistant", "content": record.get("content", "")})
                    
                    openai_record = {"messages": messages}
                    
                    f_out.write(json.dumps(openai_record) + "\n")
                    record_count += 1
                
                except json.JSONDecodeError:
                    continue
        
        return ExportFormatResult(
            source_path=str(source_path),
            output_path=str(output_path),
            format_name="openai-finetune",
            records_exported=record_count,
            output_size_bytes=output_path.stat().st_size,
        )
    
    def export_to_format(
        self,
        source_path: Path | str,
        output_path: Path | str,
        format_name: str,
        **kwargs: Any,
    ) -> ExportFormatResult:
        """
        Export dataset to specified format
        
        Args:
            source_path: Source dataset path
            output_path: Output file path
            format_name: Export format name
            **kwargs: Additional format-specific arguments
        
        Returns:
            ExportFormatResult
        """
        if format_name == "pytorch":
            return self.export_pytorch(source_path, output_path)
        elif format_name == "tensorflow":
            return self.export_tensorflow(source_path, output_path)
        elif format_name == "huggingface":
            return self.export_huggingface(source_path, output_path)
        elif format_name == "alpaca":
            return self.export_alpaca(source_path, output_path)
        elif format_name == "sharegpt":
            return self.export_sharegpt(source_path, output_path)
        elif format_name == "openai-finetune":
            system_prompt = kwargs.get("system_prompt", "You are a helpful AI assistant.")
            return self.export_openai_finetune(source_path, output_path, system_prompt)
        else:
            raise ValueError(f"Unsupported export format: {format_name}")
    
    def batch_export(
        self,
        source_path: Path | str,
        output_dir: Path | str,
        formats: list[str],
    ) -> dict[str, ExportFormatResult]:
        """
        Export dataset to multiple formats
        
        Args:
            source_path: Source dataset path
            output_dir: Output directory for exports
            formats: List of format names
        
        Returns:
            Dictionary mapping format name to ExportFormatResult
        """
        source_path = Path(source_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for format_name in formats:
            if format_name not in self.supported_formats:
                continue
            
            output_file = output_dir / f"{source_path.stem}_{format_name}.jsonl"
            
            try:
                result = self.export_to_format(source_path, output_file, format_name)
                results[format_name] = result
            except Exception:
                continue
        
        return results
