# Работа с индексами, join'ами, статистикой
Цель:

    знать и уметь применять основные виды индексов PostgreSQL
    строить и анализировать план выполнения запроса
    уметь оптимизировать запросы для с использованием индексов
    знать и уметь применять различные виды join'ов
    строить и анализировать план выполенения запроса
    оптимизировать запрос
    уметь собирать и анализировать статистику для таблицы

## 1 вариант:
Создать индексы на БД, которые ускорят доступ к данным.
В данном задании тренируются навыки:

 определения узких мест
 написания запросов для создания индекса
 оптимизации Необходимо:

 Создать индекс к какой-либо из таблиц вашей БД
 Прислать текстом результат команды explain, в которой используется данный индекс
 Реализовать индекс для полнотекстового поиска
 Реализовать индекс на часть таблицы или индекс на поле с функцией
 Создать индекс на несколько полей
 Написать комментарии к каждому из индексов
 Описать что и как делали и с какими проблемами столкнулись 

в качестве базы возьмем demo-базу от postgres-pro. https://postgrespro.ru/education/demodb

>     postgres=# create database demo
>     postgres-# ;
>     CREATE DATABASE
>     postgres=# \q
>     postgres@instance-1:~$ psql -v -d demo < /tmp/demo-big-en



####  Создать индекс к какой-либо из таблиц вашей БД
#### Прислать текстом результат команды explain, в которой используется данный индекс
 
Получим самые популярные имена пассажиров, 

>     demo=# select count(1), passenger_name from tickets group by passenger_name order by 1 desc limit 10;
>      count |   passenger_name   
>     -------+--------------------
>       6755 | ALEKSANDR IVANOV
>       6365 | ALEKSANDR KUZNECOV
>       4999 | SERGEY IVANOV
>       4601 | SERGEY KUZNECOV
>       4308 | VLADIMIR IVANOV
>       3885 | ALEKSANDR POPOV
>       3843 | VLADIMIR KUZNECOV
>       3461 | TATYANA IVANOVA
>       3435 | ALEKSANDR PETROV
>       3215 | ELENA IVANOVA
>     (10 rows)
>     
>     Time: 1054.298 ms (00:01.054)

и его план:

>     demo=# explain select count(1), passenger_name from tickets group by passenger_name order by 1 desc limit 10;
>                                                    QUERY PLAN                                                
>     ---------------------------------------------------------------------------------------------------------
>      Limit  (cost=73187.34..73187.37 rows=10 width=24)
>        ->  Sort  (cost=73187.34..73230.42 rows=17232 width=24)
>              Sort Key: (count(1)) DESC
>              ->  Finalize HashAggregate  (cost=72642.65..72814.97 rows=17232 width=24)
>                    Group Key: passenger_name
>                    ->  Gather  (cost=68851.61..72470.33 rows=34464 width=24)
>                          Workers Planned: 2
>                          ->  Partial HashAggregate  (cost=67851.61..68023.93 rows=17232 width=24)
>                                Group Key: passenger_name
>                                ->  Parallel Seq Scan on tickets  (cost=0.00..61706.07 rows=1229107 width=16)

Parallel Seq Scan on tickets указывает на сканирование таблицы.  

Вообще это аналитический запрос и выгоды от построения индекса будет мало.


>     demo=# create index idx_passenger_name on tickets(passenger_name);
>     CREATE INDEX
>     demo=# explain select count(1), passenger_name from tickets group by passenger_name order by 1 desc limit 10;
>                                                                    QUERY PLAN                                                            
>     -----------------------------------------------------------------------------------------------------------------------------------------
>      Limit  (cost=41536.06..41536.08 rows=10 width=24)
>        ->  Sort  (cost=41536.06..41579.14 rows=17232 width=24)
>              Sort Key: (count(1)) DESC
>              ->  Finalize HashAggregate  (cost=40991.36..41163.68 rows=17232 width=24)
>                    Group Key: passenger_name
>                    ->  Gather  (cost=1000.43..40819.04 rows=34464 width=24)
>                          Workers Planned: 2
>                          ->  Partial GroupAggregate  (cost=0.43..36372.64 rows=17232 width=24)
>                                Group Key: passenger_name
>                                ->  Parallel Index Only Scan using idx_passenger_name on tickets  (cost=0.43..30054.79 rows=1229107  width=16)

