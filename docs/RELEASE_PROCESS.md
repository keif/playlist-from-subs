# Release Process & Changelog Automation

This document describes the automated release and changelog generation process for yt-sub-playlist.

## Quick Start

### Option 1: Automated Script (Recommended)

```bash
./scripts/release.sh
```

This interactive script will guide you through:
- Generating changelog entries
- Creating version tags
- Bumping version numbers

### Option 2: Manual npm Commands

```bash
# Install dependencies (first time only)
npm install

# Generate changelog without version bump
npm run changelog

# Create a new release (auto-detects version bump type)
npm run release

# Create specific version types
npm run release:patch  # 4.0.0 -> 4.0.1
npm run release:minor  # 4.0.0 -> 4.1.0
npm run release:major  # 4.0.0 -> 5.0.0

# See what would change (dry-run)
npm run release:dry-run
```

## Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic changelog generation.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature (appears in changelog)
- **fix**: Bug fix (appears in changelog)
- **refactor**: Code refactoring (appears in changelog)
- **perf**: Performance improvement (appears in changelog)
- **docs**: Documentation changes (appears in changelog)
- **test**: Test additions/changes (appears in changelog)
- **build**: Build system changes (appears in changelog)
- **ci**: CI/CD changes (appears in changelog)
- **chore**: Maintenance tasks (hidden from changelog)
- **style**: Code style changes (hidden from changelog)

### Examples

#### Feature Addition
```bash
git commit -m "feat(ui): implement channel allowlist/blocklist management UI

- Add channels.html with three-mode selector
- Implement real-time search with 300ms debounce
- Add bulk selection controls
- Integrate with config page"
```

#### Bug Fix
```bash
git commit -m "fix(filtering): resolve channel ID matching issue

Channel IDs were not being correctly matched when using allowlist mode.
Updated comparison logic to handle both string and list formats.

Fixes #123"
```

#### Breaking Change
```bash
git commit -m "feat(config): migrate whitelist to allowlist system

BREAKING CHANGE: The channel_whitelist configuration field has been
replaced with channel_allowlist. Automatic migration is provided.

Migrates existing whitelist configurations to the new allowlist format."
```

## Changelog Generation Process

### How It Works

1. **standard-version** analyzes your git commit history
2. Identifies commits since the last release tag
3. Groups commits by type (feat, fix, refactor, etc.)
4. Generates changelog entries with links
5. Updates `CHANGELOG.md`
6. Bumps version in `package.json`
7. Creates a git tag (e.g., `v4.1.0`)
8. Creates a release commit

### Version Bumping Rules

The tool automatically determines the version bump type:

- **Patch** (4.0.0 → 4.0.1): Bug fixes only
- **Minor** (4.0.0 → 4.1.0): New features (backward-compatible)
- **Major** (4.0.0 → 5.0.0): Breaking changes

You can also manually specify the bump type using the scripts above.

## Release Workflow

### Standard Release Process

1. **Ensure clean working tree**
   ```bash
   git status
   # Should show no uncommitted changes
   ```

2. **Run the release script**
   ```bash
   ./scripts/release.sh
   # Select option 2, 3, or 4 based on change type
   ```

3. **Review the changes**
   ```bash
   git log -1
   # Review the release commit and tag

   cat CHANGELOG.md
   # Review the generated changelog
   ```

4. **Push to remote**
   ```bash
   git push --follow-tags origin main
   ```

### Changelog-Only Update

If you just want to update the changelog without creating a release:

```bash
npm run changelog
git add CHANGELOG.md
git commit -m "docs(changelog): update changelog"
git push
```

## Configuration Files

### `.versionrc.json`

Configuration for standard-version:
- Defines commit types and their changelog sections
- Sets URL formats for GitHub links
- Configures release commit message format
- Specifies files to bump (package.json)

### `package.json`

Contains:
- Current version number
- npm scripts for changelog generation
- devDependencies for tooling

## Manual Changelog Editing

While automation is preferred, you can manually edit `CHANGELOG.md`:

1. Follow the [Keep a Changelog](https://keepachangelog.com/) format
2. Use semantic versioning for version numbers
3. Include links to commits and comparisons
4. Group changes by type (Added, Changed, Fixed, etc.)

### Changelog Structure

```markdown
## [Unreleased]

## [4.1.0] - 2025-10-27

### Added
- New feature description

### Changed
- Modified feature description

### Fixed
- Bug fix description

### Deprecated
- Feature marked for removal

### Removed
- Removed feature description

### Security
- Security fix description
```

## Troubleshooting

### Issue: "npm: command not found"

Install Node.js and npm:
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt-get install nodejs npm

# Verify installation
node --version
npm --version
```

### Issue: "No commits found"

Ensure you have commits since the last tag:
```bash
# Check recent commits
git log --oneline

# Check last tag
git describe --tags --abbrev=0

# If no tags exist, create initial tag
git tag v3.0.0 6c1ca4f  # Use appropriate commit hash
```

### Issue: Changelog not generating correctly

1. Verify commit message format:
   ```bash
   git log --oneline -10
   # Check that commits follow conventional format
   ```

2. Check configuration:
   ```bash
   cat .versionrc.json
   # Ensure types are configured
   ```

3. Regenerate from scratch:
   ```bash
   npm run changelog:all
   # Regenerates entire changelog
   ```

## Best Practices

1. **Write clear commit messages**: Use conventional format consistently
2. **Test before release**: Run dry-run to preview changes
3. **Review changelog**: Always review generated content before pushing
4. **Tag thoughtfully**: Use semantic versioning correctly
5. **Document breaking changes**: Use BREAKING CHANGE footer for major changes

## Alternative Tools

If you prefer different tooling:

### GitHub Releases
Use GitHub's built-in release system with tag annotations

### Manual Changelog
Continue editing CHANGELOG.md manually following Keep a Changelog format

### Python-based Tools
- [commitizen](https://github.com/commitizen-tools/commitizen) - Python implementation
- [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release)

### Git Cliff
A newer, faster changelog generator:
```bash
brew install git-cliff
git cliff --tag v4.1.0 > CHANGELOG.md
```

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [standard-version Documentation](https://github.com/conventional-changelog/standard-version)
- [conventional-changelog](https://github.com/conventional-changelog/conventional-changelog)
