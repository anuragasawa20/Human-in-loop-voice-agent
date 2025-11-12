# Shared Types and Constants
****
This directory contains shared types, constants, and utilities used across both agent and backend.

## Purpose

- Ensure consistency between Python backend and TypeScript frontend
- Define common enums and constants
- Share API contracts

## Files

- `types.ts` - TypeScript type definitions (mirrored in Python models)
- `constants.py` - Python constants

## Design Decision

While we have separate implementations for Python and TypeScript, we keep the core types in sync manually. For a larger project, consider using tools like:
- OpenAPI/Swagger code generation
- Protobuf for cross-language type safety
- JSON Schema for validation

