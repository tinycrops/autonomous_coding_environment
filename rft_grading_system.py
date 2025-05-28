#!/usr/bin/env python3
"""
Reinforcement Fine-Tuning (RFT) Grading System for Autonomous Coding Environment

This module implements sophisticated grading mechanisms for evaluating and improving
code generation tasks using reinforcement fine-tuning methodology.
"""

import json
import os
import time
import openai
import requests
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Union
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, utils
import logging
from datetime import datetime
from base_task_processor import Task
import concurrent.futures
from tqdm import tqdm
import functools

# Initialize OpenAI client
client = openai.OpenAI()

class GraderStep(BaseModel):
    description: str
    conclusion: str

class GraderResponse(BaseModel):
    result: float
    steps: List[GraderStep]

class CodeGradingMetrics(BaseModel):
    """Metrics for evaluating code quality and correctness."""
    functionality_score: float = Field(ge=0.0, le=1.0)
    code_quality_score: float = Field(ge=0.0, le=1.0) 
    performance_score: float = Field(ge=0.0, le=1.0)
    error_handling_score: float = Field(ge=0.0, le=1.0)
    documentation_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

class RFTGradingSystem:
    """
    Advanced grading system for autonomous coding tasks using RFT methodology.
    """
    
    def __init__(self, model: str = "gpt-4.1-2025-04-14"):
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
        self.grading_history = []
        
    def code_functionality_grader(self, sample: Dict, item: Dict) -> float:
        """
        Binary grader for code functionality - does it work correctly?
        """
        execution_result = sample.get("execution_result", {})
        success = execution_result.get("success", False)
        
        if success:
            # Check if output matches expected (if provided)
            expected_output = item.get("expected_output")
            actual_output = execution_result.get("output", "")
            
            if expected_output:
                similarity = fuzz.token_set_ratio(
                    actual_output.strip(), 
                    expected_output.strip(), 
                    processor=utils.default_process
                ) / 100.0
                return min(1.0, similarity + 0.3)  # Bonus for execution success
            else:
                return 1.0  # No errors and no expected output to compare
        else:
            return 0.0

    def code_quality_grader(self, sample: Dict, item: Dict) -> float:
        """
        Fuzzy grader for code quality using token similarity and best practices.
        """
        code = sample.get("output_text", "")
        reference_code = item.get("reference_code", "")
        
        if not reference_code:
            # Use heuristic scoring for code quality
            return self._heuristic_code_quality_score(code)
        
        # Compare with reference implementation
        score = fuzz.token_set_ratio(code, reference_code, processor=utils.default_process) / 100.0
        return score

    def _heuristic_code_quality_score(self, code: str) -> float:
        """
        Heuristic scoring for code quality without reference.
        """
        score = 0.5  # Base score
        
        # Check for good practices
        if "def " in code:  # Function definitions
            score += 0.1
        if "try:" in code and "except" in code:  # Error handling
            score += 0.1
        if '"""' in code or "'''" in code:  # Documentation
            score += 0.1
        if "import " in code:  # Proper imports
            score += 0.1
        if "if __name__" in code:  # Main guard
            score += 0.1
        if len(code.split('\n')) > 5:  # Reasonable length
            score += 0.1
            
        return min(1.0, score)

    def combined_code_grader(self, sample: Dict, item: Dict, 
                           weights: List[float] = [0.6, 0.4]) -> float:
        """
        Combined grader weighing functionality and quality.
        """
        functionality_score = self.code_functionality_grader(sample, item)
        quality_score = self.code_quality_grader(sample, item)
        
        return weights[0] * functionality_score + weights[1] * quality_score

    def build_advanced_model_grader(self, domain: str = "general_programming") -> Dict:
        """
        Build an advanced model-based grader for code evaluation.
        """
        
        if domain == "general_programming":
            grader_prompt = """You are an expert software engineer and code reviewer.

Compare the reference_solution (if provided) with the model_generated_code and evaluate based on:

1. **Functionality**: Does the code solve the problem correctly?
2. **Code Quality**: Is it well-structured, readable, and follows best practices?
3. **Error Handling**: Does it handle edge cases and errors appropriately?
4. **Performance**: Is the solution efficient?
5. **Documentation**: Are there adequate comments and docstrings?

Return **exactly** this JSON object:
{
  "steps": [
    {"description": "functionality analysis", "conclusion": "..."},
    {"description": "code quality assessment", "conclusion": "..."},
    {"description": "error handling review", "conclusion": "..."},
    {"description": "performance evaluation", "conclusion": "..."},
    {"description": "documentation check", "conclusion": "..."}
  ],
  "result": <float 0-1 rounded to 3 decimals>
}

**Scoring Guidelines:**
- Start with base score of 0.5
- Functionality (max +0.3): Correct solution = +0.3, partial = +0.1-0.2
- Code Quality (max +0.2): Clean, readable code = +0.2
- Error Handling (max +0.1): Proper try/catch and validation = +0.1
- Performance (max +0.1): Efficient algorithm/implementation = +0.1
- Documentation (max +0.1): Good comments and docstrings = +0.1
- Penalties: Syntax errors = -0.2, security issues = -0.3

**Input:**
Task Description: {{item.description}}
Reference Solution: {{item.reference_code}}
Model Generated Code: {{sample.output_text}}
Execution Result: {{sample.execution_result}}
"""
        
        return {
            "type": "score_model",
            "name": f"{domain}_code_grader",
            "input": [
                {"role": "system", "content": grader_prompt},
                {
                    "role": "user", 
                    "content": "Task: {{item.description}}\nReference: {{item.reference_code}}\nGenerated Code: {{sample.output_text}}\nExecution: {{sample.execution_result}}"
                }
            ],
            "pass_threshold": 0.75,
            "model": self.model,
            "range": [0, 1],
            "sampling_params": {"seed": 42, "temperature": 0}
        }

    def python_model_grader(self, sample: Dict, item: Dict, 
                          model_grader: Dict) -> float:
        """
        Execute model-based grading using OpenAI API.
        """
        try:
            # Prepare the prompt
            system_prompt = model_grader["input"][0]["content"]
            user_prompt = model_grader["input"][1]["content"]
            
            # Replace placeholders
            placeholders = {
                "{{item.description}}": item.get("description", ""),
                "{{item.reference_code}}": item.get("reference_code", ""),
                "{{sample.output_text}}": sample.get("output_text", ""),
                "{{sample.execution_result}}": str(sample.get("execution_result", {}))
            }
            
            for placeholder, value in placeholders.items():
                user_prompt = user_prompt.replace(placeholder, value)
                system_prompt = system_prompt.replace(placeholder, value)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call OpenAI API
            response = client.beta.chat.completions.parse(
                model=model_grader["model"],
                messages=messages,
                seed=model_grader.get("sampling_params", {}).get("seed"),
                temperature=model_grader.get("sampling_params", {}).get("temperature", 0),
                response_format=GraderResponse,
            )
            
            parsed = response.choices[0].message.parsed
            if not isinstance(parsed, GraderResponse):
                raise ValueError(f"Invalid grader response: {parsed}")
                
            return float(parsed.result)
            
        except Exception as e:
            self.logger.error(f"Model grading failed: {e}")
            # Fallback to combined grader
            return self.combined_code_grader(sample, item)

    def evaluate_task_batch(self, tasks: List[Task], 
                          grader_func: Callable, 
                          workspace_path: str) -> Dict[str, Any]:
        """
        Evaluate a batch of tasks using the specified grader.
        """
        results = []
        total_score = 0
        
        for task in tasks:
            # Prepare sample and item for grading
            sample = {
                "output_text": task.code,
                "execution_result": task.execution_result or {}
            }
            
            item = {
                "description": task.description,
                "reference_code": getattr(task.metadata, 'reference_code', '') if task.metadata else '',
                "expected_output": getattr(task.metadata, 'expected_output', '') if task.metadata else ''
            }
            
            # Grade the task
            try:
                score = grader_func(sample, item)
                total_score += score
                
                result = {
                    "task_id": task.id,
                    "score": score,
                    "sample": sample,
                    "item": item,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Grading failed for task {task.id}: {e}")
                results.append({
                    "task_id": task.id,
                    "score": 0.0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Calculate metrics
        avg_score = total_score / len(tasks) if tasks else 0
        successful_evaluations = len([r for r in results if "error" not in r])
        
        evaluation_summary = {
            "total_tasks": len(tasks),
            "successful_evaluations": successful_evaluations,
            "average_score": avg_score,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store evaluation history
        self.grading_history.append(evaluation_summary)
        
        return evaluation_summary

    def prepare_rft_training_data(self, evaluation_results: Dict[str, Any], 
                                output_file: str) -> str:
        """
        Convert evaluation results to RFT training format.
        """
        rft_samples = []
        
        for result in evaluation_results["results"]:
            if "error" in result:
                continue
                
            rft_sample = {
                "messages": [
                    {
                        "role": "user", 
                        "content": result["item"]["description"]
                    }
                ],
                "reference_answer": result["sample"]["output_text"],
                "score": result["score"]
            }
            rft_samples.append(rft_sample)
        
        # Write to JSONL format
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            for sample in rft_samples:
                f.write(json.dumps(sample) + '\n')
        
        self.logger.info(f"Prepared {len(rft_samples)} RFT training samples in {output_file}")
        return output_file

    def launch_rft_job(self, train_file: str, test_file: str, 
                      grader_config: Dict, suffix: str = "ace_rft") -> Optional[str]:
        """
        Launch an RFT fine-tuning job using OpenAI API.
        """
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.logger.error("OPENAI_API_KEY not found in environment")
                return None
            
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Upload files
            def upload_file(file_path: str) -> str:
                with open(file_path, 'rb') as f:
                    response = requests.post(
                        "https://api.openai.com/v1/files",
                        headers=headers,
                        files={"file": f},
                        data={"purpose": "fine-tune"}
                    )
                    response.raise_for_status()
                    return response.json()["id"]
            
            train_file_id = upload_file(train_file)
            test_file_id = upload_file(test_file) if test_file else None
            
            # Launch RFT job
            payload = {
                "training_file": train_file_id,
                "test_file": test_file_id,
                "model": "o4-mini-2025-04-16",
                "suffix": suffix,
                "method": {
                    "type": "reinforcement",
                    "reinforcement": {
                        "grader": grader_config,
                        "hyperparameters": {
                            "compute_multiplier": 1.0,
                            "etest_samples": 1,
                            "eval_interval": 5,
                            "n_epochs": 3,
                            "reasoning_effort": "medium",
                        }
                    }
                },
                "seed": 42
            }
            
            response = requests.post(
                "https://api.openai.com/v1/fine_tuning/jobs",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            job_id = response.json().get("id")
            self.logger.info(f"RFT job launched with ID: {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to launch RFT job: {e}")
            return None

    def get_rft_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of an RFT job.
        """
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.get(
                f"https://api.openai.com/v1/fine_tuning/jobs/{job_id}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to get RFT job status: {e}")
            return {"error": str(e)}

    def save_grading_history(self, filepath: str) -> None:
        """Save grading history to file."""
        with open(filepath, 'w') as f:
            json.dump(self.grading_history, f, indent=2)

    def load_grading_history(self, filepath: str) -> None:
        """Load grading history from file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.grading_history = json.load(f) 