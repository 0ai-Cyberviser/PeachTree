#!/usr/bin/env python3
"""
Hancock Boot-Time AI Agent
Runs at system startup to provide instant pentesting assistance
"""

import json
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HancockAgent:
    """Boot-time AI agent for cybersecurity"""
    
    def __init__(self, model_path: str = "/opt/hancock/models/final"):
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        """Load trained Hancock model"""
        logger.info(f"Loading Hancock model from {self.model_path}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model with quantization for memory efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            bnb_4bit_use_double_quant=True
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            quantization_config=bnb_config,
            device_map="auto"
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(base_model, self.model_path)
        self.model.eval()
        
        logger.info("✅ Model loaded successfully")
    
    def query(self, prompt: str, max_tokens: int = 200) -> str:
        """Query the model"""
        if not self.model:
            return "Model not loaded"
        
        inputs = self.tokenizer(
            f"### Instruction:\n{prompt}\n\n### Response:\n",
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("### Response:")[-1].strip()


class HancockHTTPHandler(BaseHTTPRequestHandler):
    """HTTP API for Hancock agent"""
    
    agent = None  # Set by server
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
            prompt = data.get('prompt', '')
            
            if not prompt:
                self.send_error(400, "Missing 'prompt' field")
                return
            
            response = self.agent.query(prompt)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode('utf-8'))
        
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Log to file instead of console"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_http_server(agent: HancockAgent, port: int = 8080):
    """Run HTTP API server"""
    HancockHTTPHandler.agent = agent
    server = HTTPServer(('127.0.0.1', port), HancockHTTPHandler)
    logger.info(f"🌐 HTTP API running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    # Initialize agent
    agent = HancockAgent()
    agent.load_model()
    
    # Start HTTP server in background
    server_thread = threading.Thread(target=run_http_server, args=(agent, 8080), daemon=True)
    server_thread.start()
    
    # CLI interface
    logger.info("✅ Hancock AI Agent ready!")
    logger.info("HTTP API: http://127.0.0.1:8080")
    logger.info("Example: curl -X POST http://127.0.0.1:8080 -d '{\"prompt\": \"Explain SQL injection\"}'")
    
    # Keep alive
    server_thread.join()
