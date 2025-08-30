# Code-Dependency-Visualizer
Visualizer
# Code Dependency Visualizer

Visualize code dependencies across multiple languages with this FastAPI + React tool, featuring interactive graphs and robust backend analysis.

---

##  Features

- **FastAPI Backend**  
  Upload a `.zip` file or codebase—backend detects file types, extracts imports/includes, and builds a directed dependency graph using NetworkX (supports safeguards for large uploads: 50 MB / 5 k files).

- **Multi-Language Support**  
  Works with Python, C/C++, Java, JavaScript, TypeScript, and HTML.  
  Differentiates between internal files and external packages. Output includes nodes, edges, metadata, and cycle detection in clean JSON format.

- **Interactive Frontend**  
  Built with React and TypeScript, using Cytoscape.js for graph visualization. Features include toggle controls for external dependencies and init files, cycle highlighting, node details, and performance metrics during analysis.

---