но его использование даёт выгоду:
Time: 460.186 ms  vs  1054.298 ms (00:01.054)

>     demo=# drop index idx_passenger_name;
>     DROP INDEX


####  Реализовать индекс для полнотекстового поиска
без индекса (и с холодным кешом):

>     demo=# SELECT count(1) from tickets where passenger_name like '% IVANOV';
>      count 
>     -------
>      61040
>     (1 row)
>     Time: 50038.398 ms (00:50.038)

построим FTS-индекс:

>     CREATE INDEX fts_gist_idx_passenger_name ON tickets USING GIST (to_tsvector('english', passenger_name));
>     CREATE INDEX
>     Time: 104884.382 ms (01:44.884)
>     demo=# explain SELECT count(1) from tickets where passenger_name like '% IVANOV';
>                                             QUERY PLAN                                        
>     ------------------------------------------------------------------------------------------
>      Finalize Aggregate  (cost=65841.15..65841.16 rows=1 width=8)
>        ->  Gather  (cost=65840.93..65841.14 rows=2 width=8)
>              Workers Planned: 2
>              ->  Partial Aggregate  (cost=64840.93..64840.94 rows=1 width=8)
>                    ->  Parallel Seq Scan on tickets  (cost=0.00..64778.84 rows=24838 width=0)
>                          Filter: (passenger_name ~~ '% IVANOV'::text)
>     (6 rows)

параллельный скан всей таблицы.

>     demo=# SELECT count(1) from tickets where to_tsvector('english', passenger_name) @@ to_tsquery('english', 'IVANOV');
>      count 
>     -------
>      61040
>     (1 row)
>     
>     Time: 357.632 ms
>     
>     demo=# explain SELECT count(1) from tickets where to_tsvector('english', passenger_name) @@ to_tsquery('english', 'IVANOV');
>                                                    QUERY PLAN                                                
>     ---------------------------------------------------------------------------------------------------------
>      Aggregate  (cost=14487.59..14487.60 rows=1 width=8)
>        ->  Index Scan using fts_gist_idx_passenger_name on tickets  (cost=0.41..14450.72 rows=14749 width=0)
>              Index Cond: (to_tsvector('english'::regconfig, passenger_name) @@ '''ivanov'''::tsquery)

попробуем другой формат индексов GIN 
         

>     CREATE INDEX fts_gin_idx_passenger_name ON tickets USING GIN (to_tsvector('english', passenger_name));
>     Time: 10391.721 ms (00:10.392)
>     
>     demo=# SELECT count(1) from tickets where to_tsvector('english', passenger_name) @@ to_tsquery('english', 'IVANOV');
>      count 
>     -------
>      61040
>     (1 row)
>     
>     Time: 51.220 ms
результат настолько впечатляющий что я решил его воспроизвести с холодным кешом.
>     Time: 149.995 ms

 план:
>     demo=# explain SELECT count(1) from tickets where to_tsvector('english', passenger_name) @@ to_tsquery('english',  'IVANOV');
>                                                          QUERY PLAN                                                     
>     --------------------------------------------------------------------------------------------------------------------
>      Finalize Aggregate  (cost=16215.20..16215.21 rows=1 width=8)
>        ->  Gather  (cost=16214.99..16215.20 rows=2 width=8)
>              Workers Planned: 2
>              ->  Partial Aggregate  (cost=15214.99..15215.00 rows=1 width=8)
>                    ->  Parallel Bitmap Heap Scan on tickets  (cost=123.11..15199.62 rows=6145 width=0)
>                          Recheck Cond: (to_tsvector('english'::regconfig, passenger_name) @@  '''ivanov'''::tsquery)
>                          ->  Bitmap Index Scan on fts_gin_idx_passenger_name  (cost=0.00..119.42 rows=14749 width=0)
>                                Index Cond: (to_tsvector('english'::regconfig, passenger_name) @@ '''ivanov'''::tsquery)
>     (8 rows)
>     
>     demo=# drop index fts_gin_idx_passenger_name;
>     DROP INDEX

