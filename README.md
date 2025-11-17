# Continuous Stock Adjustment Plugin for InvenTree

A powerful InvenTree plugin that enables quick and intuitive stock adjustments through barcode scanning. Simply scan a barcode to instantly remove stock items, with automatic package quantity detection from supplier parts.

## Features

- **📱 Dashboard Widget**: Integrated barcode scanner in the InvenTree dashboard for quick stock removal
- **🔄 Automatic Quantity Detection**: Automatically determines removal quantity based on supplier part package sizes
- **📊 Real-time Feedback**: Instant notifications showing removed quantities and remaining stock
- **📝 Scan History**: Keeps track of recent scans with success/failure status
- **🎯 Bulk Actions**: Custom "Remove Package" action for stock items in the InvenTree interface
- **🧭 Easy Navigation**: Quick access navigation menu item for stock removal
- **🔌 RESTful API**: Programmatic access via API endpoints for integration with other systems

## Prerequisites

- **InvenTree**: Version 0.18.0 or later (recommended)
- **Python**: 3.9 or higher
- **Barcode Scanner**: Hardware or software barcode scanner (optional but recommended)
- **Permissions**: User must be authenticated and have stock management permissions

## Installation

### Option 1: InvenTree Plugin Manager (Recommended)

1. Log in to your InvenTree instance as an administrator
2. Navigate to **Settings** → **Plugins**
3. Click **Install Plugin**
4. Search for `inventree-continouous-stock-adjustment`
5. Click **Install**
6. Activate the plugin in the plugin settings

### Option 2: Manual Installation via pip

If you prefer to install the plugin manually:

```bash
# Install the plugin package
pip install inventree-continouous-stock-adjustment

# Restart your InvenTree instance
```

### Option 3: Development Installation

For development or testing:

```bash
# Clone the repository
git clone https://github.com/DanielDango/inventree-continuous-stock-adjustment.git
cd inventree-continuous-stock-adjustment

# Install Python dependencies
pip install -U wheel setuptools

# Build the plugin
python -m build

# Install the built package
pip install dist/inventree_continouous_stock_adjustment-*.whl
```

## Configuration

### Enabling the Plugin

1. Navigate to **Settings** → **Plugin Settings** in InvenTree
2. Find **Continouous Stock Adjustment** in the plugin list
3. Toggle the **Active** switch to enable the plugin
4. The plugin requires no additional settings to function

### Barcode Configuration

The plugin works with InvenTree's built-in barcode system:

1. Ensure your parts have barcodes assigned
2. Navigate to **Part** → Select a part → **Parameters** tab
3. Add or scan barcodes for your parts
4. The plugin will automatically detect these barcodes during scanning

### User Permissions

Users must have the following permissions to use this plugin:
- **Authenticated** - Must be logged in
- **Stock.change** - Permission to modify stock items
- **Stock.delete** - Permission to remove stock

## Usage

### Dashboard Widget: Quick Stock Removal

The primary way to use this plugin is through the dashboard widget:

1. **Access the Dashboard**: Navigate to your InvenTree home dashboard
2. **Locate the Widget**: Find the "Quick Stock Removal" widget
3. **Scan or Enter Barcode**: 
   - Use a barcode scanner (recommended for speed)
   - Or manually type the barcode and press Enter
4. **Automatic Processing**: The plugin will:
   - Identify the part associated with the barcode
   - Determine the removal quantity (from supplier part package size, or default to 1)
   - Remove stock from available stock items
   - Display success message with removed quantity and remaining stock
5. **View History**: Recent scans are displayed below the input with timestamps

**Example Workflow:**
```
1. Scan barcode "ABC123"
2. Plugin identifies Part: "Resistor 10kΩ" 
3. Detects package quantity: 100 pieces from supplier data
4. Removes 100 pieces from stock
5. Shows: "Successfully removed 100 pieces from stock"
6. Displays remaining stock: 500 pieces
```

### Stock Item Actions

Remove packages directly from the stock item view:

1. Navigate to **Stock** → **Stock Items**
2. Select one or more stock items
3. Click the **Actions** dropdown
4. Select **Remove Package**
5. The plugin removes one package quantity (based on supplier part data) from each selected item

### Navigation Menu

Quick access link in the main navigation:

1. Look for **Stock Removal** in the navigation menu
2. Click to access the dashboard where the widget is available
3. Start scanning immediately

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

### Barcode Scanning Process

1. **Barcode Input**: User scans or enters a barcode
2. **Barcode Resolution**: Plugin uses InvenTree's barcode scanning system to identify the associated part
3. **Quantity Determination**:
   - If quantity is specified in the request, uses that value
   - Otherwise, attempts to find supplier part with package quantity
   - Falls back to removing 1 unit if no supplier data exists
4. **Stock Removal**:
   - Finds stock items for the part with available quantity
   - Removes stock in order by stock item ID
   - Handles partial removals across multiple stock items if needed
5. **Response**: Returns success/failure with detailed information

### Package Quantity Detection

The plugin intelligently determines removal quantities:

- **Supplier Parts**: Checks for `pack_quantity_native` field
- **Example**: If a supplier sells resistors in packs of 100, scanning once removes 100 pieces
- **Fallback**: If no supplier data exists, defaults to 1 unit

### Stock Item Selection

When removing stock:
- Prioritizes stock items by ID (oldest first)
- Removes from the first item with sufficient quantity
- If insufficient, removes all from first item and continues to next
- Continues until full quantity is removed or stock is exhausted

## Troubleshooting

### Barcode Not Recognized

**Problem**: Scanning a barcode shows "Barcode not found"

**Solutions**:
- Verify the barcode is assigned to a part in InvenTree
- Check that the barcode format matches InvenTree's expected format
- Ensure the barcode scanner is properly configured
- Test by manually entering the barcode value

### No Stock Available

**Problem**: "No stock available for part" error

**Solutions**:
- Verify stock items exist for the part
- Check that stock items have quantity > 0
- Ensure stock items are not allocated or on hold
- Review stock location and availability

### Permission Denied

**Problem**: API returns 403 Forbidden

**Solutions**:
- Verify user is authenticated
- Check user has stock management permissions
- Ensure API token is valid and not expired
- Confirm plugin is activated in settings

### Package Quantity Not Detected

**Problem**: Always removes 1 unit instead of package quantity

**Solutions**:
- Verify supplier parts are configured for the part
- Check that `pack_quantity_native` field is set in supplier part
- Ensure supplier part is linked to the correct part
- Consider specifying quantity explicitly in API requests

### Dashboard Widget Not Visible

**Problem**: Widget doesn't appear on dashboard

**Solutions**:
- Verify plugin is activated in plugin settings
- Check user is authenticated
- Refresh the page or clear browser cache
- Check browser console for JavaScript errors

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
- Thanks to the InvenTree community for support and feedback

---

**Note**: This plugin requires InvenTree to be properly configured with barcode support and appropriate user permissions for stock management.
