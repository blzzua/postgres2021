
Репликация

Цель:

  

реализовать свой миникластер на 3 ВМ.

  

На 1 ВМ создаем таблицы test для записи, test2 для запросов на чтение.

Создаем публикацию таблицы test и подписываемся на публикацию таблицы test2 с ВМ №2.

  

На 2 ВМ создаем таблицы test2 для записи, test для запросов на чтение.

Создаем публикацию таблицы test2 и подписываемся на публикацию таблицы test1 с ВМ №1.

  

3 ВМ использовать как реплику для чтения и бэкапов (подписаться на таблицы из ВМ №1 и №2 ).

  

Небольшое описание, того, что получилось.

  

реализовать горячее реплицирование для высокой доступности на 4ВМ. Источником должна выступать ВМ №3. Написать с какими проблемами столкнулись.

  

Критерии оценки:

  

Выполнение ДЗ: 10 баллов

  

3 балла за задание со *

2 балл за красивое решение

  

2 балл за рабочее решение, и недостатки указанные преподавателем не устранены

  

Рекомендуем сдать до: 14.11.2021

Статус: не сдано

  

  

  

## реализовать свой миникластер на 3 ВМ.
создано 4 машины, т.к. намерения создать 4ю ноду для физ.репликации.
> for i in {1..4} ; do 
> gcloud compute instances create pg-0{i} --zone=europe-west4-c 
> done

- установка сервера:

>     sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' 
>     wget --quiet -O -    https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add  - 
>     sudo apt-get update ; sudo apt-get -y install postgresql-13

  

- внесем такие изменения в конфиги (это необходимо на серверах-источниках логической репликации):

>     ALTER SYSTEM SET wal_level = logical;
>     ALTER SYSTEM SET listen_addresses = '*';

- создание таблицы:

>       CREATE TABLE test( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );


- для обеспечения данными, создаём скрипт который будет вставлять записи:
>     while :
>     do
>         psql -d postgres --command "insert into test (message) values ('this message from host pg-01 at `date` ');"
>     sleep 1
>     done

Такой Скрипт будет необходим на pg-01, pg-02, отличющийся именем таблицы и информацией в message ( в которой виден источник сообщения)

- создадим логины:

>     CREATE ROLE rep_from_pg01 WITH REPLICATION LOGIN PASSWORD 'password_01';
>     CREATE ROLE rep_from_pg02 WITH REPLICATION LOGIN PASSWORD 'password_02';
>     CREATE ROLE rep_from_pg03 WITH REPLICATION LOGIN PASSWORD 'password_03';


Для возможности входа на сервер под этими логинами  в `/etc/postgresql/13/main/pg_hba.conf` добавляем:
>     host replication rep_from_pg01 10.164.0.0/16 md5
>     host replication rep_from_pg02 10.164.0.0/16 md5
>     host replication rep_from_pg03 10.164.0.0/16 md5
>     host all rep_from_pg01 10.164.0.0/16 md5
>     host all rep_from_pg02 10.164.0.0/16 md5
>     host all rep_from_pg03 10.164.0.0/16 md5

  
##### репликация
- репликация:

  - на pg-01 - источник таблицы test

>     CREATE PUBLICATION pub_pg01_test;
>     
>     ALTER PUBLICATION pub_pg01_test ADD TABLE test;
-    pg-02 приёмник.
		-  создаём целевую таблицу.

>     CREATE TABLE test( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );

- делаем подписку:

  

>     CREATE SUBSCRIPTION sub_from_pg01_test CONNECTION 'host=pg-01 port=5432 password=password_02 user=rep_from_pg02 dbname=postgres' PUBLICATION pub_pg01_test WITH (copy_data = true, enabled = true);


проверяем данные. 
их нет: не хватает привелегий на создание слотов и выливку из таблицы.

пришлось выдать (избыточные) привелегии.

>     ALTER USER rep_from_pg02 WITH SUPERUSER;

данные есть. 

  

##### создаём репликацию в обратном направлении: 

на  pg-02
вносим необходимые изменения в конфиг:

>     ALTER SYSTEM SET wal_level = logical;
>     ALTER SYSTEM SET listen_addresses = '*';

создаем логин
даём логину привелегии на выливку и создание слотов. 

> ALTER USER rep_from_pg01 WITH SUPERUSER;

- таблица + публикация:
создается на стороне публикации pg-02

>     CREATE TABLE test2( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );
>     CREATE PUBLICATION pub_pg02_test FOR TABLE test2;

- логин для подписки. в нем указываем получателя.

>     CREATE ROLE rep_from_pg02 WITH REPLICATION LOGIN PASSWORD 'password_02';
>     ALTER USER rep_from_pg02 WITH SUPERUSER;

и на стороне подписки
>     CREATE TABLE test2( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP NOT NULL );

собственно подписка:

>     CREATE SUBSCRIPTION sub_from_pg02_test CONNECTION 'host=pg-02 port=5432 password=password_01 user=rep_from_pg01 dbname=postgres' PUBLICATION pub_pg02_test WITH (copy_data = true, enabled = true);
данные есть, обновляются.



##### 3 ВМ использовать как реплику для чтения и бэкапов (подписаться на таблицы из ВМ №1 и №2 ). 

- на хостах pg-01 и pg-02 создаём логин для того чтобы с pg-03 ходил подписчик и забирал данные.

>     CREATE ROLE rep_from_pg03 WITH REPLICATION LOGIN PASSWORD 'password_03';
>     ALTER USER rep_from_pg03 WITH SUPERUSER;

- на pg-03:
	- создаем таблицы:

>     CREATE TABLE test( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP NOT NULL, replicated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );
>     CREATE TABLE test2( note_id serial PRIMARY KEY, message varchar(255) NOT NULL, created_at TIMESTAMP NOT NULL, replicated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );

я добавил поле, которое автоматически будет заполняться на стороне приёмника текущей датой.

- создаем публикации: 
	- pg-01
>     CREATE PUBLICATION pg01_test_to_pg3 FOR TABLE test;
-
	- pg-01

>     CREATE PUBLICATION pg02_test_to_pg3 FOR TABLE test2;

на pg-03 создаем подписки. используем всё те-же публикации.
>     CREATE SUBSCRIPTION sub_from_pg01_test CONNECTION 'host=pg-01 port=5432 password=password_03 user=rep_from_pg03 dbname=postgres' PUBLICATION pub_pg01_test WITH (copy_data = true, enabled = true, slot_name = 'pg01_test_to_pg3');
>     
>     CREATE SUBSCRIPTION sub_from_pg02_test2 CONNECTION 'host=pg-02 port=5432 password=password_03 user=rep_from_pg03 dbname=postgres' PUBLICATION pub_pg02_test WITH (copy_data = true, enabled = true, slot_name = 'pg02_test_to_pg3');

я переиспользовал всё те-же публикации. но это означает что я не смогу воспльзоваться теми-же слотами. приходится использовать параметр slot_name.


примеры запросов 