#### Реализовать индекс на часть таблицы или индекс на поле с функцией
 
 passenger_name представлено в виде ИМЯ ФАМИЛИЯ, разделеное пробелом. построим индекс на фамилию как split_part(passenger_name,' ',2)

>     demo=# CREATE INDEX func_idx_passenger_name ON tickets (split_part(passenger_name,' ',2));
>     CREATE INDEX
>     Time: 7496.510 ms (00:07.497)
>     
>     demo=# SELECT count(1) from tickets where split_part(passenger_name,' ',2) = 'IVANOV';
>      count 
>     -------
>      61040
>     (1 row)
>     
>     Time: 25.312 ms
>     сбросил кеш:
>     Time: 34.419 ms
>     
>     demo=# explain SELECT count(1) from tickets where split_part(passenger_name,' ',2) = 'IVANOV';
>                                                 QUERY PLAN                                            
>     --------------------------------------------------------------------------------------------------
>      Aggregate  (cost=13850.49..13850.50 rows=1 width=8)
>        ->  Bitmap Heap Scan on tickets  (cost=129.03..13813.62 rows=14749 width=0)
>              Recheck Cond: (split_part(passenger_name, ' '::text, 2) = 'IVANOV'::text)
>              ->  Bitmap Index Scan on func_idx_passenger_name  (cost=0.00..125.35 rows=14749 width=0)
>                    Index Cond: (split_part(passenger_name, ' '::text, 2) = 'IVANOV'::text)
>     (5 rows)


#### Создать индекс на несколько полей

в примере был запрос для "какие перелеты включены в билет Антонины Кузнецовой" где ранее выяснили что билет имеет ticket_no=0005432661915

>     SELECT   to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when,
>              f.departure_city || ' (' || f.departure_airport || ')' AS departure,
>              f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival,
>              tf.fare_conditions AS class,
>              tf.amount
>     FROM     ticket_flights tf
>              JOIN flights_v f ON tf.flight_id = f.flight_id
>     WHERE    tf.ticket_no = '0005432661915'
>     ORDER BY f.scheduled_departure;

получим пару пассажиров с "большим количеством перелётов" - в десятке из самых популярных,  и "нормальным" - от 10 до 20 перелётов: 

>     demo=# select count(1), passenger_name from tickets group by passenger_name order by 1 desc limit 10;
>      count |   passenger_name   
>     -------+--------------------
>       6755 | ALEKSANDR IVANOV
>       6365 | ALEKSANDR KUZNECOV
>       4999 | SERGEY IVANOV
>       4601 | SERGEY KUZNECOV
>       4308 | VLADIMIR IVANOV
>       3885 | ALEKSANDR POPOV
>       3843 | VLADIMIR KUZNECOV
>       3461 | TATYANA IVANOVA
>       3435 | ALEKSANDR PETROV
>       3215 | ELENA IVANOVA
>     (10 rows)
> 
> 
>     demo=# select count(1), passenger_name from tickets group by passenger_name having count(1) between 10 and 20 order by random()  limit 1  ;  
>      count | passenger_name  
>     -------+-----------------
>         12 | MARIANNA DENISOVA
>     (1 row)

"ELENA IVANOVA" - будет нашим "многолетающим" пассажиром. и "MARIANNA DENISOVA" - "немного летающим пассажиром"


на базе примера, построим запрос в котором вытащим инорфмацию из tickets для интересующего нас пассажира:

