$ErrorActionPreference = "Stop"

# Resolve shim directory to find .pocket
$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PocketDir = Join-Path $ShimDir ".pocket"
$TaskScope = "."
$GoVersion = "1.25.6"
$GoInstallDir = "$PocketDir\tools\go\$GoVersion"
$GoBin = "$GoInstallDir\go\bin\go.exe"

# Expected checksums for each platform.
$Checksums = @{
    "aix-ppc64" = "13c8bca505dd902091304da8abfacaf3512f40c3faefae70db33337d9a42c90e"
    "darwin-amd64" = "e2b5b237f5c262931b8e280ac4b8363f156e19bfad5270c099998932819670b7"
    "darwin-arm64" = "984521ae978a5377c7d782fd2dd953291840d7d3d0bd95781a1f32f16d94a006"
    "dragonfly-amd64" = "6fdcdd4f769fe73a9c5602eb25533954903520f2a2a1953415ec4f8abf5bda52"
    "freebsd-386" = "be22b65ded1d4015d7d9d328284c985932771d120a371c7df41b2d4d1a91e943"
    "freebsd-amd64" = "61e1d50e332359474ff6dcf4bc0bd34ba2d2cf4ef649593a5faa527f0ab84e2b"
    "freebsd-arm" = "546c2c6e325e72531bf6c8122a2360db8f8381e2dc1e8d147ecb0cb49b5f5f93"
    "freebsd-arm64" = "648484146702dd58db0e2c3d15bda3560340d149ed574936e63285a823116b77"
    "freebsd-riscv64" = "663d7a9532bb4ac03c7a36b13b677b36d71031cd757b8acaee085e36c9ec8bc2"
    "illumos-amd64" = "c6adb151f8f50a25ef5a3f7b1be67155045daa766261e686ea210b93b46bbbd5"
    "linux-386" = "59fe62eee3cca65332acef3ebe9b6ff3272467e0a08bf7f68f96334902bf23b9"
    "linux-amd64" = "f022b6aad78e362bcba9b0b94d09ad58c5a70c6ba3b7582905fababf5fe0181a"
    "linux-arm64" = "738ef87d79c34272424ccdf83302b7b0300b8b096ed443896089306117943dd5"
    "linux-armv6l" = "679f0e70b27c637116791e3c98afbf8c954deb2cd336364944d014f8e440e2ae"
    "linux-loong64" = "433fe54d8797700b44fc4f1d085f9cd50ab3511b9b484fdfbb7b6c32a2be2486"
    "linux-mips" = "a5beaf2d135b8e9a2f3d91fa7e7d3761ffc97630484168bbc9a21f3901119c11"
    "linux-mips64" = "f2d72c1ac315d453f429f48900f43cd8d0aa296a2b82fa90dba7dfb907483fd8"
    "linux-mips64le" = "9b808ef978fd6414edd16736daa4a601c7e2dadff3bd640ade8a976535c974d4"
    "linux-mipsle" = "4e0b190b05c8359455d96d379c751d403554dcadf6765932845b2886e555bfd6"
    "linux-ppc64" = "5d0f479023b1481c9188cc066eca1293e6f8a67a882a6d93afafccfb51981476"
    "linux-ppc64le" = "bee02dbe034b12b839ae7807a85a61c13bee09ee38f2eeba2074bd26c0c0ab73"
    "linux-riscv64" = "82a6b989afda1681ecb1f4fa96f1006484f42643eb5e76bed58f7f97316bf84b"
    "linux-s390x" = "3d97cc5670a0da9cb177037782129f0bf499ecb47abc40488248548abd2c2c35"
    "netbsd-386" = "eb526fff2568fc9938d6eda6f0f50449661c693fcd89ab6f84e5e77e0a98d99b"
    "netbsd-amd64" = "959d786e3384403ac9d957c04d71da905b02f457406ca123662cbd4688f9ce6e"
    "netbsd-arm" = "fe6c3957f7feaf17ac72ca27590cc4914c19162fc0912869048cb3dc92f5c3fd"
    "netbsd-arm64" = "ddb5ec67fc4a0510b23560b7c01413bd9dde513cebfb5441a93e934f7e0c6853"
    "openbsd-386" = "167a18ff7db53f1652f3a65c905056bc14e7ab4319357498d0af998a83f457a9"
    "openbsd-amd64" = "06ec42383ff1e17abc0472e0a92eb028cb40b16ea09e2a86f80fbe60912d62de"
    "openbsd-arm" = "751df8eadd0f3d7be8ea6cda3af1e2e942099f6c97abcc0cfb5c8a0ac8e0cf3f"
    "openbsd-arm64" = "d9828a6162c0c0fdb2d7e9dc8285c43b18a3dab62bf5e83b5891a4384f3157ad"
    "openbsd-ppc64" = "73090f93dc861f2be9dc06d8209f32cd7ce7864b9b3e28f0cd54a9e031672699"
    "openbsd-riscv64" = "6d4932cb639c1172cf5861b031bd0a24f7341ef579aac15b392779e10c69343b"
    "plan9-386" = "b9db67922a94abe580e7bde9172eee2c223ade914cd12790d955a24554c134d5"
    "plan9-amd64" = "aa1ff9aa3e1ed09ecb21d09d736997d2de9f373fea9402815b3221946d17dcd5"
    "plan9-arm" = "94ec04501527876a542960096f0199495cbd9f9103b229d5299382aa51d9cc32"
    "solaris-amd64" = "9a1e89979be591b44e63be766c6571f5dc27b5fc3b79965c943186fcdaca0386"
    "windows-386" = "873da5cec02b6657ecd5b85e562a38fb5faf1b6e9ea81b2eb0b9a9b5aea5cb35"
    "windows-amd64" = "19b4733b727ba5c611b5656187f3ac367d278d64c3d4199a845e39c0fdac5335"
    "windows-arm64" = "8f2d8e6dd0849a2ec0ade1683bcfb7809e64d264a4273d8437841000a28ffb60"
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
