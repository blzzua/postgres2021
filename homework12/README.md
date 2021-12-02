## Разворачиваем и настраиваем БД с большими данными
### Цель:
-  знать различные механизмы загрузки данных
 -   уметь пользоваться различными механизмами загрузки данных

Необходимо провести сравнение скорости работы запросов на различных СУБД

-    Выбрать одну из СУБД
-    Загрузить в неё данные (10 Гб)
-    Сравнить скорость выполнения запросов на PosgreSQL и выбранной СУБД
 -   Описать что и как делали и с какими проблемами столкнулись

Критерии оценки:

Выполнение ДЗ: 10 баллов
-    2 балла за красивое решение
-    2 балла за рабочее решение, и недостатки указанные преподавателем не устранены


#### Выбрать одну из СУБД
- Сравнить скорость выполнения запросов на PosgreSQL и выбранной СУБД
Описать что и как делали и с какими проблемами столкнулись

В порядке обзора: рассмотрел bigquery-public-data chicago_taxi_trips

сделал запросы, например:
>     SELECT count(1) as cnt_, sum(trip_total) as sum_total  , company, 
>         FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips` 
>         GROUP BY company
>         order by 1 desc
>         limit 100;

Это читает 5гб данные,  в зависимости от кеширования отрабатывает от нескольких секунд, до 1.8 сек.

#### Загрузить в неё данные (10 Гб)

##### установка postgresql

>     sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' 
>     wget --quiet -O -    https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add  -      
>     sudo apt-get update ; sudo apt-get -y install postgresql-13

- подключаем диск на 100гб, 
- создаем раздел
- форматируем
- монтируем в каталог /var/lib/postgresql/13 где располагается сервер.
- прописываем необходимые изменения в /etc/fstab чтобы он монтировался при старте операционной системы.

##### export/import dataset
- создаем bucket/каталог gs (google cloud storage) gs://pg-bigdata/chicago_taxitrips/
- экспортируем датасет в gs://pg-bigdata/chicago_taxitrips/
- создаем там каталог для данных скачанных с gc
качаю первых 40 файлов. это объем порядка 20гб

>     gsutil -m cp gs://pg-bigdata/chicago_taxitrips/data0000000000{0,1,2,3}*.csv /var/lib/postgresql/13/data/

это даст мне порядка 10 гб сырых данных.

настраиваем сервер так, чтобы побыстрее прогрузить initial load (я могу себе в этом случае позволить).

>     ALTER SYSTEM SET synchronous_commit = 'off';
>     ALTER SYSTEM SET max_wal_senders = 0; -- требует wal_level = minimal
>     ALTER SYSTEM SET wal_level = minimal;
>     ALTER SYSTEM SET fsync=off;
>     ALTER SYSTEM SET full_page_writes=off;

- для работы с table создал базу taxi 

>     create table taxi_trips (
>     unique_key text, 
>     taxi_id text, 
>     trip_start_timestamp TIMESTAMP, 
>     trip_end_timestamp TIMESTAMP, 
>     trip_seconds bigint, 
>     trip_miles numeric, 
>     pickup_census_tract bigint, 
>     dropoff_census_tract bigint, 
>     pickup_community_area bigint, 
>     dropoff_community_area bigint, 
>     fare numeric, 
>     tips numeric, 
>     tolls numeric, 
>     extras numeric, 
>     trip_total numeric, 
>     payment_type text, 
>     company text, 
>     pickup_latitude numeric, 
>     pickup_longitude numeric, 
>     pickup_location text, 
>     dropoff_latitude numeric, 
>     dropoff_longitude numeric, 
>     dropoff_location text
>     );

*причина выбора этого датасета была в том, чтобы не вычислять DDL create table* 

убедившись что загрузка отрабатывает:

>     COPY taxi_trips(unique_key, taxi_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles, pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area, fare, tips, tolls, extras, trip_total, payment_type, company, pickup_latitude, pickup_longitude, pickup_location, dropoff_latitude, dropoff_longitude, dropoff_location) 
>     FROM '/var/lib/postgresql/13/data/data000000000000.csv' DELIMITER ',' CSV HEADER;

т.к. загрузка занимает продолжительное время, порядка 30 сек файл с 630тыс записей,  я сделал truncate таблицы, и сформировал скрипт который зальет  все данные.

>     for file in /var/lib/postgresql/13/data/data*.csv; 
>     do
>     	echo -e "Processing $file file..."
>     	psql -d taxi -c "\\COPY taxi_trips(unique_key, taxi_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles, pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area, fare, tips, tolls, extras, trip_total, payment_type, company, pickup_latitude, pickup_longitude, pickup_location, dropoff_latitude, dropoff_longitude, dropoff_location) FROM '$file' DELIMITER ',' CSV HEADER;"
>     done

в таком режиме скорость заливки примерно порядка 25 сек на файл 630тыс записей. 40 файлов = 25 млн записей.


#### Описать что и как делали и с какими проблемами столкнулись.

##### Попытки работать с данными сразу-в-лоб:
>     taxi=# SELECT count(1) as cnt_, sum(trip_total) as sum_total  , company 
>         FROM taxi_trips 
>         GROUP BY company
>         order by 1 desc
>         limit 100;
>     Time: 721295.932 ms (12:01.296)


>     SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips >     group by payment_type order by 3 limit 10;
>     Time: 673418.743 ms (11:13.419)

12 и 11:13 минут. по сути всё упирается в random-чтение с диска.

попробуем ускорить?
##### pgtune
первое очевидное - pgtune в режиме DWH:

>     max_connections = 20
>     shared_buffers = 2GB
>     effective_cache_size = 6GB
>     maintenance_work_mem = 1GB
>     checkpoint_completion_target = 0.9
>     wal_buffers = 16MB
>     default_statistics_target = 500
>     random_page_cost = 1.1
>     effective_io_concurrency = 200
>     work_mem = 26214kB
>     min_wal_size = 4GB
>     max_wal_size = 16GB
>     max_worker_processes = 4
>     max_parallel_workers_per_gather = 2
>     max_parallel_workers = 4
>     max_parallel_maintenance_workers = 2

а также удаление опций для более-быстрой загрузки в ущерб durability.

>     taxi=# SELECT count(1) as cnt_, sum(trip_total) as sum_total  , company FROM taxi_trips GROUP BY company order by 1 desc limit 100;
>     ...
>     Time: 350827.237 ms (05:50.827)
>     
>     taxi=# SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by
> payment_type order by 3 limit 10;
>     ...
>     (10 rows)
>     
>     Time: 350168.151 ms (05:50.168)


основное время уходит на random read таблиц:

##### попытка использовать индексы по столбцам:
(каждый индекс создается 20+минут)

>     CREATE INDEX CONCURRENTLY  ind_trip_total ON taxi_trips (trip_total);
>     CREATE INDEX CONCURRENTLY  ind_company ON taxi_trips (company);
>     CREATE INDEX CONCURRENTLY  ind_payment_type ON taxi_trips (payment_type);
>     CREATE INDEX CONCURRENTLY  ind_tips ON taxi_trips (tips);
абсолютно не эффективно, сервер не использует индексы в таких запросах. 

- специализированные индексы для запросов:

>     CREATE INDEX CONCURRENTLY  ind_q1 ON taxi_trips (company) INCLUDE (trip_total,trip_total)
>     CREATE INDEX CONCURRENTLY  ind_q2 ON taxi_trips (payment_type) INCLUDE (tips,trip_total)


taxi=# SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by payment_type order by 3 limit 10;
 payment_type | tips_percent |    c     
--------------+--------------+----------
 Prepaid      |            0 |       76
 Way2ride     |           15 |       78
 Pcard        |            3 |     5380
 Dispute      |            0 |    14752
 Mobile       |           15 |    32744
 Prcard       |            1 |    41331
 Unknown      |            2 |    69668
 No Charge    |            2 |   125727
 Credit Card  |           17 | 10831829
 Cash         |            0 | 14871120
(10 rows)

Time: 348979.625 ms (05:48.980)
explain не показал использование индекса, а только лишь паралеллизм



SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by payment_type order by 3 limit 10;
Time: 684075.375 ms (11:24.075)

#### расширение cstore_fdw.

git clone https://github.com/citusdata/cstore_fdw

sudo apt-get -y install protobuf-c-compiler libprotobuf-c-dev

# проверка доступости pg_config в PATH
which pg_config 

sudo apt-get -y install make gcc
# по факту ошибки  cstore_fdw.c:17:10: fatal error: postgres.h: No such file or directory
sudo apt -y install postgresql-server-dev-13     

cd cstore_fdw
make ;  make install 
можно убедиться что расширение  cstore_fdw.so находится в  /usr/lib/postgresql/13/lib/cstore_fdw.so

добавляем в конфиг:
shared_preload_libraries = 'cstore_fdw'
рестарт.

CREATE EXTENSION cstore_fdw;
CREATE SERVER cstore_server FOREIGN DATA WRAPPER cstore_fdw;


-- create foreign table
CREATE FOREIGN TABLE taxi_trips_cs (
unique_key text, 
taxi_id text, 
trip_start_timestamp TIMESTAMP, 
trip_end_timestamp TIMESTAMP, 
trip_seconds bigint, 
trip_miles numeric, 
pickup_census_tract bigint, 
dropoff_census_tract bigint, 
pickup_community_area bigint, 
dropoff_community_area bigint, 
fare numeric, 
tips numeric, 
tolls numeric, 
extras numeric, 
trip_total numeric, 
payment_type text, 
company text, 
pickup_latitude numeric, 
pickup_longitude numeric, 
pickup_location text, 
dropoff_latitude numeric, 
dropoff_longitude numeric, 
dropoff_location text
)
SERVER cstore_server
OPTIONS(compression 'pglz');

COPY taxi_trips_cs(unique_key, taxi_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles, pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area, fare, tips, tolls, extras, trip_total, payment_type, company, pickup_latitude, pickup_longitude, pickup_location, dropoff_latitude, dropoff_longitude, dropoff_location) 
FROM '/var/lib/postgresql/13/data/data000000000000.csv' DELIMITER ',' CSV HEADER;


CREATE INDEX CONCURRENTLY  ind_trip_total ON taxi_trips (trip_total);
CREATE INDEX CONCURRENTLY  ind_company ON taxi_trips (company);
CREATE INDEX CONCURRENTLY  ind_tips ON taxi_trips (tips);





не забыть очистить бакет и остановить машину




запросы в режиме многопоточность


taxi=# SELECT count(1) as cnt_, sum(trip_total) as sum_total  , company FROM taxi_trips GROUP BY company order by 1 desc limit 100;
...
Time: 350827.237 ms (05:50.827)

taxi=# SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by payment_type order by 3 limit 10;
...
(10 rows)

Time: 350168.151 ms (05:50.168)


кеширование не помогает.


##### построены специальные индексы:

CREATE INDEX CONCURRENTLY  ind_q1 ON taxi_trips (company) INCLUDE (trip_total,trip_total)
CREATE INDEX CONCURRENTLY  ind_q2 ON taxi_trips (payment_type) INCLUDE (tips,trip_total)

>      taxi=# SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by payment_type order by 3 limit 10;
>       payment_type | tips_percent |    c     
>      --------------+--------------+----------
>       Prepaid      |            0 |       76
>       Way2ride     |           15 |       78
>       Pcard        |            3 |     5380
>       Dispute      |            0 |    14752
>       Mobile       |           15 |    32744
>       Prcard       |            1 |    41331
>       Unknown      |            2 |    69668
>       No Charge    |            2 |   125727
>       Credit Card  |           17 | 10831829
>       Cash         |            0 | 14871120
>      (10 rows)
>      
>      Time: 348979.625 ms (05:48.980)

explain не показал использование индекса, а только лишь паралеллизм

но не всегда.
>      SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips group by payment_type order by 3 limit 10;
>      Time: 684075.375 ms (11:24.075)


#####  4. расширение cstore_fdw
https://github.com/citusdata/cstore_fdw

>     git clone https://github.com/citusdata/cstore_fdw

согласно документации понадобится
>     sudo apt-get -y install protobuf-c-compiler libprotobuf-c-dev

>     # проверка доступости pg_config в PATH
>     which pg_config  
sudo apt-get -y install make gcc
>     # по факту ошибки  cstore_fdw.c:17:10: fatal error: postgres.h: No such file or directory
>     sudo apt -y install postgresql-server-dev-13     

непосредственно сборка:
>     cd cstore_fdw
>     make ;  make install 
можно убедиться что расширение  cstore_fdw.so находится в  /usr/lib/postgresql/13/lib/cstore_fdw.so

добавляем в конфиг:
>     shared_preload_libraries = 'cstore_fdw'
рестарт.

создаем расширение и таблицу в бд (по примеру из документации):

>     CREATE EXTENSION cstore_fdw;
>     CREATE SERVER cstore_server FOREIGN DATA WRAPPER cstore_fdw;
>     
>     -- create foreign table
>     CREATE FOREIGN TABLE taxi_trips_cs (
>     unique_key text, 
>     taxi_id text, 
>     trip_start_timestamp TIMESTAMP, 
>     trip_end_timestamp TIMESTAMP, 
>     trip_seconds bigint, 
>     trip_miles numeric, 
>     pickup_census_tract bigint, 
>     dropoff_census_tract bigint, 
>     pickup_community_area bigint, 
>     dropoff_community_area bigint, 
>     fare numeric,
>     tips numeric, 
>     tolls numeric, 
>     extras numeric, 
>     trip_total numeric, 
>     payment_type text, 
>     company text, 
>     pickup_latitude numeric, 
>     pickup_longitude numeric, 
>     pickup_location text, 
>     dropoff_latitude numeric, 
>     dropoff_longitude numeric, 
>     dropoff_location text
>     )
>     SERVER cstore_server
>     OPTIONS(compression 'pglz');
>     
>     COPY taxi_trips_cs(unique_key, taxi_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles, pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area, fare, tips, tolls, extras, trip_total, payment_type, company, pickup_latitude, pickup_longitude, pickup_location, dropoff_latitude, dropoff_longitude, dropoff_location) 
>     FROM '/var/lib/postgresql/13/data/data000000000000.csv' DELIMITER ',' CSV HEADER;

заливаем всё. 
 и проблуем
>     taxi=# SELECT payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c FROM taxi_trips_cs group by payment_type order by 3 limit 10;
>     (10 rows)
>     
>     Time: 11193.946 ms (00:11.194)
**11! секунд**, с холодным кешом. 
кеширование немного помогает: Time: 9163.143 ms (00:09.163)

второй запрос:
>     SELECT count(1) as cnt_, sum(trip_total) as sum_total  , company FROM taxi_trips_cs GROUP BY company order by 1 desc limit 100;
>     Time: 8293.151 ms (00:08.293)
8 сек тоже хороший результат. 


