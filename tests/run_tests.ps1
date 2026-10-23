$ErrorActionPreference = "Stop"
$compiler = Get-Command gcc -ErrorAction Stop
$sourceRoot = Split-Path -Parent $PSScriptRoot
$parserSource = Join-Path $sourceRoot "parser.c"
$shellSource = Join-Path (Join-Path $sourceRoot "src") "parser.c"
$utilsSource = Join-Path (Join-Path $sourceRoot "src") "utils.c"
$includeDirectory = Join-Path $sourceRoot "src"
$testSource = Join-Path $PSScriptRoot "test_parser.c"

foreach ($standard in @("c11", "c99")) {
    $output = Join-Path ([System.IO.Path]::GetTempPath()) "mysh-parser-$PID-$standard.exe"
    try {
        & $compiler.Source "-std=$standard" "-Wall" "-Wextra" "-Wpedantic" `
            "-Werror" "-D_POSIX_C_SOURCE=200809L" "-D_DEFAULT_SOURCE" `
            "-I$includeDirectory" $parserSource $shellSource $utilsSource `
            $testSource "-o" $output
        if ($LASTEXITCODE -ne 0) {
            throw "Compilation failed for $standard (exit $LASTEXITCODE)."
        }

        & $output
        if ($LASTEXITCODE -ne 0) {
            throw "Parser tests failed for $standard (exit $LASTEXITCODE)."
        }
    }
    finally {
        Remove-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue
    }
}
