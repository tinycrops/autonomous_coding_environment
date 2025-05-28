#!/usr/bin/env python3
"""
RFT Demonstration Script

This script demonstrates the integration of Reinforcement Fine-Tuning (RFT) 
capabilities into the autonomous coding environment.
"""

import os
import json
import time
from typing import List
from colorama import Fore, Style, init
import logging

from base_task_processor import Task, Metadata
from rft_enhanced_task_processor import RFTEnhancedTaskProcessor
from rft_grading_system import RFTGradingSystem

# Initialize colorama
init(autoreset=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_tasks() -> List[Task]:
    """Create a variety of sample coding tasks for demonstration."""
    
    tasks = [
        Task(
            id="task_001_calculator",
            description="Create a simple calculator that can perform basic arithmetic operations (add, subtract, multiply, divide). Include error handling for division by zero.",
            metadata=Metadata(
                description="Basic calculator implementation",
                tags=["arithmetic", "calculator", "basic"],
                complexity=3,
                estimated_time="15 minutes",
                poetic_description="A digital abacus that dances with numbers in the realm of computation."
            )
        ),
        
        Task(
            id="task_002_fibonacci", 
            description="Implement a function to generate the Fibonacci sequence up to n terms. Include both iterative and recursive approaches.",
            metadata=Metadata(
                description="Fibonacci sequence generator",
                tags=["algorithms", "sequences", "recursion"],
                complexity=4,
                estimated_time="20 minutes",
                poetic_description="Golden spirals encoded in the language of mathematics and code."
            )
        ),
        
        Task(
            id="task_003_palindrome",
            description="Create a function that checks if a given string is a palindrome. Handle edge cases like empty strings and non-alphabetic characters.",
            metadata=Metadata(
                description="Palindrome checker function",
                tags=["strings", "algorithms", "validation"],
                complexity=3,
                estimated_time="15 minutes", 
                poetic_description="Words that read the same forwards and backwards, mirrors in the world of text."
            )
        ),
        
        Task(
            id="task_004_file_processor",
            description="Write a script that reads a text file, counts word frequencies, and writes the results to a JSON file. Include proper error handling for file operations.",
            metadata=Metadata(
                description="File processing with word frequency analysis",
                tags=["file-io", "text-processing", "json"],
                complexity=5,
                estimated_time="25 minutes",
                poetic_description="A digital librarian that counts whispers in the pages of text."
            )
        ),
        
        Task(
            id="task_005_data_validator",
            description="Create a data validation class that can validate email addresses, phone numbers, and postal codes using regular expressions.",
            metadata=Metadata(
                description="Data validation utilities",
                tags=["validation", "regex", "class-design"],
                complexity=6,
                estimated_time="30 minutes",
                poetic_description="A guardian at the gates of data, ensuring only the worthy may pass."
            )
        )
    ]
    
    return tasks

def demonstrate_basic_rft_grading():
    """Demonstrate basic RFT grading capabilities."""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🧪 DEMONSTRATING BASIC RFT GRADING")
    print(f"{Fore.CYAN}{'='*60}")
    
    # Create RFT grading system
    rft_grader = RFTGradingSystem()
    
    # Example code samples for grading
    sample_good = {
        "output_text": '''
def calculator(a, b, operation):
    """Simple calculator with error handling."""
    try:
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError("Invalid operation")
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print(calculator(10, 5, "add"))  # Should print 15
    print(calculator(10, 0, "divide"))  # Should handle error
''',
        "execution_result": {"success": True, "output": "15\nError: Cannot divide by zero\nNone"}
    }
    
    sample_poor = {
        "output_text": '''
def calc(a, b, op):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
''',
        "execution_result": {"success": False, "error": "Incomplete implementation"}
    }
    
    item = {
        "description": "Create a simple calculator with error handling",
        "expected_output": "15\nError: Cannot divide by zero\nNone"
    }
    
    # Grade both samples
    good_score = rft_grader.combined_code_grader(sample_good, item)
    poor_score = rft_grader.combined_code_grader(sample_poor, item)
    
    print(f"{Fore.GREEN}✅ Good implementation score: {good_score:.3f}")
    print(f"{Fore.RED}❌ Poor implementation score: {poor_score:.3f}")
    
    return rft_grader

def demonstrate_rft_enhanced_processing():
    """Demonstrate the RFT-enhanced task processing."""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🚀 DEMONSTRATING RFT-ENHANCED TASK PROCESSING")
    print(f"{Fore.CYAN}{'='*60}")
    
    # Create RFT-enhanced processor
    processor = RFTEnhancedTaskProcessor(model="o4-mini")
    
    # Set grader configuration for general programming
    processor.set_grader_config("general_programming")
    
    # Create sample tasks
    tasks = create_sample_tasks()[:3]  # Use first 3 tasks for demo
    
    # Create workspace
    workspace_path = "rft_demo_workspace"
    os.makedirs(workspace_path, exist_ok=True)
    
    print(f"{Fore.BLUE}📋 Processing {len(tasks)} tasks with RFT enhancement...")
    
    # Process tasks with RFT
    processed_tasks = []
    for task in tasks:
        print(f"\n{Fore.YELLOW}Processing: {task.id}")
        processed_task = processor.process_task_with_rft(task, workspace_path)
        processed_tasks.append(processed_task)
        
        # Show results
        score = None
        for tag in processed_task.metadata.tags:
            if tag.startswith("rft_score_"):
                score = float(tag.split("_")[-1])
                break
        
        if score:
            color = Fore.GREEN if score >= 0.75 else Fore.YELLOW if score >= 0.5 else Fore.RED
            print(f"{color}📊 Score: {score:.3f}")
    
    return processor, processed_tasks

def demonstrate_batch_processing():
    """Demonstrate batch processing with RFT evaluation."""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📦 DEMONSTRATING BATCH PROCESSING WITH RFT")
    print(f"{Fore.CYAN}{'='*60}")
    
    # Create processor
    processor = RFTEnhancedTaskProcessor(model="o4-mini")
    processor.set_grader_config("general_programming")
    
    # Create all sample tasks
    tasks = create_sample_tasks()
    
    # Create workspace
    workspace_path = "rft_batch_workspace"
    os.makedirs(workspace_path, exist_ok=True)
    
    print(f"{Fore.BLUE}🚀 Batch processing {len(tasks)} tasks...")
    
    # Process all tasks
    processed_tasks = processor.batch_process_with_rft(tasks, workspace_path)
    
    # Show batch results
    scores = []
    for task in processed_tasks:
        for tag in task.metadata.tags:
            if tag.startswith("rft_score_"):
                scores.append(float(tag.split("_")[-1]))
                break
    
    if scores:
        avg_score = sum(scores) / len(scores)
        print(f"\n{Fore.CYAN}📊 Batch Results:")
        print(f"{Fore.CYAN}   Average Score: {avg_score:.3f}")
        print(f"{Fore.CYAN}   Scores: {[f'{s:.3f}' for s in scores]}")
    
    return processor

def demonstrate_performance_analytics():
    """Demonstrate performance analytics and improvement tracking."""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📈 DEMONSTRATING PERFORMANCE ANALYTICS")
    print(f"{Fore.CYAN}{'='*60}")
    
    # Create processor and run some tasks to generate data
    processor = RFTEnhancedTaskProcessor(model="o4-mini")
    processor.set_grader_config("general_programming")
    
    tasks = create_sample_tasks()[:2]
    workspace_path = "rft_analytics_workspace"
    os.makedirs(workspace_path, exist_ok=True)
    
    # Process tasks to generate improvement history
    for task in tasks:
        processor.process_task_with_rft(task, workspace_path)
    
    # Get analytics
    analytics = processor.get_performance_analytics()
    
    print(f"{Fore.GREEN}📊 Performance Analytics:")
    print(json.dumps(analytics, indent=2))
    
    # Save improvement history
    processor.save_improvement_history()
    print(f"{Fore.BLUE}💾 Improvement history saved")
    
    return analytics

def demonstrate_rft_training_preparation():
    """Demonstrate preparation of RFT training data."""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🎓 DEMONSTRATING RFT TRAINING DATA PREPARATION")
    print(f"{Fore.CYAN}{'='*60}")
    
    # Note: This is a simulation since we need API keys for actual training
    processor = RFTEnhancedTaskProcessor(model="o4-mini")
    processor.set_grader_config("general_programming")
    
    # Export high-quality training data (if any exists)
    try:
        output_file = "rft_demo_export.jsonl"
        exported_file = processor.export_training_dataset(output_file, min_score=0.8)
        print(f"{Fore.GREEN}📤 Exported training data to: {exported_file}")
        
        # Show sample of exported data
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    sample = json.loads(lines[0])
                    print(f"{Fore.YELLOW}📋 Sample exported data:")
                    print(json.dumps(sample, indent=2))
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ No training data available yet: {e}")

def main():
    """Main demonstration function."""
    
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🎯 REINFORCEMENT FINE-TUNING (RFT) DEMONSTRATION")
    print(f"{Fore.MAGENTA}   Autonomous Coding Environment Enhancement")
    print(f"{Fore.MAGENTA}{'='*80}")
    
    try:
        # 1. Basic grading demonstration
        rft_grader = demonstrate_basic_rft_grading()
        
        # 2. Enhanced task processing
        processor, processed_tasks = demonstrate_rft_enhanced_processing()
        
        # 3. Batch processing
        batch_processor = demonstrate_batch_processing()
        
        # 4. Performance analytics
        analytics = demonstrate_performance_analytics()
        
        # 5. Training data preparation
        demonstrate_rft_training_preparation()
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}✅ RFT DEMONSTRATION COMPLETED SUCCESSFULLY")
        print(f"{Fore.GREEN}{'='*60}")
        
        print(f"\n{Fore.CYAN}🎯 Key Features Demonstrated:")
        print(f"{Fore.CYAN}   • Advanced code grading with multiple criteria")
        print(f"{Fore.CYAN}   • Automatic task improvement through iteration")
        print(f"{Fore.CYAN}   • Batch processing with performance evaluation")
        print(f"{Fore.CYAN}   • Performance analytics and trend tracking")
        print(f"{Fore.CYAN}   • RFT training data preparation")
        
        print(f"\n{Fore.YELLOW}🚀 Next Steps:")
        print(f"{Fore.YELLOW}   • Set OPENAI_API_KEY environment variable")
        print(f"{Fore.YELLOW}   • Set AUTO_RFT_TRAINING=true to enable automatic training")
        print(f"{Fore.YELLOW}   • Run more tasks to generate training data")
        print(f"{Fore.YELLOW}   • Monitor RFT job status and update models")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)

if __name__ == "__main__":
    main() 