
## Домашнее задание
-   задание со звездочкой *: не удаляя существующий GCE инстанс сделайте новый, поставьте на его PostgreSQL, удалите файлы с данными из /var/lib/postgres, перемонтируйте внешний диск который сделали ранее от первой виртуальной машины ко второй и запустите PostgreSQL на второй машине так чтобы он работал с данными на внешнем диске, расскажите как вы это сделали и что в итоге получилось.

 - Решил что для усложнения можно попытаться сделать машину с другой операционной системой. центос7.
- отмонтирование диска GCE:
	- VM instances 
	- choose instance 
	-  edit 
	-  additional disks
	-  навести так чтобы появилась иконка edit 
	-  корзинка.
	-  save,
	- и только тогда, когда удалится диск из одной машины, его можно монтировать в другую. 

у меня диск с LVM в  центосе google-gpc нет LVM. 
- устанавливаем:
    

> yum install lvm2

- обнаруживаем PV, VG, LV

>     [root@pg-02-2 ~]# vgscan  
>     Reading volume groups from cache.  
>     Found volume group "vg" using metadata type lvm2  
>     [root@pg-02-2 ~]# pvscan  
>     PV /dev/sdb1 VG vg lvm2 [<10.00 GiB / 0 free]  
>     Total: 1 [<10.00 GiB] / in use: 1 [<10.00 GiB] / in no VG: 0 [0 ]  
>     [root@pg-02-2 ~]# vgscan  
>     Reading volume groups from cache.  
>     Found volume group "vg" using metadata type lvm2  
>     [root@pg-02-2 ~]# lvscan  
>     inactive '/dev/vg/pgdata' [<10.00 GiB] inherit

LV имеет статус inactive, делаем его активным

   

> [root@pg-02-2 ~]# lvchange -a y /dev/vg/pgdata

можно сделать активным все волумы в группе:
    

> [root@pg-02-2 ~]# vgchange -a y vg
> 1 logical volume(s) in volume group "vg" now active


- установка постгреса в центос7
- https://www.postgresql.org/download/linux/redhat/

>     sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
>     sudo yum install -y postgresql14-server
>     sudo /usr/pgsql-14/bin/postgresql-14-setup initdb
>     sudo systemctl enable postgresql-14
>     sudo systemctl start postgresql-14

- остановка экземпляра
- удаление файлов пгдата:

>     sudo systemctl stop postgresql-14
>     rm -rf /var/lib/pgsql/14

*на самом деле лучше не удалять, а отложить в сторону, потому что некоторые файлы оттуда пригодятся.*
 в каталоге /var/lib/pgsql есть файл /var/lib/pgsql/.bash_profile
он будет очень полезен для оболочки под пользователем postgres поэтому его тоже сохраним.

 - монтируем файловую систему на диске /dev/vg/pgdata  в  /var/lib/pgsql  так что каталог 14/main , лежащий в корне будет находиться в /var/lib/pgsql/14/main
    

> [root@pg-02-2 /]#  mount /dev/vg/pgdata /var/lib/pgsql/

- также добавляем строчку в /etc/fstab чтобы монтировать автоматически при загрузке.
    

> /dev/mapper/vg-pgdata /var/lib/pgsql ext4 defaults 0 0

- права на файловой системе выдаются на пользователей, но хранятся не на имена, а на uid, guid - цифры. например файлы теперю имеют вот такие права:

>     [root@pg-02-2 /]# stat /var/lib/pgsql/14/main/  
>     File: ‘/var/lib/pgsql/14/main/’  
>     ...
>     Access: (0700/drwx------) Uid: ( 113/ UNKNOWN) Gid: ( 121/ UNKNOWN)

- сменим их на те которые актуальные postgres:postgres 

    

> [root@pg-02-2 /]# chown -R postgres:postgres /var/lib/pgsql/

- первая попытка стартануть сервер оказалась неуспешная

>     [root@pg-02-2 /]# systemctl status postgresql-14.service  
>     ● postgresql-14.service - PostgreSQL 14 database server  
>     Loaded: loaded (/usr/lib/systemd/system/postgresql-14.service; enabled; vendor preset: disabled)  
>     Active: failed (Result: exit-code) since Sun 2021-10-17 12:42:24 UTC; 10s ago  
>     Docs: https://www.postgresql.org/docs/14/static/  
>     Process: 1904 ExecStart=/usr/pgsql-14/bin/postmaster -D ${PGDATA} (code=exited, status=0/SUCCESS)  
>     Process: 2077 ExecStartPre=/usr/pgsql-14/bin/postgresql-14-check-db-dir ${PGDATA}
> (code=exited, status=1/FAILURE)  
>     Main PID: 1904 (code=exited, status=0/SUCCESS)  
>       
>     Oct 17 12:42:24 pg-02-2 systemd[1]: Starting PostgreSQL 14 database server...  
>     Oct 17 12:42:24 pg-02-2 systemd[1]: postgresql-14.service: control process exited, code=exited status=1  
>     Oct 17 12:42:24 pg-02-2 systemd[1]: Failed to start PostgreSQL 14 database server.  
>     Oct 17 12:42:24 pg-02-2 systemd[1]: Unit postgresql-14.service entered failed state.  
>     Oct 17 12:42:24 pg-02-2 systemd[1]: postgresql-14.service failed.

оказывается сервер не стартует потому, что данные субд ищутся в каталоге /var/lib/pgsql/14/data/

это написано в логе /var/log/messages

