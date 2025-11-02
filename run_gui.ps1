# Скрипт для запуска GUI приложения системы бронирования
# Использование: .\run_gui.ps1

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

# Проверка зависимостей
Write-Host "Проверка зависимостей..." -ForegroundColor Cyan
pip install -q -r requirements.txt

# Запуск GUI приложения
Write-Host "Запуск GUI приложения..." -ForegroundColor Green
Write-Host ("=" * 50) -ForegroundColor Gray
python main.py

