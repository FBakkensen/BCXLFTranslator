# Business Central Terminology Integration - Step-by-Step TDD Implementation

This document provides a detailed breakdown of each feature into smaller, testable steps following Test-Driven Development principles. Each step includes a specific Copilot prompt designed to facilitate implementation.

## Feature 1: XLIFF Terminology Parser

### Step 1.1: Basic XLIFF File Loading
**Goal**: Create a function to load and validate an XLIFF file.

**Copilot Prompt**:
```
Implement a function to load and validate an XLIFF file following TDD principles.

Requirements:
- Create a function that takes an XLIFF file path as input
- Load the file using appropriate XML parsing
- Verify it's a valid XLIFF file with expected structure
- Return the parsed XML document object
- Raise appropriate exceptions for invalid files

Write these tests first:
1. Test loading a valid XLIFF file
2. Test behavior with non-existent file path
3. Test behavior with a file that isn't valid XLIFF
4. Test behavior with an empty file
5. Test behavior with a file that has XML syntax errors

Follow the Red-Green-Refactor cycle:
1. Write failing tests first that verify the expected behavior
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use pytest fixtures for test file setup.
Don't use hardcoded solutions that directly return expected test values.
```

### Step 1.2: Trans-Unit Extraction
**Goal**: Create a function to extract all trans-unit elements from an XLIFF document.

**Copilot Prompt**:
```
Implement a function to extract trans-unit elements from an XLIFF document following TDD principles.

Requirements:
- Function should take a parsed XLIFF document object as input
- Extract all trans-unit elements with their source and target texts
- Handle different XLIFF structure variations
- Return a list of dictionaries with {id, source_text, target_text} for each trans-unit

Write these tests first:
1. Test extracting trans-units from a simple XLIFF document
2. Test handling empty trans-units (no source/target)
3. Test handling trans-units with source but no target
4. Test handling different XLIFF namespaces
5. Test extraction from nested structure variations

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use pytest fixtures with sample XLIFF content for testing.
Make sure to use proper XML namespace handling.
```

### Step 1.3: Object Type Identification
**Goal**: Identify object types (Table, Page, Field, etc.) from trans-unit elements.

**Copilot Prompt**:
```
Implement a function to identify Business Central object types from trans-unit elements following TDD principles.

Requirements:
- Function should take a trans-unit dictionary with id, source_text, target_text
- Analyze the id and other attributes to identify BC object type (Table, Page, Field)
- Extract context information if available
- Return the original dictionary enriched with {object_type, context} fields

Write these tests first:
1. Test identifying Table objects from typical Business Central XLIFF patterns
2. Test identifying Page objects
3. Test identifying Field objects
4. Test extracting context from notes or other attributes
5. Test handling trans-units with no recognizable object type
6. Test handling various BC-specific ID patterns

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use realistic Business Central XLIFF patterns in test fixtures.
Include both positive and negative test cases.
```

### Step 1.4: Terminology Candidate Filtering
**Goal**: Filter trans-units to identify terminology candidates based on criteria.

**Copilot Prompt**:
```
Implement a function to filter for terminology candidates from trans-units following TDD principles.

Requirements:
- Function should take a list of enriched trans-unit dictionaries
- Apply filtering rules to identify good terminology candidates:
  * High-priority elements (Tables, Fields, Pages)
  * Business-specific terms
  * Common UI terms
- Return filtered list of terminology candidate dictionaries

Write these tests first:
1. Test filtering for Table/Page/Field object types
2. Test handling terms with business-specific indicators
3. Test filtering out common words that aren't terminology candidates
4. Test handling edge cases (very short terms, numbers only, etc.)
5. Test prioritization of different object types

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Include a mix of good and bad terminology candidates in test fixtures.
Test both inclusion and exclusion criteria.
```

### Step 1.5: Complete Parser Integration
**Goal**: Integrate all previous steps into a complete terminology parser.

**Copilot Prompt**:
```
Implement the complete XLIFF terminology parser by integrating the previous components following TDD principles.

Requirements:
- Create a main parsing function that takes a file path and optional parameters
- Integrate file loading, trans-unit extraction, object type identification, and filtering
- Return a final list of terminology entries as {source_term, target_term, context, object_type}
- Add logging for parsing process
- Handle errors gracefully with appropriate exceptions

Write these tests first:
1. Test the complete parsing flow with a simple XLIFF file
2. Test parsing with filtering options
3. Test integration of all components
4. Test error propagation from any component
5. Test with complex, realistic Business Central XLIFF file
6. Test performance with larger files

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use comprehensive test fixtures that test the entire parsing flow.
Test both happy path and error conditions.
Ensure proper test isolation using pytest fixtures.
```

