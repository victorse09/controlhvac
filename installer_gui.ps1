Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Instalador de ControlHVAC"
$form.Size = New-Object System.Drawing.Size(560, 420)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(248, 250, 252)

# Title Panel
$topPanel = New-Object System.Windows.Forms.Panel
$topPanel.Size = New-Object System.Drawing.Size(560, 80)
$topPanel.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$form.Controls.Add($topPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "ControlHVAC - CMMS Climatización"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(56, 189, 248)
$titleLabel.Location = New-Object System.Drawing.Point(20, 15)
$titleLabel.Size = New-Object System.Drawing.Size(500, 30)
$topPanel.Controls.Add($titleLabel)

$subTitle = New-Object System.Windows.Forms.Label
$subTitle.Text = "Asistente de Instalación para Windows (v1.0.0)"
$subTitle.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$subTitle.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$subTitle.Location = New-Object System.Drawing.Point(22, 45)
$subTitle.Size = New-Object System.Drawing.Size(500, 20)
$topPanel.Controls.Add($subTitle)

# Directory label
$dirLabel = New-Object System.Windows.Forms.Label
$dirLabel.Text = "Carpeta de instalación de la aplicación:"
$dirLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$dirLabel.ForeColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$dirLabel.Location = New-Object System.Drawing.Point(25, 105)
$dirLabel.Size = New-Object System.Drawing.Size(480, 20)
$form.Controls.Add($dirLabel)

$pathBox = New-Object System.Windows.Forms.TextBox
$pathBox.Text = "$env:LOCALAPPDATA\Programs\ControlHVAC"
$pathBox.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$pathBox.Location = New-Object System.Drawing.Point(25, 130)
$pathBox.Size = New-Object System.Drawing.Size(380, 26)
$form.Controls.Add($pathBox)

$browseBtn = New-Object System.Windows.Forms.Button
$browseBtn.Text = "Examinar..."
$browseBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$browseBtn.Location = New-Object System.Drawing.Point(415, 128)
$browseBtn.Size = New-Object System.Drawing.Size(105, 30)
$browseBtn.Add_Click({
    $fbd = New-Object System.Windows.Forms.FolderBrowserDialog
    $fbd.SelectedPath = $pathBox.Text
    if ($fbd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $pathBox.Text = $fbd.SelectedPath
    }
})
$form.Controls.Add($browseBtn)

# Options checkboxes
$chkDesktop = New-Object System.Windows.Forms.CheckBox
$chkDesktop.Text = "Crear acceso directo en el Escritorio"
$chkDesktop.Checked = $true
$chkDesktop.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$chkDesktop.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
$chkDesktop.Location = New-Object System.Drawing.Point(25, 175)
$chkDesktop.Size = New-Object System.Drawing.Size(400, 24)
$form.Controls.Add($chkDesktop)

$chkStart = New-Object System.Windows.Forms.CheckBox
$chkStart.Text = "Crear acceso en el Menú Inicio"
$chkStart.Checked = $true
$chkStart.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$chkStart.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
$chkStart.Location = New-Object System.Drawing.Point(25, 205)
$chkStart.Size = New-Object System.Drawing.Size(400, 24)
$form.Controls.Add($chkStart)

$chkLaunch = New-Object System.Windows.Forms.CheckBox
$chkLaunch.Text = "Ejecutar ControlHVAC al finalizar la instalación"
$chkLaunch.Checked = $true
$chkLaunch.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$chkLaunch.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
$chkLaunch.Location = New-Object System.Drawing.Point(25, 235)
$chkLaunch.Size = New-Object System.Drawing.Size(400, 24)
$form.Controls.Add($chkLaunch)

# Progress Bar & Status
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(25, 275)
$progressBar.Size = New-Object System.Drawing.Size(495, 20)
$progressBar.Visible = $false
$form.Controls.Add($progressBar)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = ""
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
$statusLabel.Location = New-Object System.Drawing.Point(25, 300)
$statusLabel.Size = New-Object System.Drawing.Size(495, 20)
$form.Controls.Add($statusLabel)

# Action Buttons
$installBtn = New-Object System.Windows.Forms.Button
$installBtn.Text = "Instalar Ahora"
$installBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$installBtn.BackColor = [System.Drawing.Color]::FromArgb(14, 165, 233)
$installBtn.ForeColor = [System.Drawing.Color]::White
$installBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$installBtn.Location = New-Object System.Drawing.Point(265, 335)
$installBtn.Size = New-Object System.Drawing.Size(135, 34)

$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = "Cancelar"
$cancelBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$cancelBtn.Location = New-Object System.Drawing.Point(415, 335)
$cancelBtn.Size = New-Object System.Drawing.Size(105, 34)
$cancelBtn.Add_Click({ $form.Close() })

$form.Controls.Add($installBtn)
$form.Controls.Add($cancelBtn)

# Installation Logic
$installBtn.Add_Click({
    $targetPath = $pathBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($targetPath)) {
        [System.Windows.Forms.MessageBox]::Show("Por favor especifica una ruta válida.", "Error", "OK", "Warning")
        return
    }

    $installBtn.Enabled = $false
    $browseBtn.Enabled = $false
    $pathBox.Enabled = $false
    $cancelBtn.Enabled = $false
    $progressBar.Visible = $true
    $progressBar.Style = "Marquee"
    $statusLabel.Text = "Copiando archivos del sistema..."
    $form.Refresh()

    try {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
        $sourceDir = Join-Path $scriptDir "dist\ControlHVAC"
        if (-not (Test-Path $sourceDir)) {
            $sourceDir = Join-Path $scriptDir "ControlHVAC"
        }

        if (-not (Test-Path $targetPath)) {
            New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
        }

        Copy-Item -Path "$sourceDir\*" -Destination $targetPath -Recurse -Force

        $statusLabel.Text = "Configurando accesos directos..."
        $form.Refresh()

        $wshShell = New-Object -ComObject WScript.Shell
        $exeTarget = Join-Path $targetPath "ControlHVAC.exe"
        $iconTarget = Join-Path $targetPath "assets\icons\app_icon.ico"

        if ($chkDesktop.Checked) {
            $desktopDir = [Environment]::GetFolderPath("Desktop")
            $dShortcut = $wshShell.CreateShortcut((Join-Path $desktopDir "ControlHVAC.lnk"))
            $dShortcut.TargetPath = $exeTarget
            $dShortcut.WorkingDirectory = $targetPath
            if (Test-Path $iconTarget) { $dShortcut.IconLocation = $iconTarget }
            $dShortcut.Description = "ControlHVAC CMMS"
            $dShortcut.Save()
        }

        if ($chkStart.Checked) {
            $startDir = [Environment]::GetFolderPath("Programs")
            $appMenu = Join-Path $startDir "ControlHVAC"
            if (-not (Test-Path $appMenu)) { New-Item -ItemType Directory -Path $appMenu -Force | Out-Null }
            $sShortcut = $wshShell.CreateShortcut((Join-Path $appMenu "ControlHVAC.lnk"))
            $sShortcut.TargetPath = $exeTarget
            $sShortcut.WorkingDirectory = $targetPath
            if (Test-Path $iconTarget) { $sShortcut.IconLocation = $iconTarget }
            $sShortcut.Description = "ControlHVAC CMMS"
            $sShortcut.Save()
        }

        $progressBar.Style = "Continuous"
        $progressBar.Value = 100
        $statusLabel.Text = "¡Instalación finalizada con éxito!"
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(22, 163, 74)

        if ($chkLaunch.Checked) {
            Start-Process -FilePath $exeTarget -WorkingDirectory $targetPath
        }

        [System.Windows.Forms.MessageBox]::Show("¡ControlHVAC se instaló correctamente!", "Instalación Exitosa", "OK", "Information")
        $form.Close()
    }
    catch {
        $progressBar.Visible = $false
        $statusLabel.Text = "Error en la instalación: $($_.Exception.Message)"
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(220, 38, 38)
        [System.Windows.Forms.MessageBox]::Show("Ocurrió un error durante la instalación: `n$($_.Exception.Message)", "Error de Instalación", "OK", "Error")
        $installBtn.Enabled = $true
        $cancelBtn.Enabled = $true
    }
})

[void]$form.ShowDialog()
