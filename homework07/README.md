
Домашнее задание

Работа с журналами
Цель:

- уметь работать с журналами и контрольными точками
- уметь настраивать параметры журналов
- Настройте выполнение контрольной точки раз в 30 секунд.
> checkpoint_timeout = '30s'

- 10 минут c помощью утилиты pgbench подавайте нагрузку.
- Измерьте, какой объем журнальных файлов был сгенерирован за это время. Оцените, какой объем приходится в среднем на одну контрольную точку.

	 - оказывается сервер ротирует вал-логи, причём т.к. команда архивации не настроена - удаляет их.

Поэтому я настроил архивацию:

создал каталог `/var/lib/postgresql/13/wal_archive/`

добавил конфиг-опции 

>     archive_mode = on             # enables archiving; off, on, or always
>     archive_command = 'test ! -f /var/lib/postgresql/13/wal_archive/%f && cp %p /var/lib/postgresql/13/wal_archive/%f'

потом выяснил что политика удерживания "ненужных" вал-логов регулируется опцией: wal_keep_size по-умолчанию = 0 то есть не удерживать.
установил значение в 10гб
wal_keep_size = '10GB'


также узнал что 16мб размер  wal_segment_size это во время создания экземпляра, и не меняется. 

результат:

объемы вал-логов за 10 минут  pgbench даёт: 32-38 файлов по 16мб  = 512-608мб ( tps = 760 - 778 ) 

оценка не точная в связи с тем, как себя ведет ротация журнала. 

- Проверьте данные статистики: все ли контрольные точки выполнялись точно по расписанию. Почему так произошло?

  - статистика в представлении pg_stat_bgwriter
  - статистика накопительная, со времени создания экземпляра. 
  - но возможно сбросить. 

>     select pg_stat_reset();
>     select pg_stat_reset_shared('bgwriter');
> 
> SELECT total_checkpoints, seconds_since_start / total_checkpoints AS
> sec_between_checkpoints FROM (SELECT EXTRACT(EPOCH FROM (now() -
> pg_postmaster_start_time())) AS seconds_since_start,
> (checkpoints_timed+checkpoints_req) AS total_checkpoints FROM
> pg_stat_bgwriter ) AS sub;
> 
>      total_checkpoints | sec_between_checkpoints 
>     -------------------+-------------------------
>                     17 |      29.034037235294118
... выполняя несколько раз в процессе работы нагрузки, получал цифры:
>     -------------------+-------------------------
>                     21 |      28.933503523809524

(1 row)

из этого очевидно что чекпоинты происходят не в-точности по расписанию, а немного чаще.  
Причину почему чаще - не знаю. Думаю что это связано с частотой выполнения транзакций. в данном случае есть много частых транзакций.

- Сравните tps в синхронном/асинхронном режиме утилитой pgbench. Объясните полученный результат.

	- синхронный:
tps = 766.635859

	- изменяем конфиг опцию

> synchronous_commit = off
-
	- скорость началась с 2395.6, и спустя 2 минуты упала до 1200. Средняя 1427 за 10 минут, (но она бы стремилась к 1200 при более продолжительном тестировании). 



- Создайте новый кластер с включенной контрольной суммой страниц. Создайте таблицу. Вставьте несколько значений. Выключите кластер. Измените пару байт в таблице. - Включите кластер и сделайте выборку из таблицы. Что и почему произошло? как проигнорировать ошибку и продолжить работу?

>     postgres@pg-07:~$ psql -p 5434 
>     psql (13.4 (Ubuntu 13.4-4.pgdg20.04+1))
>     Type "help" for help.
>     
>     postgres=# show data_checksums ;
>      data_checksums 
>     ----------------
>      off
>     (1 row)
>     
>     postgres=# \q

- Создайте новый кластер с включенной контрольной суммой страниц. Создайте таблицу. Вставьте несколько значений. Выключите кластер. Измените пару байт в таблице. - Включите кластер и сделайте выборку из таблицы. Что и почему произошло? как проигнорировать ошибку и продолжить работу?

я с удивлением для себя обнаружил что **по-умолчанию кластер создаётся с выключенными чек-суммами**. это обескураживает.

>     postgres@pg-07:~$ /usr/lib/postgresql/13/bin/pg_checksums -c /var/lib/postgresql/13/main/
>     pg_checksums: error: data checksums are not enabled in cluster
>     
>     postgres=# show data_checksums ;
>      data_checksums 
>     ----------------
>      off
>     (1 row)

остановил сервер
для того чтобы кластер создавался с чек-суммами надо добавлять опцию --data-checksums,  специальной опции "без чек-сум" нет.
создаём кластер без чексум:

