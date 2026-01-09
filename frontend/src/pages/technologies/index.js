import React from "react";
import { Container, Main } from "../../components";
import styles from "./styles.module.css";
import MetaTags from "react-meta-tags";

const Technologies = () => {
  return (
    <Main>
      <MetaTags>
        <title>Технологии — Foodgram</title>
        <meta
          name="description"
          content="Технологии проекта Foodgram: Django, DRF, Postgres, Docker, Nginx, React и CI/CD."
        />
        <meta property="og:title" content="Технологии — Foodgram" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Технологии</h1>

        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Стек проекта</h2>

            <div className={styles.text}>
              <p className={styles.textItem}>
                Ниже — основные технологии, которые используются в Foodgram, и
                за что каждая из них отвечает.
              </p>
            </div>

            <h2 className={styles.subtitle}>Backend</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <b>Python</b> — основной язык проекта
                </li>
                <li className={styles.textItem}>
                  <b>Django</b> — веб-фреймворк, модели, админка, ORM
                </li>
                <li className={styles.textItem}>
                  <b>Django REST Framework</b> — REST API, сериализация,
                  пагинация, права доступа
                </li>
                <li className={styles.textItem}>
                  <b>Djoser / Token auth</b> — регистрация, логин, токены
                </li>
                <li className={styles.textItem}>
                  <b>PostgreSQL</b> — основная база данных
                </li>
                <li className={styles.textItem}>
                  <b>Gunicorn</b> — WSGI-сервер для запуска Django
                </li>
              </ul>
            </div>

            <h2 className={styles.subtitle}>Frontend</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <b>React</b> — SPA, роутинг, компоненты, состояние
                </li>
                <li className={styles.textItem}>
                  <b>React Router</b> — маршрутизация страниц
                </li>
                <li className={styles.textItem}>
                  <b>Fetch/AJAX</b> — запросы к API
                </li>
              </ul>
            </div>

            <h2 className={styles.subtitle}>Инфраструктура</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <b>Docker</b> — контейнеризация backend / frontend / nginx /
                  db
                </li>
                <li className={styles.textItem}>
                  <b>Docker Compose</b> — запуск всех сервисов одной командой
                </li>
                <li className={styles.textItem}>
                  <b>Nginx</b> — раздача фронта, прокси для API, статика и media
                </li>
                <li className={styles.textItem}>
                  <b>Volumes</b> — хранение статики/media и сборки фронта между
                  контейнерами
                </li>
              </ul>
            </div>

            <h2 className={styles.subtitle}>Качество кода и CI/CD</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <b>Black</b> — автоформатирование Python-кода
                </li>
                <li className={styles.textItem}>
                  <b>Flake8 + плагины</b> — линтинг и стиль
                </li>
                <li className={styles.textItem}>
                  <b>isort</b> — порядок импортов
                </li>
                <li className={styles.textItem}>
                  <b>GitHub Actions</b> — линт → сборка образов → деплой на
                  сервер
                </li>
              </ul>
            </div>

            <h2 className={styles.subtitle}>Что можно улучшить дальше</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  HTTPS-терминация на Nginx/Traefik + автоматические сертификаты
                </li>
                <li className={styles.textItem}>
                  Перевод токен-авторизации на JWT
                </li>
                <li className={styles.textItem}>
                  Кэширование (например, Redis) для тяжёлых запросов
                </li>
                <li className={styles.textItem}>
                  Полноценный мониторинг и алерты (логирование, метрики)
                </li>
              </ul>
            </div>

            <div className={styles.text}>
              <p className={styles.textItem}>
                ← Вернуться на{" "}
                <a href="/recipes" className={styles.textLink}>
                  рецепты
                </a>{" "}
                или почитать{" "}
                <a href="/about" className={styles.textLink}>
                  о проекте
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      </Container>
    </Main>
  );
};

export default Technologies;
