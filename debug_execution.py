#!/usr/bin/env python3
"""Debug script to test task execution."""

import os
import tempfile
from base_task_processor import BaseTaskProcessor, Task

def debug_task_execution():
    print("🔍 Debugging task execution...")
    
    processor = BaseTaskProcessor()
    
    # Create a simple task
    task = Task(
        id="debug_task",
        description="Create a simple function that adds two numbers"
    )
    
    # Generate code
    task.code = processor.generate_code_for_task(task)
    print(f"📝 Generated code length: {len(task.code)} characters")
    
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_workspace:
        print(f"📁 Workspace: {temp_workspace}")
        
        # Test execution
        result = processor.execute_task_code(task, temp_workspace)
        
        print(f"📊 Execution result:")
        print(f"  - Success: {result['success']}")
        print(f"  - Return code: {result.get('return_code', 'N/A')}")
        print(f"  - Error: {result.get('error', 'None')}")
        if result.get('output'):
            print(f"  - Output: {result['output'][:200]}...")

if __name__ == "__main__":
    debug_task_execution() 