## Feature 2: Terminology Database Model

### Step 2.1: Database Schema Creation
**Goal**: Create the SQLite database schema for terminology storage.

**Copilot Prompt**:
```
Implement a function to create the SQLite database schema for terminology storage following TDD principles.

Requirements:
- Create a function that initializes a new SQLite database with required schema
- Implement Terms table with: id, source_term, target_term, context, object_type, language
- Implement Metadata table with: id, source_file, version, language_pair, import_date
- Add appropriate indexes for term lookup optimization
- Handle database creation and schema upgrades

Write these tests first:
1. Test database creation with specified path
2. Test schema validation (tables, columns, indexes exist)
3. Test handling of existing database files
4. Test schema version tracking
5. Test handling database connection errors

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use in-memory SQLite for testing to avoid file dependencies.
Test schema correctness by querying sqlite_master.
```

### Step 2.2: Term Entry Functions
**Goal**: Implement functions to add and retrieve individual terminology entries.

**Copilot Prompt**:
```
Implement functions to add and retrieve terminology entries from the database following TDD principles.

Requirements:
- Function to add a single terminology entry
- Function to retrieve a single entry by source_term and language
- Function to check if a term exists
- Function to update an existing entry
- Proper parameter validation and error handling

Write these tests first:
1. Test adding a new terminology entry
2. Test retrieving an entry by source_term and language
3. Test checking for term existence
4. Test updating an existing entry
5. Test handling duplicate entries
6. Test parameter validation and error cases

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use pytest fixtures for database setup and teardown.
Test with various term attributes and edge cases.
```

### Step 2.3: Bulk Import and Metadata Functions
**Goal**: Implement bulk terminology import and metadata management.

**Copilot Prompt**:
```
Implement functions for bulk terminology import and metadata management following TDD principles.

Requirements:
- Function to bulk import a list of terminology entries
- Function to store metadata about the import (source file, version, etc.)
- Function to retrieve metadata for a language pair
- Transaction handling for bulk operations
- Performance optimization for large imports

Write these tests first:
1. Test bulk import of multiple terminology entries
2. Test transaction rollback on partial failures
3. Test storing metadata for an import operation
4. Test retrieving metadata by language pair
5. Test bulk import performance with large datasets
6. Test handling duplicate entries during bulk import

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use larger test datasets to verify bulk operation performance.
Test both successful operations and error handling scenarios.
```

### Step 2.4: Term Lookup and Querying
**Goal**: Implement advanced term lookup and querying functions.

**Copilot Prompt**:
```
Implement advanced term lookup and querying functions following TDD principles.

Requirements:
- Function to look up terms with filtering options
- Function to retrieve terms by object type
- Function to search for terms using pattern matching
- Support for pagination for large result sets
- Optimized query construction for performance

Write these tests first:
1. Test lookup with various filter combinations
2. Test retrieving terms by object type
3. Test pattern matching searches
4. Test pagination of results
5. Test query performance with large datasets
6. Test edge cases (no results, maximum results)

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test query performance with appropriately sized datasets.
Verify correct SQL query construction through results.
```

### Step 2.5: Database Class Integration
**Goal**: Create a complete database management class integrating all functions.

**Copilot Prompt**:
```
Implement a complete TerminologyDatabase class integrating all database functions following TDD principles.

Requirements:
- Create a class that encapsulates all database operations
- Constructor should handle database initialization/connection
- Include methods for all previously implemented functions
- Add context manager support for easy connection handling
- Implement proper resource cleanup

Write these tests first:
1. Test class instantiation with different parameters
2. Test context manager functionality
3. Test integration of all database operations
4. Test proper cleanup on close/destruction
5. Test connection state management
6. Test error handling throughout the class

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test the complete class API for consistency and correctness.
Verify resource cleanup to prevent connection leaks.
```

## Feature 3: In-Memory Terminology Dictionary

### Step 3.1: Basic In-Memory Dictionary Structure
**Goal**: Create the basic in-memory dictionary structure for fast terminology lookup.

**Copilot Prompt**:
```
Implement the basic in-memory dictionary structure for terminology following TDD principles.

Requirements:
- Create a class that will hold terminology in memory
- Define the internal data structure optimized for lookup speed
- Implement the basic loading mechanism (without database integration yet)
- Support case-insensitive lookups while preserving original case
- Include basic initialization and stats methods

Write these tests first:
1. Test class initialization with basic parameters
2. Test adding entries to the in-memory structure
3. Test simple lookups from the structure
4. Test case-insensitive matching
5. Test basic statistics about loaded terms
6. Test memory usage with various dataset sizes

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Focus on the data structure design for efficient lookups.
Test with various term types and sizes.
```

