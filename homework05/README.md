Домашнее задание

Работа с базами данных, пользователями и правами
Цель:

создание новой базы данных, схемы и таблицы
создание роли для чтения данных из созданной схемы созданной базы ### данных
создание роли для чтения и записи из созданной схемы созданной базы данных

1. создайте новый кластер PostgresSQL 13 (на выбор - GCE, CloudSQL)
	- Выбрал CloudSQL 
	pg-05-permissions 

2. зайдите в созданный кластер под пользователем postgres
	- для возможности аутентификации необходимо обеспечить доступ к субд. простейший метод это разрешить сеть для инстанса. 
	- зайти в его настройки -> connections. -> отметить галочку public IP 
	- а также, там же. add network: 
	-> authorized network,  name + cidr сети. /32 - для сети из одного хоста.
3. создайте новую базу данных testdb
	
```
postgres=> create database testdb;
CREATE DATABASE
postgres=> \l testnm
                             List of databases
  Name  |  Owner   | Encoding |  Collate   |   Ctype    | Access privileges 
--------+----------+----------+------------+------------+-------------------
 testnm | postgres | UTF8     | en_US.UTF8 | en_US.UTF8 | 
(1 row)
```

4. зайдите в созданную базу данных под пользователем postgres

```
postgres=> \c testnm
psql (14.0 (Ubuntu 14.0-1.pgdg20.04+1), server 13.3)
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
You are now connected to database "testnm" as user "postgres".
```

5. создайте новую схему testnm

```
testnm=> create schema testnm;
CREATE SCHEMA
```

6. создайте новую таблицу t1 с одной колонкой c1 типа integer

```
testnm=# create table t1 (c1 int);
CREATE TABLE
```

7. вставьте строку со значением c1=1

```
testnm=# insert into t1 values(1);
INSERT 0 1
```

8. создайте новую роль readonly

```
testnm=> CREATE ROLE readonly;
CREATE ROLE
```

9. дайте новой роли право на подключение к базе данных testdb

```
testnm=> GRANT CONNECT ON DATABASE testnm TO readonly;
GRANT
```

10. дайте новой роли право на использование схемы testnm

```
testnm=> GRANT USAGE ON SCHEMA testnm TO readonly;
GRANT
```

11. дайте новой роли право на select для всех таблиц схемы testnm

```
testnm=> GRANT SELECT ON ALL TABLES IN SCHEMA testnm TO readonly;
GRANT
```

12. создайте пользователя testread с паролем test123

```
postgres=> create role testread with LOGIN PASSWORD 'test123';
CREATE ROLE
```

13. дайте роль readonly пользователю testread

```postgres=> grant readonly to testread;
GRANT ROLE
```

14. зайдите под пользователем testread в базу данных testdb
 - тут только я и заметил что я базу создал с именем testnm. 
решил её переименовать. 
```
postgres=> alter database testnm rename to testdb;
postgres=>\q
ALTER DATABASE
postgres@heaven:~$ psql -h 34.147.33.164 -U testread -d testdb; 
Password for user testread: 
psql (14.0 (Ubuntu 14.0-1.pgdg20.04+1), server 13.3)
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
Type "help" for help.
```

15. сделайте select * from t1;

```
testdb=> select * from t1;
ERROR:  permission denied for table t1
```

16. получилось? (могло если вы делали сами не по шпаргалке и не упустили один существенный момент про который позже)
 - недостаточно прав.
17. напишите что именно произошло в тексте домашнего задания
  - нет права на селект
18. у вас есть идеи почему? ведь права то дали?
  -  предположительно потому, что права дали на таблицы в схеме testnm, а t1 находится в схеме public
19. посмотрите на список таблиц

```
testdb=> \d+
                                     List of relations
 Schema | Name | Type  |  Owner   | Persistence | Access method |    Size    | Description 
--------+------+-------+----------+-------------+---------------+------------+-------------
 public | t1   | table | postgres | permanent   | heap          | 8192 bytes | 
(1 row)
```

20. подсказка в шпаргалке под пунктом 20
21. а почему так получилось с таблицей (если делали сами и без шпаргалки то может у вас все нормально)
   - потому что это дефолтная схема для моего пользователя, для новой базы.
22. вернитесь в базу данных testdb под пользователем postgres

23. удалите таблицу t1
```
testdb=> drop table t1;
DROP TABLE
```

24. создайте ее заново но уже с явным указанием имени схемы testnm

```
testdb=> create table testnm.t1 (c1 int);
CREATE TABLE
```

25. вставьте строку со значением c1=1

```
testdb=> insert into testnm.t1 values(1);
INSERT 0 1
```
26. зайдите под пользователем testread в базу данных testdb

27. сделайте select * from testnm.t1;
```
testdb=> select * from testnm.t1;
ERROR:  permission denied for table t1
```

28. получилось?
  -  нет
29. есть идеи почему? если нет - смотрите шпаргалку
  -  таблица была создана после того как выдались права. * без подглядывания в шпаргалку*
30. как сделать так чтобы такое больше не повторялось? если нет идей - смотрите шпаргалку
  - выдать права роли по-умолчанию на схему(чтобы не выдавать права при пересоздании таблиц. для уже созданных таблиц необходимо еще раз выдать права на селект для роли.
```
testdb=> GRANT SELECT ON ALL TABLES IN SCHEMA testnm TO readonly;
GRANT
```
31. сделайте select * from testnm.t1;
```
testdb=> select * from testnm.t1;
 c1 
----
  1
(1 row)
```

32. получилось?
 - да(
33. есть идеи почему? если нет - смотрите шпаргалку
31. сделайте select * from testnm.t1;
32. получилось?
33. ура!

34. теперь попробуйте выполнить команду create table t2(c1 integer); insert into t2 values (2);
```
testdb=> create table t2(c1 integer); insert into t2 values (2);
CREATE TABLE
INSERT 0 1
```
35. а как так? нам же никто прав на создание таблиц и insert в них под ролью readonly?
 - дефолтные права схеме public. 
36. есть идеи как убрать эти права? если нет - смотрите шпаргалку
 - пришлось обратиться к шпаргалке, найти команды
```
revoke CREATE on SCHEMA public FROM public; 
revoke all on DATABASE testdb FROM public
```

37. если вы справились сами то расскажите что сделали и почему, если смотрели шпаргалку - объясните что сделали и почему выполнив указанные в ней команды
```
+5 неуспешных попыток отобрать права, преимущественно правами.
testdb=> ALTER DEFAULT PRIVILEGES IN SCHEMA public revoke ALL ON TABLES FROM testread ;
ALTER DEFAULT PRIVILEGES

testdb=> revoke create on schema public from testread;
REVOKE
testdb=> revoke create on schema public from readonly;
REVOKE
```

38. теперь попробуйте выполнить команду create table t3(c1 integer); insert into t2 values (2);
```
testdb=> create table t7(c1 integer); insert into t2 values (2);
ERROR:  permission denied for schema public
```
39. расскажите что получилось и почему 
- Наконец-то отобрал права. 
