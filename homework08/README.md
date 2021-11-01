
### Механизм блокировок  
Цель:  
  
*понимать как работает механизм блокировок объектов и строк*  
  
- Настройте сервер так, чтобы в журнал сообщений сбрасывалась информация о блокировках, удерживаемых более 200 миллисекунд. Воспроизведите ситуацию, при которой в журнале появятся такие сообщения.  
параметр  
log_lock_waits  
  

>     postgres=# alter system set log_lock_waits = 'on';  
>     ALTER SYSTEM  
>     postgres=# alter system set deadlock_timeout = '200ms';  
>     ALTER SYSTEM  
>     postgres=# select pg_reload_conf();  
>     pg_reload_conf  
>     ----------------  
>     t  
>     (1 row)

  
- Смоделируйте ситуацию обновления одной и той же строки тремя командами UPDATE в разных сеансах. 

>     postgres=# create database locks;  
>     CREATE DATABASE  
>     postgres=# \c locks  
>     psql (14.0 (Ubuntu 14.0-1.pgdg20.04+1), server 13.4 (Ubuntu 13.4-4.pgdg20.04+1))  
>     You are now connected to database "locks" as user "postgres".  
>     locks=# create table t1 (a integer, b varchar null);  
>     CREATE TABLE  
>     locks=# insert into t1 values(1,'aaaaaaaaaaaaaaaaa');  
>     insert into t1 values(2,'bbbbbbbbbbbbbbbbb');  
>     insert into t1 values(3,'ccccccccccccccccc');  
>     INSERT 0 1  
>     INSERT 0 1  
>     INSERT 0 1

  
  
откроем одну сессию, и заблокируем все записи:  

>     locks=# begin;  
>     BEGIN  
>     locks=*# update t1 set b = b || b;  
>     UPDATE 3  
>     locks=*#

  
и откроем во второй сессии транзакцию и попробуем обновить одну из записей.  

> locks=*# update t1 set a = 4 where a = 3;

  
посмотрим в лог `/var/log/postgresql/postgresql-13-main.log`:  
  

>     2021-10-31 15:47:20.874 EET [156244] postgres@locks LOG: process 156244 still waiting for ShareLock on transaction 505 after 200.078 ms
> 
>     2021-10-31 15:47:20.874 EET [156244] postgres@locks DETAIL: Process holding the lock: 156268. Wait queue: 156244.  
>     2021-10-31 15:47:20.874 EET [156244] postgres@locks CONTEXT: while updating tuple (0,3) in relation "t1"  
>     2021-10-31 15:47:20.874 EET [156244] postgres@locks STATEMENT: update t1 set a = 4 where a = 3;

  
прерву апдейт из второй транзакции, а также закоммитим первый.  

>     ERROR: canceling statement due to user request  
>     CONTEXT: while updating tuple (0,3) in relation "t1"

  

- Изучите возникшие блокировки в представлении pg_locks и убедитесь, что все они понятны. 

- Пришлите список блокировок и объясните, что значит каждая.  

  
#### взаимоблокировки
- Воспроизведите взаимоблокировку трех транзакций. Можно ли разобраться в ситуации постфактум, изучая журнал сообщений?  
  
сделаю три файла-сценария:  
  
c1.sql:  

>     begin;  
>     update t1 set b = 'locked by 1' where a = 1;  
>     select pg_sleep(10);  
>     update t1 set b = 'locked by 1' where a = 2;  
>     commit;

  
c2.sql:  

>     begin;  
>     update t1 set b = 'locked by 2' where a = 2;  
>     select pg_sleep(10);  
>     update t1 set b = 'locked by 2' where a = 3;  
>     commit;

  
c3.sql:  

>     begin;  
>     update t1 set b = 'locked by 3' where a = 3;  
>     select pg_sleep(10);  
>     update t1 set b = 'locked by 3' where a = 1;  
>     commit;

  
c.sh (скрипт оболочки): 

>     psql -d locks -f c1.sql -L c1.log&  
>     sleep 1 ;  
>     psql -d locks -f c2.sql -L c2.log&  
>     sleep 1 ;  
>     psql -d locks -f c3.sql -L c3.log&
 
  
запустим эту конструкцию:  
> 
>     postgres@heaven:~$ ./c.sh  
>     BEGIN  
>     UPDATE 1  
>     BEGIN  
>     UPDATE 1  
>     BEGIN  
>     UPDATE 1  
>     pg_sleep  
>     ----------  
>       
>     (1 row)  
>       
>     pg_sleep  
>     ----------  
>       
>     (1 row)  
>       
>     pg_sleep  
>     ----------  
>       
>     (1 row)
> 
>     psql:c3.sql:4: ERROR: deadlock detected  
>     DETAIL: Process 156533 waits for ShareLock on transaction 507; blocked by process 156524.  
>     Process 156524 waits for ShareLock on transaction 508; blocked by process 156527.  
>     Process 156527 waits for ShareLock on transaction 509; blocked by process 156533.  
>     HINT: See server log for query details.  
>     CONTEXT: while updating tuple (0,4) in relation "t1"  
>     UPDATE 1  
>     ROLLBACK  
>     COMMIT  
>     UPDATE 1  
>     COMMIT
  