### Step 3.2: Database Loading Integration
**Goal**: Implement database loading into the in-memory dictionary.

**Copilot Prompt**:
```
Implement database loading functionality for the in-memory terminology dictionary following TDD principles.

Requirements:
- Create a method to load terminology from a TerminologyDatabase
- Support filtering by language pair during loading
- Optimize loading performance for large datasets
- Track load statistics and timing
- Handle database connection issues

Write these tests first:
1. Test loading from a mock database interface
2. Test filtering by language pair
3. Test loading performance with large datasets
4. Test handling database errors during load
5. Test partial loading and validation
6. Test load statistics accuracy

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use mocking to test database interactions.
Test performance characteristics with realistic data volumes.
```

### Step 3.3: Advanced Lookup Features
**Goal**: Implement advanced lookup features for the in-memory dictionary.

**Copilot Prompt**:
```
Implement advanced lookup features for the in-memory terminology dictionary following TDD principles.

Requirements:
- Add context-aware lookup methods
- Implement exact and partial matching options
- Support for lookup by object type
- Add performance metrics for lookups
- Optimize for high-throughput scenarios

Write these tests first:
1. Test context-aware term lookups
2. Test exact vs. partial matching scenarios
3. Test lookup by object type filtering
4. Test lookup performance under high throughput
5. Test edge cases (no matches, multiple matches)
6. Test metric collection during lookups

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test lookup accuracy with ambiguous terms.
Include performance benchmarking for lookup operations.
```

### Step 3.4: Memory Optimization
**Goal**: Implement memory optimization techniques for the in-memory dictionary.

**Copilot Prompt**:
```
Implement memory optimization techniques for the in-memory terminology dictionary following TDD principles.

Requirements:
- Analyze and optimize memory usage patterns
- Implement smart loading strategies (lazy loading, partial loading)
- Add memory usage monitoring and reporting
- Create methods to trim/optimize the dictionary
- Balance memory usage vs. lookup performance

Write these tests first:
1. Test memory usage with various dataset sizes
2. Test lazy loading implementation
3. Test memory optimization methods
4. Test performance impact of optimizations
5. Test memory usage reporting accuracy

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Use realistic data volumes for memory testing.
Compare different optimization strategies in tests.
```

### Step 3.5: Complete Dictionary Class
**Goal**: Finalize the in-memory terminology dictionary with comprehensive functionality.

**Copilot Prompt**:
```
Implement the complete in-memory terminology dictionary class with comprehensive functionality following TDD principles.

Requirements:
- Integrate all previously implemented features
- Add refresh/reload capabilities
- Implement thread safety for concurrent access
- Add comprehensive statistics and reporting
- Include serialization/deserialization support for fast startup

Write these tests first:
1. Test the complete API integration
2. Test refresh and reload functionality
3. Test thread safety with concurrent lookups
4. Test comprehensive statistics collection
5. Test serialization and deserialization
6. Test end-to-end usage scenarios

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test complete workflows from loading to lookup.
Ensure thread safety with concurrent test scenarios.
```

## Feature 4: Translation Process Integration

### Step 4.1: Translation Pipeline Analysis
**Goal**: Analyze the existing translation pipeline and design integration points.

**Copilot Prompt**:
```
Analyze the existing translation pipeline and design terminology integration points following TDD principles.

Requirements:
- Create functions to analyze the current translation pipeline flow
- Identify integration points for terminology lookup
- Design a non-intrusive way to extend the pipeline
- Create test harnesses to verify behavior before/after changes
- Document the integration approach

Write these tests first:
1. Test identifying key pipeline stages
2. Test intercepting translation requests
3. Test mocking terminology lookups in the pipeline
4. Test maintaining existing behavior with no terminology matches
5. Test the design with simple examples

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Focus on understanding the existing pipeline through tests.
Use mocking to explore behavior without making changes.
```

### Step 4.2: Terminology Lookup Integration
**Goal**: Integrate terminology lookup into the translation process.

**Copilot Prompt**:
```
Implement terminology lookup integration into the translation process following TDD principles.

Requirements:
- Create a function to check terminology before translation
- Integrate with the existing translation pipeline
- Preserve the original behavior when no terminology match exists
- Handle different text cases and formats
- Track when terminology is used vs. fallback

Write these tests first:
1. Test finding terms in the terminology dictionary
2. Test falling back to existing translation when no match exists
3. Test handling case variations (uppercase, lowercase, title case)
4. Test with terminology available vs. not available
5. Test tracking of terminology usage
6. Test with realistic translation inputs

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Start with simple integration and expand to handle more complex cases.
Test behavior with and without terminology matches.
```

