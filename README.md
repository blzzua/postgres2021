#### научиться работать с Google Cloud Platform на уровне Google Compute Engine (IaaS)
#### научиться управлять уровнем изолции транзации в PostgreSQL и понимать особенность работы уровней read commited и repeatable read
#### создать новый проект в Google Cloud Platform, например postgres2021-, где yyyymmdd год, месяц и день вашего рождения (имя проекта должно быть уникально на уровне GCP)


1. регистрация в cloud.google.com
2. создание проекта.
3. дать возможность доступа к этому проекту пользователю ifti@yandex.ru с ролью Project Editor 
  - Выбрать проект. 
  - Открыть https://console.cloud.google.com/iam-admin/iam
  - IAM -> IAM -> +ADD

4.  далее создать инстанс виртуальной машины Compute Engine с дефолтными параметрами
  - Compute -> Compute Engine ->  VM instances -> Create instance 
  - Выбрать имя, натыкать нужную конфигурацию, локацию, не забыть выбрать операционную систему в разделе Boot disk (ubuntu 20.04 as current lts)
  - Create  или equivalent command line 
  
5. добавить свой ssh ключ в GCE metadata
    - compute engine -> Metadata  -> SSH Keys
    - во время генерациия имя файла ключа лучше всего использовать 
    - ssh-keygen -f ~/.ssh/google_compute_engine
Если эту опцию выполнить раньше чем создать машину, тогда нет необходимости добавлять публичный ключ на удалённый хост. ssh-add 

6.    зайти удаленным ssh (первая сессия), не забывайте про ssh-add
  - установка gcloud cli для linux (не через snap), а через apt описано в https://cloud.google.com/sdk/docs/install: 
    - добавить урл репозитория, 
    - если в репо проверка подписи, то добавить добавить ключи в операционную систему
    - ``sudo apt-get install google-cloud-sdk``
  - при первом входе необходима аутентификация:
    gcloud auth login – запускает браузер, получает токен для дальнейшей работы. 
  - ``gcloud compute ssh pg-01 ``


7. поставить PostgreSQL
    -  установка

```
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
DEBIAN_FRONTEND=noninteractive sudo apt -y install postgresql-14 
```

    -  убедимся что сервис работает:

```
root@pg-01:~# pg_lsclusters 
Ver Cluster Port Status Owner    Data directory              Log file
14  main    5432 online postgres /var/lib/postgresql/14/main /var/log/postgresql/postgresql-14-main.log
```

    - gcloud compute ssh pg-01 

 - запустить везде psql из под пользователя postgres
 - выключить auto commit

```
test=# \echo :AUTOCOMMIT
on
test=# \set AUTOCOMMIT OFF
test=# \echo :AUTOCOMMIT
OFF
```

 - зайти вторым ssh (вторая сессия)
    - gcloud compute ssh pg-01 

 - запустить везде psql из под пользователя postgres

```
# sudo su - postgres
$ psql
```

для начала создать базу

    postgres=# create database test;
    CREATE DATABASE

- сменить базу на тестовую. в обоих сессиях.

    postgres=# \c test;
    You are now connected to database "test" as user "postgres".

- выключить auto commit

    test=# \echo :AUTOCOMMIT
    on
    test=# \set AUTOCOMMIT OFF
    test=# \echo :AUTOCOMMIT
    OFF



 - сделать в первой сессии новую таблицу и наполнить ее данными create table persons(id serial, first_name text, second_name text); insert into persons(first_name, second_name) values('ivan', 'ivanov'); insert into persons(first_name, second_name) values('petr', 'petrov'); commit;


    test=# create table persons(id serial, first_name text, second_name text);
    CREATE TABLE
    test=*# insert into persons(first_name, second_name) values('ivan', 'ivanov');
    INSERT 0 1
    test=*# insert into persons(first_name, second_name) values('petr', 'petrov');
    INSERT 0 1
    test=*# commit;
    COMMIT



 - посмотреть текущий уровень изоляции: show transaction isolation level

```
test=# show transaction isolation level
test-# ;
 transaction_isolation 
-----------------------
 read committed
(1 row)
```

    - чтобы отличать сессии между собой, изменим тест приглашения в psql, по умолчанию приглашение имеет вид:

    \echo :PROMPT1
    %/%R%x%# 

    - изменим в первой сессии на 

    \set PROMPT1 'S1: %/%R%x%# '

    - во второй сессии

    \set PROMPT1 'S2: %/%R%x%# '


- начать новую транзакцию в обоих сессиях с дефолтным (не меняя) уровнем изоляции
- в первой сессии добавить новую запись insert into persons(first_name, second_name) values('sergey', 'sergeev');

```
S1: test=*# insert into persons(first_name, second_name) values('sergey', 'sergeev');
INSERT 0 1
```

- сделать select * from persons во второй сессии

```
S2: test=*# select * from persons ; 
    id | first_name | second_name 
----+------------+-------------
    1 | ivan       | ivanov
    2 | petr       | petrov
(2 rows)
```

- видите ли вы новую запись и если да то почему?
    - записи нет потому что во второй сессии уровень изоляции по-умолчанию read committed, а вставка в первой сессии не закомичена.

- завершить первую транзакцию - commit;

```
S1: test=*# commit;
COMMIT
```

- сделать select * from persons во второй сессии

```
S2: test=*# select * from persons ; 
    id | first_name | second_name 
----+------------+-------------
    1 | ivan       | ivanov
    2 | petr       | petrov
    3 | sergey     | sergeev
(3 rows)
```


- видите ли вы новую запись и если да то почему?
    - да, потому что уровень изоляции в сессии 2 read committed, а коммит был.

- завершите транзакцию во второй сессии

```
S2: test=*# commit;
COMMIT
```

- начать новые но уже repeatable read транзации - set transaction isolation level repeatable read;

```
S1: test=# set transaction isolation level repeatable read;
SET

S2: test=# set transaction isolation level repeatable read;
SET
```

- в первой сессии добавить новую запись insert into persons(first_name, second_name) values('sveta', 'svetova');

```
S1: test=*# insert into persons(first_name, second_name) values('sveta', 'svetova');
INSERT 0 1
```


- сделать select * from persons во второй сессии

```
S2: test=*# select * from persons;
    id | first_name | second_name 
----+------------+-------------
    1 | ivan       | ivanov
    2 | petr       | petrov
    3 | sergey     | sergeev
(3 rows)
```

- видите ли вы новую запись и если да то почему?
    - записи нет.

- завершить первую транзакцию - commit;

- сделать select * from persons во второй сессии

```
S2: test=*# select * from persons;
id | first_name | second_name 
----+------------+-------------
1 | ivan       | ivanov
2 | petr       | petrov
3 | sergey     | sergeev
(3 rows)
```

- видите ли вы новую запись и если да то почему?
    - записи нет. т.к. уровень изоляции repeatable read, не допускает видеть изменные данные другими транзакциями которые начались позже чем текущая, в т.ч. закоммиченные.

- завершить вторую транзакцию

- сделать select * from persons во второй сессии
- видите ли вы новую запись и если да то почему?
    - Да, запись есть, т.к. на момент запроса/открытия транзакции в сессии 2, коммит для вставки записи 4 уже произошёл.

```
S2: test=# select * from persons;
    id | first_name | second_name 
----+------------+-------------
    1 | ivan       | ivanov
    2 | petr       | petrov
    3 | sergey     | sergeev
    4 | sveta      | svetova
(4 rows)
```


- остановите виртуальную машину но не удаляйте ее
    - 👍
