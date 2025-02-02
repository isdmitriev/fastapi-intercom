# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт, который будет использовать приложение
EXPOSE 8000

# Запускаем приложение с помощью uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]