### Step 4.3: Translation Source Tracking
**Goal**: Implement tracking of translation sources (Microsoft vs. Google).

**Copilot Prompt**:
```
Implement translation source tracking (Microsoft Terminology vs. Google Translate) following TDD principles.

Requirements:
- Create a mechanism to track the source of each translation
- Extend the translation result to include source information
- Support tracking at both segment and word levels
- Preserve tracking through the entire pipeline
- Make source information available for later stages

Write these tests first:
1. Test tracking terminology-based translations
2. Test tracking Google-based translations
3. Test maintaining tracking info through the pipeline
4. Test mixed sources within a single translation
5. Test retrieving source information from results
6. Test with various translation scenarios

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Design a clean way to associate source info with translations.
Test preservation of source info throughout processing.
```

### Step 4.4: Post-Processing Integration
**Goal**: Ensure terminology integration works with existing post-processing.

**Copilot Prompt**:
```
Ensure terminology integration works properly with existing post-processing following TDD principles.

Requirements:
- Analyze existing post-processing steps (case matching, etc.)
- Modify post-processing to work with terminology translations
- Ensure terminology benefits from the same post-processing
- Maintain source tracking through post-processing
- Verify no regression in existing functionality

Write these tests first:
1. Test case matching with terminology-based translations
2. Test other post-processing with terminology translations
3. Test maintaining source information through post-processing
4. Test comparing results with and without terminology
5. Test with various text patterns requiring post-processing
6. Test for any regressions in existing functionality

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with existing post-processing test cases.
Verify no change in behavior for non-terminology translations.
```

### Step 4.5: Complete Translation Integration
**Goal**: Finalize the complete translation pipeline with terminology integration.

**Copilot Prompt**:
```
Implement the complete translation pipeline with terminology integration following TDD principles.

Requirements:
- Integrate all previous steps into the main translation flow
- Ensure proper order of operations (terminology check, Google fallback, post-processing)
- Add configuration options for enabling/disabling terminology
- Optimize the integrated pipeline for performance
- Ensure all tracking and statistics work end-to-end

Write these tests first:
1. Test the complete translation flow with terminology enabled
2. Test enabling/disabling terminology via configuration
3. Test end-to-end translation with mixed terminology sources
4. Test performance of the integrated pipeline
5. Test with realistic XLIFF translation scenarios
6. Test comprehensive statistics collection

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test end-to-end behavior with realistic data.
Verify performance remains acceptable after integration.
```

## Feature 5: Translation Attribution Annotation

### Step 5.1: Note Generation
**Goal**: Create functions to generate attribution notes based on translation source.

**Copilot Prompt**:
```
Implement functions to generate attribution notes for translations following TDD principles.

Requirements:
- Create a function that generates attribution notes based on translation source
- Support different note formats for Microsoft Terminology vs. Google Translate
- Include relevant metadata in the notes
- Ensure notes comply with XLIFF format requirements
- Handle edge cases (mixed sources, no source info)

Write these tests first:
1. Test generating Microsoft Terminology attribution notes
2. Test generating Google Translate attribution notes
3. Test generating notes for mixed-source translations
4. Test note format compliance with XLIFF standards
5. Test handling missing source information
6. Test with various metadata combinations

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with different note formats and content.
Ensure generated notes are well-formed XML.
```

### Step 5.2: XLIFF Note Integration
**Goal**: Implement functions to add notes to XLIFF trans-unit elements.

**Copilot Prompt**:
```
Implement functions to add attribution notes to XLIFF trans-units following TDD principles.

Requirements:
- Create a function to add a note to an XLIFF trans-unit element
- Handle existing notes (preserve or update)
- Ensure proper XML structure and namespaces
- Support different XLIFF versions
- Validate note addition correctness

Write these tests first:
1. Test adding a note to a trans-unit with no existing notes
2. Test adding a note to a trans-unit with existing notes
3. Test note preservation when updating
4. Test with different XLIFF versions and structures
5. Test XML correctness after note addition
6. Test failure handling for invalid inputs

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with various XLIFF structures.
Verify XML correctness after modifications.
```

### Step 5.3: Attribution Process Integration
**Goal**: Integrate attribution note generation into the translation process.

