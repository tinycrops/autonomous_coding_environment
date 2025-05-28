import unittest
import tempfile
import os
import ast
import subprocess
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import openai
from colorama import Fore
import logging
from base_task_processor import Task, BaseTaskProcessor

client = openai.OpenAI()

class TestCase(BaseModel):
    name: str
    description: str
    test_code: str
    expected_result: Optional[str] = None
    test_type: str = "unit"  # unit, integration, functional

class TestSuite(BaseModel):
    task_id: str
    test_cases: List[TestCase] = Field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""

class TestCaseData(BaseModel):
    """Structured test case data for generation response."""
    name: str
    description: str
    test_code: str
    expected_result: Optional[str] = None
    test_type: str = "unit"

class TestGenerationResponse(BaseModel):
    test_cases: List[TestCaseData] = Field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""
    testing_strategy: str

class TestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    output: str = ""

class ACETestFramework:
    """Testing framework for the Autonomous Coding Environment."""
    
    def __init__(self, model: str = "o4-mini"):
        self.model = model
        self.logger = logging.getLogger(__name__)
        
    def generate_tests_for_task(self, task: Task) -> TestSuite:
        """Generate comprehensive tests for a given task."""
        system_message = """
        You are an expert software testing engineer. Generate comprehensive unit tests for the given task and code.
        
        Create tests that cover:
        1. Normal operation cases
        2. Edge cases and boundary conditions
        3. Error handling scenarios
        4. Input validation
        
        Generate Python unittest test cases that can verify the code works correctly.
        Include setup and teardown code if needed.
        """
        
        user_message = f"""
        Task: {task.description}
        
        Code to test:
        {task.code}
        
        Generate comprehensive test cases including:
        - Unit tests for main functionality
        - Edge case testing
        - Error handling verification
        - Input validation tests
        
        Provide the tests in a structured format with test cases, setup, and teardown code.
        """
        
        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=TestGenerationResponse,
            )
            
            test_response = response.choices[0].message.parsed
            test_cases = []
            
            for test_data in test_response.test_cases:
                test_case = TestCase(
                    name=test_data.name,
                    description=test_data.description,
                    test_code=test_data.test_code,
                    expected_result=test_data.expected_result,
                    test_type=test_data.test_type
                )
                test_cases.append(test_case)
            
            test_suite = TestSuite(
                task_id=task.id,
                test_cases=test_cases,
                setup_code=test_response.setup_code,
                teardown_code=test_response.teardown_code
            )
            
            self.logger.info(f"{Fore.GREEN}✅ Generated {len(test_cases)} tests for task {task.id}")
            return test_suite
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}❌ Error generating tests: {str(e)}")
            # Return empty test suite
            return TestSuite(task_id=task.id)
    
    def create_test_file(self, task: Task, test_suite: TestSuite) -> str:
        """Create a complete test file for the task."""
        test_file_content = f'''#!/usr/bin/env python3
"""
Generated tests for task: {task.id}
Description: {task.description}
"""

import unittest
import sys
import os
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

# Add the task code inline for testing
TASK_CODE = """{task.code}"""

# Execute the task code to make functions available
exec(TASK_CODE)

class Test{task.id.replace("_", "").title()}(unittest.TestCase):
    """Test suite for {task.id}"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        {test_suite.setup_code if test_suite.setup_code else "pass"}
    
    def tearDown(self):
        """Clean up after each test method."""
        {test_suite.teardown_code if test_suite.teardown_code else "pass"}

'''
        
        # Add individual test methods
        for test_case in test_suite.test_cases:
            test_method = f'''
    def {test_case.name}(self):
        """
        {test_case.description}
        Test type: {test_case.test_type}
        """
        {test_case.test_code}
'''
            test_file_content += test_method
        
        # Add test runner
        test_file_content += '''

if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
'''
        
        return test_file_content
    
    def run_tests_for_task(self, task: Task, test_suite: TestSuite, workspace_path: str) -> List[TestResult]:
        """Run the generated tests for a task."""
        test_file_content = self.create_test_file(task, test_suite)
        test_filename = os.path.join(workspace_path, f"test_{task.id}.py")
        
        try:
            # Write test file
            with open(test_filename, 'w', encoding='utf-8') as f:
                f.write(test_file_content)
            
            # Run tests
            self.logger.info(f"{Fore.BLUE}🧪 Running tests for task {task.id}")
            result = subprocess.run(
                ['python', '-m', 'unittest', f'test_{task.id}', '-v'],
                capture_output=True,
                text=True,
                cwd=workspace_path,
                timeout=60
            )
            
            # Parse test results
            test_results = self._parse_test_output(result.stdout, result.stderr, test_suite.test_cases)
            
            success_count = len([r for r in test_results if r.passed])
            total_count = len(test_results)
            
            if success_count == total_count:
                self.logger.info(f"{Fore.GREEN}✅ All {total_count} tests passed for task {task.id}")
            else:
                self.logger.warning(f"{Fore.YELLOW}⚠️ {success_count}/{total_count} tests passed for task {task.id}")
            
            return test_results
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"{Fore.YELLOW}⏳ Tests timed out for task {task.id}")
            return [TestResult(
                test_name="timeout",
                passed=False,
                error_message="Test execution timed out"
            )]
        except Exception as e:
            self.logger.error(f"{Fore.RED}❌ Error running tests: {str(e)}")
            return [TestResult(
                test_name="error",
                passed=False,
                error_message=str(e)
            )]
        finally:
            # Clean up test file
            try:
                if os.path.exists(test_filename):
                    os.remove(test_filename)
            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}⚠️ Failed to clean up test file: {str(e)}")
    
    def _parse_test_output(self, stdout: str, stderr: str, test_cases: List[TestCase]) -> List[TestResult]:
        """Parse unittest output to extract test results."""
        results = []
        
        # Simple parsing - could be enhanced with more sophisticated parsing
        lines = stdout.split('\n') + stderr.split('\n')
        
        for test_case in test_cases:
            # Look for test results in output
            passed = True
            error_message = None
            
            for line in lines:
                if test_case.name in line:
                    if 'FAIL' in line or 'ERROR' in line:
                        passed = False
                        error_message = line
                        break
                    elif 'ok' in line.lower():
                        passed = True
                        break
            
            # If no specific result found, check overall status
            if error_message is None and ('FAILED' in stderr or 'ERROR' in stderr):
                # Check if this specific test is mentioned in errors
                for line in lines:
                    if test_case.name in line and ('FAIL' in line or 'ERROR' in line):
                        passed = False
                        error_message = line
                        break
            
            results.append(TestResult(
                test_name=test_case.name,
                passed=passed,
                error_message=error_message,
                output=stdout[:500] if stdout else ""  # Truncate output
            ))
        
        return results
    
    def generate_test_report(self, task: Task, test_results: List[TestResult]) -> str:
        """Generate a formatted test report."""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.passed])
        failed_tests = total_tests - passed_tests
        
        report = f"""
# Test Report for Task: {task.id}

**Task Description:** {task.description}
**Total Tests:** {total_tests}
**Passed:** {passed_tests}
**Failed:** {failed_tests}
**Success Rate:** {(passed_tests/total_tests*100):.1f}% if {total_tests > 0} else 0%

## Test Results:

"""
        
        for result in test_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report += f"- **{result.test_name}:** {status}\n"
            if result.error_message:
                report += f"  - Error: {result.error_message}\n"
        
        if failed_tests > 0:
            report += "\n## Failed Test Details:\n"
            for result in test_results:
                if not result.passed:
                    report += f"\n### {result.test_name}\n"
                    report += f"Error: {result.error_message}\n"
                    if result.output:
                        report += f"Output: {result.output[:200]}...\n"
        
        return report

