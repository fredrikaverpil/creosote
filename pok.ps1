$ErrorActionPreference = "Stop"

# Resolve shim directory to find .pocket
$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PocketDir = Join-Path $ShimDir ".pocket"
$TaskScope = "."
$GoVersion = "1.25.5"
$GoInstallDir = "$PocketDir\tools\go\$GoVersion"
$GoBin = "$GoInstallDir\go\bin\go.exe"

# Expected checksums for each platform.
$Checksums = @{
    "aix-ppc64" = "89d3300aeb8a49354c04d43abf2a0dca6a75ac772b3bc2edaac52de513041572"
    "darwin-amd64" = "b69d51bce599e5381a94ce15263ae644ec84667a5ce23d58dc2e63e2c12a9f56"
    "darwin-arm64" = "bed8ebe824e3d3b27e8471d1307f803fc6ab8e1d0eb7a4ae196979bd9b801dd3"
    "dragonfly-amd64" = "51478a265f45b68ce761aa303c1ecf185949f6eb0b2106e3066ec4d32361b38a"
    "freebsd-386" = "f8ff9fa5309fbbbd7d52f5d3f7181feb830dfd044d23c38746a2ada091f751b5"
    "freebsd-amd64" = "a2d2b2aeb218bd646fd8708bacc96c9d4de1b6c9ea48ceb9171e9e784f676650"
    "freebsd-arm" = "b83a5cb1695c7185a13840661aef6aa1b46202d41a72528ecde51735765c6641"
    "freebsd-arm64" = "938fc0204f853c24ab03967105146af6590903dd14f869fe912db7a735f654f6"
    "freebsd-riscv64" = "7b0cc61246cf6fc9e576135cfcd2b95e870b0f2ee5bf057325b2d76119001e4e"
    "illumos-amd64" = "ea5cafcf995ef4a82ced5a7134f18bbc5ca554c345075d18f37d2e192fe2c1ff"
    "linux-386" = "db908a86e888574ed3432355ba5372ad3ef2c0821ba9b91ceaa0f6634620c40c"
    "linux-amd64" = "9e9b755d63b36acf30c12a9a3fc379243714c1c6d3dd72861da637f336ebb35b"
    "linux-arm64" = "b00b694903d126c588c378e72d3545549935d3982635ba3f7a964c9fa23fe3b9"
    "linux-armv6l" = "0b27e3dec8d04899d6941586d2aa2721c3dee67c739c1fc1b528188f3f6e8ab5"
    "linux-loong64" = "0be2f27172a85de1b9c0c7f324832023b177d07cfa04a55dc67a3cc965fe969e"
    "linux-mips" = "0e7c387a6914c81b53278f023da2004e17d8d8e851749cdb5df15ad59e54ff3e"
    "linux-mips64" = "32ef8f4c4896c1e88dcbbf79c353d3e46dc38410e649327ee47e073e3326b06f"
    "linux-mips64le" = "437dc493b3ce97a65e7abc7e8ecb935f504b4805aff749baba219841bd970335"
    "linux-mipsle" = "675cd3e0cb7d9131602a0de06f5471ce969fd95d388baf1ec05106a1cdeb20b6"
    "linux-ppc64" = "a2159b254b025a816673365db565b3bd64f99fb185eb3f4cedabbf992097304d"
    "linux-ppc64le" = "f0904b647b5b8561efc5d48bb59a34f2b7996afab83ccd41c93b1aeb2c0067e4"
    "linux-riscv64" = "05de84b319bc91b9cecbc6bf8eb5fcd814cf8a9d16c248d293dbd96f6cc0151b"
    "linux-s390x" = "a5d0a72b0dfd57f9c2c0cdd8b7e0f401e0afb9e8c304d3410f9b0982ce0953da"
    "netbsd-386" = "57e79e72d1110954c6567082137f0228c46eb4d612211b3bf48dadb6a27eeaa2"
    "netbsd-amd64" = "d6062fa06c33613be60436b3e6422f2de43c28350bb30dbbc459782985eea7bd"
    "netbsd-arm" = "457d844df4aa6cd51616b2334e378cc295ee7bcca1cb21869adfc16f5f379bfd"
    "netbsd-arm64" = "5030511891f670dba65a6d8f15e687f623030ac5b63661a423a7dad53990b634"
    "openbsd-386" = "27cba5feeedfb08dea2770420c6024d7ea72eedad08132a9759c0f05f66f2486"
    "openbsd-amd64" = "c873e93f6bd125a23b359914ba34d62e6af21111b06c14ce344b724aa1ef933b"
    "openbsd-arm" = "e5a8cc469c66248bc2031327e66a4ad48a8f379435677386db52ef1aa7b2b0e2"
    "openbsd-arm64" = "cdd655fa0e15bc839d0c353bfb728b8d22a8012e54a11e297be919c3cf7ad866"
    "openbsd-ppc64" = "a149370fda34ce27fa78a452248f6f2040fe5ab955dce246d4d92de2c2d511c1"
    "openbsd-riscv64" = "be96cf8460011088cb75b330357796ecf1ac2ffffac77a3d1f798cbd7e6a2bc0"
    "plan9-386" = "a3926108324c4b161080b03cd941db58090fba1194610093ee5716ee98997287"
    "plan9-amd64" = "f171e529236b850ed4a1e714c317dddcf46855b575d9d018c654cf78b3ea1a2e"
    "plan9-arm" = "aaf285e49f39717029f4759c0f9b2860dbf23c20fb659122006ba1e145643721"
    "solaris-amd64" = "fb61c56ca80a2e1e5f74609ded64546166a5ab431c0d581ce718310cf27f6b9f"
    "windows-386" = "a593393ea7715ffd315158f622a76226c3a4c4a0a6f92b1aeae03d7380cc06a3"
    "windows-amd64" = "ae756cce1cb80c819b4fe01b0353807178f532211b47f72d7fa77949de054ebb"
    "windows-arm64" = "55a94a423a6b8f3ac2ac4d05a6e44d7760c6520a2c6dcef7425f6bac79c4eece"
}

# Find Go binary.
$GoCmd = $null
if (Get-Command go -ErrorAction SilentlyContinue) {
    $GoCmd = "go"
} elseif (Test-Path $GoBin) {
    $GoCmd = $GoBin
} else {
    # Download Go.
    Write-Host "Go not found, downloading go$GoVersion..."

    $Arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }
    $Platform = "windows-$Arch"
    $ZipUrl = "https://go.dev/dl/go$GoVersion.windows-$Arch.zip"
    $ZipPath = "$env:TEMP\go$GoVersion.zip"

    New-Item -ItemType Directory -Force -Path $GoInstallDir | Out-Null
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath

    # Verify checksum if available.
    $ExpectedHash = $Checksums[$Platform]
    if ($ExpectedHash) {
        $ActualHash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLower()
        if ($ActualHash -ne $ExpectedHash) {
            Remove-Item $ZipPath -Force
            Write-Error "Checksum verification failed!`nExpected: $ExpectedHash`nActual:   $ActualHash"
            exit 1
        }
        Write-Host "Checksum verified."
    } else {
        Write-Host "Warning: No checksum available for $Platform, skipping verification."
    }

    Expand-Archive -Path $ZipPath -DestinationPath $GoInstallDir -Force
    Remove-Item $ZipPath

    $GoCmd = $GoBin
    Write-Host "Go $GoVersion installed to $GoInstallDir"
}

$env:TASK_SCOPE = $TaskScope
& $GoCmd run -C $PocketDir . @args
exit $LASTEXITCODE
