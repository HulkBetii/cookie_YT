
 = New-Object -ComObject WScript.Shell
 = .CreateShortcut('C:\Users\HulkBeoti\Desktop\Fix GPM Active.lnk')
.TargetPath = 'C:\GPM\fix_gpm_active.bat'
.WorkingDirectory = 'C:\GPM'
.IconLocation = 'shell32.dll,238'
.Description = 'Fix GPM Active DNS and Hosts'
.Save()