>     postgres=# select * from test;
>      note_id |                               message                                |         created_at         |         replicated_at         
>     ---------+----------------------------------------------------------------------+----------------------------+-------------------------------
>            1 | aaa                                                                  | 2021-11-21 14:57:59.888568 | 2021-11-21 20:38:35.910391+00
>            2 | this message from host pg-01  19634 at Sun Nov 21 15:28:11 UTC 2021  | 2021-11-21 15:28:11.531345 | 2021-11-21 20:38:35.910391+00
>            3 | this message from host pg-01  5724 at Sun Nov 21 15:29:20 UTC 2021   | 2021-11-21 15:29:20.783724 | 2021-11-21 20:38:35.910391+00
>            4 | this message from host pg-01  29881 at Sun Nov 21 15:29:21 UTC 2021  | 2021-11-21 15:29:21.833738 | 2021-11-21 20:38:35.910391+00
>     ....
>           28 | this message from host pg-01  5637 at Sun Nov 21 20:18:31 UTC 2021   | 2021-11-21 20:18:31.159144 | 2021-11-21 20:38:35.910391+00
>           29 | this message from host pg-01  12163 at Sun Nov 21 20:18:32 UTC 2021  | 2021-11-21 20:18:32.209882 | 2021-11-21 20:38:35.910391+00
>           30 | this message from host pg-01  28190 at Sun Nov 21 20:18:33 UTC 2021  | 2021-11-21 20:18:33.25682  | 2021-11-21 20:38:35.910391+00
>           31 | this message from host pg-01  13539 at Sun Nov 21 20:31:33 UTC 2021  | 2021-11-21 20:31:34.036935 | 2021-11-21 20:38:35.910391+00
>           32 | this message from host pg-01  14177 at Sun Nov 21 20:31:35 UTC 2021  | 2021-11-21 20:31:35.08669  | 2021-11-21 20:38:35.910391+00
>     (32 rows)
>     
>     postgres=# select * from test2;
>      note_id |                            message                            |         created_at         |         replicated_at         
>     ---------+---------------------------------------------------------------+----------------------------+-------------------------------
>            1 | this message from host pg-02 at Sun Nov 21 17:28:08 UTC 2021  | 2021-11-21 17:28:08.134544 | 2021-11-21 20:34:05.077356+00
>            2 | this message from host pg-02 at Sun Nov 21 17:28:09 UTC 2021  | 2021-11-21 17:28:09.19066  | 2021-11-21 20:34:05.077356+00
>            3 | this message from host pg-02 at Sun Nov 21 17:28:10 UTC 2021  | 2021-11-21 17:28:10.24399  | 2021-11-21 20:34:05.077356+00
>     (3 rows)




##### реализовать горячее реплицирование для высокой доступности на 4ВМ. 
- Источником должна выступать ВМ №3. -
- Написать с какими проблемами столкнулись.
  
разворачиваем хост pg-04. он будет физической репликацией pg-03
создаем экземпляр. останавливаем. удаляем его данные.
`rm -rf /var/lib/postgresql/13/main/*`

- создаём логин для бекапа (и дальнейшей репликации) на pg-03
>     postgres=# CREATE ROLE rep_from_pg04 WITH REPLICATION LOGIN PASSWORD 'password_04';
и разрешаем ходить с того хоста:
>     host    replication     rep_from_pg04   10.164.0.0/16            md5

находясь на pg-04 в каталоге для данных  делаем бекап с pg-03
>     cd /var/lib/postgresql/13/main/
>     
>     postgres@pg-04:~/13/main$ pg_basebackup -h pg-03 -p 5432 -U rep_from_pg04 -R -D /var/lib/postgresql/13/main
>     Password: 
>     postgres@pg-04:~/13/main$ ls -la 
>     total 224
>     drwx------ 19 postgres postgres   4096 Nov 21 23:09 .
>     drwxr-xr-x  3 postgres postgres   4096 Nov 21 14:44 ..
>     -rw-------  1 postgres postgres      3 Nov 21 23:09 PG_VERSION
>     -rw-------  1 postgres postgres    224 Nov 21 23:09 backup_label
>     ...
>     drwx------  3 postgres postgres   4096 Nov 21 23:09 pg_wal
>     drwx------  2 postgres postgres   4096 Nov 21 23:09 pg_xact
>     -rw-------  1 postgres postgres    379 Nov 21 23:09 postgresql.auto.conf
>     -rw-------  1 postgres postgres      0 Nov 21 23:09 standby.signal

    
добавляем в postgresql.auto.conf конфигурацию 
>     hot_standby = 'on'
также обращаем внимание на то, что там есть строка о том с какого сервера каким образом  подписаться на 
>     primary_conninfo = 'user=rep_from_pg04 password=password_04 channel_binding=prefer host=''pg-03'' port=5432 sslmode=prefer sslcompression=0 sslsni=1 ssl_min_protocol_version=TLSv1.2 gssencmode=prefer krbsrvname=postgres target_session_attrs=any'

проверим работу репликации. дадим нагрузку, и проверим как изменяются кол-во записей.


