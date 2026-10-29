Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\VBJanu\Desktop\personal assistant"
WshShell.Run "c:\Users\VBJanu\Desktop\personal assistant\run_jarvis_doll.vbs", 0, False
Set WshShell = Nothing