>     postgres@pg-07:~$ pg_createcluster 13 nocs 
>     Creating new PostgreSQL cluster 13/nocs ...
>     /usr/lib/postgresql/13/bin/initdb -D /var/lib/postgresql/13/nocs --auth-local peer --auth-host md5
>     The files belonging to this database system will be owned by user "postgres".
>     This user must also own the server process.
>     
>     The database cluster will be initialized with locale "C.UTF-8".
>     The default database encoding has accordingly been set to "UTF8".
>     The default text search configuration will be set to "english".
>     
>     Data page checksums are disabled.
>     
>     fixing permissions on existing directory /var/lib/postgresql/13/nocs ... ok
>     creating subdirectories ... ok
>     selecting dynamic shared memory implementation ... posix
>     selecting default max_connections ... 100
>     selecting default shared_buffers ... 128MB
>     selecting default time zone ... Etc/UTC
>     creating configuration files ... ok
>     running bootstrap script ... ok
>     performing post-bootstrap initialization ... ok
>     syncing data to disk ... ok
>     
>     Success. You can now start the database server using:
>     
>         pg_ctlcluster 13 nocs start
>     
>     Warning: systemd does not know about the new cluster yet. Operations like "service postgresql start" will not handle it. To fix,
> run:
>       sudo systemctl daemon-reload
>     Ver Cluster Port Status Owner    Data directory              Log file
>     13  nocs    5434 down   postgres /var/lib/postgresql/13/nocs /var/log/postgresql/postgresql-13-nocs.log
>     postgres@pg-07:~$ #psql -p 5434 
>     postgres@pg-07:~$ pg_ctlcluster 13 nocs start
>     Warning: the cluster will not be running as a systemd service. Consider using systemctl:
>       sudo systemctl start postgresql@13-nocs

  
сервер создался на порту  5434

>     postgres@pg-07:~$ psql -p 5434 
>     psql (13.4 (Ubuntu 13.4-4.pgdg20.04+1))
>     Type "help" for help.
>     
>     postgres=# show data_checksums ;
>      data_checksums 
>     ----------------
>      off
>     (1 row)

к счастью можно чексуммы менять, при выключенном экземпляре, но без процесса пересоздания баз/таблиц из бекапа например.

>     postgres@pg-07:~$ /usr/lib/postgresql/13/bin/pg_checksums --enable  /var/lib/postgresql/13/main/
>     Checksum operation completed
>     Files scanned:  931
>     Blocks scanned: 10555
>     pg_checksums: syncing data directory
>     pg_checksums: updating control file
>     Checksums enabled in cluster
>     postgres@pg-07:~$ /usr/lib/postgresql/13/bin/pg_checksums -c /var/lib/postgresql/13/main/
>     Checksum operation completed
>     Files scanned:  931
>     Blocks scanned: 10555
>     Bad checksums:  0
>     Data checksum version: 1
>     postgres@pg-07:~$ /usr/lib/postgresql/13/bin/pg_checksums --disable  /var/lib/postgresql/13/main/
>     pg_checksums: syncing data directory
>     pg_checksums: updating control file
>     Checksums disabled in cluster
>     postgres@pg-07:~$ /usr/lib/postgresql/13/bin/pg_checksums -c /var/lib/postgresql/13/main/
>     pg_checksums: error: data checksums are not enabled in cluster

создадим базу тест. 

>     postgres@pg-07:~$ psql -p 5434
>     psql (13.4 (Ubuntu 13.4-4.pgdg20.04+1))
>     Type "help" for help.
>     
>     postgres=# create database test;
>     CREATE DATABASE

выясним оид базы и таблицы:

>     postgres=# SELECT oid, datname FROM pg_database  where datname='test';
>       oid  | datname 
>     -------+---------
>      16851 | test
>     (1 row)
>     postgres=# \c test  
>     You are now connected to database "test" as user "postgres".
>     test=# SELECT oid FROM pg_class WHERE relname = 't1';  
>     oid  
>     -------  
>     16852  
>     (1 row)

выключим сервер и поменяем пару байт в таблице. 

стартанём сервер.  сделаем выборку.

>     postgres=# \c test
>     You are now connected to database "test" as user "postgres".
>     test=# select * from t1;
>     ERROR:  invalid page in block 0 of relation base/16851/16852

Как справиться с этой ситуацией,  я не нашёл этого, обратился к документации и интернету. 
https://pganalyze.com/docs/log-insights/server/S6
нашёл опцию zero_damaged_pages 

>     test=# alter system set zero_damaged_pages = 'on' ;
>     ALTER SYSTEM

это позволило игнорировать ошибку в первый и последующие разы, но при рестарте ошибка воспроизводилась. 
перестроил таблицу с помощью 
`vacuum full t1;`
тогда ошибка ушла, но в правильности своих действий не уверен. в текущей ситуации я заведомо уверен что масштаб ошибки всеголишь 1 таблица. её удалось "починить", в крайнем случае можно пересоздать, перелив данные которые удастся спасти. 
