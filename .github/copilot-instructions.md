# GitHub Copilot Instructions

This repository contains an InvenTree plugin for continuous stock adjustment through barcode scanning.

## Repository Structure

- `continouous_stock_adjustment/` - Python plugin code (InvenTree backend)
- `frontend/` - React/TypeScript frontend components
- `.github/workflows/` - CI/CD workflows
- `pyproject.toml` - Python project configuration

## Technology Stack

### Backend
- **Framework**: InvenTree Plugin System (Django-based)
- **Python Version**: >= 3.9
- **Key Dependencies**: InvenTree plugin mixins (SettingsMixin, UrlsMixin, UserInterfaceMixin)

### Frontend
- **Framework**: React 19.1.1+ with TypeScript 5.6.2
- **Build Tool**: Vite 6.0.5
- **UI Library**: Mantine 8.2.7+
- **i18n**: Lingui for translations
- **Package Manager**: npm

## Development Setup

### Python Development
```bash
# Install Python dependencies
pip install -U wheel setuptools twine build ruff

# Build the plugin
python -m build
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Start development server
```

## Code Style & Linting

### Python
- **Linter**: Ruff with preview features enabled
- **Pre-commit hooks**: Configured via `.pre-commit-config.yaml`
- Run linting: `ruff check`
- Auto-fix: `ruff check --fix --preview`
- Format: `ruff format --preview`

### JavaScript/TypeScript
- **Linter/Formatter**: Biome 2.0.0
- **Config**: `biome.json` with custom rule overrides
- **Style**: Single quotes, no trailing commas, space indentation
- Run linting: `npm run lint` or `npx @biomejs/biome check src`
- Auto-fix: `npm run lint:fix`

## Build & Test

### Python Build
```bash
python -m build
```

### Frontend Build
```bash
cd frontend
npm run translate  # Extract and compile translations
npm run build     # TypeScript compile + Vite build
npm run lint      # Lint check
```

### CI Workflow
The CI checks both Python and frontend builds:
1. Python linting with ruff
2. Python package build
3. Frontend translation extraction
4. Frontend build and lint

## Key Patterns

### Plugin Structure
- Main plugin class: `ContinouousStockAdjustment` in `core.py`
- Uses InvenTree mixins for settings, URLs, and UI integration
- Version defined in `__init__.py` as `PLUGIN_VERSION`

### Frontend UI Components
- Custom panels via `get_ui_panels()` method
- Dashboard items via `get_ui_dashboard_items()` method
- Static files served through plugin's `plugin_static_file()` method

### URL Routing
- Custom API endpoints defined in `setup_urls()` method
- Views in `views.py`, serializers in `serializers.py`

## Important Notes

- The plugin is designed for barcode-based stock removal workflows
- Targets the 'part' model for displaying custom panels
- Dashboard items only visible to staff users
- Settings are configurable through InvenTree's plugin settings interface

## Testing Guidelines

- No explicit test infrastructure is currently set up
- Manual testing recommended through InvenTree plugin interface
- API testing code available in `api_test.py`

## Common Tasks

### Update Plugin Version
Edit `PLUGIN_VERSION` in `continouous_stock_adjustment/__init__.py`

### Add New Setting
Add to `SETTINGS` dict in `core.py` following InvenTree plugin settings format

### Add UI Component
Implement in frontend and reference via `plugin_static_file()` in plugin methods

### Add API Endpoint
1. Create view in `views.py`
2. Add URL pattern in `setup_urls()` method
3. Create serializer in `serializers.py` if needed
