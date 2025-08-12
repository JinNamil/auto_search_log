# 🧾 Log Analyzer (Python)

This is a **Python-based log analysis tool** that scans log files in a specified directory, searches for defined keywords, and presents a summary in the terminal or saves it to a file.  
The program is highly configurable via an `.ini` file.

---

## 📁 Features

- ✅ Supports multiple filename patterns (e.g. `*.log, *.txt`)
- ✅ Searches for one or more keywords across all matched log files
- ✅ Shows file-by-file keyword frequency as a table
- ✅ Saves detailed search results (matched lines with line numbers) to a file
- ✅ Displays progress bar while processing files
- ✅ Utilizes multi-core CPUs for faster processing using `ProcessPoolExecutor`
- ✅ Automatically creates the log directory if it doesn't exist

---

## 🧩 Configuration: `log_config.ini`

Create a file named `log_config.ini` in the same directory as the Python script.

```ini
[LOG]
log_dir = ./logs               ; Path to the directory containing logs
file_pattern = *.log, *.txt    ; Comma-separated file patterns to match

[SEARCH]
log1 = "error"                 ; Keyword 1
log2 = "fail"                  ; Keyword 2
log3 = "timeout"               ; Add more if needed...

[OUTPUT]
output_file = search_results.txt
