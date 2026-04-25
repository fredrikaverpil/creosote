$ErrorActionPreference = "Stop"

# Resolve shim directory to find .pocket
$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PocketDir = Join-Path $ShimDir ".pocket"
$TaskScope = "."
$GoVersion = "1.26.2"
$GoInstallDir = "$PocketDir\tools\go\$GoVersion"
$GoBin = "$GoInstallDir\go\bin\go.exe"

# Expected checksums for each platform.
$Checksums = @{
    "aix-ppc64" = "e6f759fbdd5b1e3ecce3161d8bd9b9aeaf15c4112b7c101097e9d329b310d858"
    "darwin-amd64" = "bc3f1500d9968c36d705442d90ba91addf9271665033748b82532682e90a7966"
    "darwin-arm64" = "32af1522bf3e3ff3975864780a429cc0b41d190ec7bf90faa661d6d64566e7af"
    "dragonfly-amd64" = "b4f3f74412914e54140cbf8b5c76d2f8eeff3a5003310c9244c61ba8a0ecd94b"
    "freebsd-386" = "fab09ea1988aae3ae2c8186455e8956d539d04e2ee4973e8887853432d0e8039"
    "freebsd-amd64" = "f271fd829a2a6b36fa1c72cdaafb18410a106da982c93a626d4e8b0fa0f0fa21"
    "freebsd-arm" = "38713f1516cd2b0097ea05594ec1c842fe690dace8301c7d34d91b92250b4424"
    "freebsd-arm64" = "d78bb171900134efdd1d0d49e5e80cd8c8b614f0e46c508d0b6bac30fb996fdf"
    "illumos-amd64" = "e88cd85e9e253ceda4077367072aa10d2f92bc2fa6e59a811c00bbe95dc9b02d"
    "linux-386" = "89835cdc4dfebde7fe28c9c6dc080bb3753f6b0354301966ff9f62d14991bd7d"
    "linux-amd64" = "990e6b4bbba816dc3ee129eaeaf4b42f17c2800b88a2166c265ac1a200262282"
    "linux-arm64" = "c958a1fe1b361391db163a485e21f5f228142d6f8b584f6bef89b26f66dc5b23"
    "linux-armv6l" = "0000e45577827b0a8868588c543cbe4232853def1d3d7a344ad6e60ce2b015c8"
    "linux-loong64" = "4dcb87e845fe5c015c8cf6affb4636fcf1699182b70454783caed85c5dfa3267"
    "linux-mips" = "2d57e4167932a4872e31570465f48d8b6818002c77275bae969bdbb6d7238b5e"
    "linux-mips64" = "b0b49bb5c528e623a926b8242f03cfd612971150e18eeb3f638d751218c09cdf"
    "linux-mips64le" = "5ffc9da2b0ee939c8503c9d9278d6857909ca8577dae3b71221ab2821dc7826a"
    "linux-mipsle" = "ab1fe1c38ffa6bbda029dea33bf36167aca4ff3a25c9d6ed0af38da120678ddc"
    "linux-ppc64" = "589f7ef241104f153e910244b71d70f4aad0d4584651ca80a5188186dda63a2e"
    "linux-ppc64le" = "62b7645dd2404052535617c59e91cf03c7aa28e332dbaddbe4c0d7de7bcc6736"
    "linux-riscv64" = "c5c697faa4dc05364b6e163d2ab8161b32a120eeed54192457d57d7ef7c2091a"
    "linux-s390x" = "410726ed10a0ea6745c2ea8da4f0e769fd3ce819cd4a41a67ad08b094d5dfc31"
    "netbsd-386" = "e8ffab99dd65fef14097d6af48ea6302793f2298a7b2e5f00a284bd933feba4c"
    "netbsd-amd64" = "1f5c33c923983ee8433ad8098dcd87a0e1fdccd18d05a91844c2be60507a61fe"
    "netbsd-arm" = "85761320e364b65424d2952a3388970d86e072c8dce8dcad2a1dca41555c2b96"
    "netbsd-arm64" = "3ca3561bf4452e799d11e5312182f79cd342d506136cd44c2b47991206ec23f5"
    "openbsd-386" = "0644073c0ae1ade26d26953ef882d7d419855dca25b0e992ae416a47967d37b3"
    "openbsd-amd64" = "72f69217a88e3d0975a75adf9fc92ff10ea65def56e6c34d8612428bf769581e"
    "openbsd-arm" = "3aafe792df65abf1777b5cc678075ebba1bd8063e6450e81e742fef696e0bcbd"
    "openbsd-arm64" = "efd410fc60a17690ad43fe8dd00bf1fd4c1dc920d81970b9f422f313b0930b92"
    "openbsd-ppc64" = "98a2cadd416066739e00b1bc297727c3108dba9001811b177ce57afef518f8bd"
    "openbsd-riscv64" = "adf39a1a7e56d5c1a2cb69ad06752c5da6b808d2a029b7b6d6d5bb6e11a2168e"
    "plan9-386" = "eb2f95f6f43701eb98a31f5efdd9b5f14ff6e0afd289e1f94559462f83e73cfd"
    "plan9-amd64" = "d347fecec7532309fccf3570021ba8a00a0acce120fea02a46cc295936588b0f"
    "plan9-arm" = "70700c5af45201a8e82436fb824f3551e357e3002094c8416e78e1aa51d4a0ab"
    "solaris-amd64" = "cd45d13200697b3263e39cdf364f0cb9d9adc39d9574ab575e481b64cb7fb8b1"
    "windows-386" = "4a8b02c34625fecd9c6583442101c9796fc265a5fc1edb9340d71bed0300f94c"
    "windows-amd64" = "98eb3570bade15cb826b0909338df6cc6d2cf590bc39c471142002db3832b708"
    "windows-arm64" = "094d05caaf6ba235e2bd570b625d064ceb65943866252722a8f3fdba232139c6"
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