>     postgres=# select count(1) from test;
>      count 
>     -------
>         44
>     (1 row)
>     
>     postgres=# select count(1) from test;
>      count 
>     -------
>         47
>     (1 row)
>     
>     postgres=# select count(1) from test2;
>      count 
>     -------
>         13
>     (1 row)
>     
>     postgres=# select count(1) from test2;
>      count 
>     -------
>         17
>     (1 row)

работает. 

проверим рид-онли.

>     postgres=# update test set message = 'test4' ;
>     ERROR:  cannot execute UPDATE in a read-only transaction

также добавим некоторые конфигурации, чтобы накатывание не убивало неочень продолжительные транзакции которые, мешают восстанавливать лог.

>     postgres=# alter system set max_standby_archive_delay = '4h';
>     ALTER SYSTEM
>     postgres=# alter system set max_standby_streaming_delay = '4h';
>     ALTER SYSTEM
>     postgres=# alter system set hot_standby_feedback  = 'on';
>     ALTER SYSTEM

##### ошибки:

1. чтобы оперировать именами а не ип-адресами, хотел записать на хосты в /etc/hosts такие строки (адреса получил из консоли)
pg-01   10.164.0.11
pg-02   10.164.0.12
pg-03   10.164.0.13
pg-04   10.164.0.14

но  оказывается  это лишнее. в GCP реализован механизм, чтобы резолвить хосты по имени.
в /etc/resolv.conf добавлена строка вида:
search search ZONE.c.PROJECT_ID.internal. c.PROJECT_ID.internal. google.internal. 
что позволяет распознавать имена машин в одной зоне, и проекте.

2. нужно настроить сервер так, чтобы слушать порт не на localhost. а интерфейс с (например) внутренним IP адресом.

3. логинам подписок нужно прописать как replication, так и просто право подключаться к базе pg_hba.conf 

4. необходимые привелегии логину подписки, на создание слота репликации, на стороне публикациии, и выливки COPY.
диагностируется ошибками в логе 

>     2021-11-21 16:22:17.240 UTC [6758] rep_from_pg02@postgres DETAIL:  There are no running transactions.
>     2021-11-21 16:22:17.240 UTC [6758] rep_from_pg02@postgres STATEMENT:  CREATE_REPLICATION_SLOT "sub_from_pg01_test_16399_sync_16392" TEMPORARY LOGICAL pgoutput USE_SNAPSHOT
>     2021-11-21 16:22:17.244 UTC [6758] rep_from_pg02@postgres ERROR:  permission denied for table test
>     2021-11-21 16:22:17.244 UTC [6758] rep_from_pg02@postgres STATEMENT:  COPY public.test TO STDOUT

5. первые попытки переиспользовать публикацию
>     postgres=# CREATE SUBSCRIPTION sub_from_pg01_test CONNECTION 'host=pg-01 port=5432 >     password=password_03 user=rep_from_pg03 dbname=postgres' PUBLICATION pub_pg02_test WITH >     (copy_data = true, enabled = true);
>     ERROR:  could not create replication slot "sub_from_pg01_test": ERROR:  replication slot "sub_from_pg01_test" already exists

дальнейшие попытки неуспешны, 
>     CREATE SUBSCRIPTION sub_from_pg01_test CONNECTION 'host=pg-01 port=5432 password=password_03 user=rep_from_pg03 dbname=postgres' PUBLICATION pub_pg02_test WITH (copy_data = true, enabled = true, slot_name = 'pg01_test_to_pg3');

но лишь потому что я ошибся в имени публикации pub_**pg02**_test на которую подписываюсь (а надо было на pub_**pg01**_test)

А так успешно работает несколько подписок на одну публикацию (как и должно быть).

Также успешно работает ситуация когда в целевая таблица имеет лишнее поле, но с default-значением (или null).

5. не забыть остановить ноды:
gcloud compute instances stop pg-0{1..4} 
No zone specified. Using zone [europe-west4-c] for instances: [pg-01, pg-02, pg-03, pg-04].




