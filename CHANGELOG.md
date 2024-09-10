# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-09-10

### Added

- Implemented ReactiveSmartGraph class for building complex, reactive workflows
- Added Pipeline class for creating sequences of connected components
- Introduced BranchingComponent for conditional processing
- Created CompletionComponent for integrating Large Language Models
- Implemented various input handlers (TextInputHandler, JSONInputHandler, etc.)
- Added support for multiple toolkits (DuckDuckGoToolkit, TavilyToolkit, MemoryToolkit)
- Implemented GraphVisualizer for graph visualization
- Added error handling and custom exceptions
- Introduced logging system with SmartGraphLogger
- Created utility functions for processing observables
- Implemented state management within components
- Added support for asynchronous operations

### Changed

- Refactored core functionality to use reactive programming principles
- Enhanced type hinting across the codebase
- Improved project structure and module organization

### Removed

- Deprecated old non-reactive components

## [0.1.0] - 2024-07-25

### Added

- Initial release of SmartGraph
- Implemented basic graph structure and component system
- Added preliminary support for LLM integration
- Created basic memory management system

### Changed

- Established project structure and development guidelines

### Removed

- N/A
