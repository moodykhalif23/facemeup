# Usage: .\scripts\build-android.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Config

$JAVA_HOME   = "C:\Program Files\Android\Android Studio\jbr"
$ANDROID_SDK = "$env:LOCALAPPDATA\Android\Sdk"
$FRONTEND    = Join-Path $PSScriptRoot "..\frontend"

$env:JAVA_HOME         = $JAVA_HOME
$env:ANDROID_SDK_ROOT  = $ANDROID_SDK
$env:PATH              = "$JAVA_HOME\bin;" + $env:PATH

# Helpers

function Step($msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Die($msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

# Preflight

Step "Checking prerequisites"

if (-not (Test-Path "$JAVA_HOME\bin\java.exe")) {
    Die "Android Studio JVM not found at $JAVA_HOME"
}
if (-not (Test-Path $ANDROID_SDK)) {
    Die "Android SDK not found at $ANDROID_SDK"
}
if (-not (Test-Path $FRONTEND)) {
    Die "Frontend directory not found at $FRONTEND"
}

$javaVersion = & "$JAVA_HOME\bin\java.exe" -version 2>&1 | Select-String "version"
Write-Host "  Java     : $javaVersion"
Write-Host "  SDK      : $ANDROID_SDK"
Write-Host "  Frontend : $FRONTEND"

Push-Location $FRONTEND
try {

# Step 1 - Clean old build artifacts and caches

Step "Cleaning old build artifacts"
if (Test-Path "dist")                { Remove-Item -Recurse -Force "dist" }
if (Test-Path "node_modules\.vite")  { Remove-Item -Recurse -Force "node_modules\.vite" }
if (Test-Path "android\app\build")   { Remove-Item -Recurse -Force "android\app\build" }
if (Test-Path "android\build")       { Remove-Item -Recurse -Force "android\build" }
Write-Host "  Cleared dist, Vite cache, and Gradle build outputs" -ForegroundColor Green

# Step 2 - Install dependencies

Step "Installing npm dependencies"
npm install
if ($LASTEXITCODE -ne 0) { Die "npm install failed" }

# Step 3 - Web build

Step "Building web app (Vite)"
npm run build
if ($LASTEXITCODE -ne 0) { Die "npm run build failed" }

# Step 4 - Add Android platform (first run only)

if (-not (Test-Path "android")) {
    Step "Adding Android platform"
    npx cap add android
    if ($LASTEXITCODE -ne 0) { Die "cap add android failed" }
} else {
    Write-Host "  Android platform already exists, skipping cap add"
}

# Step 5 - Generate splash + icon assets

Step "Generating splash screen and icon assets"

# Search common logo locations
$logoCandidates = @(
    "src\assets\logo.png",
    "src\assets\icon.png",
    "src\assets\skincare.png",
    "public\logo.png",
    "public\icon.png",
    "public\skincare.png"
)

$logoSrc = $null
foreach ($candidate in $logoCandidates) {
    if (Test-Path $candidate) {
        $logoSrc = $candidate
        break
    }
}

if (-not (Test-Path "assets\icon-only.png")) {
    if ($logoSrc) {
        New-Item -ItemType Directory -Force -Path "assets" | Out-Null
        Copy-Item $logoSrc "assets\icon-only.png"
        Copy-Item $logoSrc "assets\splash.png"
        Write-Host "  Copied $logoSrc to assets/"
    } else {
        Write-Host "  WARNING: No source logo found — skipping asset generation" -ForegroundColor Yellow
        Write-Host "           Place a PNG at src\assets\logo.png and re-run to generate icons."
    }
}

if (Test-Path "assets\icon-only.png") {
    npx capacitor-assets generate --android
    if ($LASTEXITCODE -ne 0) { Die "Asset generation failed" }
}

# Step 6 - Capacitor sync

Step "Syncing Capacitor (web assets + plugins -> Android)"
npx cap sync android
if ($LASTEXITCODE -ne 0) { Die "cap sync android failed" }

# Step 6b - Fix adaptive icon XMLs (capacitor-assets generates broken @mipmap/ic_launcher_background)

Step "Fixing adaptive icon XML references"

$iconXml = @'
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground>
        <inset android:drawable="@mipmap/ic_launcher_foreground" android:inset="16.7%" />
    </foreground>
</adaptive-icon>
'@

$iconDir = "android\app\src\main\res\mipmap-anydpi-v26"
if (Test-Path $iconDir) {
    Set-Content "$iconDir\ic_launcher.xml"       $iconXml -Encoding UTF8
    Set-Content "$iconDir\ic_launcher_round.xml" $iconXml -Encoding UTF8
    Write-Host "  Fixed ic_launcher.xml and ic_launcher_round.xml"
} else {
    Write-Host "  WARNING: $iconDir not found, skipping icon XML fix" -ForegroundColor Yellow
}

# Step 7 - Gradle build

Step "Building APK with Gradle"
Push-Location android
try {
    .\gradlew assembleDebug
    if ($LASTEXITCODE -ne 0) { Die "Gradle build failed" }
} finally {
    Pop-Location
}

} finally {
    Pop-Location
}

# Done

$apk = "$FRONTEND\android\app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $apk) {
    $size = [math]::Round((Get-Item $apk).Length / 1MB, 1)
    Write-Host "`n✓ BUILD SUCCESSFUL" -ForegroundColor Green
    Write-Host "  App : SkinCare AI (com.skincare.app)"
    Write-Host "  APK : $apk ($size MB)"
    Write-Host "  Install: adb install `"$apk`""
} else {
    Die "APK not found after build"
}
