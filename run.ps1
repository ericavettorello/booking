# Скрипт для запуска Python скриптов с активацией виртуального окружения
# Использование: .\run.ps1 connect_db.py
#           или: .\run.ps1 backend.py
#           или: .\run.ps1 main.py (для GUI)

param(
    [Parameter(Mandatory=$true)]
    [string]$Script
)

# Установка кодировки для корректного отображения русского текста
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Проверка наличия виртуального окружения
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Ошибка: Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Создайте его командой: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Активация виртуального окружения
Write-Host "Активация виртуального окружения..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Проверка зависимостей (только для GUI)
if ($Script -eq "main.py" -or $Script -eq "gui.py") {
    Write-Host "Проверка зависимостей..." -ForegroundColor Cyan
    pip install -q -r requirements.txt
}

# Запуск скрипта
Write-Host "Запуск скрипта: $Script" -ForegroundColor Green
Write-Host ("=" * 50) -ForegroundColor Gray
python $Script