в это-же время в логе были сообщения:  
> 
> 
>     2021-10-31 15:58:52.952 EET [156524] postgres@locks LOG: process 156524 still waiting for ShareLock on transaction 508 after 200.152 ms
> 
>     2021-10-31 15:58:52.952 EET [156524] postgres@locks DETAIL: Process holding the lock: 156527. Wait queue: 156524.  
>     2021-10-31 15:58:52.952 EET [156524] postgres@locks CONTEXT: while updating tuple (0,5) in relation "t1"  
>     2021-10-31 15:58:52.952 EET [156524] postgres@locks STATEMENT: update t1 set b = 'locked by 1' where a = 2;  
>       
>     2021-10-31 15:58:53.951 EET [156527] postgres@locks LOG: process 156527 still waiting for ShareLock on transaction 509 after 200.085 ms
> 
>     2021-10-31 15:58:53.951 EET [156527] postgres@locks DETAIL: Process holding the lock: 156533. Wait queue: 156527.  
>     2021-10-31 15:58:53.951 EET [156527] postgres@locks CONTEXT: while updating tuple (0,6) in relation "t1"  
>     2021-10-31 15:58:53.951 EET [156527] postgres@locks STATEMENT: update t1 set b = 'locked by 2' where a = 3;  
>       
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks LOG: process 156533 detected deadlock while waiting for ShareLock on transaction
> 507 after 200.128 ms  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks DETAIL: Process holding the lock: 156524. Wait queue: .  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks CONTEXT: while updating tuple (0,4) in relation "t1"  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks STATEMENT: update t1 set b = 'locked by 3' where a = 1;  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks ERROR: deadlock detected  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks DETAIL: Process 156533 waits for ShareLock on transaction 507; blocked by
> process 156524.  
>     Process 156524 waits for ShareLock on transaction 508; blocked by process 156527.  
>     Process 156527 waits for ShareLock on transaction 509; blocked by process 156533.  
>     Process 156533: update t1 set b = 'locked by 3' where a = 1;  
>     Process 156524: update t1 set b = 'locked by 1' where a = 2;  
>     Process 156527: update t1 set b = 'locked by 2' where a = 3;  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks HINT: See server log for query details.  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks CONTEXT: while updating tuple (0,4) in relation "t1"  
>     2021-10-31 15:58:54.960 EET [156533] postgres@locks STATEMENT: update t1 set b = 'locked by 3' where a = 1;  
>     2021-10-31 15:58:54.961 EET [156527] postgres@locks LOG: process 156527 acquired ShareLock on transaction 509 after 1209.750 ms  
>     2021-10-31 15:58:54.961 EET [156527] postgres@locks CONTEXT: while updating tuple (0,6) in relation "t1"  
>     2021-10-31 15:58:54.961 EET [156527] postgres@locks STATEMENT: update t1 set b = 'locked by 2' where a = 3;  
>     2021-10-31 15:58:54.968 EET [156524] postgres@locks LOG: process 156524 acquired ShareLock on transaction 508 after 2216.791 ms  
>     2021-10-31 15:58:54.968 EET [156524] postgres@locks CONTEXT: while updating tuple (0,5) in relation "t1"  
>     2021-10-31 15:58:54.968 EET [156524] postgres@locks STATEMENT: update t1 set b = 'locked by 1' where a = 2;

  -  Результат:
        - Цепочка блокировок: процесс 156533 ждет -> 156524 -> 156527 -> 156533 который является также стартовым в цепочке.  
	- В дополнение в логе  есть информация какой процесс какую команду выполнял, и какую строку ожидал.  
	- Отстреленным является Process 156533: update t1 set b = 'locked by 3' where a = 1;  
  
    
    
  
- Могут ли две транзакции, выполняющие единственную команду UPDATE одной и той же таблицы (без where), заблокировать друг друга?  
    -  я думаю нет, т.к. должна произойти эскалация блокировки на таблицу и тогда объект блокировки будет единственный и его нельзя дать заблокировать одновременно двум процессам.  
    - для того чтобы такое произошло, необходимо чтобы один проесс обновлял таблицу в одном порядке( например в порядке возрастания pk или даты). другой процесс в другом порядке (например в обратном). Но это не управляется без какой-то конструкции содержащей where. (например курсор может определить порядок с помощью order by, но само обновление будет использовать where: update .. where currrent of cursor_name)
- Попробуйте воспроизвести такую ситуацию.
    - 😕
