Находясь в папке infra, выполните команду docker-compose up.
При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://127.0.0.1 изучите фронтенд веб-приложения, а по адресу http://127.0.0.1/api/docs/ — спецификацию API. 

Для подключения шифрования на сервере, разворачиваем контейнеры через docker compose и выполняем из директори `infra`:

```bash
sudo docker compose exec -it nginx sh
apk add certbot certbot-nginx
certbot --nginx
```
