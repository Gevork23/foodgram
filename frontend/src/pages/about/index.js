import React from "react";
import { Container, Main } from "../../components";
import styles from "./styles.module.css";
import MetaTags from "react-meta-tags";

const About = () => {
  const githubRepo = "https://github.com/Gevork23/foodgram";
  const authorLink = "https://github.com/Gevork23";

  return (
    <Main>
      <MetaTags>
        <title>О проекте — Foodgram</title>
        <meta
          name="description"
          content="Foodgram — сервис для публикации рецептов, избранного и списка покупок. О проекте, возможностях и структуре."
        />
        <meta property="og:title" content="О проекте — Foodgram" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>О проекте</h1>

        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Что такое Foodgram?</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                <b>Foodgram</b> — веб-приложение для тех, кто любит готовить и
                делиться рецептами. Здесь можно публиковать свои блюда, собирать
                подборки, подписываться на авторов и держать под рукой список
                ингредиентов для покупок.
              </p>
              <p className={styles.textItem}>
                Проект сделан как учебный, но реализован “как настоящий”: с
                отдельным backend и frontend, контейнеризацией через Docker и
                автоматическим деплоем.
              </p>
            </div>

            <h2 className={styles.subtitle}>Что умеет сайт</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  Регистрация и авторизация пользователей
                </li>
                <li className={styles.textItem}>
                  Создание, редактирование и удаление рецептов
                </li>
                <li className={styles.textItem}>
                  Добавление рецептов в <b>Избранное</b>
                </li>
                <li className={styles.textItem}>
                  Добавление рецептов в <b>Список покупок</b> и подсчёт
                  ингредиентов
                </li>
                <li className={styles.textItem}>
                  Подписки на авторов и просмотр их рецептов
                </li>
                <li className={styles.textItem}>
                  Фильтрация рецептов по тегам (завтрак / обед / ужин)
                </li>
                <li className={styles.textItem}>
                  Загрузка изображений блюд и аватаров
                </li>
              </ul>
            </div>

            <h2 className={styles.subtitle}>Как устроен проект</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Frontend — SPA (React). Backend — REST API (Django + DRF).
                Раздачу статики и проксирование API делает Nginx. Всё упаковано
                в Docker-контейнеры и поднимается через docker compose.
              </p>
              <p className={styles.textItem}>
                Это позволяет легко обновлять приложение: собираем образы,
                пушим в Docker Hub и деплоим на сервере одной командой.
              </p>
            </div>

            <h2 className={styles.subtitle}>Демо-доступ</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Для просмотра публичной части регистрация не нужна. Чтобы
                создавать рецепты и пользоваться избранным/корзиной — нужно
                войти в аккаунт.
              </p>
              <p className={styles.textItem}>
                (Если проект учебный — можно указать, что подтверждение email не
                включено.)
              </p>
            </div>
          </div>

          <aside>
            <h2 className={styles.additionalTitle}>Ссылки</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Репозиторий проекта:{" "}
                <a
                  href={githubRepo}
                  className={styles.textLink}
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub
                </a>
              </p>
              <p className={styles.textItem}>
                Автор:{" "}
                <a
                  href={authorLink}
                  className={styles.textLink}
                  target="_blank"
                  rel="noreferrer"
                >
                  Профиль GitHub
                </a>
              </p>

              <p className={styles.textItem}>
                Полезные разделы:
                <br />
                <a href="/technologies" className={styles.textLink}>
                  Технологии проекта →
                </a>
              </p>

              <h2 className={styles.additionalTitle}>Быстрый старт</h2>
              <div className={styles.text}>
                <p className={styles.textItem}>
                  Локально проект запускается через Docker Compose.
                </p>
                <p className={styles.textItem}>
                  На сервере — через образы из Docker Hub и Nginx-прокси.
                </p>
              </div>

              <h2 className={styles.additionalTitle}>Контакты</h2>
              <div className={styles.text}>
                <p className={styles.textItem}>
                  Email:{" "}
                  <a
                    className={styles.textLink}
                    href="mailto:gevork230702@mail.ru"
                  >
                    gevork230702@mail.ru
                  </a>
                </p>
              </div>
            </div>
          </aside>
        </div>
      </Container>
    </Main>
  );
};

export default About;
