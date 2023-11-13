###  Проект Yatube 

Социальная сеть для публикации личных дневников

## Технологический стек:

- Python 3
- HTML
- Django
- Django ORM
- SQL
- Git
- Unittest
- Pytest
- Pillow

## Запуск проекта

Клонировать репозиторий и перейти в него в командной строке:

``` bash
 git clone git@github.com:JRushFobos/Yatube.git
```

``` bash
 cd hw05_final
```

Cоздать и активировать виртуальное окружение:

``` bash
 py -3.7 -m venv venv
```

``` bash
 source venv/Scripts/activate
```

``` bash
 python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

``` bash
 pip install -r requirements.txt
```

Выполнить миграции:

``` bash
 python manage.py makemigrations
```

``` bash
 python manage.py migrate
```

Создаем суперпользователя:

``` bash
 python manage.py createsuperuser
```

Собираем статику:

``` bash
 python manage.py collectstatic
```

Секретный ключ вынести в .env 

``` bash
SECRET_KEY='secret_key'
```

Запускаем проект:

``` bash
 python manage.py runserver
```

После чего проект будет доступен по адресу http://localhost/

## Примеры запросов:

Отображение постов и публикаций (GET, POST)

```bash
http://127.0.0.1:8000/posts/
```

Получение, изменение, удаление поста с соответствующим id (GET, PUT, PATCH, DELETE)

```bash
http://127.0.0.1:8000/posts/{id}/
```

Получение информации о подписках текущего пользователя, создание новой подписки на пользователя (GET, POST)
 
 ```bash
http://127.0.0.1:8000/posts/follow/