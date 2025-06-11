import logging
import re
from bs4 import BeautifulSoup as SoupParser
from datetime import datetime, timedelta
import requests
import time

# url страницы с новостями
NEWS_SOURCE_URL = 'https://www.rbc.ru/short_news'

# Время, начиная с которого будем проверять новости (2 часа назад от текущего момента)
previous_publication_time = datetime.now() - timedelta(hours=2)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename="news.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s"
)


# Функция извлекающая детали статьи (аннотацию и время публикации) по URL
def extract_article_details(article_url):

    # Запрос
    response = requests.get(article_url)
    page_content = SoupParser(response.content, 'html.parser')

    # Поиск аннотации статьи в разных возможных местах на странице
    if page_content.find('div', class_='article__text__overview'):
        article_summary = page_content.find('div', class_='article__text__overview').text
    elif page_content.find('span', class_='MuiTypography-root MuiTypography-text quote-style-a93m3e'):
        article_summary = page_content.find(
            'span', class_='MuiTypography-root MuiTypography-text quote-style-a93m3e').text
    elif page_content.find('div', class_='article__text article__text_free'):
        article_summary = page_content.find(
            'div', class_='article__text article__text_free').find_all('p')[0].text
    else:
        article_summary = 'Недоступно'

    # Поиск времени публикации статьи
    if page_content.find('time', class_='article__header__date'):
        publication_time = datetime.strptime(
            page_content.find('time', class_='article__header__date')['content']
            .split('+')[0], '%Y-%m-%dT%H:%M:%S')
    elif page_content.find('div', class_='MuiGrid-root MuiGrid-item quote-style-1wxaqej'):
        publication_time = datetime.strptime(
            page_content.find('time')['datetime'].split('.')[0],
            '%Y-%m-%dT%H:%M:%S') + timedelta(hours=3)
    else:
        logging.warning(f"Время публикации не найдено: {article_url}")
        publication_time = datetime.now()

    return article_summary, publication_time

# Функция фильтрующая статьи по ключевым словам в заголовках
def find_relevant_articles(articles_list):

    # Список для хранения подходящих статей
    matched_articles = []

    # Поиск статей по ключевым словам
    for article in articles_list:
        article_link_tag = article.find('a', class_='item__link rm-cm-item-link js-rm-central-column-item-link')
        article_title = article.find('span', class_='normal-wrap').text

        if re.search(r'Росс\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'облас\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'Кита\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'Англи\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'США', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'санкц\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'ЦБ\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        elif re.search(r'дрон\w*', article_title):
            article_url = article_link_tag['href']
            article_details = extract_article_details(article_url)
        else:
            continue

        summary_text = article_details[0] # Извлечение основого текста статьи
        publish_time = article_details[1] # Извлечение времени публикации статьи
        formatted_publish_time = publish_time.strftime('%Y-%m-%d %H:%M:%S')

        # Добавляем статью в список
        matched_articles.append([
            article_title,
            summary_text,
            publish_time,
            article_url
        ])

        # Формируем запись и зыписываем в лог
        log_message = f"""
            Заголовок: {article_title}
            Текст: {summary_text}
            Время публикации: {formatted_publish_time}
            Ссылка: {article_url}"""
        logging.info(log_message)

    return matched_articles

# Проверяем, явялется статья новой относительно последней проверки
def verify_publication_recency(article_item):

    global previous_publication_time

    time_text = datetime.now().strftime('%Y-%m-%d') + article_item.find(
        'span', class_='item__category').text
    article_time = datetime.strptime(time_text, '%Y-%d-%m%H:%M')

    if article_time <= previous_publication_time:
        return 0, False
    return article_time, True

# Основная функция для получения и обработки новостной ленты
def fetch_news_feed():

    response = requests.get(NEWS_SOURCE_URL)
    parsed_content = SoupParser(response.content, 'html.parser')

    articles = parsed_content.find_all('div', class_='item__wrap l-col-center')
    current_article_time, is_recent = verify_publication_recency(articles[0])

    if not is_recent:
        return False, False

    relevant_articles = find_relevant_articles(articles)

    return current_article_time, relevant_articles


if __name__ == '__main__':
    iteration_count = 0
    # 16 иттераций по 15 минут = 4 часа
    while iteration_count < 16:
        latest_article_time, articles_found = fetch_news_feed()

        # Если есть новые статьи, обновляем время последней проверки
        if latest_article_time:
            previous_publication_time = latest_article_time

        iteration_count += 1
        # Пауза между проверками = 15 минут
        time.sleep(900)