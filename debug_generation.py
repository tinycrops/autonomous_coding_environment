#!/usr/bin/env python3
"""Debug script to see what code is being generated."""

import tempfile
import subprocess
import os
from base_task_processor import BaseTaskProcessor, Task

def debug_code_generation():
    print("🔍 Debugging code generation...")
    
    processor = BaseTaskProcessor()
    
    # Create a simple task
    task = Task(
        id="debug_task",
        description="Create a simple function that adds two numbers"
    )
    
    print(f"📝 Task: {task.description}")
    
    # Generate code
    code = processor.generate_code_for_task(task)
    
    print(f"\n📄 Generated code:")
    print("=" * 50)
    print(code)
    print("=" * 50)
    
    # Test if the code is valid Python
    try:
        compile(code, "test", "exec")
        print("✅ Code compiles successfully")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return
    
    # Test execution by writing to a temporary file and running it
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute the file
        result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Code executes successfully")
            if result.stdout:
                print(f"📤 Output:\n{result.stdout}")
        else:
            print(f"❌ Execution failed with return code {result.returncode}")
            if result.stderr:
                print(f"📤 Error:\n{result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("❌ Execution timed out")
    except Exception as e:
        print(f"❌ Execution error: {e}")
    finally:
        # Clean up
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.unlink(temp_file)

if __name__ == "__main__":
    debug_code_generation() 