**Copilot Prompt**:
```
Integrate attribution note generation into the translation process following TDD principles.

Requirements:
- Add note generation to the translation pipeline
- Connect source tracking with note generation
- Ensure notes are added to the correct trans-units
- Preserve existing behavior for all other aspects
- Add configuration options for controlling attribution

Write these tests first:
1. Test end-to-end flow with attribution enabled
2. Test attribution with mixed translation sources
3. Test enabling/disabling attribution via config
4. Test attribution with different XLIFF structures
5. Test preserving other translation behavior
6. Test with realistic translation scenarios

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test the complete flow from translation to attribution.
Verify note content matches the actual translation sources.
```

### Step 5.4: Custom Attribution Formats
**Goal**: Support customizable attribution format templates.

**Copilot Prompt**:
```
Implement support for customizable attribution format templates following TDD principles.

Requirements:
- Create a templating system for attribution notes
- Support placeholders for source, date, and other metadata
- Allow configuration of different templates
- Provide default templates
- Validate template syntax

Write these tests first:
1. Test default templates for each source type
2. Test custom templates with various placeholders
3. Test template validation
4. Test applying templates with different data
5. Test template configuration options
6. Test invalid template handling

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test template rendering with various data combinations.
Verify configuration properly affects template selection.
```

### Step 5.5: Attribution Reporting
**Goal**: Add reporting of attribution statistics.

**Copilot Prompt**:
```
Implement attribution statistics reporting following TDD principles.

Requirements:
- Track statistics about attribution (counts by source)
- Create reporting functions for attribution stats
- Integrate with the existing statistics system
- Support console and file output formats
- Include attribution details in overall reports

Write these tests first:
1. Test tracking attribution statistics
2. Test attribution reporting in different formats
3. Test integration with overall statistics
4. Test reporting with various attribution scenarios
5. Test formatting and output options
6. Test with mixed translation sources

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Verify statistics accuracy with different source mixes.
Test integration with the broader statistics system.
```

## Feature 6: Translation Statistics Collection

### Step 6.1: Core Statistics Tracking
**Goal**: Implement core statistics tracking for terminology usage.

**Copilot Prompt**:
```
Implement core statistics tracking for terminology usage following TDD principles.

Requirements:
- Create a statistics class to track terminology usage
- Track counts of Microsoft vs. Google translations
- Support incremental statistic updates during translation
- Calculate derived statistics (percentages, ratios)
- Ensure thread safety for concurrent updates

Write these tests first:
1. Test initializing a statistics tracker with default values
2. Test incrementing Microsoft terminology usage counts and verifying the count increases
3. Test incrementing Google Translate counts and verifying the count increases
4. Test calculating percentage of Microsoft terminology usage vs. Google Translate
5. Test resetting statistics to initial state
6. Test thread safety by simulating concurrent updates to statistics

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test statistics accuracy with various count scenarios.
Verify thread safety with simulated concurrent updates.
```

### Step 6.2: Translation Process Integration
**Goal**: Integrate statistics collection into the translation process.

**Copilot Prompt**:
```
Integrate statistics collection into the translation process following TDD principles.

Requirements:
- Add statistics collection points in the translation pipeline
- Ensure statistics are updated for each translation source
- Support collecting statistics at different granularity levels
- Maintain cumulative statistics across multiple files
- Ensure no performance impact on the translation process

Write these tests first:
1. Test statistics are updated when a term is translated using Microsoft terminology
2. Test statistics are updated when a term is translated using Google Translate
3. Test statistics accumulate correctly across multiple translation units
4. Test statistics accumulate correctly when translating multiple files
5. Test collecting statistics at different granularity levels (term-level vs. file-level)
6. Test translation performance with and without statistics collection to verify minimal overhead

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with realistic translation scenarios.
Verify minimal performance overhead from statistics.
```

### Step 6.3: Detailed Statistics Collection
**Goal**: Implement detailed statistics with categorization and grouping.

**Copilot Prompt**:
```
Implement detailed statistics with categorization and grouping following TDD principles.

Requirements:
- Extend statistics to track by object type (Table, Page, Field)
- Support grouping statistics by context or file
- Implement hierarchical statistics aggregation
- Add filters for statistical analysis
- Support comparison between different statistic sets

Write these tests first:
1. Test collecting statistics broken down by object type (Table, Page, Field)
2. Test grouping statistics by context (e.g., Sales, Purchase, Inventory)
3. Test grouping statistics by source file or module
4. Test hierarchical aggregation (e.g., total stats, by file, by object type within file)
5. Test filtering statistics by criteria (e.g., only Tables, only specific context)
6. Test comparing statistics between two different translation runs

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with varied data to verify categorization works.
Verify aggregation produces correct rolled-up statistics.
```

