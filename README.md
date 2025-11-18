# Continuous Stock Adjustment Plugin for InvenTree

A powerful InvenTree plugin that enables quick and intuitive stock adjustments through barcode scanning. Simply scan a barcode to instantly remove stock items, with automatic package quantity detection from supplier parts.

## Features

- **📱 Dedicated Page View**: Standalone stock removal page accessible via navigation menu for optimal scanning workflow
- **📊 Dashboard Widget**: Quick access barcode scanner widget on the InvenTree dashboard
- **🔄 Automatic Quantity Detection**: Smart removal quantities based on supplier part package sizes
- **📝 Scan History**: Real-time tracking of recent scans with success/failure status
- **🎯 Bulk Actions**: Custom "Remove Package" action for stock items in the interface
- **🔌 RESTful API**: Programmatic access for system integration

## Prerequisites

- InvenTree 0.18.0 or later (recommended)
- Python 3.9 or higher
- Authenticated user with stock management permissions (`Stock.change` and `Stock.delete`)
- Barcode scanner (optional but recommended for best experience)

## Installation

**Note:** All commands must be run within the InvenTree virtual environment.

### Via pip (Recommended)

```bash
pip install inventree-continouous-stock-adjustment
```

Then restart your InvenTree instance.

### From Source

```bash
git clone https://github.com/DanielDango/inventree-continuous-stock-adjustment.git
cd inventree-continuous-stock-adjustment
pip install -U wheel setuptools
python -m build
pip install dist/inventree_continouous_stock_adjustment-*.whl
```

## Configuration

### Enable the Plugin

1. Go to **Settings** → **Plugin Settings**
2. Find **Continouous Stock Adjustment** and toggle **Active**
3. No additional settings required

### Barcode Setup

The plugin uses InvenTree's built-in barcode system. Ensure parts have barcodes assigned via the part detail page or barcode scanning interface.

### Required Permissions

Users need these permissions:
- **Stock.change** - Modify stock items
- **Stock.delete** - Remove stock

## Usage

The plugin provides three ways to remove stock via barcode scanning:

### 1. Standalone Page View (Recommended)

Access the dedicated stock removal page via the navigation menu or directly at:
**`/app/plugin/continouous-stock-adjustment/stock-removal/`**

1. **Navigate**: Click **Stock Removal** in the InvenTree navigation menu (or visit the URL directly)
2. **Scan or Enter Barcode**: Use a barcode scanner or manually type the barcode
3. **Press Enter or Click Button**: The system automatically processes the barcode
4. **View Results**: Success/failure notifications appear with quantity and remaining stock details
5. **Check History**: Recent scans are displayed below with timestamps

This dedicated page provides the best user experience for continuous barcode scanning operations.

### 2. Dashboard Widget

Quick access from the InvenTree home dashboard:

1. **Access Dashboard**: Navigate to your InvenTree home page
2. **Find Widget**: Locate the "Quick Stock Removal" widget
3. **Scan Barcode**: Enter or scan a barcode and press Enter
4. **View History**: Recent scans appear below the input field

### 3. Stock Item Actions

Remove packages directly from stock item views:

1. Navigate to **Stock** → **Stock Items**
2. Select one or more stock items
3. Click **Actions** dropdown → **Remove Package**
4. The plugin removes one package quantity from each selected item

**Example Workflow:**
```
1. Scan barcode "ABC123"
2. System identifies Part: "Resistor 10kΩ" 
3. Detects package quantity: 100 pieces from supplier data
4. Removes 100 pieces from stock
5. Shows: "Successfully removed 100 pieces from stock"
6. Displays remaining stock: 500 pieces
```



## API Reference

The plugin exposes a RESTful API endpoint for programmatic access:

### Endpoint: Barcode Scan

**URL:** `/plugin/continouous-stock-adjustment/scan/`

**Method:** `POST`

**Authentication:** Required (Token or Session)

#### Request Body

```json
{
  "barcode": "ABC123",
  "quantity": 10.5  // Optional - if omitted, uses package quantity from supplier part
}
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Successfully removed 100.0 pieces from stock",
  "part_id": 42,
  "part_name": "Resistor 10kΩ",
  "quantity_removed": 100.0,
  "remaining_stock": 500.0
}
```

#### Error Responses

**Barcode Not Found (404)**
```json
{
  "success": false,
  "message": "Barcode not found or does not match a part"
}
```

**Insufficient Stock (400)**
```json
{
  "success": false,
  "message": "No stock available for part: Resistor 10kΩ",
  "part_id": 42,
  "part_name": "Resistor 10kΩ"
}
```

