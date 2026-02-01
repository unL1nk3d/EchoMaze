# EchoMaze Project Documentation

### Project Overview
EchoMaze is a lightweight, modular database system designed for managing IP addresses in penetration testing environments. It facilitates organizing pivoting scenarios, maintaining clear records of targets, and suggesting commands to operators in specific situations. The system helps map noise levels during penetration tests using a point-based scoring mechanism and provides tips for maintaining a low profile during intrusions, similar to tools like BloodHound.

The project aims to integrate an MCP (Model Context Protocol) server and LLM (Large Language Model) capabilities to assist agents in saving and retrieving data efficiently.

EchoMaze consists of several key modules:

* **GATHERINGDB**: A database module that handles persistence of IP addresses, ports, and associated data. It uses a DAO (Data Access Object) pattern for CRUD operations on IP nodes and ports, supporting hierarchical relationships for pivoting paths.
* **cheatIngestor**: A module that ingests and processes templates (e.g., MITRE ATT&CK techniques) provided by operators. It follows clean architecture principles with ports and adapters for document ingestion and auto-completion features.
* **UI**: A CLI-based graphical interface built with the asciimatics library. The main interface is the `TreeIPFrame` class in `frames/tree_ip_frame.py`, which displays hierarchical IP data. It uses a `UIMapper` class from `UI/models.py` to transform database entities into consumable nodes (hierarchical lists and tuples). The `GenericModel` class centralizes repository queries and commands for the UI.
* **Commands**: Contains functions for creating directories based on IP structures and parsing scan reports from nmap (gnmap files). It integrates with the core system to import data from nmap scans and reload from directories.
* **WorkflowScreamer**: A utility module for creating workflow directories (context, exploits, scan) and parsing scans to support organized penetration testing workflows.
* **Core**: The central logic module that orchestrates database operations, port-service mapping, and integration between modules.

### Compilation and Testing Commands
- To run the application: `python launch.py`
- To run the UI: `python launch.py --ui`
- To initialize the database: `python launch.py --init-db`
- To import from nmap: `python launch.py --import-from-nmap [--nmap-file <file>]`
- To reload from directory: `python launch.py --reload-from-directory`

### Code Style Guidelines
- `cheatIngestor` follows clean architecture with ports, adapters, and separation of concerns.
- `GATHERINGDB` uses the DAO pattern for database interactions.
- General: Use TDD (Test-Driven Development); create tests in `UI/tests/` before implementing features.

### Testing Instructions
Before creating a new feature, develop a test case (TDD) in the `UI/tests` directory to validate the functionality. Implement the feature to pass the test. Run tests using the project's testing framework.

## Development Environment Tips
- Activate the virtual environment: `& C:\Users\ispi2\.virtualenvs\BLWSL-l5dQw78k\Scripts\Activate.ps1`