>     SELECT   to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when,
>              f.departure_city || ' (' || f.departure_airport || ')' AS departure,
>              f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival,
>              tf.ticket_no,
>              tf.fare_conditions AS class,
>              tf.amount
>     FROM     ticket_flights tf
>              JOIN flights_v f ON tf.flight_id = f.flight_id
>              JOIN tickets t ON t.ticket_no =  tf.ticket_no
>     WHERE    t.passenger_name = 'ELENA IVANOVA'
>     ORDER BY f.scheduled_departure;
> 

в psql,  я делал их в одну строку:
>     demo=# SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM  ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name =  'MARIANNA DENISOVA' ORDER BY f.scheduled_departure;
>     
>         when    |       departure       |        arrival        |   ticket_no   |  class   |  amount  
>     ------------+-----------------------+-----------------------+---------------+----------+----------
>      19.08.2016 | Moscow (DME)          | Bryansk (BZK)         | 0005432697630 | Economy  |  3400.00
>      26.08.2016 | Bryansk (BZK)         | Moscow (DME)          | 0005432697630 | Economy  |  3400.00
>      27.08.2016 | Novosibirsk (OVB)     | Moscow (DME)          | 0005432196813 | Economy  | 27900.00
>      16.09.2016 | Moscow (VKO)          | St. Petersburg (LED)  | 0005433794268 | Economy  |  6300.00
>      16.09.2016 | St. Petersburg (LED)  | Khabarovsk (KHV)      | 0005433794268 | Economy  | 62100.00
>      23.09.2016 | Khabarovsk (KHV)      | St. Petersburg (LED)  | 0005433794268 | Economy  | 62100.00
>      23.09.2016 | St. Petersburg (LED)  | Moscow (VKO)          | 0005433794268 | Business | 18800.00
>      09.01.2017 | Moscow (DME)          | Rostov (ROV)          | 0005432414288 | Economy  |  9200.00
>      10.01.2017 | Rostov (ROV)          | Sochi (AER)           | 0005432414288 | Economy  |  4200.00
>      14.01.2017 | Moscow (VKO)          | Perm (PEE)            | 0005434859000 | Economy  | 11700.00
>      14.01.2017 | Perm (PEE)            | Novosibirsk (OVB)     | 0005434859000 | Economy  | 16600.00
>      18.01.2017 | Sochi (AER)           | Rostov (ROV)          | 0005432414288 | Economy  |  4200.00
>      18.01.2017 | Rostov (ROV)          | Moscow (DME)          | 0005432414288 | Economy  |  9200.00
>      26.01.2017 | Novosibirsk (OVB)     | Perm (PEE)            | 0005434859000 | Economy  | 16600.00
>      26.01.2017 | Perm (PEE)            | Moscow (VKO)          | 0005434859000 | Business | 35000.00
>      09.02.2017 | Mineralnye Vody (MRV) | Moscow (DME)          | 0005433145289 | Economy  | 13000.00
>      16.02.2017 | Moscow (DME)          | Mineralnye Vody (MRV) | 0005433145289 | Economy  | 13000.00
>      16.04.2017 | Moscow (SVO)          | Cheboksary (CSY)      | 0005434456518 | Economy  |  6200.00
>      16.04.2017 | Cheboksary (CSY)      | Nizhnekamsk (NBC)     | 0005434456518 | Economy  |  3100.00
>      23.04.2017 | Nizhnekamsk (NBC)     | Cheboksary (CSY)      | 0005434456518 | Economy  |  3100.00
>      24.04.2017 | Cheboksary (CSY)      | Moscow (SVO)          | 0005434456518 | Economy  |  6200.00
>      02.05.2017 | Kaliningrad (KGD)     | Moscow (DME)          | 0005432964527 | Economy  | 11000.00
>      11.05.2017 | Moscow (DME)          | Kaliningrad (KGD)     | 0005432964527 | Economy  | 11000.00
>      21.06.2017 | Moscow (SVO)          | St. Petersburg (LED)  | 0005432103533 | Economy  |  6000.00
>      25.07.2017 | Moscow (DME)          | Nizhnevartovsk (NJC)  | 0005434480117 | Economy  | 23100.00
>      04.08.2017 | Tyumen (TJM)          | Uraj (URJ)            | 0005433367980 | Economy  |  3300.00
>      04.08.2017 | Moscow (VKO)          | Gelendzhik (GDZ)      | 0005433475710 | Economy  | 12300.00
>      04.08.2017 | Uraj (URJ)            | Moscow (DME)          | 0005433367980 | Economy  | 16700.00
>      05.08.2017 | Nizhnevartovsk (NJC)  | Moscow (DME)          | 0005434480117 | Economy  | 23100.00
>      11.08.2017 | Moscow (DME)          | Uraj (URJ)            | 0005433367980 | Economy  | 16700.00
>      12.08.2017 | Uraj (URJ)            | Tyumen (TJM)          | 0005433367980 | Economy  |  3300.00
>      17.08.2017 | Gelendzhik (GDZ)      | Moscow (VKO)          | 0005433475710 | Economy  | 12300.00
>     (32 rows)
>     
>     Time: 2733.747 ms (00:02.734)

