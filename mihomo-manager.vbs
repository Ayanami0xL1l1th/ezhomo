Option Explicit
Dim WshShell, choice, result, objWMIService, colProcesses, mihomoPath, mihomoDir, isRunning

' 设置路径
mihomoPath = "mihomo.exe"
mihomoDir = "."

' 创建对象
Set WshShell = CreateObject("WScript.Shell")

' 显示主菜单
choice = ShowMainMenu()

If choice = "" Then
    WScript.Quit
End If

' 执行选择的操作
ExecuteChoice choice

' ===============================================
' 函数定义
' ===============================================

Function ShowMainMenu()
    Dim menuText, userChoice
    
    menuText = "=== Mihomo 管理工具 ===" & vbCrLf & vbCrLf
    menuText = menuText & "1. 启动 Mihomo" & vbCrLf
    menuText = menuText & "2. 停止 Mihomo" & vbCrLf
    menuText = menuText & "3. 重启 Mihomo" & vbCrLf
    menuText = menuText & "4. 检查状态" & vbCrLf
    menuText = menuText & "5. 重新加载配置" & vbCrLf
    menuText = menuText & "6. 设置开机自启" & vbCrLf
    menuText = menuText & "7. 移除开机自启" & vbCrLf
    menuText = menuText & "8. 检查自启状态" & vbCrLf & vbCrLf
    menuText = menuText & "直接按回车或取消退出"
    
    userChoice = InputBox(menuText, "Mihomo 管理工具", "")
    ShowMainMenu = userChoice
End Function

Sub ExecuteChoice(choice)
    Select Case choice
        Case "1"
            StartMihomo
        Case "2"
            StopMihomo
        Case "3"
            RestartMihomo
        Case "4"
            CheckStatus
        Case "5"
            ReloadConfig
        Case "6"
            EnableAutostart
        Case "7"
            DisableAutostart
        Case "8"
            CheckAutostartStatus
        Case Else
            MsgBox "无效的选择", vbExclamation, "Mihomo 管理工具"
    End Select
End Sub

Function IsMihomoRunning()
    Dim objWMIService, colProcesses
    
    Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
    Set colProcesses = objWMIService.ExecQuery("Select * from Win32_Process Where Name = 'mihomo.exe'")
    
    If colProcesses.Count > 0 Then
        IsMihomoRunning = True
    Else
        IsMihomoRunning = False
    End If
End Function

Sub StartMihomo()
    If IsMihomoRunning() Then
        MsgBox "Mihomo 已经在运行中", vbExclamation, "Mihomo 管理工具"
        Exit Sub
    End If
    
    ' 使用独立进程启动，确保不会随脚本退出而终止
    Dim startupinfo, cmd
    Set startupinfo = CreateObject("WScript.Shell")
    
    ' 隐藏窗口启动
    cmd = "cmd /c start /B """ & mihomoPath & """ -d """ & mihomoDir & """"
    WshShell.Run cmd, 0, False
    
    ' 等待几秒检查是否启动成功
    WScript.Sleep 3000
    
    If IsMihomoRunning() Then
        MsgBox "Mihomo 启动成功", vbInformation, "Mihomo 管理工具"
    Else
        MsgBox "Mihomo 可能启动失败，请检查日志", vbExclamation, "Mihomo 管理工具"
    End If
End Sub

Sub StopMihomo()
    If Not IsMihomoRunning() Then
        MsgBox "Mihomo 未在运行", vbExclamation, "Mihomo 管理工具"
        Exit Sub
    End If
    
    ' 先尝试正常终止
    result = WshShell.Run("taskkill /f /im mihomo.exe", 0, True)
    
    If result = 0 Then
        MsgBox "已停止 Mihomo", vbInformation, "Mihomo 管理工具"
    Else
        ' 尝试使用 PowerShell 强制终止
        Dim psCmd
        psCmd = "powershell -Command ""Stop-Process -Name 'mihomo' -Force -ErrorAction SilentlyContinue"""
        result = WshShell.Run(psCmd, 0, True)
        
        If result = 0 Then
            MsgBox "已强制停止 Mihomo", vbInformation, "Mihomo 管理工具"
        Else
            MsgBox "停止失败", vbCritical, "Mihomo 管理工具"
        End If
    End If
End Sub

Sub RestartMihomo()
    MsgBox "正在重启 Mihomo...", vbInformation, "Mihomo 管理工具"
    
    If IsMihomoRunning() Then
        StopMihomo
        WScript.Sleep 2000
    Else
        MsgBox "Mihomo 未运行，直接启动", vbInformation, "Mihomo 管理工具"
    End If
    
    StartMihomo
End Sub

Sub CheckStatus()
    If IsMihomoRunning() Then
        ' 尝试获取版本信息
        Dim versionInfo
        On Error Resume Next
        Set versionInfo = CreateObject("MSXML2.XMLHTTP")
        versionInfo.Open "GET", "http://127.0.0.1:9090/version", False
        versionInfo.setRequestHeader "Authorization", "Bearer 123456"
        versionInfo.Send
        
        If Err.Number = 0 And versionInfo.Status = 200 Then
            MsgBox "状态: Mihomo 正在运行" & vbCrLf & "API: 服务正常", vbInformation, "状态检查"
        Else
            MsgBox "状态: Mihomo 正在运行" & vbCrLf & "API: 无法连接", vbInformation, "状态检查"
        End If
        On Error GoTo 0
    Else
        MsgBox "状态: Mihomo 未运行", vbExclamation, "状态检查"
    End If
