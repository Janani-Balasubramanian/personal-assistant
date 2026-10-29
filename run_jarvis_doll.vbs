Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\VBJanu\Desktop\personal assistant"
WshShell.Run chr(34) & "C:\Users\VBJanu\Desktop\personal assistant\.venv\Scripts\pythonw.exe" & chr(34) & " " & chr(34) & "C:\Users\VBJanu\Desktop\personal assistant\watchdog.py" & chr(34), 1, False
Set WshShell = Nothing