>     SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'ELENA IVANOVA' ORDER BY f.scheduled_departure;

для ELENA IVANOVA это будет 9тыс+ записей. 
>     demo=# SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'ELENA IVANOVA' ORDER BY f.scheduled_departure;
>     Time: 8954.963 ms (00:08.955)

план:

>     demo=# explain SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'MARIANNA DENISOVA' ORDER BY f.scheduled_departure; 
>                                                              QUERY PLAN                                                         
>     ----------------------------------------------------------------------------------------------------------------------------
>      Sort  (cost=88513.22..88514.16 rows=378 width=132)
>        Sort Key: f.scheduled_departure
>        ->  Nested Loop  (cost=0.98..88497.03 rows=378 width=132)
>              Join Filter: (f.arrival_airport = ml_1.airport_code)
>              ->  Nested Loop  (cost=0.98..87709.78 rows=378 width=93)
>                    Join Filter: (f.departure_airport = ml.airport_code)
>                    ->  Nested Loop  (cost=0.98..87121.92 rows=378 width=44)
>                          ->  Nested Loop  (cost=0.56..86956.39 rows=378 width=32)
>                                ->  Seq Scan on tickets t  (cost=0.00..86288.21 rows=133 width=14)
>                                      Filter: (passenger_name = 'MARIANNA DENISOVA'::text)
>                                ->  Index Scan using ticket_flights_pkey on ticket_flights tf  (cost=0.56..4.99 rows=3 width=32)
>                                      Index Cond: (ticket_no = t.ticket_no)
>                          ->  Index Scan using flights_pkey on flights f  (cost=0.42..0.44 rows=1 width=20)
>                                Index Cond: (flight_id = tf.flight_id)
>                    ->  Materialize  (cost=0.00..4.56 rows=104 width=53)
>                          ->  Seq Scan on airports_data ml  (cost=0.00..4.04 rows=104 width=53)
>              ->  Materialize  (cost=0.00..4.56 rows=104 width=53)
>                    ->  Seq Scan on airports_data ml_1  (cost=0.00..4.04 rows=104 width=53)

 2733.747 ms (00:02.734) и  8954.963 ms (00:08.955) сек соотв. для разных пассажиров.
сканирование таблицы tickets, и все связи с помощью nested loop.
              
##### построим индекс по имени пассажира, и полю-связи ticket_no

>     demo=# create index idx_passenger_name_ticket_no on tickets(passenger_name, ticket_no);
>     Time: 19706.540 ms (00:19.707)


>     demo=# SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'MARIANNA DENISOVA' ORDER BY f.scheduled_departure;
>     (32 rows)

Time: 2.423 ms
Time: 202.284 ms -- сбросил кеш.


>     demo=# SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'ELENA IVANOVA' ORDER BY f.scheduled_departure;
Time: 126.734 ms
Time: 8204.093 ms (00:08.204) -- сбросил кеш.