End Sub

Sub ReloadConfig()
    If Not IsMihomoRunning() Then
        MsgBox "Mihomo 未运行，无法重新加载配置", vbExclamation, "Mihomo 管理工具"
        Exit Sub
    End If
    
    Dim reloadCommand
    reloadCommand = "powershell -Command ""Invoke-RestMethod -Uri 'http://127.0.0.1:9090/configs?reload=true' -Method PUT -Headers @{'Authorization'='Bearer 123456'}"""
    
    result = WshShell.Run(reloadCommand, 0, True)
    
    If result = 0 Then
        MsgBox "配置重新加载成功", vbInformation, "Mihomo 管理工具"
    Else
        MsgBox "重新加载失败", vbCritical, "Mihomo 管理工具"
    End If
End Sub

Function IsAdmin()
    ' 检查是否以管理员权限运行
    Dim shell, fso, tempFile, tempPath
    
    Set shell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    tempPath = shell.ExpandEnvironmentStrings("%TEMP%")
    tempFile = tempPath & "\test_admin.txt"
    
    On Error Resume Next
    fso.CreateTextFile(tempFile).Write "test"
    
    If Err.Number = 0 Then
        fso.DeleteFile(tempFile)
        IsAdmin = True
    Else
        IsAdmin = False
    End If
    On Error GoTo 0
End Function

Sub EnableAutostart()
    If Not IsAdmin() Then
        MsgBox "请以管理员身份运行此脚本来设置开机自启！" & vbCrLf & vbCrLf & _
               "右键点击脚本，选择'以管理员身份运行'", vbCritical, "Mihomo 管理工具"
        Exit Sub
    End If
    
    Dim fullPath, fullDir, psCommand
    
    fullPath = WshShell.CurrentDirectory & "\" & mihomoPath
    fullDir = WshShell.CurrentDirectory
    
    ' 检查文件是否存在
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FileExists(fullPath) Then
        MsgBox "找不到 Mihomo: " & fullPath, vbCritical, "Mihomo 管理工具"
        Exit Sub
    End If
    
    ' 创建计划任务的 PowerShell 命令
    psCommand = "powershell -ExecutionPolicy Bypass -Command """ & _
        "$Action = New-ScheduledTaskAction -Execute '" & fullPath & "' -Argument '-d """ & fullDir & """' -WorkingDirectory '" & fullDir & "'; " & _
        "$Trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay '00:00:30'; " & _
        "$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; " & _
        "$Principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; " & _
        "Register-ScheduledTask -TaskName 'MihomoProxy' -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description 'Mihomo Proxy Service AutoStart'""" & _
        ""
    
    ' 执行 PowerShell 命令
    result = WshShell.Run(psCommand, 0, True)
    
    If result = 0 Then
        MsgBox "计划任务创建成功！" & vbCrLf & vbCrLf & _
               "Mihomo 将在系统启动时自动运行", vbInformation, "Mihomo 管理工具"
    Else
        MsgBox "创建失败，请检查权限或重试", vbCritical, "Mihomo 管理工具"
    End If
End Sub

Sub DisableAutostart()
    If Not IsAdmin() Then
        MsgBox "请以管理员身份运行此脚本来移除开机自启！" & vbCrLf & vbCrLf & _
               "右键点击脚本，选择'以管理员身份运行'", vbCritical, "Mihomo 管理工具"
        Exit Sub
    End If
    
    Dim psCommand
    psCommand = "powershell -ExecutionPolicy Bypass -Command ""Unregister-ScheduledTask -TaskName 'MihomoProxy' -Confirm:$false"""
    
    result = WshShell.Run(psCommand, 0, True)
    
    If result = 0 Then
        MsgBox "开机自启已禁用", vbInformation, "Mihomo 管理工具"
    Else
        ' 检查是否是因为任务不存在
        Dim checkCmd, checkResult
        checkCmd = "powershell -Command ""Get-ScheduledTask -TaskName 'MihomoProxy' -ErrorAction SilentlyContinue"""
        
        Set checkResult = WshShell.Exec(checkCmd)
        While checkResult.Status = 0
            WScript.Sleep 100
        Wend
        
        Dim output
        output = checkResult.StdOut.ReadAll()
        
        If InStr(output, "MihomoProxy") = 0 Then
            MsgBox "未找到 Mihomo 开机自启任务", vbInformation, "Mihomo 管理工具"
        Else
            MsgBox "禁用失败", vbCritical, "Mihomo 管理工具"
        End If
    End If
End Sub

Sub CheckAutostartStatus()
    Dim psCommand, checkResult, output
    
    psCommand = "powershell -Command ""Get-ScheduledTask -TaskName 'MihomoProxy' -ErrorAction SilentlyContinue"""
    
    Set checkResult = WshShell.Exec(psCommand)
    While checkResult.Status = 0
        WScript.Sleep 100
    Wend
    
    output = checkResult.StdOut.ReadAll()
    
    If InStr(output, "MihomoProxy") > 0 Then
        MsgBox "Mihomo 开机自启已启用", vbInformation, "自启状态检查"
    Else
        MsgBox "Mihomo 开机自启未设置", vbInformation, "自启状态检查"
    End If
End Sub

' 清理对象
Set WshShell = Nothing