### Step 6.4: Statistics Persistence
**Goal**: Implement statistics persistence between runs.

**Copilot Prompt**:
```
Implement statistics persistence between runs following TDD principles.

Requirements:
- Create functions to serialize statistics to disk
- Implement loading of statistics from previous runs
- Support merging statistics from multiple sources
- Add version tracking for statistics format
- Ensure backward compatibility

Write these tests first:
1. Test serializing statistics to JSON and saving to disk
2. Test loading statistics from a saved JSON file
3. Test merging statistics from a current run with previously saved statistics
4. Test handling older versions of statistics format (version compatibility)
5. Test proper error handling when loading corrupt or invalid statistics files
6. Test loading and saving large statistics datasets efficiently

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test persistence with realistic statistics data.
Verify proper handling of edge cases in stored data.
```

### Step 6.5: Complete Statistics System
**Goal**: Finalize the complete statistics collection system.

**Copilot Prompt**:
```
Implement the complete statistics collection system following TDD principles.

Requirements:
- Integrate all previous statistics components
- Create a unified statistics API
- Add configuration options for statistics collection
- Implement efficient updates and querying
- Ensure complete test coverage of features

Write these tests first:
1. Test the complete statistics API for consistency across all methods
2. Test enabling/disabling statistics collection via configuration options
3. Test adjusting statistics detail level via configuration
4. Test a complete translation workflow with integrated statistics collection
5. Test querying collected statistics through the API
6. Test performance with large datasets and complex aggregations

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test the complete statistics system with real-world scenarios.
Verify all components work together correctly.
```

## Feature 7: Statistics Report Generation

### Step 7.1: Basic Console Reporting
**Goal**: Implement basic statistics reporting to the console.

**Copilot Prompt**:
```
Implement basic statistics reporting to the console following TDD principles.

Requirements:
- Create a function to format statistics for console output
- Display summary statistics (counts, percentages)
- Format output for readability
- Support different detail levels
- Include timing and session information

Write these tests first:
1. Test formatting basic statistics summary (counts, percentages) for console output
2. Test displaying statistics with different levels of detail (summary vs. detailed)
3. Test formatting output with appropriate spacing and alignment
4. Test inclusion of timing information (duration, timestamps) in the report
5. Test handling empty or minimal statistics (edge cases)
6. Test output adapts to different terminal width constraints

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with mocked console to capture output.
Verify reporting accuracy with different statistics sets.
```

### Step 7.2: CSV Report Generation
**Goal**: Implement statistics export to CSV format.

**Copilot Prompt**:
```
Implement statistics export to CSV format following TDD principles.

Requirements:
- Create a function to export statistics to CSV
- Support different levels of detail
- Include headers and proper formatting
- Handle file output (path, overwrite options)
- Ensure compatibility with spreadsheet applications

Write these tests first:
1. Test generating CSV with correct headers for statistics data
2. Test CSV data rows match the statistics values accurately
3. Test proper escaping of special characters in CSV output
4. Test file writing with new file creation and overwrite options
5. Test handling file system errors (e.g., permission denied, disk full)
6. Test CSV output can be correctly parsed by standard CSV parsers

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test CSV formatting and structure.
Verify file handling works correctly.
```

### Step 7.3: JSON Report Generation
**Goal**: Implement statistics export to JSON format.

**Copilot Prompt**:
```
Implement statistics export to JSON format following TDD principles.

Requirements:
- Create a function to export statistics to JSON
- Support nested statistics structure
- Include metadata and context information
- Implement pretty-printing option
- Support streaming for large datasets

Write these tests first:
1. Test generating valid JSON from statistics data
2. Test JSON structure includes all relevant statistics fields
3. Test proper nesting of hierarchical statistics data
4. Test inclusion of metadata (timestamp, version, run info) in JSON
5. Test pretty-printed JSON is properly formatted with indentation
6. Test streaming large statistics datasets to JSON without memory issues

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test JSON validity and structure.
Verify large statistics sets are handled efficiently.
```

### Step 7.4: HTML Report Generation
**Goal**: Implement statistics export to HTML format with visualizations.

