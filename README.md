<h2>ATOLL BACKEND</h2>

<h4>front: https://github.com/PirateThunder/atoll_front.git </h4>
<h4>mobile: https://github.com/BrightOS/AtollMobile.git </h4>

<h4>Реализованная функциональность</h4>
<ul>
    <li>Авторизация(Header Token)</li>
    <li>Аутентификация/Регистрация</li>
    <li>Личный кабинет спортсмена</li>
    <li>Личный кабинет администратора</li>
    <li>Личный кабинет партнёра</li>
    <li>Личный кабинет представителя</li>
    <li>Блок просмотра мероприятий</li>
    <li>Блок просмотра пользователей</li>
    <li>Просмотр заявок на создание мероприятий</li>
    <li>Просмотр отзывов</li>
    <li>Просмотр рейтингов мероприятия</li>
    <li>Профиль</li>
    <li>Возможность изменения профиля</li>
    <li>Возможность изменения роли</li>
    <li>Возможность скачать мобильное приложение</li>
    <li>Система уведомлений через телеграм</li>
    <li>Система уведомлений на почту</li>
</ul>

<h4>Основной стек технологий:</h4>
<ul>
    <li>python3.11</li>
    <li>FastAPI</li>
    <li>mongodb</li>
    <li>motor</li>
    <li>nginx</li>
    <li>ubuntu22</li>
    <li>certbot</li>
    <li>pydantic</li>
    <li>uvicorn</li>
    <li>nginx</li>
    <li>systemd</li>
 </ul>


# Демо к сайту
<p>Демо сервиса доступно по адресу: https://atoll.divarteam.ru/</p>

<p>dbarov3@gmail.com - sportsman</p>
<p>ilyakhakimov03@gmail.com - partner</p>
<p>sabarsenrash@gmail.com - admin</p>
<p>recrea.tor@yandex.ru - representative</p>
<p>ermolovivan2018@gmail.com> - sportsman</p>

<p>code = 1111 для всех</p>


# Демо к API
<p>Демо сервиса доступно по адресу: https://api.atoll.divarteam.ru/docs</p>

<p>dbarov3@gmail.com - sportsman, test_token = 1111</p>
<p>ilyakhakimov03@gmail.com - partner, test_token = 2222</p>
<p>sabarsenrash@gmail.com - admin, test_token = 3333</p>
<p>recrea.tor@yandex.ru - representative, test_token = 4444</p>
<p>ermolovivan2018@gmail.com> - sportsman, test_token = 5555</p>


СРЕДА ЗАПУСКА
------------
1) Ubuntu 22
2) ASGI(uvicorn)
3) MongoDB,
4) Nginx
5) Python3.11


УСТАНОВКА
------------
###
Настройка системы
~~~
sudo apt update
sudo apt upgrade
apt autoremove
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11
~~~
Создаём пользователя
~~~
adduser atoll_back
usermod -aG sudo atoll_back
su - atoll_back
~~~

Установка poetry
~~~
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="/home/conductor/.local/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="/home/conductor/.local/bin:$PATH"' >> ~/.profile
poetry config virtualenvs.in-project true
exec "$SHELL"
poetry --version
~~~

Установка репозитория
~~~
git clone git@github.com:papergoldbag/atoll_back.git
cd atoll_back
poetry env use python3.11
poetry install
~~~

Нужно создать файл .env и поместить туда
~~~
mongo_host=
mongo_port=
mongo_db_name=
mongo_user=
mongo_password=
mongo_auth_db=

tg_bot_token=
vk_bot_token=

mailru_login=
mailru_password=
mailru_server="smtp.mail.ru"
mailru_port=465
~~~


### База данных
Установка
~~~
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl daemon-reload
sudo systemctl enable mongod
sudo systemctl restart mongod
~~~

Создание доступа
~~~
mongosh
use admin
db.createUser({
  user: "admin",
  pwd: passwordPrompt(),
  roles:[{role: "userAdminAnyDatabase" , db:"admin"}]
})
db.createUser(
{
  user: "root",
  pwd: passwordPrompt(),
  roles: ["root"]
})
db.createUser(
{
  user: "atoll",
  pwd: passwordPrompt(),
  roles: [
  {role: "readWrite", db: "prod"}
  ]
})

...
~~~


### API как сервис
Нужно скопировать файл conductor.service в /etc/systemd/system/conductor.service
~~~
sudo cp ./api.service /etc/systemd/system/api.service
sudo systemctl start api
~~~


### Бот как сервис
Нужно скопировать файл conductor_bot.service в /etc/systemd/system/conductor_bot.service
~~~
sudo cp ./tg_bot.service /etc/systemd/system/tg_bot.service
sudo systemctl start tg_bot
~~~


### Настройка Proxy Nginx
Установка
~~~
sudo apt install nginx
~~~
Конфигурация
~~~
rm -rf /etc/nginx/sites-enabled/default
sudo cp ./conductor.nginx /etc/nginx/sites-enabled/conductor
~~~
Перезапуск
~~~
sudo systemctl restart nginx
~~~


### Запуск системы через Docker
Систему также возможно запустить через Docker


### РАЗРАБОТЧИКИ
<h4>Илья Хакимов - Frontend https://t.me/ilyakhakimov03 </h4>
<h4>Денис Шайхльбарин - Android https://t.me/BrightOS </h4>
<h4>Арсен Сабирзянов - Backend https://t.me/arpakit </h4>
<h4>Иван Ермолов - Data-Scientist https://t.me/ivan_20190721 </h4>
<h4>Рустам Афанасьев - Project manager, Analytic https://t.me/rcr_tg </h4>
