# Output Formats Documentation

## Overview

httpcheck supports multiple output formats to suit different use cases and integration needs. The default table format is designed for human readability, while JSON and CSV formats enable easy parsing and integration with other tools.

## Available Formats

### Table Format (Default)

The default table format provides a clean, human-readable output:

```bash
# Basic usage
$ httpcheck google.com
----------  ---
google.com  200
----------  ---

# Verbose mode
$ httpcheck google.com -v
+------------+--------+----------------+---------+
| Domain     | Status | Response Time  | Message |
+============+========+================+=========+
| google.com | 200    | 0.23s          | OK      |
+------------+--------+----------------+---------+
```

### JSON Format

JSON output is ideal for programmatic processing and integration with other tools.

#### Basic JSON Output

```bash
$ httpcheck google.com --output json
[
  {
    "domain": "google.com",
    "status": "200",
    "message": "OK",
    "response_time": 0.237
  }
]
```

#### Verbose JSON Output

Verbose mode includes redirect information:

```bash
$ httpcheck http://google.com --output json -v
[
  {
    "domain": "google.com",
    "status": "200",
    "message": "OK",
    "response_time": 0.156,
    "redirect_chain": [
      {
        "url": "http://google.com/",
        "status": 301
      },
      {
        "url": "http://www.google.com/",
        "status": 200
      }
    ],
    "redirect_timing": [
      {
        "url": "http://google.com/",
        "status": 301,
        "time": 0.156
      },
      {
        "url": "http://www.google.com/",
        "status": 200,
        "time": 0.0
      }
    ]
  }
]
```

### CSV Format

CSV format is perfect for spreadsheet applications and data analysis.

#### Basic CSV Output

```bash
$ httpcheck google.com github.com --output csv
domain,status,response_time
google.com,200,0.154
github.com,200,0.297
```

#### Verbose CSV Output

Verbose mode includes additional columns:

```bash
$ httpcheck http://google.com https://github.com --output csv -v
domain,status,message,response_time,redirect_count,final_url
google.com,200,OK,0.19,2,http://www.google.com/
github.com,200,OK,0.181,0,github.com
```

## Usage Examples

### Processing JSON with jq

```bash
# Get all domains with non-200 status
$ httpcheck @domains.txt --output json | jq '.[] | select(.status != "200")'

# Extract just domains and status codes
$ httpcheck @domains.txt --output json | jq -r '.[] | "\(.domain): \(.status)"'

# Count successful checks
$ httpcheck @domains.txt --output json | jq '[.[] | select(.status == "200")] | length'
```

### Importing CSV to Excel/Google Sheets

```bash
# Generate CSV report
$ httpcheck @domains.txt --output csv -v > website_report.csv

# The CSV can be directly opened in Excel or imported to Google Sheets
```

### Monitoring Integration

```bash
# Send results to monitoring system
$ httpcheck @critical_sites.txt --output json | curl -X POST \
    -H "Content-Type: application/json" \
    -d @- https://monitoring.example.com/api/checks

# Save daily reports
$ httpcheck @sites.txt --output csv -v > reports/$(date +%Y-%m-%d).csv
```

### Automation Scripts

```python
import json
import subprocess

# Run httpcheck and parse results
result = subprocess.run(
    ['httpcheck', 'example.com', '--output', 'json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
for site in data:
    if site['status'] != '200':
        print(f"Alert: {site['domain']} returned {site['status']}")
```

## Output Format Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `--output table` | Default human-readable format | Manual checking, terminal output |
| `--output json` | JSON array of results | API integration, automation |
| `--output csv` | CSV with headers | Spreadsheets, data analysis |

## Combining with Other Options

Output formats work with all other httpcheck options:

```bash
# JSON with quiet mode (errors only)
$ httpcheck @sites.txt --output json -q

# CSV with custom timeout
$ httpcheck @sites.txt --output csv --timeout 10

# JSON with threading
$ httpcheck @sites.txt --output json -f --workers 20

# CSV with redirect details
$ httpcheck @sites.txt --output csv -v --show-redirect-timing
```

## Error Handling

Errors are included in structured output:

### JSON Error Example
```json
{
  "domain": "nonexistent.example",
  "status": "[connection error]",
  "message": "Connection failed",
  "response_time": 0.0
}
```

### CSV Error Example
```csv
domain,status,response_time
nonexistent.example,[connection error],0.0
```

## Best Practices

1. **Use JSON for automation**: JSON is easier to parse reliably than CSV
2. **Use CSV for reports**: CSV opens directly in spreadsheet applications
3. **Use verbose mode for debugging**: Include redirect chains and timing
4. **Pipe to files for large checks**: `httpcheck @sites.txt --output json > results.json`
5. **Combine with Unix tools**: Use `jq`, `grep`, `awk` for filtering

## Implementation Notes

- Response times are rounded to 3 decimal places
- JSON output is pretty-printed with 2-space indentation
- CSV headers are always included
- Special characters are properly escaped in both formats
- Empty results return `[]` for JSON and empty string for CSV
