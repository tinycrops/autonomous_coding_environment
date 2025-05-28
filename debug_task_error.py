#!/usr/bin/env python3
"""Debug script to see what's causing the task execution errors."""

import os
import tempfile
from base_task_processor import BaseTaskProcessor, Task

def debug_task_error():
    print("🔍 Debugging task execution errors...")
    
    processor = BaseTaskProcessor()
    
    # Create a task similar to what the system generates
    task = Task(
        id="debug_task",
        description="Implement the core `square(x)` function that returns the square of input `x` (i.e., `x * x`)."
    )
    
    # Generate code
    task.code = processor.generate_code_for_task(task)
    print(f"📝 Generated code:")
    print("=" * 50)
    print(task.code)
    print("=" * 50)
    
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_workspace:
        print(f"📁 Workspace: {temp_workspace}")
        
        # Test execution with detailed error capture
        result = processor.execute_task_code(task, temp_workspace)
        
        print(f"📊 Detailed execution result:")
        print(f"  - Success: {result['success']}")
        print(f"  - Return code: {result.get('return_code', 'N/A')}")
        print(f"  - STDOUT: {repr(result.get('output', ''))}")
        print(f"  - STDERR: {repr(result.get('error', ''))}")
        
        # Also try to manually run the file to see what happens
        task_file = os.path.join(temp_workspace, f"{task.id}.py")
        print(f"\n🔧 Manual file check:")
        print(f"  - File exists: {os.path.exists(task_file)}")
        if os.path.exists(task_file):
            with open(task_file, 'r') as f:
                content = f.read()
            print(f"  - File size: {len(content)} chars")
            print(f"  - First 100 chars: {repr(content[:100])}")

if __name__ == "__main__":
    debug_task_error() 