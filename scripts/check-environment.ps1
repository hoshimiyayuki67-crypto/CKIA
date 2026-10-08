$ErrorActionPreference = 'Continue'
$tools = @('py', 'python', 'flutter', 'git', 'docker')
foreach ($tool in $tools) {
    $command = Get-Command $tool -ErrorAction SilentlyContinue
    if ($command) {
        Write-Output "$tool : $($command.Source)"
    } else {
        Write-Output "$tool : NOT FOUND"
    }
}
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -0p
}
if (Get-Command flutter -ErrorAction SilentlyContinue) {
    & flutter --version
}
Write-Output 'Target: Python 3.11 + Flutter 3.x + Android SDK. Docker is optional for local development.'