>     Oct 17 12:42:24 pg-02-2 postgresql-14-check-db-dir: "/var/lib/pgsql/14/data/" is missing or empty.
>     Oct 17 12:42:24 pg-02-2 postgresql-14-check-db-dir: Use "/usr/pgsql-14/bin/postgresql-14-setup initdb" to initialize the  database cluster.
>     Oct 17 12:42:24 pg-02-2 postgresql-14-check-db-dir: See /usr/share/doc/postgresql14-14.0/README.rpm-dist for more information.

управляется в настройках юнита переменной среды:

Environment=PGDATA=/var/lib/pgsql/14/data/

подхода два: поменять конфиг или поменять путь.
изменяю конфиг:

[root@pg-02-2 /]# EDITOR=mcedit systemctl edit --full postgresql-14.service

меняем путь на /var/lib/pgsql/14/main/

стартуем, следуюющая ошибка

Oct 17 12:48:34 pg-02-2 postmaster[2170]: postmaster: could not access the server configuration file "/var/lib/pgsql/14/main/postgresql.conf": No such file or directory

основной конфиг лежал вместе с пгдата. как раз хорошо если сохранился оригинальный пгдата, если нет, то можно вытащить sample config из пакета..

[root@pg-02-2 data]# rpm -ql postgresql14-server | grep postgresql.conf  
/usr/pgsql-14/share/postgresql.conf.sample

копируем из бекапа postgresql.conf в /var/lib/pgsql/14/main/postgresql.conf

старт, лог /var/log/messages

>     Oct 17 12:57:17 pg-02-2 postmaster: 2021-10-17 12:57:17.376 UTC [2258] LOG: redirecting log output to logging collector process  
>     Oct 17 12:57:17 pg-02-2 postmaster: 2021-10-17 12:57:17.376 UTC [2258] HINT: Future log output will appear in directory "log".  
>     Oct 17 12:57:17 pg-02-2 systemd: postgresql-14.service: main process exited, code=exited, status=1/FAILURE

идем в указанный каталог, где пишутся логи:
в моем случае /var/lib/pgsql/14/main/log/postgresql-Sun.log
текст ошибки:

>     2021-10-17 12:57:17.390 UTC [2258] LOG: could not open configuration file "/var/lib/pgsql/14/main/pg_hba.conf": No such file or directory  
>     2021-10-17 12:57:17.390 UTC [2258] FATAL: could not load pg_hba.conf  
>     2021-10-17 12:57:17.392 UTC [2258] LOG: database system is shut dow

уже относительный успех, сервер работает но в логе  есть пару ошибок:

>     2021-10-17 12:59:39.768 UTC [2307] LOG: could not open usermap file "/var/lib/pgsql/14/main/pg_ident.conf": No such file or directory
> 
>     2021-10-17 12:59:39.772 UTC [2311] LOG: database system was shut down at 2021-10-17 12:14:31 UTC  
>     2021-10-17 12:59:39.820 UTC [2307] LOG: database system is ready to accept connections  
>     2021-10-17 13:00:00.040 UTC [2336] FATAL: database locale is incompatible with operating system  
>     2021-10-17 13:00:00.040 UTC [2336] DETAIL: The database was initialized with LC_COLLATE "C.UTF-8", which is not recognized by  setlocale().  
>     2021-10-17 13:00:00.040 UTC [2336] HINT: Recreate the database with another locale or install the missing locale.

- первая `"/var/lib/pgsql/14/main/pg_ident.conf": No such file or directory`   решается восстановлением из бекапа или из sample из каталога /usr/pgsql-14/share/

- вторая - генерацией локали для операционной системы 
2021-10-17 13:00:00.040 UTC [2336] DETAIL: The database was initialized with LC_COLLATE "C.UTF-8", which is not recognized by setlocale().  

в центосе вместо генерирования,  придется использовать механизм: просто объявить какую-то локаль типа en_US.UTF-8 как C.UTF-8

> localedef -i en_US -f UTF-8 C.UTF-8

для удобства работы в оболочке из-под пользователя, вернём из бекапа файл  /var/lib/pgsql/.bash_profile
(в нем прописана переменная среды PGDATA=/var/lib/pgsql/14/data, если путь был изменен - то его также следует изменить и тут)

проверка работы - успех.

>     -bash-4.2$ psql  
>     psql (14.0)  
>     Type "help" for help.  
>     postgres=# \l
>                                   List of databases
>        Name    |  Owner   | Encoding | Collate |  Ctype  |   Access privileges   
>     -----------+----------+----------+---------+---------+-----------------------
>      demo      | postgres | UTF8     | C.UTF-8 | C.UTF-8 | 
>      postgres  | postgres | UTF8     | C.UTF-8 | C.UTF-8 | 
>      template0 | postgres | UTF8     | C.UTF-8 | C.UTF-8 | =c/postgres          +
>                |          |          |         |         | postgres=CTc/postgres
>      template1 | postgres | UTF8     | C.UTF-8 | C.UTF-8 | =c/postgres          +
>                |          |          |         |         | postgres=CTc/postgres
>     (4 rows)
>     
>     postgres=# \c demo  
>     You are now connected to database "demo" as user "postgres".  
>     demo=# select * from bookings.aircrafts;  
>     aircraft_code | model | range  
>     ---------------+---------------------+-------  
>     773 | Boeing 777-300 | 11100  
>     763 | Boeing 767-300 | 7900  
>     SU9 | Sukhoi SuperJet-100 | 3000  
>     320 | Airbus A320-200 | 5700  
>     321 | Airbus A321-200 | 5600  
>     319 | Airbus A319-100 | 6700  
>     733 | Boeing 737-300 | 4200  
>     CN1 | Cessna 208 Caravan | 1200  
>     CR2 | Bombardier CRJ-200 | 2700  
>     (9 rows)
