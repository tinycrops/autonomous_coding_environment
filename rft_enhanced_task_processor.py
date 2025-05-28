#!/usr/bin/env python3
"""
RFT-Enhanced Task Processor

This module extends the base task processor with reinforcement fine-tuning capabilities,
enabling continuous self-improvement through structured feedback and model refinement.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
from colorama import Fore, Style
import numpy as np

from base_task_processor import BaseTaskProcessor, Task, Metadata
from rft_grading_system import RFTGradingSystem, CodeGradingMetrics
import functools

class RFTEnhancedTaskProcessor(BaseTaskProcessor):
    """
    Enhanced task processor with RFT capabilities for continuous improvement.
    """
    
    def __init__(self, model: str = "o4-mini", rft_model: Optional[str] = None):
        super().__init__(model)
        self.rft_grader = RFTGradingSystem()
        self.rft_model = rft_model  # Fine-tuned model ID if available
        self.improvement_history = []
        self.performance_threshold = 0.75  # Minimum score before attempting improvement
        self.rft_training_data_path = "data/rft_training"
        self.current_grader_config = None
        
        # Ensure RFT data directory exists
        os.makedirs(self.rft_training_data_path, exist_ok=True)
        
        # Load existing improvement history
        self._load_improvement_history()

    def set_grader_config(self, domain: str = "general_programming") -> None:
        """Set the grader configuration for the current domain."""
        self.current_grader_config = self.rft_grader.build_advanced_model_grader(domain)
        self.logger.info(f"Set grader config for domain: {domain}")

    def process_task_with_rft(self, task: Task, workspace_path: str, 
                            enable_improvement: bool = True) -> Task:
        """
        Process a task with RFT enhancement - generate, execute, grade, and improve if needed.
        """
        self.logger.info(f"{Fore.BLUE}🚀 Processing task {task.id} with RFT enhancement")
        
        # Use fine-tuned model if available
        generation_model = self.rft_model if self.rft_model else self.model
        
        # Generate code
        if not task.code:
            original_model = self.model
            self.model = generation_model
            task.code = self.generate_code_for_task(task)
            self.model = original_model
        
        # Execute code
        execution_result = self.execute_task_code(task, workspace_path)
        task.execution_result = execution_result
        
        # Grade the result
        if self.current_grader_config:
            grader_func = functools.partial(
                self.rft_grader.python_model_grader, 
                model_grader=self.current_grader_config
            )
        else:
            grader_func = self.rft_grader.combined_code_grader
        
        # Evaluate single task
        evaluation_result = self.rft_grader.evaluate_task_batch([task], grader_func, workspace_path)
        task_score = evaluation_result["results"][0]["score"]
        
        self.logger.info(f"{Fore.YELLOW}📊 Task {task.id} scored: {task_score:.3f}")
        
        # Store grading result in task metadata
        if not task.metadata:
            task.metadata = Metadata(
                description=task.description,
                tags=["rft-processed"],
                complexity=5,
                estimated_time="unknown",
                poetic_description="A task enhanced through reinforcement learning."
            )
        
        # Add RFT metrics to metadata
        task.metadata.tags.append(f"rft_score_{task_score:.3f}")
        
        # Attempt improvement if score is below threshold and improvement is enabled
        if enable_improvement and task_score < self.performance_threshold:
            task = self._attempt_task_improvement(task, workspace_path, task_score)
        
        return task

    def _attempt_task_improvement(self, task: Task, workspace_path: str, 
                                initial_score: float) -> Task:
        """
        Attempt to improve a task through iterative refinement.
        """
        self.logger.info(f"{Fore.BLUE}🔧 Attempting to improve task {task.id} (score: {initial_score:.3f})")
        
        max_improvement_attempts = 3
        best_score = initial_score
        best_code = task.code
        
        for attempt in range(max_improvement_attempts):
            # Generate improved code using execution feedback
            improved_code = self.improve_task_code(task, task.execution_result)
            
            # Create a temporary task for testing
            temp_task = Task(
                id=f"{task.id}_improved_{attempt}",
                description=task.description,
                code=improved_code,
                metadata=task.metadata
            )
            
            # Execute improved code
            improved_execution = self.execute_task_code(temp_task, workspace_path)
            temp_task.execution_result = improved_execution
            
            # Grade improved version
            if self.current_grader_config:
                grader_func = functools.partial(
                    self.rft_grader.python_model_grader, 
                    model_grader=self.current_grader_config
                )
            else:
                grader_func = self.rft_grader.combined_code_grader
            
            improved_evaluation = self.rft_grader.evaluate_task_batch([temp_task], grader_func, workspace_path)
            improved_score = improved_evaluation["results"][0]["score"]
            
            self.logger.info(f"{Fore.YELLOW}📈 Improvement attempt {attempt + 1}: {improved_score:.3f}")
            
            # Keep the best version
            if improved_score > best_score:
                best_score = improved_score
                best_code = improved_code
                task.execution_result = improved_execution
                
                # Update metadata
                task.metadata.tags.append(f"improved_attempt_{attempt + 1}")
                
                # Stop if we've reached a good score
                if improved_score >= self.performance_threshold:
                    self.logger.info(f"{Fore.GREEN}✅ Task improvement successful!")
                    break
            else:
                self.logger.info(f"{Fore.YELLOW}⚠️ No improvement in attempt {attempt + 1}")
        
        # Apply best result
        task.code = best_code
        
        # Record improvement attempt
        improvement_record = {
            "task_id": task.id,
            "initial_score": initial_score,
            "final_score": best_score,
            "improvement": best_score - initial_score,
            "attempts": max_improvement_attempts,
            "timestamp": datetime.now().isoformat()
        }
        self.improvement_history.append(improvement_record)
        
        return task

    def batch_process_with_rft(self, tasks: List[Task], workspace_path: str) -> List[Task]:
        """
        Process multiple tasks with RFT, collecting data for potential fine-tuning.
        """
        self.logger.info(f"{Fore.BLUE}🚀 Batch processing {len(tasks)} tasks with RFT")
        
        processed_tasks = []
        for task in tasks:
            processed_task = self.process_task_with_rft(task, workspace_path)
            processed_tasks.append(processed_task)
        
        # Evaluate batch performance
        self._evaluate_batch_performance(processed_tasks, workspace_path)
        
        return processed_tasks

    def _evaluate_batch_performance(self, tasks: List[Task], workspace_path: str) -> Dict[str, Any]:
        """
        Evaluate overall batch performance and decide if RFT training is warranted.
        """
        if self.current_grader_config:
            grader_func = functools.partial(
                self.rft_grader.python_model_grader, 
                model_grader=self.current_grader_config
            )
        else:
            grader_func = self.rft_grader.combined_code_grader
        
        evaluation_result = self.rft_grader.evaluate_task_batch(tasks, grader_func, workspace_path)
        avg_score = evaluation_result["average_score"]
        
        self.logger.info(f"{Fore.CYAN}📊 Batch average score: {avg_score:.3f}")
        
        # If performance is below threshold, consider RFT training
        if avg_score < self.performance_threshold:
            self.logger.info(f"{Fore.YELLOW}🎯 Performance below threshold, preparing RFT training data")
            self._prepare_rft_training_session(evaluation_result)
        
        return evaluation_result

    def _prepare_rft_training_session(self, evaluation_result: Dict[str, Any]) -> None:
        """
        Prepare and potentially launch RFT training based on evaluation results.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        train_file = os.path.join(self.rft_training_data_path, f"rft_train_{timestamp}.jsonl")
        
        # Prepare training data
        self.rft_grader.prepare_rft_training_data(evaluation_result, train_file)
        
        # Check if we have enough data for training
        with open(train_file, 'r') as f:
            sample_count = sum(1 for _ in f)
        
        if sample_count >= 20:  # Minimum samples for meaningful training
            self.logger.info(f"{Fore.GREEN}🎓 Sufficient data for RFT training ({sample_count} samples)")
            
            # Optionally auto-launch RFT training
            if self.current_grader_config and os.environ.get("AUTO_RFT_TRAINING", "false").lower() == "true":
                self._launch_rft_training(train_file)
        else:
            self.logger.info(f"{Fore.YELLOW}📚 Need more data for RFT training (have {sample_count}, need 20+)")

    def _launch_rft_training(self, train_file: str) -> Optional[str]:
        """
        Launch RFT training job.
        """
        if not self.current_grader_config:
            self.logger.error("No grader config set for RFT training")
            return None
        
        # For now, create a basic test file by splitting the training data
        test_file = train_file.replace("_train_", "_test_")
        self._split_training_data(train_file, test_file, test_ratio=0.2)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"ace_rft_{timestamp}"
        
        job_id = self.rft_grader.launch_rft_job(
            train_file=train_file,
            test_file=test_file,
            grader_config=self.current_grader_config,
            suffix=suffix
        )
        
        if job_id:
            self.logger.info(f"{Fore.GREEN}🚀 RFT training launched with job ID: {job_id}")
            
            # Store job info for monitoring
            job_info = {
                "job_id": job_id,
                "launch_time": datetime.now().isoformat(),
                "train_file": train_file,
                "test_file": test_file,
                "suffix": suffix
            }
            
            job_file = os.path.join(self.rft_training_data_path, f"rft_job_{job_id}.json")
            with open(job_file, 'w') as f:
                json.dump(job_info, f, indent=2)
        
        return job_id

    def _split_training_data(self, train_file: str, test_file: str, test_ratio: float = 0.2) -> None:
        """
        Split training data into train/test sets.
        """
        with open(train_file, 'r') as f:
            lines = f.readlines()
        
        # Shuffle and split
        import random
        random.shuffle(lines)
        split_idx = int(len(lines) * (1 - test_ratio))
        
        train_lines = lines[:split_idx]
        test_lines = lines[split_idx:]
        
        # Write train file
        with open(train_file, 'w') as f:
            f.writelines(train_lines)
        
        # Write test file
        with open(test_file, 'w') as f:
            f.writelines(test_lines)
        
        self.logger.info(f"Split data: {len(train_lines)} train, {len(test_lines)} test samples")

    def check_rft_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of an RFT training job.
        """
        return self.rft_grader.get_rft_job_status(job_id)

    def update_model_after_rft(self, job_id: str) -> bool:
        """
        Update the processor to use a newly fine-tuned model.
        """
        job_status = self.check_rft_job_status(job_id)
        
        if job_status.get("status") == "succeeded":
            fine_tuned_model = job_status.get("fine_tuned_model")
            if fine_tuned_model:
                self.rft_model = fine_tuned_model
                self.logger.info(f"{Fore.GREEN}✅ Updated to use fine-tuned model: {fine_tuned_model}")
                return True
        
        return False

    def get_performance_analytics(self) -> Dict[str, Any]:
        """
        Get analytics on task performance and improvement trends.
        """
        if not self.improvement_history:
            return {"message": "No improvement history available"}
        
        improvements = [record["improvement"] for record in self.improvement_history]
        initial_scores = [record["initial_score"] for record in self.improvement_history]
        final_scores = [record["final_score"] for record in self.improvement_history]
        
        analytics = {
            "total_improvement_attempts": len(self.improvement_history),
            "average_improvement": np.mean(improvements),
            "average_initial_score": np.mean(initial_scores),
            "average_final_score": np.mean(final_scores),
            "successful_improvements": len([i for i in improvements if i > 0]),
            "improvement_rate": len([i for i in improvements if i > 0]) / len(improvements),
            "best_improvement": max(improvements) if improvements else 0,
            "recent_performance": final_scores[-10:] if len(final_scores) >= 10 else final_scores
        }
        
        return analytics

    def _load_improvement_history(self) -> None:
        """Load improvement history from file."""
        history_file = os.path.join(self.rft_training_data_path, "improvement_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.improvement_history = json.load(f)
                self.logger.info(f"Loaded {len(self.improvement_history)} improvement records")
            except Exception as e:
                self.logger.warning(f"Failed to load improvement history: {e}")

    def save_improvement_history(self) -> None:
        """Save improvement history to file."""
        history_file = os.path.join(self.rft_training_data_path, "improvement_history.json")
        try:
            with open(history_file, 'w') as f:
                json.dump(self.improvement_history, f, indent=2)
            self.logger.info(f"Saved {len(self.improvement_history)} improvement records")
        except Exception as e:
            self.logger.error(f"Failed to save improvement history: {e}")

    def export_training_dataset(self, output_file: str, min_score: float = 0.8) -> str:
        """
        Export high-quality task examples for external training.
        """
        # Collect high-scoring examples from grading history
        high_quality_samples = []
        
        for evaluation in self.rft_grader.grading_history:
            for result in evaluation["results"]:
                if result.get("score", 0) >= min_score and "error" not in result:
                    sample = {
                        "messages": [{"role": "user", "content": result["item"]["description"]}],
                        "reference_answer": result["sample"]["output_text"],
                        "score": result["score"],
                        "execution_success": result["sample"]["execution_result"].get("success", False)
                    }
                    high_quality_samples.append(sample)
        
        # Write to JSONL
        with open(output_file, 'w') as f:
            for sample in high_quality_samples:
                f.write(json.dumps(sample) + '\n')
        
        self.logger.info(f"Exported {len(high_quality_samples)} high-quality samples to {output_file}")
        return output_file 