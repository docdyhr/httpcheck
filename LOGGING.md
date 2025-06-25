# Logging Configuration for onSite

## Overview

onSite supports comprehensive logging configuration through the `config.json` file. Logs are stored in `~/Library/Logs/onSite/` following macOS best practices.

## Configuration Options

The logging configuration is specified in the `logging` section of `~/.httpcheck/config.json`:

```json
{
  "check_interval": 900,
  "logging": {
    "level": "INFO",
    "console": false,
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "rotation": {
      "max_bytes": 5242880,
      "backup_count": 5
    },
    "module_levels": {
      "urllib3": "WARNING",
      "requests": "WARNING"
    }
  }
}
```

### Basic Settings

- **`level`**: Main logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- **`console`**: Enable/disable console output in addition to file logging (boolean)
- **`format`**: Log message format using Python logging format strings
- **`date_format`**: Timestamp format for log entries

### Log Rotation

- **`rotation.max_bytes`**: Maximum size of log file before rotation (default: 5MB)
- **`rotation.backup_count`**: Number of backup files to keep (default: 5)

### Module-Specific Levels

Control logging verbosity for specific Python modules:

```json
"module_levels": {
  "urllib3": "WARNING",
  "requests": "WARNING",
  "urllib3.connectionpool": "ERROR"
}
```

## Changing Log Settings

### Via Menu Bar

1. Click the onSite icon in menu bar
2. Go to Settings → Logging
3. Select "Level" to change the main log level
4. Toggle "Console" to enable/disable console output

### Via Config File

1. Edit `~/.httpcheck/config.json`
2. Modify the `logging` section
3. Restart onSite for changes to take effect

## Log Levels Explained

- **`DEBUG`**: Detailed information for diagnosing problems (includes HTTP requests)
- **`INFO`**: General informational messages (site checks, configuration changes)
- **`WARNING`**: Warning messages for non-critical issues
- **`ERROR`**: Error messages for failures that don't stop the app
- **`CRITICAL`**: Critical failures that might stop the app

## Example Configurations

### Production (Default)
```json
"logging": {
  "level": "INFO",
  "console": false
}
```

### Debugging HTTP Issues
```json
"logging": {
  "level": "DEBUG",
  "console": true,
  "module_levels": {
    "urllib3": "DEBUG",
    "requests": "DEBUG"
  }
}
```

### Minimal Logging
```json
"logging": {
  "level": "WARNING",
  "rotation": {
    "max_bytes": 1048576,
    "backup_count": 2
  }
}
```

## Viewing Logs

- **From Menu**: Settings → Logging → View logs
- **Console.app**: Logs open in macOS Console app by default
- **Terminal**: `tail -f ~/Library/Logs/onSite/onsite.log`
- **Log location**: `~/Library/Logs/onSite/onsite.log`

## Troubleshooting

### Logs Not Updating
- Check if log file has correct permissions
- Verify config.json syntax is valid JSON
- Restart onSite after config changes

### Too Much Output
- Set main level to `INFO` or `WARNING`
- Set `urllib3` and `requests` modules to `WARNING` or `ERROR`

### Missing Details
- Set level to `DEBUG`
- Enable specific module debugging as needed

## Legacy Support

The old `debug_mode` setting is still supported for backward compatibility:
- `"debug_mode": true` sets log level to DEBUG
- New `logging.level` setting takes precedence