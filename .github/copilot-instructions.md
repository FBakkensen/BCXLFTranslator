<!-- Use this file to provide workspace-specific custom instructions to Copilot. -->

# Development Guidelines

## Test-Driven Development Principles

1. **Red-Green-Refactor Cycle**:
   - Write failing tests first (Red)
   - Write minimal code to make tests pass (Green)
   - Refactor while keeping tests passing (Refactor)

2. **Test Requirements**:
   - Every new feature must have corresponding test(s) before implementation
   - Tests should be focused and test one thing at a time
   - Use descriptive test names that explain the behavior being tested

3. **Testing Process**:
   - Write test(s) first and run them to see them fail
   - Implement the minimal code necessary to make tests pass
   - Run the full test suite to ensure no regressions
   - Only then proceed with refactoring if needed

4. **Code Organization**:
   - Keep test files close to the code they test
   - Follow test file naming convention: `test_*.py`
   - Group related tests together in test classes or modules

5. **Testing Best Practices**:
   - Use pytest fixtures for test setup and cleanup
   - Keep tests independent and isolated
   - Mock external dependencies appropriately
   - Include both happy path and error cases
   - Test edge cases and boundary conditions
6. **Documentation**:
   - Document each test case using the Behavior-Driven Development (BDD) style like this.
     ```python
     def test_function_name():
         """
         Given a specific input
         When the function is called
         Then it should return the expected output
         """
     ```

## Python Zen Principles

1. **Code Clarity and Aesthetics**:
   - Beautiful is better than ugly
   - Readability counts
   - Explicit is better than implicit

2. **Code Simplicity**:
   - Simple is better than complex
   - Complex is better than complicated
   - Flat is better than nested
   - Sparse is better than dense

3. **Code Design**:
   - There should be one-- and preferably only one --obvious way to do it
   - Special cases aren't special enough to break the rules
   - Although practicality beats purity
   - Namespaces are one honking great idea -- let's do more of those!

4. **Error Handling**:
   - Errors should never pass silently
   - Unless explicitly silenced
   - In the face of ambiguity, refuse the temptation to guess

5. **Implementation Timing**:
   - Now is better than never
   - Although never is often better than right now
   - If the implementation is hard to explain, it's a bad idea
   - If the implementation is easy to explain, it may be a good idea

## Implementation Guidelines

1. **Code Development**:
   - Never implement hardcoded solutions that directly return expected test values
   - Develop proper algorithms that work for all cases, not just test cases
   - Implement the simplest solution that works for the general case
   - Function implementation should be independent of test data

2. **Verification**:
   - Always run the full test suite before committing changes
   - Ensure all tests pass before considering work complete
   - Review test coverage for new code
   - Document any test-specific setup or requirements

Remember: Red -> Green -> Refactor, and never implement features without tests or with hardcoded solutions!