**Copilot Prompt**:
```
Implement statistics export to HTML format with visualizations following TDD principles.

Requirements:
- Create a function to generate HTML reports from statistics
- Include basic visualizations (charts, tables)
- Make reports self-contained (include CSS/JS)
- Support interactive elements for exploration
- Ensure cross-browser compatibility

Write these tests first:
1. Test generating valid HTML structure from statistics data
2. Test inclusion of CSS and JavaScript in the generated HTML
3. Test creation of data tables with correct statistics values
4. Test generation of chart visualization data for source percentages
5. Test self-contained nature (no external dependencies) of the report
6. Test HTML validity against W3C standards

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test HTML validity and structure.
Verify visualizations are correctly generated.
```

### Step 7.5: Unified Reporting System
**Goal**: Implement a unified reporting system for all formats.

**Copilot Prompt**:
```
Implement a unified statistics reporting system for all formats following TDD principles.

Requirements:
- Create a unified API for generating reports in any format
- Support configurable report generation
- Implement automatic format detection
- Include timestamp and session information
- Support batch generation of multiple report formats

Write these tests first:
1. Test generating reports in all supported formats through a unified API
2. Test report generation with different configuration options
3. Test automatic format detection based on file extension
4. Test consistent inclusion of timestamp and session information across formats
5. Test generating multiple report formats in a single operation
6. Test applying a consistent set of filters across different output formats

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test the complete reporting system.
Verify all formats work through the unified API.
```

## Feature 8: Command-line Interface for Terminology Extraction

### Step 8.1: Argument Parsing for Extraction
**Goal**: Implement argument parsing for terminology extraction command.

**Copilot Prompt**:
```
Implement argument parsing for terminology extraction command following TDD principles.

Requirements:
- Add --extract-terminology parameter
- Add --lang parameter for language specification
- Support optional parameters for extraction configuration
- Validate parameter combinations
- Show appropriate help messages

Write these tests first:
1. Test parsing the --extract-terminology parameter with a valid file path
2. Test parsing the --lang parameter with valid language codes
3. Test validation fails when required parameters are missing
4. Test parsing optional configuration parameters with valid values
5. Test help message contains information about terminology extraction
6. Test error messages when invalid parameter combinations are provided

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with various command-line argument combinations.
Verify error handling with invalid arguments.
```

### Step 8.2: Extraction Command Implementation
**Goal**: Implement the terminology extraction command functionality.

**Copilot Prompt**:
```
Implement the terminology extraction command functionality following TDD principles.

Requirements:
- Create a function to execute terminology extraction from the command line
- Parse the reference XLIFF file specified by the user
- Extract terminology using the parser
- Report on the extraction process
- Handle errors gracefully

Write these tests first:
1. Test extracting terminology from a valid reference XLIFF file
2. Test proper error message when specified file doesn't exist
3. Test handling malformed XLIFF files with appropriate error messages
4. Test extraction process reports correct counts of terms extracted
5. Test extraction with various filtering options
6. Test progress reporting during extraction of large files

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Mock file operations for testing.
Test both success and failure scenarios.
```

### Step 8.3: Database Storage Integration
**Goal**: Implement database storage of extracted terminology.

**Copilot Prompt**:
```
Implement database storage of extracted terminology from CLI following TDD principles.

Requirements:
- Connect extraction command to the terminology database
- Store extracted terms with proper metadata
- Handle database errors gracefully
- Report on storage results
- Support update/merge options for existing databases

Write these tests first:
1. Test storing extracted terminology entries in the database
2. Test updating existing terminology entries with new translations
3. Test skipping existing entries based on configuration option
4. Test storing metadata about the extraction source and process
5. Test graceful handling of database connection errors
6. Test reporting correct counts of added/updated/skipped terms

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Mock the database for command testing.
Test with various database states and conditions.
```

### Step 8.4: Extraction Results Reporting
**Goal**: Implement detailed reporting of terminology extraction results.

**Copilot Prompt**:
```
Implement detailed reporting of terminology extraction results following TDD principles.

Requirements:
- Create functions to report on extraction results
- Show statistics about extracted terminology
- Include information about database storage
- Support different output formats (console, file)
- Provide detailed logs for troubleshooting

Write these tests first:
1. Test reporting summary statistics about extracted terminology
2. Test detailed reporting with term-by-term information
3. Test reporting database storage results (added, updated, skipped)
4. Test generating reports in different output formats (text, CSV)
5. Test detailed logging for troubleshooting extraction issues
6. Test including error and warning counts in the extraction report

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test report formatting and content.
Verify statistics accuracy in reports.
```

### Step 8.5: Complete Extraction Command
**Goal**: Finalize the complete terminology extraction command.

