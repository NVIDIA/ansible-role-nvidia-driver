#!/bin/bash
set -euo pipefail

# Ensure boolean values in tasks/main.yml use canonical YAML 1.2 literals
if grep -E '^\s+[a-z_]+:\s*(yes|no)\s*$' tasks/main.yml; then
    echo "ERROR: found yes/no boolean literals in tasks/main.yml"
    exit 1
fi