class TaskValidator:
    """Validates task implementations using static analysis and testing."""
    
    def __init__(self, test_framework: ACETestFramework):
        self.test_framework = test_framework
        self.logger = logging.getLogger(__name__)
    
    def validate_task_code(self, task: Task) -> Dict[str, Any]:
        """Perform static analysis on task code."""
        validation_results = {
            "syntax_valid": False,
            "has_main_function": False,
            "has_docstrings": False,
            "has_error_handling": False,
            "complexity_score": 0,
            "issues": []
        }
        
        try:
            # Parse the code into an AST
            tree = ast.parse(task.code)
            validation_results["syntax_valid"] = True
            
            # Analyze the AST
            for node in ast.walk(tree):
                # Check for main function
                if isinstance(node, ast.FunctionDef) and node.name == 'main':
                    validation_results["has_main_function"] = True
                
                # Check for docstrings
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and 
                        isinstance(node.body[0].value.value, str)):
                        validation_results["has_docstrings"] = True
                
                # Check for error handling
                if isinstance(node, (ast.Try, ast.ExceptHandler)):
                    validation_results["has_error_handling"] = True
            
            # Calculate complexity (simple metric based on control flow)
            complexity = sum(1 for node in ast.walk(tree) 
                           if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)))
            validation_results["complexity_score"] = complexity
            
            self.logger.info(f"{Fore.GREEN}✅ Static analysis completed for task {task.id}")
            
        except SyntaxError as e:
            validation_results["issues"].append(f"Syntax Error: {str(e)}")
            self.logger.error(f"{Fore.RED}❌ Syntax error in task {task.id}: {str(e)}")
        except Exception as e:
            validation_results["issues"].append(f"Analysis Error: {str(e)}")
            self.logger.error(f"{Fore.RED}❌ Error analyzing task {task.id}: {str(e)}")
        
        return validation_results
    
    def full_task_validation(self, task: Task, workspace_path: str) -> Dict[str, Any]:
        """Perform complete validation including static analysis and testing."""
        validation_report = {
            "task_id": task.id,
            "static_analysis": self.validate_task_code(task),
            "test_results": [],
            "overall_quality": "unknown"
        }
        
        # Generate and run tests
        test_suite = self.test_framework.generate_tests_for_task(task)
        if test_suite.test_cases:
            test_results = self.test_framework.run_tests_for_task(task, test_suite, workspace_path)
            validation_report["test_results"] = [result.model_dump() for result in test_results]
            
            # Calculate overall quality
            static_score = self._calculate_static_score(validation_report["static_analysis"])
            test_score = len([r for r in test_results if r.passed]) / len(test_results) if test_results else 0
            
            overall_score = (static_score + test_score) / 2
            
            if overall_score >= 0.8:
                validation_report["overall_quality"] = "excellent"
            elif overall_score >= 0.6:
                validation_report["overall_quality"] = "good"
            elif overall_score >= 0.4:
                validation_report["overall_quality"] = "fair"
            else:
                validation_report["overall_quality"] = "poor"
        
        return validation_report
    
    def _calculate_static_score(self, static_analysis: Dict[str, Any]) -> float:
        """Calculate a quality score from static analysis results."""
        score = 0.0
        
        if static_analysis["syntax_valid"]:
            score += 0.3
        if static_analysis["has_main_function"]:
            score += 0.2
        if static_analysis["has_docstrings"]:
            score += 0.2
        if static_analysis["has_error_handling"]:
            score += 0.2
        if len(static_analysis["issues"]) == 0:
            score += 0.1
        
        return score 