param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$User = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Principal = New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Python = "$Root\.venv\Scripts\python.exe"
$ServerAction = New-ScheduledTaskAction -Execute $Python -Argument "`"$Root\serve.py`"" -WorkingDirectory $Root
$env:LAB_PORT = "$Port"
$ServerTrigger = New-ScheduledTaskTrigger -AtLogOn -User $User
$ServerSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$ServerTask = New-ScheduledTask -Action $ServerAction -Trigger $ServerTrigger -Principal $Principal -Settings $ServerSettings
if ($Port -ne 8000) { throw 'Las tareas automaticas usan el puerto 8000. Use Start-Lab.ps1 -Port para otro puerto.' }
$AlertAction = New-ScheduledTaskAction -Execute $Python -Argument "`"$Root\manage.py`" process_alerts --send" -WorkingDirectory $Root
$AlertTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$BackupAction = New-ScheduledTaskAction -Execute $Python -Argument "`"$Root\manage.py`" backup_inventory" -WorkingDirectory $Root
$BackupTrigger = New-ScheduledTaskTrigger -Daily -At '18:00'
$Tasks = @{
    'LoteLAB-Servidor' = $ServerTask
    'LoteLAB-Alertas' = (New-ScheduledTask -Action $AlertAction -Trigger $AlertTrigger -Principal $Principal -Settings $Settings)
    'LoteLAB-Respaldo' = (New-ScheduledTask -Action $BackupAction -Trigger $BackupTrigger -Principal $Principal -Settings $Settings)
}
foreach ($Name in $Tasks.Keys) {
    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) { throw "Ya existe $Name. No se sobrescribio ninguna tarea." }
}
foreach ($Name in $Tasks.Keys) {
    Register-ScheduledTask -TaskName $Name -InputObject $Tasks[$Name] | Out-Null
}
Write-Output 'Tareas registradas para el usuario actual, sin elevacion. Se ejecutan con sesion Windows iniciada.'