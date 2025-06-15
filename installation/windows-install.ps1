# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

if (-not (Test-CommandExists 'git')) {
    Write-Host "Error: Git is not installed on your system." -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/downloads" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-CommandExists 'python')) {
    Write-Host "Error: Python is not installed on your system." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Clone the repository
$repoUrl = "https://github.com/ChanBong/chirp.git"
$repoName = "chirp"

if (Test-Path $repoName) {
    $confirmation = Read-Host "A folder named '$repoName' already exists. Do you want to delete it? (y/n)"
    if ($confirmation -eq 'y') {
        Write-Host "Removing existing folder..." -ForegroundColor Yellow
        Remove-Item -Path $repoName -Recurse -Force
    } 
    else {
        Write-Host "Moving on..." -ForegroundColor Cyan
    }
}
else {
    Write-Host "Cloning repository..." -ForegroundColor Cyan
    git clone $repoUrl
}

Set-Location $repoName

Write-Host "Running bootstrap.py..." -ForegroundColor Cyan
python bootstrap.py

Write-Host "Installation completed successfully!" -ForegroundColor Green