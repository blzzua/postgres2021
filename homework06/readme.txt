Домашнее задание

Настройка autovacuum с учетом оптимальной производительности
Цель:

    запустить нагрузочный тест pgbench
    настроить параметры autovacuum для достижения максимального уровня устойчивой производительности

    создать GCE инстанс типа e2-medium и standard disk 10GB
    установить на него PostgreSQL 13 с дефолтными настройками
    применить параметры настройки PostgreSQL из прикрепленного к материалам занятия файла

параметры:
max_connections = 40
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 500
random_page_cost = 4
effective_io_concurrency = 2
work_mem = 6553kB
min_wal_size = 4GB
max_wal_size = 16GB


проверяем какие конфиги включаются в головной конфиг-файл:
postgres@heaven:~$ grep include /etc/postgresql/13/main/postgresql.conf 
                                        # can include strftime() escapes
include_dir = 'conf.d'                  # include files ending in '.conf' from
#include_if_exists = '...'              # include file only if it exists
#include = '...'                        # include file

добавляем в каталог include_dir файл с именем например:
/etc/postgresql/13/main/conf.d/01-pgbench.conf
если сделать так, то создавая файлы типа 02-name.conf можно именовать изменения, и сделать так, чтобы нумерация сделала так что более позднее изменение переприменяло предыдущие.
рестарт экземпляра. 
лично у меня в проде центос, и конфиги лежат прямо рядом с файлами бд.




    зайти под пользователем postgres - sudo su postgres
    выполнить pgbench -i postgres

postgres@heaven:~$ pgbench -i postgres 
dropping old tables...
NOTICE:  table "pgbench_accounts" does not exist, skipping
NOTICE:  table "pgbench_branches" does not exist, skipping
NOTICE:  table "pgbench_history" does not exist, skipping
NOTICE:  table "pgbench_tellers" does not exist, skipping
creating tables...
generating data (client-side)...
100000 of 100000 tuples (100%) done (elapsed 0.09 s, remaining 0.00 s)
vacuuming...
creating primary keys...
done in 0.55 s (drop tables 0.00 s, create tables 0.02 s, client-side generate 0.32 s, vacuum 0.10 s, primary keys 0.11 s).
postgres@heaven:~$ 


    запустить pgbench -c8 -P 10 -T 600 -U postgres postgres


transaction type: <builtin: TPC-B (sort of)>
scaling factor: 1
query mode: simple
number of clients: 8
number of threads: 1
duration: 600 s
number of transactions actually processed: 156308
latency average = 30.707 ms
latency stddev = 32.359 ms
tps = 260.486745 (including connections establishing)
tps = 260.488548 (excluding connections establishing)


    дать отработать до конца
    дальше настроить autovacuum максимально эффективно
    построить график по получившимся значениям
    так чтобы получить максимально ровное значение tps

для удобства мониторинг:
включим логирование вызовов автовакуума:
1. log_autovacuum_min_duration = '0'
2. вывод утилиты дополним временными метками. с помощью утилиты awk '{print strftime("%F %T"), $0}' 

оказалось что утилита pgbench выдаёт свой вывод в stderr, перенаправляем его  stdout с помощью 2>&1 ).
pgbench -c8 -P 10 -T 600 -U postgres postgres 2>&1 | awk '{print strftime("%F %T"), $0}' 
вывод будет иметь вид:

2021-10-27 17:11:08 starting vacuum...end.
2021-10-27 17:11:18 progress: 10.0 s, 311.4 tps, lat 25.449 ms stddev 23.238
2021-10-27 17:11:28 progress: 20.0 s, 225.5 tps, lat 35.592 ms stddev 39.447
2021-10-27 17:11:38 progress: 30.0 s, 237.1 tps, lat 33.745 ms stddev 34.693
2021-10-27 17:11:48 progress: 40.0 s, 279.2 tps, lat 28.684 ms stddev 29.672
2021-10-27 17:11:58 progress: 50.0 s, 248.8 tps, lat 32.100 ms stddev 31.316

события 
2021-10-27 17:16:42.072 EEST [318005] LOG:  automatic vacuum of table "postgres.public.pgbench_tellers": index scans: 0
        pages: 0 removed, 7 remain, 1 skipped due to pins, 0 skipped frozen
        tuples: 253 removed, 26 remain, 17 are dead but not yet removable, oldest xmin: 253249
        buffer usage: 39 hits, 0 misses, 0 dirtied
        avg read rate: 0.000 MB/s, avg write rate: 0.000 MB/s
        system usage: CPU: user: 0.00 s, system: 0.00 s, elapsed: 0.00 s
        WAL usage: 5 records, 0 full page images, 983 bytes
2021-10-27 17:16:42.072 EEST [318005] LOG:  automatic analyze of table "postgres.public.pgbench_tellers" system usage: CPU: user: 0.00 s, system: 0.00 s, elapsed: 0.00 s


это можно использовать для графика.
довольно заметно что низким tps соответсвтуют высокие stddev. (посчитал коэф. корелляции -0.96 - практически обратно-пропорциональная зависимость)  



Критерии оценки:

Выполнение ДЗ: 10 баллов

    2 балл за красивое решение

    2 балл за рабочее решение, и недостатки указанные преподавателем не устранены

Рекомендуем сдать до: 24.10.2021