Напомню тайминги без индексов:
 2733.747 ms (00:02.734) и  8954.963 ms (00:08.955) сек соотв. для разных пассажиров.

план

>     demo=# explain SELECT to_char(f.scheduled_departure, 'DD.MM.YYYY') AS when, f.departure_city || ' (' || f.departure_airport || ')' AS departure, f.arrival_city || ' (' || f.arrival_airport || ')' AS arrival, tf.ticket_no, tf.fare_conditions AS class, tf.amount FROM     ticket_flights tf JOIN flights_v f ON tf.flight_id = f.flight_id JOIN tickets t ON t.ticket_no =  tf.ticket_no WHERE    t.passenger_name = 'ELENA IVANOVA' ORDER BY f.scheduled_departure;
> 
>                                                                   QUERY PLAN                                                            
> 
>     --------------------------------------------------------------------------------------------------------------------------------------
>      Sort  (cost=23828.52..23850.34 rows=8728 width=132)
>        Sort Key: f.scheduled_departure
>        ->  Hash Join  (cost=12.21..23257.21 rows=8728 width=132)
>              Hash Cond: (f.arrival_airport = ml_1.airport_code)
>              ->  Hash Join  (cost=6.88..18624.00 rows=8728 width=93)
>                    Hash Cond: (f.departure_airport = ml.airport_code)
>                    ->  Nested Loop  (cost=1.54..18594.81 rows=8728 width=44)
>                          ->  Nested Loop  (cost=1.12..14772.63 rows=8728 width=32)
>                                ->  Index Only Scan using idx_passenger_name_ticket_no on tickets t  (cost=0.56..76.25 rows=3068 width=14)
>                                      Index Cond: (passenger_name = 'ELENA IVANOVA'::text)
>                                ->  Index Scan using ticket_flights_pkey on ticket_flights tf  (cost=0.56..4.76 rows=3 width=32)
>                                      Index Cond: (ticket_no = t.ticket_no)
>                          ->  Index Scan using flights_pkey on flights f  (cost=0.42..0.44 rows=1 width=20)
>                                Index Cond: (flight_id = tf.flight_id)
>                    ->  Hash  (cost=4.04..4.04 rows=104 width=53)
>                          ->  Seq Scan on airports_data ml  (cost=0.00..4.04 rows=104 width=53)
>              ->  Hash  (cost=4.04..4.04 rows=104 width=53)
>                    ->  Seq Scan on airports_data ml_1  (cost=0.00..4.04 rows=104 width=53)
>     (18 rows)


####  Написать комментарии к каждому из индексов

>     demo=# COMMENT ON INDEX idx_passenger_name_ticket_no IS 'JIRA-1234 Быстрый поиск перелётов по ФИО пассажира';
>     COMMENT

#### Описать что и как делали и с какими проблемами столкнулись 

Ошибки синтаксиса и "новизна" полнотекстовых индексов. Ранее не доводилось пользоваться ими. Пришлось читать документацию.
  
Поиск по функции удивил своей производительность, если быть уверенным в написании функции, которая хорошо вычленяет искомые данные, то такой вариант хорошо работает для точного поиска, и поиска по высокоселективным диапазоам. Такого нет в MS SQL. Ближайший эквивалент - построение вычислимого поля и построение индекса по нему. 

В моей практике были случаи когда таблицы имели разные, приводимые, типы полей по которым была связь join. Но из-за приведения индексы не работали, а введенная в экплуатацию функциональность съедала много CPU на сервере. И построение индекса по функции стало спасением ситуации (СУБД SAP ASE).

Составной индекс в данном примере - хорошо подходит для поиска при малом объеме, т.к. существенно ускоряет выборку из tickets. но большой набор записей увеличивает стоимость запроса в nested loop при связи ticket_flights.  Если же установить SLO/SLA на скорость выполнения запроса, то надо усекать количество выбираемых билетов/перелётов" на пассажира по какому-то признаку, например "последние 100 перелётов по дате". (административное решение),  с пейджингом остальных записей.

