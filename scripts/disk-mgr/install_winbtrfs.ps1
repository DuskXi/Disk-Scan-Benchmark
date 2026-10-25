<#
.SYNOPSIS
    Installs the WinBtrfs driver (https://github.com/maharmstone/btrfs) on a CI runner without a reboot.
.DESCRIPTION
    The driver is signed with the author's open-source code-signing certificate; trusting that certificate as a
    publisher lets pnputil install it silently. Exports WINBTRFS_DIR (folder with mkbtrfs.exe for this CPU) to the
    following workflow steps. Experimental: the driver is not WHQL-signed and may be blocked by driver policy.
#>
param([string]$Version = "1.10")

$ErrorActionPreference = "Stop"
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64" } else { "amd64" }
$root = Join-Path $env:RUNNER_TEMP "winbtrfs"
$zip = "$root.zip"

Invoke-WebRequest "https://github.com/maharmstone/btrfs/releases/download/v$Version/btrfs-$Version.zip" -OutFile $zip
Expand-Archive $zip $root -Force

$cert = (Get-AuthenticodeSignature (Join-Path $root "btrfs.cat")).SignerCertificate
if ($cert) {
    $store = [Security.Cryptography.X509Certificates.X509Store]::new("TrustedPublisher", "LocalMachine")
    $store.Open("ReadWrite")
    $store.Add($cert)
    $store.Close()
    Write-Host "[winbtrfs] trusted publisher: $($cert.Subject)"
}

pnputil /add-driver (Join-Path $root "btrfs.inf") /install
$state = sc.exe query btrfs | Out-String
if ($state -notmatch "RUNNING") {
    sc.exe start btrfs | Out-Null
    Start-Sleep -Seconds 2
    $state = sc.exe query btrfs | Out-String
}
Write-Host $state
if ($state -notmatch "RUNNING") {
    Get-WinEvent -LogName Microsoft-Windows-CodeIntegrity/Operational -MaxEvents 30 -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match "btrfs" } | Format-List TimeCreated, Id, Message
    throw "The WinBtrfs driver did not start"
}
"WINBTRFS_DIR=$(Join-Path $root $arch)" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
Write-Host "[winbtrfs] driver $Version running; mkbtrfs in $(Join-Path $root $arch)"
