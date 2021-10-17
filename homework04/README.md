

## Домашнее задание

Установка и настройка PostgteSQL в контейнере Docker

Цель:
 - установить PostgreSQL в Docker контейнере
 -    настроить контейнер для внешнего подключения

 - сделать в GCE инстанс с Ubuntu 20.04
 -  поставить на нем Docker Engine
	 - Лично мне кажется неправильным устанавливать программное обеспечение с помощью curl | bash, особенно в операционной системе с пакетным менеждером. 
Инструкция по установке пакетом есть на сайте докера. 

>     sudo apt-get update
>     sudo apt-get -y install apt-transport-https ca-certificates curl gnupg lsb-release
>     curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
>     echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg]  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
>     sudo apt-get update
>     sudo apt-get -y install docker-ce docker-ce-cli containerd.io

• сделать каталог /var/lib/postgres
> mkdir /var/lib/postgres

• развернуть контейнер с PostgreSQL 13 смонтировав в него /var/lib/postgres

>    docker run --name pg-docker --network pg-net -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 -v /var/lib/postgres:/var/lib/postgresql/data postgres:14 

• развернуть контейнер с клиентом postgres
> docker run -it --rm --network pg-net --name pg-client postgres:14 psql -h pg-docker -U postgres

• подключится из контейнера с клиентом к контейнеру с сервером и сделать
таблицу с парой строк

>     postgres=# create table t (a int);
>     CREATE TABLE
>     postgres=# insert into t values(1);
>     INSERT 0 1
>     postgres=# insert into t values(2);
>     INSERT 0 1


 - подключится к контейнеру с сервером с ноутбука/компьютера извне инстансов GCP
	 - необходимо создать правило в файрволе, которое разрешит подключаться к сервисам извне GCP. 
я решил создать правило которое разрешит подключаться к любому порту по протоколу tcp с моего компьютера.

>    gcloud compute firewall-rules create allow-tcp-from-me --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:0-65535 --source-ranges=$HOMEIP/32 --target-tags=home

   - добавить машине тег, в моём случае home. и правило применяется к этой машине, и возможно будет прицепиться к ней.  проверка:

>     oleg@home:/tmp$ psql -h 34.91.75.132  -U postgres 
>     Password for user postgres: 
>     Timing is on.
>     psql (14.0 (Ubuntu 14.0-1.pgdg20.04+1))
>     Type "help" for help.
>     
>     postgres=# select * from t;
>      a 
>     ---
>      1
>      2
>     (2 rows)
>     
>     Time: 47,304 ms

• удалить контейнер с сервером

>     root@pg-04:~# docker stop /pg-docker 
>     /pg-docker
>     root@pg-04:~# docker rm /pg-docker 
>     /pg-docker

• создать его заново
> docker run --name pg-docker --network pg-net -e  POSTGRES_PASSWORD=postgres -d -p 5432:5432 -v /var/lib/postgres:/var/lib/postgresql/data postgres:14

• подключится снова из контейнера с клиентом к контейнеру с сервером

>     root@pg-04:~# docker run -it --rm --network pg-net --name pg-client postgres:14 psql -h pg-docker -U postgres 
>     Password for user postgres: 
>     psql (14.0 (Debian 14.0-1.pgdg110+1))
>     Type "help" for help.
>     
>     postgres=# select * from t;
>      a 
>     ---
>      1
>      2
>     (2 rows)

- проверить, что данные остались на месте
  - данные на месте. 

- оставляйте в ЛК ДЗ комментарии что и как вы делали и как боролись с проблемами

