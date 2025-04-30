# Test-Driven Development Principles

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