$ErrorActionPreference = "Stop"

# Resolve shim directory to find .pocket
$ShimDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PocketDir = Join-Path $ShimDir ".pocket"
$TaskScope = "."
$GoVersion = "1.26.0"
$GoInstallDir = "$PocketDir\tools\go\$GoVersion"
$GoBin = "$GoInstallDir\go\bin\go.exe"

# Expected checksums for each platform.
$Checksums = @{
    "aix-ppc64" = "ca464cc9c48d66e905e6978924554057b693f0aea697372fa8f7e108cc212261"
    "darwin-amd64" = "1ca28b7703cbea05a65b2a1d92d6b308610ef92f8824578a0874f2e60c9d5a22"
    "darwin-arm64" = "b1640525dfe68f066d56f200bef7bf4dce955a1a893bd061de6754c211431023"
    "dragonfly-amd64" = "f688f36f1b3ae17f2ca0a6f8d5e8cba46a972de26ef6241b21ab9645b291243e"
    "freebsd-386" = "9f07792e085f0d212c75ba403cb73e7f2f71eace48a38fab58711270dd7b1cef"
    "freebsd-amd64" = "7bba5a430d2c562af87b6c1a31cccf72c43107b7318b48aa8a02441df61acd08"
    "freebsd-arm" = "fe15a74bdb33954ebc9312efb01ac1871f7fc9cc712993058de8fc2a4dc8c8f7"
    "freebsd-arm64" = "5d92e2d65a543811dca9f76a2b533cbdc051bdd5015bf789b137e2dcc33b2d52"
    "illumos-amd64" = "2191668cd3aea0a05e646e6f7919ea357e666c15facf417f33e5cf18b7f00dd9"
    "linux-386" = "35e2ec7a7ae6905a1fae5459197b70e3fcbc5e0a786a7d6ba8e49bcd38ad2e26"
    "linux-amd64" = "aac1b08a0fb0c4e0a7c1555beb7b59180b05dfc5a3d62e40e9de90cd42f88235"
    "linux-arm64" = "bd03b743eb6eb4193ea3c3fd3956546bf0e3ca5b7076c8226334afe6b75704cd"
    "linux-armv6l" = "3f6b48d96f0d8dff77e4625aa179e0449f6bbe79b6986bfa711c2cfc1257ebd8"
    "linux-loong64" = "33947cd7686f1cd5f097d2a5a30427a4ade114ea00b7570c85a2abf1af3d0507"
    "linux-mips" = "a4ece61d4bac43b6983fde2c6b9cfc1af7f0d5d6a073219583d4e93b11559c25"
    "linux-mips64" = "197c2e97fa9ec1ad05998e0982d1a1ae761980df154424e5f29f3912e9ea4e5e"
    "linux-mips64le" = "61c52b4ab0dceae29f10df29045483596c3f06810c9b511e8336a97428a95a1b"
    "linux-mipsle" = "b3a13cc5a5f9250b02cf4ba19914c90c7034e68a5ccb9affa5198aadbcedac9a"
    "linux-ppc64" = "ef7232a49101d163a93bac34d03bfbc4fb18f75d7526d77ac307e16d9d83c300"
    "linux-ppc64le" = "3066b2284b554da76cf664d217490792ba6f292ec0fc20bf9615e173cc0d2800"
    "linux-riscv64" = "ab9226ecddda0f682365c949114b653a66c2e9330e7b8d3edea80858437d2ff2"
    "linux-s390x" = "d62137f11530b97f3503453ad7d9e570af070770599fb8054f4e8cd0e905a453"
    "netbsd-386" = "f79ae29d97980bf4c42120c0bebea758426dfa250ab39bcd909bccf057d5eced"
    "netbsd-amd64" = "22fc488ddd2c5958378fba2560866d6dae298160ba198e51ca5b998dc77b92f1"
    "netbsd-arm" = "1c70fd89c12dfda71f755dae1d7796f14702442b50ef2831117a641358276c5a"
    "netbsd-arm64" = "379d6ef6dfa8b67a7776744a536e69a1dc0fe5aeed48eb882ac71f89a98ba8ab"
    "openbsd-386" = "02084b48b800d28a434f89e8d19c7c5d47b7eb1339d5cf6104da56a7ad0aa23a"
    "openbsd-amd64" = "97884d7e5f566230f65820c02019ea253b53800157975918b6b6b7f03bf1b022"
    "openbsd-arm" = "2618746ffa6b93216d698c2ae923738373bd433c1253438c5ad8efdd2fd0a388"
    "openbsd-arm64" = "5a43668bf3c49d302ec50ac55d7e3f28a410cbda56485d7ebb9759f83e03e56f"
    "openbsd-ppc64" = "00fbd0df705ac70f2833f97a893b7819f99704a3711c2096907f859703fe3e83"
    "openbsd-riscv64" = "d00373b08c4fa396887fab8f6217824b5d3cad5409db326d535cfcf68916b9ea"
    "plan9-386" = "d8bcdb292a902e52adcce3b96a12474bd69cfd331bf92ad399afb51e009503b4"
    "plan9-amd64" = "847fa33e55206b0c40b99252e0219cc356ff58ccd4e143ce0a378ebfd75446b0"
    "plan9-arm" = "8872abd44fb3087e9c1bc0982e4c3be442018c4ad7cb5150ed29d68839e75ce4"
    "solaris-amd64" = "ec424798ae65c23dea6f4ef58d5fed85c56305eeb4a74e7af9a7d73bf335c93c"
    "windows-386" = "50674f3d6a071fa1a4c1d76dc37fafa0330df87d84087a262fee020da5396b6b"
    "windows-amd64" = "9bbe0fc64236b2b51f6255c05c4232532b8ecc0e6d2e00950bd3021d8a4d07d4"
    "windows-arm64" = "73bdbb9f64aa152758024485c5243a1098182bb741fcc603b6fb664ee5e0fe35"
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
