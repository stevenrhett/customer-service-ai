# Global Cursor Commands

This directory contains global Cursor commands that are available across all projects.

## Git Commands

- **git-status.sh** - Quick git status with recent commits
- **git-commit.sh** - Stage all changes and commit with message

## File Operations

- **find-file.sh** - Find files by name pattern
- **search-in-files.sh** - Search for text pattern in files
- **list-large-files.sh** - List largest files in directory
- **show-tree.sh** - Show directory structure

## Development Tools

- **check-ports.sh** - Check what's running on common dev ports
- **kill-port.sh** - Kill process on specific port
- **create-venv.sh** - Create Python virtual environment
- **count-loc.sh** - Count lines of code

## Utilities

- **env-info.sh** - Show environment information
- **clean-build.sh** - Clean common build artifacts
- **create-gitignore.sh** - Create comprehensive .gitignore
- **extract-urls.sh** - Extract URLs from text
- **generate-password.sh** - Generate secure random password
- **quick-backup.sh** - Create quick backup of current directory

## Usage

1. Open Cursor's command palette (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows/Linux)
2. Type "Cursor: Run Command" or search for the command name
3. Select the command you want to run

## Examples

```bash
# Quick git operations
git-status.sh
git-commit.sh "Fix bug in auth"

# Find files
find-file.sh config
search-in-files.sh "TODO"

# Development
check-ports.sh
kill-port.sh 8000
create-venv.sh

# Utilities
env-info.sh
clean-build.sh
generate-password.sh 20
```

## Customization

These commands are stored in `~/.cursor/commands` and can be edited to fit your workflow.

