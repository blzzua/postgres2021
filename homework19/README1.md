### Секционирование таблицы
Цель:

научиться секционировать таблицы.

Секционировать большую таблицу из демо базы flights
Критерии оценки:

Выполнение ДЗ: 10 баллов

Архивация журналов, то ради чего производится  партционирование.

Разбиение данных по дате. По дате мы можем разнести только следующие таблицы flights и tickets:

Проверим конфиг. опцию которая будет удалять партиции из плана
>     demo=# show enable_partition_pruning;
>      enable_partition_pruning 
>     --------------------------
>      on
>     (1 row)

переименуем таблицу  в flights_orig, чтобы вместо неё создать новую.

>     demo=# alter table flights rename to flights_orig;
>     ALTER TABLE

в таблице хранятся данные с 2016-08-14 по 2017-09-14 (scheduled_departure)

    

> create table flights(like flights_щкшп) partition by range(scheduled_departure);

сгенерируем скрипт который создаст партиции, например на 2 года от первой записи.
>     DAT_CUR="2016-08-14";
>     for i in {1..24}; do 
>         D1=$(date --date="$DAT_CUR" +"%Y-%m-01");
>         D2=$(date --date="$DAT_CUR + 1 month" +"%Y-%m-01");
>         TABLE_NAME=flights_$(date --date="$DAT_CUR + 1 month" +"%Y%m");
>         echo "create table $TABLE_NAME partition of flights for values from ('$D1') to ('$D2');"
>         DAT_CUR=$(date --date="$DAT_CUR + 1 month" +"%Y-%m-%d");
>     done

>     create table flights_201609 partition of flights for values from ('2016-08-01') to ('2016-09-01');
>     create table flights_201610 partition of flights for values from ('2016-09-01') to ('2016-10-01');
>     create table flights_201611 partition of flights for values from ('2016-10-01') to ('2016-11-01');
>     create table flights_201612 partition of flights for values from ('2016-11-01') to ('2016-12-01');
>     create table flights_201701 partition of flights for values from ('2016-12-01') to ('2017-01-01');
>     create table flights_201702 partition of flights for values from ('2017-01-01') to ('2017-02-01');
>     create table flights_201703 partition of flights for values from ('2017-02-01') to ('2017-03-01');
>     create table flights_201704 partition of flights for values from ('2017-03-01') to ('2017-04-01');
>     create table flights_201705 partition of flights for values from ('2017-04-01') to ('2017-05-01');
>     create table flights_201706 partition of flights for values from ('2017-05-01') to ('2017-06-01');
>     create table flights_201707 partition of flights for values from ('2017-06-01') to ('2017-07-01');
>     create table flights_201708 partition of flights for values from ('2017-07-01') to ('2017-08-01');
>     create table flights_201709 partition of flights for values from ('2017-08-01') to ('2017-09-01');
>     create table flights_201710 partition of flights for values from ('2017-09-01') to ('2017-10-01');
>     create table flights_201711 partition of flights for values from ('2017-10-01') to ('2017-11-01');
>     create table flights_201712 partition of flights for values from ('2017-11-01') to ('2017-12-01');
>     create table flights_201801 partition of flights for values from ('2017-12-01') to ('2018-01-01');
>     create table flights_201802 partition of flights for values from ('2018-01-01') to ('2018-02-01');
>     create table flights_201803 partition of flights for values from ('2018-02-01') to ('2018-03-01');
>     create table flights_201804 partition of flights for values from ('2018-03-01') to ('2018-04-01');
>     create table flights_201805 partition of flights for values from ('2018-04-01') to ('2018-05-01');
>     create table flights_201806 partition of flights for values from ('2018-05-01') to ('2018-06-01');
>     create table flights_201807 partition of flights for values from ('2018-06-01') to ('2018-07-01');
>     create table flights_201808 partition of flights for values from ('2018-07-01') to ('2018-08-01');

перельём данные. 
demo=# insert into flights select * from flights_orig ;
INSERT 0 214867

можно порадоваться что наши аналитические запросы стали быстрее работать, например:

