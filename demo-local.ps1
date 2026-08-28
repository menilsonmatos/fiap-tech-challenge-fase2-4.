$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} else {
    throw "Python 3.11 ou superior nao foi encontrado. Instale em https://www.python.org/downloads/ e execute novamente."
}

$env:PYTHONPATH = Join-Path $projectRoot "src"
& $python -m unittest discover -s tests -v

$demoOutput = Join-Path $projectRoot "demo-output"
& $python -m alfabetizacao_pipeline.cli batch `
    --source data/source/indicador_alfabetizacao.csv `
    --output $demoOutput
& $python -m alfabetizacao_pipeline.cli simulate-stream `
    --events data/source/eventos_indicadores.jsonl `
    --output $demoOutput

Write-Host ""
Write-Host "Demonstracao concluida com sucesso." -ForegroundColor Green
Write-Host "Resultados: $demoOutput"
Write-Host "Gold por UF: $demoOutput\gold\indicadores_uf.csv"
Write-Host "Ranking municipal: $demoOutput\gold\ranking_vulnerabilidade.csv"
