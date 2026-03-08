$ErrorActionPreference = "Stop"

# Resolve shim directory to find .pocket
$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PocketDir = Join-Path $ShimDir ".pocket"
$TaskScope = "."
$GoVersion = "1.26.1"
$GoInstallDir = "$PocketDir\tools\go\$GoVersion"
$GoBin = "$GoInstallDir\go\bin\go.exe"

# Expected checksums for each platform.
$Checksums = @{
    "aix-ppc64" = "75441456c5fb8338b2691d22d7e91cc756f79defaa4268d6e04ab85ca1a1f4a3"
    "darwin-amd64" = "65773dab2f8cc4cd23d93ba6d0a805de150ca0b78378879292be0b903b8cdd08"
    "darwin-arm64" = "353df43a7811ce284c8938b5f3c7df40b7bfb6f56cb165b150bc40b5e2dd541f"
    "dragonfly-amd64" = "f415e65bfcb03989a4b6eddedcd582cd509ea619af588b1341416216642c78fb"
    "freebsd-386" = "afb86dcd5240cf93627171a169973c75d9d139a69ed8e0be120d49b24943c13f"
    "freebsd-amd64" = "d89034a0b54fdc234815fecfb76d7d06a7d180d7a6124aa47715a4cacc9fe999"
    "freebsd-arm" = "c60b5b09a24680e40a906df62af71563af4cca0106f01390f2a2346bbfbc4aaa"
    "freebsd-arm64" = "d62b358dbf7bcfc33402e7e221d848e7fd8d7ac902b33920f2c23c8a32ba76db"
    "illumos-amd64" = "78e9a3d99fab9626b773a859f28f69ca5240846487f51b92b51251ef04f210bc"
    "linux-386" = "da75d696c6b9440fe9fb6418429f29eaeee947707ee8c6ddb567c558051a1cc2"
    "linux-amd64" = "031f088e5d955bab8657ede27ad4e3bc5b7c1ba281f05f245bcc304f327c987a"
    "linux-arm64" = "a290581cfe4fe28ddd737dde3095f3dbeb7f2e4065cab4eae44dfc53b760c2f7"
    "linux-armv6l" = "c9937198994dc173b87630a94a0d323442bef81bf7589b1170d55a8ebf759bda"
    "linux-loong64" = "922b0f308771ce7e162f6c14a9d4bc86db329eaacf6db875e967ad7e5a6b065c"
    "linux-mips" = "8711f0396539d9051f27b7743c69ab48359dea75cfaa37b8c70b6ddf6b5d8259"
    "linux-mips64" = "bbe2604bdf51e08d6386da7632f07379f88f31b2431ae71839a7064201a8ffd3"
    "linux-mips64le" = "1d97c7293a9760afb4a6e02d19e627d7eecea75b4f06096fd39b7977e4830b96"
    "linux-mipsle" = "2051d0dc77d8e35aaab39236ae1f913098bbee493c7ed6a6281a8dd5dc1e5db7"
    "linux-ppc64" = "a14f56b7483c3829e7eb92766956b0b7c3cbb21d055d31c3d327a15baf5535c6"
    "linux-ppc64le" = "f56eed002998f5f51fa07fd4ed0c5de5e02d51cec7a4007f771c7576620d9d45"
    "linux-riscv64" = "56f8a63ae986c75e91001d65e17648564a10f0d2b18d696d13c91e459da1abd4"
    "linux-s390x" = "60fe623ef63e6338c055ec0e0e3f4fa85c97a056de2d2f6ee38591e2bfa9cdde"
    "netbsd-386" = "158b816ce02a2a8cb07aca558bd332ba3b6f56d3b873f48979231f8beaa458a1"
    "netbsd-amd64" = "42bf3dba3d2c023fb7cce66806e300d389951b2ba50484eb6a2d8cdb8baa8b50"
    "netbsd-arm" = "7107542cc768b1bdf713e33e7034dd2a5ca98e7357643c2c9695c6be5176a590"
    "netbsd-arm64" = "498845f0c6b5eb3136c1a21b87940e55a039639f0757b91016172e67ce899032"
    "openbsd-386" = "aba9d96b620eac5a3b47c0e58dc2a2d773c365991a6e1a9b681b8c77542adbed"
    "openbsd-amd64" = "8801baa1cc9d221b863b005555ba3c6cbd27fb50b651f7e31ea129d0ada27577"
    "openbsd-arm" = "cdeb25b4d496c3e6610d86292af8c2699bca40cfdad27dd6366ea032e29f233b"
    "openbsd-arm64" = "398f0074552368b0f8d874712a69bb4c999d16edaceaa31ff7dde735f524e815"
    "openbsd-ppc64" = "74e95fa65c22cd2ab09a69532517bac51da5a66827766abd721f20a4fd9120dc"
    "openbsd-riscv64" = "1a78ed5f05959bda1a7feee108bb96fd46ca50f8f8ff60484fef0b6436bf36c0"
    "plan9-386" = "214a665bbf5204caa1111a15a9607b3f0057ea9721e0dafbd5a71303de0708c4"
    "plan9-amd64" = "c6b0bd3c0f0f4c62191c665a27df9f79470572ad29ecf6064368f3bde43c14bc"
    "plan9-arm" = "9caf03c5455fe14dd622cba54edc4655a895e302f09e34a6dd19c4ebc7c53786"
    "solaris-amd64" = "e9d67570e05e43120692be78bf7497a22ff413526f8d6b7378bba9607a151b5b"
    "windows-386" = "6a26b7ce038d96d2b3457ea4933667fb85c896411860216daf6ea17ecd4b25c5"
    "windows-amd64" = "9b68112c913f45b7aebbf13c036721264bbba7e03a642f8f7490c561eebd1ecc"
    "windows-arm64" = "c17e09676be0faad3cbed1c81bb02f38fb73e2f93d048571cc13730fe23f2d5b"
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
