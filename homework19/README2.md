### Партиционирование типа шардинг.
Разделение таблицы на непересекающиеся части одинаковой структуры, которые являются свойствами одной и той-же базовой сущности.
центральная сущность базы - строка bookings. 

шардировать будем по пк bookings (book_ref).

шардировать будем все таблицы-журналы в которых может быть book_ref, даже если его там нет:
- bookings
- tickets
- ticket_flights
- boarding_passes

Но придется добавить или пробросить значение поля book_ref в эти таблицы (ticket_flights, boarding_passes).

Процедура:
- добавление полей, и данных (формирование непартиционированных таблиц с акутальными данными).
- бекап данных
  - удаление констрейнтов мешающих удалению таблиц
  - удаление оригинальных таблиц
  - и замена их партиционированными версиями
  - заливка данных в партиционированные таблицы из бекапов.

#### формирование поля book_ref и проброс данных 
>     alter table ticket_flights add book_ref character(6);
>     
>     update ticket_flights tf set book_ref = t.book_ref from tickets t where tf.ticket_no = t.ticket_no;
>     
>     alter table boarding_passes add book_ref character(6);
>     
>     update boarding_passes bp set book_ref = tf.book_ref from ticket_flights tf where bp.ticket_no = tf.ticket_no and bp.flight_id = tf.flight_id ; 
>     UPDATE 7925812
может забрать много времени.
>     Time: 355817.523 ms (05:55.818)

#### замена исходных таблиц партиционированными версиями

##### bookings
удаление констрейнтов я производил с помощью графических инструментов, и не сохранил скриптов:

>     CREATE TABLE bookings.bookings (
>         book_ref character(6) NOT NULL,
>         book_date timestamp with time zone NOT NULL,
>         total_amount numeric(10,2) NOT NULL
>     ) PARTITION BY HASH (book_ref);
>     
>     CREATE TABLE bookings_0 PARTITION OF bookings FOR VALUES WITH (MODULUS 4, REMAINDER 0);
>     CREATE TABLE bookings_1 PARTITION OF bookings FOR VALUES WITH (MODULUS 4, REMAINDER 1);
>     CREATE TABLE bookings_2 PARTITION OF bookings FOR VALUES WITH (MODULUS 4, REMAINDER 2);
>     CREATE TABLE bookings_3 PARTITION OF bookings FOR VALUES WITH (MODULUS 4, REMAINDER 3);
>     
##### tickets 
>     insert into bookings.tickets select * from bookings.tickets_orig;
>     
>     ALTER TABLE bookings.ticket_flights drop CONSTRAINT ticket_flights_ticket_no_fkey;
>     
>     ALTER TABLE bookings.tickets_orig drop CONSTRAINT tickets_pkey;
>     
>     ALTER TABLE bookings.tickets ADD CONSTRAINT tickets_pkey PRIMARY KEY (ticket_no,book_ref); 
>        
>     ALTER TABLE bookings.ticket_flights ADD CONSTRAINT ticket_flights_ticket_no_fkey FOREIGN KEY (ticket_no,book_ref) REFERENCES tickets(ticket_no,book_ref);
>     --alter TABLE bookings.tickets rename to tickets_orig;  
>     
>     CREATE TABLE bookings.tickets (
>         ticket_no character(13) NOT NULL,
>         book_ref character(6) NOT NULL,
>         passenger_id character varying(20) NOT NULL,
>         passenger_name text NOT NULL,
>         contact_data jsonb
>     ) PARTITION BY HASH (book_ref);
>     
>     CREATE TABLE tickets_0 PARTITION OF tickets FOR VALUES WITH (MODULUS 4, REMAINDER 0);
>     CREATE TABLE tickets_1 PARTITION OF tickets FOR VALUES WITH (MODULUS 4, REMAINDER 1);
>     CREATE TABLE tickets_2 PARTITION OF tickets FOR VALUES WITH (MODULUS 4, REMAINDER 2);
>     CREATE TABLE tickets_3 PARTITION OF tickets FOR VALUES WITH (MODULUS 4, REMAINDER 3);
>     
>     
##### ticket_flights
>      
>     select * into bookings.ticket_flights_orig from bookings.ticket_flights;
>     
>     alter table boarding_passes drop constraint boarding_passes_ticket_no_fkey; 
>     drop table bookings.ticket_flights;
>     
>     CREATE TABLE bookings.ticket_flights (
>         book_ref character(6),
>         ticket_no character(13) NOT NULL,
>         flight_id integer NOT NULL,
>         fare_conditions character varying(10) NOT NULL,
>         amount numeric(10,2) NOT NULL,
>         CONSTRAINT ticket_flights_amount_check CHECK ((amount >= (0)::numeric)),
>         CONSTRAINT ticket_flights_fare_conditions_check
>         CHECK (((fare_conditions)::text = ANY (ARRAY[('Economy'::character varying)::text, ('Comfort'::character varying)::text, ('Business'::character varying)::text])))
>     ) PARTITION BY HASH (book_ref);
>     
>     
>     CREATE TABLE ticket_flights_0 PARTITION OF ticket_flights FOR VALUES WITH (MODULUS 4, REMAINDER 0);
>     CREATE TABLE ticket_flights_1 PARTITION OF ticket_flights FOR VALUES WITH (MODULUS 4, REMAINDER 1);
>     CREATE TABLE ticket_flights_2 PARTITION OF ticket_flights FOR VALUES WITH (MODULUS 4, REMAINDER 2);
>     CREATE TABLE ticket_flights_3 PARTITION OF ticket_flights FOR VALUES WITH (MODULUS 4, REMAINDER 3);
>     
>     insert into bookings.ticket_flights select book_ref, ticket_no, flight_id, fare_conditions,  amount from bookings.ticket_flights_orig;



