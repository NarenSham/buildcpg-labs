# Shared vs Lab-Specific Data

## Overview
In a multi-lab environment, some data is **shared** across labs, while other datasets remain **lab-specific**. Proper organization is crucial for maintainability and scalability.

## Lab-Specific Data
- Stored within the lab’s dedicated folder.
- Includes lab experiments, transformations, and temporary datasets.
- Changes affect only the corresponding lab.

## Shared Data
- Placed in a centralized `shared` directory.
- Includes:
  - Standardized reference datasets (e.g., product catalogs, master lists)
  - Common transformations or utility tables
- Any updates must consider impact on all labs consuming the shared data.

## Guidelines
1. Only include truly reusable datasets in `shared`.
2. Maintain versioning for shared datasets to prevent breaking changes.
3. Document dependencies clearly in lab README files.

## Benefits
- Prevents accidental data contamination.
- Encourages modularity and reuse.
- Simplifies debugging and troubleshooting across labs.
