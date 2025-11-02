# Скрипт для первоначальной настройки проекта
# Запустите этот скрипт один раз для настройки окружения

Write-Host "=== Настройка проекта системы бронирования ===" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия виртуального окружения
if (-not (Test-Path "venv")) {
    Write-Host "Создание виртуального окружения..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Ошибка при создании виртуального окружения!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Виртуальное окружение создано" -ForegroundColor Green
} else {
    Write-Host "✓ Виртуальное окружение уже существует" -ForegroundColor Green
}

# Активация виртуального окружения
Write-Host ""
Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Установка зависимостей
Write-Host ""
Write-Host "Установка зависимостей..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Все зависимости установлены!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== Настройка завершена! ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Теперь вы можете использовать:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1 connect_db.py  - для проверки подключения" -ForegroundColor White
    Write-Host "  .\run.ps1 backend.py     - для создания таблиц" -ForegroundColor White
    Write-Host "  .\run.ps1 check_tables.py - для проверки таблиц" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ Ошибка при установке зависимостей!" -ForegroundColor Red
    exit 1
}