**Server Error (500)**
```json
{
  "success": false,
  "message": "Error processing barcode: [error details]"
}
```

### API Usage Example (Python)

```python
import requests

# InvenTree API configuration
INVENTREE_URL = "http://your-inventree-instance.com"
API_TOKEN = "your-api-token"

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# Scan a barcode and remove stock
response = requests.post(
    f"{INVENTREE_URL}/plugin/continouous-stock-adjustment/scan/",
    headers=headers,
    json={"barcode": "ABC123"}
)

result = response.json()
if result["success"]:
    print(f"Removed {result['quantity_removed']} from {result['part_name']}")
    print(f"Remaining stock: {result['remaining_stock']}")
else:
    print(f"Error: {result['message']}")
```

### API Usage Example (cURL)

```bash
curl -X POST http://your-inventree-instance.com/plugin/continouous-stock-adjustment/scan/ \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{"barcode": "ABC123"}'
```

## How It Works

1. **Barcode Scanning**: User scans or enters a barcode
2. **Part Identification**: Plugin uses InvenTree's barcode system to identify the part
3. **Quantity Determination**:
   - Uses API-specified quantity if provided
   - Otherwise, reads supplier part `pack_quantity_native` field
   - Defaults to 1 unit if no supplier data exists
4. **Stock Removal**: Removes stock from available items (oldest first by ID), handling partial removals across multiple items if needed
5. **Feedback**: Returns success/failure with quantity and remaining stock details

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Barcode Not Recognized** | Verify barcode is assigned to a part in InvenTree; check barcode format matches InvenTree's expectations |
| **No Stock Available** | Ensure stock items exist with quantity > 0 and are not allocated |
| **Permission Denied (403)** | Verify user authentication and stock management permissions; confirm plugin is active |
| **Removing 1 Instead of Package Qty** | Check supplier part configuration has `pack_quantity_native` set; consider specifying quantity in API requests |
| **Page/Widget Not Visible** | Confirm plugin is active, user is authenticated, and refresh browser cache |

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/DanielDango/inventree-continuous-stock-adjustment.git
cd inventree-continuous-stock-adjustment

# Install Python dependencies
pip install -U wheel setuptools twine build ruff

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install frontend dependencies
cd frontend
npm install
```

### Frontend Development

```bash
cd frontend

# Start development server with hot reload
npm run dev

# Extract translations
npm run translate

# Build production bundle
npm run build

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Python Development

```bash
# Run Python linting
ruff check

# Auto-fix Python issues
ruff check --fix --preview

# Format Python code
ruff format --preview

# Build the plugin package
python -m build
```

### Testing in InvenTree

1. Build the plugin: `python -m build`
2. Install in your InvenTree environment: `pip install dist/*.whl`
3. Restart InvenTree
4. Activate the plugin in settings
5. Test functionality in the dashboard

### Project Structure

```
.
├── continouous_stock_adjustment/   # Python plugin code
│   ├── __init__.py                # Version definition
│   ├── core.py                    # Main plugin class
│   ├── views.py                   # API views
│   ├── serializers.py             # API serializers
│   └── api_test.py                # API testing script
├── frontend/                      # React/TypeScript frontend
│   ├── src/
│   │   ├── Dashboard.tsx         # Dashboard widget component
│   │   ├── Panel.tsx             # Panel component
│   │   └── Settings.tsx          # Settings component
│   ├── package.json
│   └── vite.config.ts
├── pyproject.toml                # Python project configuration
├── README.md                     # This file
└── LICENSE                       # MIT License
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow code style**: Run linters before committing
3. **Test thoroughly**: Ensure changes don't break existing functionality
4. **Document changes**: Update README if adding new features
5. **Submit a pull request**: With clear description of changes

### Code Style

- **Python**: Follows Ruff linting with preview features
- **TypeScript/React**: Uses Biome for linting and formatting
- **Commits**: Use clear, descriptive commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Daniel Schwab**
- Email: daniel.schwab@hadiko.de
- GitHub: [@DanielDango](https://github.com/DanielDango)

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/DanielDango/inventree-continuous-stock-adjustment/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/DanielDango/inventree-continuous-stock-adjustment/discussions)
- **InvenTree Docs**: [Plugin Documentation](https://docs.inventree.org/en/latest/plugins/)

## Acknowledgments

- Built for the [InvenTree](https://inventree.org/) inventory management system
- Uses the InvenTree plugin framework and UI components

---

**Note**: This plugin requires InvenTree to be properly configured with barcode support and appropriate user permissions for stock management.
