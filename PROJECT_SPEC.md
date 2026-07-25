# Vancouver Rideshare Event Tracker (MVP)

## Мета
Сервіс для водіїв таксі/Uber у Ванкувері (Lower Mainland), який збирає події з Luma/Meetup, фільтрує за часом завершення та відображає їх на Google Maps.

## Архітектура
1. **Scraper (Python):** Збирає події через API/JSON Luma, отримує координати, час початку/завершення.
2. **Database (PostgreSQL / PostGIS):** Зберігає події та їх геопозиції.
3. **Web Frontend/Backend (FastAPI + HTML/JS або Next.js):** Відображає карту з маркерами подій на поточний день.

## Завдання для АІ-агента
1. Налаштувати `docker-compose.yml` для підняття бази даних, скрапера та веб-сервера.
2. Написати базовий Python-скрипт для парсингу Luma JSON/Next.js даних.
3. Створити просту веб-сторінку з Google Maps API.