количество рейсов за зиму из-в  аэропорт Домодедово, за зиму 2016-17 года (пришлось наложить дополнительное условие т.к. в оригинальной таблице есть индекс по (flight_no, scheduled_departure) который используется в простом аналитическом запросе по дате, и обнаружить что происходит выпадение неиспользуемых партиций при сканировании таблицы. 

>     demo=# explain select count(1) from flights_orig where scheduled_departure between '2016-12-01'::date and '2017-03-01'::date and 'DME' in (departure_airport, arrival_airport);
>                                                                                                     QUERY PLAN                                                                                                
>     ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
>      Finalize Aggregate  (cost=6165.23..6165.24 rows=1 width=8)
>        ->  Gather  (cost=6165.11..6165.22 rows=1 width=8)
>              Workers Planned: 1
>              ->  Partial Aggregate  (cost=5165.11..5165.12 rows=1 width=8)
>                    ->  Parallel Seq Scan on flights_orig  (cost=0.00..5151.85 rows=5307 width=0)
>                          Filter: ((scheduled_departure >= '2016-12-01'::date) AND (scheduled_departure <= '2017-03-01'::date) AND (('DME'::bpchar = departure_airport) OR ('DME'::bpchar = arrival_airport)))
>     (6 rows)

>     demo=# explain select count(1) from flights where scheduled_departure between '2016-12-01'::date and '2017-03-01'::date and 'DME' in (departure_airport, arrival_airport);
>     
>                                                                                                        QUERY PLAN                                                                                                   
>     ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
>      Finalize Aggregate  (cost=6348.68..6348.69 rows=1 width=8)
>        ->  Gather  (cost=6348.47..6348.68 rows=2 width=8)
>              Workers Planned: 2
>              ->  Partial Aggregate  (cost=5348.47..5348.48 rows=1 width=8)
>                    ->  Parallel Append  (cost=0.00..5339.01 rows=3785 width=0)
>                          Subplans Removed: 20
>                          ->  Parallel Seq Scan on flights_201702 flights_2  (cost=0.00..406.01 rows=1832 width=0)
>                                Filter: ((scheduled_departure >= '2016-12-01'::date) AND (scheduled_departure <= '2017-03-01'::date) AND (('DME'::bpchar = departure_airport) OR ('DME'::bpchar = arrival_airport)))
>                          ->  Parallel Seq Scan on flights_201701 flights_1  (cost=0.00..405.69 rows=1829 width=0)
>                                Filter: ((scheduled_departure >= '2016-12-01'::date) AND (scheduled_departure <= '2017-03-01'::date) AND (('DME'::bpchar = departure_airport) OR ('DME'::bpchar = arrival_airport)))
>                          ->  Parallel Seq Scan on flights_201704 flights_4  (cost=0.00..405.44 rows=1 width=0)
>                                Filter: ((scheduled_departure >= '2016-12-01'::date) AND (scheduled_departure <= '2017-03-01'::date) AND (('DME'::bpchar = departure_airport) OR ('DME'::bpchar = arrival_airport)))
>                          ->  Parallel Seq Scan on flights_201703 flights_3  (cost=0.00..366.73 rows=1652 width=0)
>                                Filter: ((scheduled_departure >= '2016-12-01'::date) AND (scheduled_departure <= '2017-03-01'::date) AND (('DME'::bpchar = departure_airport) OR ('DME'::bpchar = arrival_airport)))
>     (14 rows)


Однако индексы и есть проблема этого партиционирования. 
Построить тот уникальный индекс,  который по (flight_no, scheduled_departure) содержит дату - получилось, а PK в той его форме, как планировали архитекторы, суррогатный flight_id - не удаётся. т.к. у нас партиционирование по дате:

>     demo=# ALTER TABLE ONLY flights ADD CONSTRAINT part_flights_flight_no_scheduled_departure_key UNIQUE (flight_no, scheduled_departure);
>     ALTER TABLE
>     demo=# ALTER TABLE ONLY flights ADD CONSTRAINT part_flights_pkey PRIMARY KEY (flight_id);
>     ERROR:  unique constraint on partitioned table must include all partitioning columns
>     DETAIL:  PRIMARY KEY constraint on table "flights" lacks column "scheduled_departure" which is part of the partition key.

Собственно основные запросы, которые джоинятся по нему, будут работать не эффективно. Технически можно добавить их в партиции. 
>     ALTER TABLE ONLY flights_201609 ADD CONSTRAINT flights_201609_pkey PRIMARY KEY (flight_id); и т.д

Это с одной стороны всётаки даст необходимые индексы для джоина. Но уникальный flight_id необходим для консистентности данных в зависимых таблицах, а его обеспечить не удастся.

>     demo=# ALTER TABLE ONLY ticket_flights ADD CONSTRAINT part_ticket_flights_flight_id_fkey FOREIGN KEY (flight_id) REFERENCES flights(flight_id);
>     ERROR:  there is no unique constraint matching given keys for referenced table "flights"

#### вывод 
Я считаю отсутствие глобальных индексов над партиционированными таблицами - фатальный недостаток партиционирования для таких баз как эта. Записи из Журнала рейсов не могут быть удалены для обеспечения целостности данных по билетам. Надо либо отказываться от внешних ключей над партционированными таблицами, и обеспечивать целостность другими методами, например привнесение натуральных компонентов в уникальность (год и месяц даты является частью в номера рейса). Для журнала вообще можно отказаться от FK, чтобы была возможность их архивации включая удаление.