>     select * into bookings.boarding_passes_orig from bookings.boarding_passes;
>     
>     drop table boarding_passes;
>     
>     CREATE TABLE bookings.boarding_passes (
>         book_ref character(6) NOT NULL,
>         ticket_no character(13) NOT NULL,
>         flight_id integer NOT NULL,
>         boarding_no integer NOT NULL,
>         seat_no character varying(4) NOT NULL
>     ) PARTITION BY HASH (book_ref);
>     
>     CREATE TABLE boarding_passes_0 PARTITION OF boarding_passes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
>     CREATE TABLE boarding_passes_1 PARTITION OF boarding_passes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
>     CREATE TABLE boarding_passes_2 PARTITION OF boarding_passes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
>     CREATE TABLE boarding_passes_3 PARTITION OF boarding_passes FOR VALUES WITH (MODULUS 4, REMAINDER 3);
>     
>     insert into bookings.boarding_passes select book_ref,ticket_no,flight_id,boarding_no,seat_no from bookings.boarding_passes_orig;




ошибка: 

alter table flights add book_ref character(6);
update flights f set book_ref = tf.book_ref from ticket_flights tf where f.flight_id = tf.flight_id ; 

оказалось не все перелёты были забронированы через booking-таблицу, порядка 30% перелётов не учитывались в booking. С этой таблицей приедтся работать по-особенному. 

И самое интересно - это партционирование таблицы журнала полётов:

>     select * into bookings.flights_orig from bookings.flights;
>     drop view flights_v;  
>     drop view routes;
>     drop table bookings.flights;
>     
>     таблица создается с book_ref допускающей NULL.
>     
>     CREATE TABLE bookings.flights (
>         book_ref character(6),
>         flight_id integer NOT NULL,
>         flight_no character(6) NOT NULL,
>         scheduled_departure timestamp with time zone NOT NULL,
>         scheduled_arrival timestamp with time zone NOT NULL,
>         departure_airport character(3) NOT NULL,
>         arrival_airport character(3) NOT NULL,
>         status character varying(20) NOT NULL,
>         aircraft_code character(3) NOT NULL,
>         actual_departure timestamp with time zone,
>         actual_arrival timestamp with time zone,
>         CONSTRAINT flights_check CHECK ((scheduled_arrival > scheduled_departure)),
>         CONSTRAINT flights_check1 CHECK (((actual_arrival IS NULL) OR ((actual_departure IS NOT NULL) AND (actual_arrival IS NOT NULL) AND (actual_arrival > actual_departure)))),
>         CONSTRAINT flights_status_check CHECK (((status)::text = ANY (ARRAY[('On Time'::character varying)::text, ('Delayed'::character varying)::text, ('Departed'::character varying)::text, ('Arrived'::character varying)::text, ('Scheduled'::character varying)::text, ('Cancelled'::character varying)::text])))
>     ) PARTITION BY LIST (book_ref);
>     
создаётся партиция для NULL-значений. (полёты, в которых не участвовали пассажиры, через наш booking-журнал)
>     
>     create table flights_null partition of flights for values in (NULL);

создаётся партиция для остальных значений, партиционированная по хешу book_ref. 
>     
>     CREATE TABLE bookings.flights_values partition of flights default PARTITION BY HASH (book_ref);
>     
создаются партиции для хешированных значений
>     CREATE TABLE flights_values_0 PARTITION OF flights_values FOR VALUES WITH (MODULUS 4, REMAINDER 0);
>     CREATE TABLE flights_values_1 PARTITION OF flights_values FOR VALUES WITH (MODULUS 4, REMAINDER 1);
>     CREATE TABLE flights_values_2 PARTITION OF flights_values FOR VALUES WITH (MODULUS 4, REMAINDER 2);
>     CREATE TABLE flights_values_3 PARTITION OF flights_values FOR VALUES WITH (MODULUS 4, REMAINDER 3);
>     
>     --drop table  flights
>     
>     insert into bookings.flights
>     select book_ref,flight_id,flight_no,
>     	scheduled_departure,scheduled_arrival,
>     	departure_airport,arrival_airport,status,
>     	aircraft_code,actual_departure,actual_arrival
>     from bookings.flights_orig;

распределение данных по партициям.
>     demo=# select '0', count(1) from only flights_values_0 
>     demo-# union all 
>     demo-# select '1',count(1) from only flights_values_1 
>     demo-# union all 
>     demo-# select '2',count(1) from only flights_values_2 
>     demo-# union all 
>     demo-# select '3',count(1) from only flights_values_3 
>     demo-# union all 
>     demo-# select 'N',count(1) from only flights_null;
>      ?column? | count 
>     ----------+-------
>      3        | 37488
>      0        | 37543
>      2        | 37709
>      1        | 37848
>      N        | 64279
>     (5 rows)