**Copilot Prompt**:
```
Implement the complete terminology extraction command following TDD principles.

Requirements:
- Integrate all extraction components (parsing, storage, reporting)
- Add advanced options (filters, overwrite behavior)
- Implement proper exit codes for automation
- Add verbose/quiet modes
- Ensure complete error handling and user feedback

Write these tests first:
1. Test end-to-end extraction workflow from file parsing to database storage
2. Test applying filters to include/exclude certain terminology types
3. Test different overwrite behaviors (skip, replace, merge)
4. Test exit codes for success, warnings, and various error conditions
5. Test verbose mode provides detailed output and quiet mode suppresses output
6. Test comprehensive error handling with different failure scenarios

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test end-to-end command functionality.
Verify proper behavior in various usage scenarios.
```

## Feature 9: Command-line Interface for Using Terminology

### Step 9.1: Argument Parsing for Terminology Usage
**Goal**: Implement argument parsing for terminology usage.

**Copilot Prompt**:
```
Implement argument parsing for terminology usage in translation following TDD principles.

Requirements:
- Add --use-terminology flag
- Add options for terminology database specification
- Support enabling/disabling specific terminology features
- Validate parameter combinations
- Update help documentation

Write these tests first:
1. Test parsing the --use-terminology flag is recognized
2. Test parsing database path specification with the --db parameter
3. Test parsing feature-specific enabling/disabling parameters
4. Test validation of conflicting or invalid parameter combinations
5. Test that help text includes terminology usage parameters
6. Test compatibility with existing translation command parameters

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test with various command-line argument combinations.
Verify integration with existing argument parsing.
```

### Step 9.2: Configuration Integration
**Goal**: Integrate terminology usage with the configuration system.

**Copilot Prompt**:
```
Integrate terminology usage with the configuration system following TDD principles.

Requirements:
- Connect CLI arguments to configuration settings
- Add terminology-specific configuration options
- Support configuration via file and environment
- Implement precedence rules for different sources
- Update configuration documentation

Write these tests first:
1. Test CLI arguments correctly set terminology configuration options
2. Test loading terminology settings from a configuration file
3. Test reading terminology configuration from environment variables
4. Test precedence order (CLI arguments override file settings, etc.)
5. Test default values are applied when settings aren't specified
6. Test configuration validation rejects invalid terminology settings

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test configuration from different sources.
Verify precedence rules work correctly.
```

### Step 9.3: Translation Command Integration
**Goal**: Integrate terminology usage into the main translation command.

**Copilot Prompt**:
```
Integrate terminology usage into the main translation command following TDD principles.

Requirements:
- Modify translation command to use terminology when enabled
- Connect configuration to the translation pipeline
- Ensure fallback behavior works correctly
- Add terminology status reporting during translation
- Maintain backward compatibility

Write these tests first:
1. Test translation uses terminology database when enabled
2. Test translation falls back to Google Translate when terminology is disabled
3. Test configuration options control terminology behavior correctly
4. Test translation reports terminology usage statistics
5. Test backward compatibility with existing command syntax
6. Test terminology database connection errors are handled gracefully

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test end-to-end translation with terminology.
Verify configuration properly controls behavior.
```

### Step 9.4: Help Documentation Updates
**Goal**: Update help documentation for terminology usage.

**Copilot Prompt**:
```
Update help documentation for terminology usage following TDD principles.

Requirements:
- Update main help text with terminology features
- Add detailed help for terminology options
- Create examples showing terminology usage
- Include best practices in documentation
- Format help text for readability

Write these tests first:
1. Test main help text includes basic terminology feature description
2. Test detailed help includes all terminology command parameters
3. Test help includes practical examples of terminology usage
4. Test help contains best practices section for terminology
5. Test help text formatting is consistent and readable
6. Test help is accessible through various command invocations

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test help text content and structure.
Verify examples are correct and useful.
```

### Step 9.5: Complete Translation Command with Terminology
**Goal**: Finalize the complete translation command with terminology support.

**Copilot Prompt**:
```
Implement the complete translation command with terminology support following TDD principles.

Requirements:
- Integrate all terminology components with translation
- Ensure all command variations work correctly
- Add comprehensive reporting of terminology usage
- Support batch processing with terminology
- Ensure complete error handling

Write these tests first:
1. Test end-to-end translation with terminology integration
2. Test all command variations and parameter combinations
3. Test detailed reporting of terminology usage statistics after translation
4. Test batch processing multiple files with terminology support
5. Test graceful handling of various error conditions
6. Test performance with large files and large terminology databases

Follow the Red-Green-Refactor cycle:
1. Write failing tests first
2. Implement minimal code to make tests pass
3. Refactor the code while keeping tests passing

Test the complete command functionality.
Verify proper behavior in all usage scenarios.
```