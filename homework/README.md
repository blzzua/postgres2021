
## Домашнее задание



Установка и настройка PostgreSQL

Цель:

-   создавать дополнительный диск для уже существующей виртуальной машины, размечать его и делать на нем файловую систему
    
-   переносить содержимое базы данных PostgreSQL на дополнительный диск
    
-   переносить содержимое БД PostgreSQL между виртуальными машинами

-   создайте виртуальную машину c Ubuntu 20.04 LTS (bionic) в GCE типа e2-medium в default VPC в любом регионе и зоне, например us-central1-a
	- создана машина pg-02 в проекте postgres2021-19840604
   
-   поставьте на нее PostgreSQL через sudo apt

>     sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' ; 
>     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
>     apt-get update 
>     apt-get -y install postgresql-14

    
-   проверьте что кластер запущен через sudo -u postgres pg_lsclusters

>     postgres@pg-02:~$ pg_lsclusters  
>     Ver Cluster Port Status Owner Data directory Log file  
>     14 main 5432 online postgres /var/lib/postgresql/14/main /var/log/postgresql/postgresql-14-main.log

    
-   зайдите из под пользователя postgres в psql и сделайте произвольную таблицу с произвольным содержимым postgres=# create table test(c1 text); postgres=# insert into test values('1'); \q
	- для демонстрационных целей будем использовать базу https://postgrespro.ru/education/demodb 
	- wget https://edu.postgrespro.ru/demo-small-20161013.zip
	- sudo apt -y install unzip
	- unzip demo-small-20161013.zip
	- в результате у нас есть 100мб файл с дампом базы demo_small.sql
	- создадим базу и прогрузим её:

>     postgres=# create database demo;  
>     CREATE DATABASE
>     postgres=# \c demo  
>     You are now connected to database "demo" as user "postgres".
>     demo=# \i demo_small.sql

-   остановите postgres например через sudo -u postgres pg_ctlcluster 13 main stop
    
-   создайте новый standard persistent диск GKE через Compute Engine -> Disks в том же регионе и зоне что GCE инстанс размером например 10GB
	- ✅
    
-  добавьте свеже-созданный диск к виртуальной машине - надо зайти в режим ее редактирования и дальше выбрать пункт attach existing disk
	- ✅

    
-   проинициализируйте диск согласно инструкции и подмонтировать файловую систему, только не забывайте менять имя диска на актуальное, в вашем случае это скорее всего будет /dev/sdb - [https://www.digitalocean.com/community/tutorials/how-to-partition-and-format-storage-devices-in-linux](https://www.digitalocean.com/community/tutorials/how-to-partition-and-format-storage-devices-in-linux)
			- обнаруживаем добавленный диск, и его имя.

>     root@pg-02:~# dmesg -T| grep disk
>     [Sun Oct 17 10:10:47 2021] sd 0:0:2:0: [sdb] Attached SCSI disk
	
		# я предпочитаю работать с диском через LVM, а также производить разметку диска GPT с использованием утилиты fdisk
	    root@pg-02:~# fdisk /dev/sdb
	    
	    Command (m for help): g           
	    Created a new GPT disklabel (GUID: BD5FD588-481A-1649-944B-C94FC70CCE10).
	    The old gpt signature will be removed by a write command.
	    
	    Command (m for help): p
	    
	    Disk /dev/sdb: 10 GiB, 10737418240 bytes, 20971520 sectors
	    Disk model: PersistentDisk  
	    Units: sectors of 1 * 512 = 512 bytes
	    Sector size (logical/physical): 512 bytes / 4096 bytes
	    I/O size (minimum/optimal): 4096 bytes / 4096 bytes
	    Disklabel type: gpt
	    Disk identifier: BD5FD588-481A-1649-944B-C94FC70CCE10
	    
	# создание раздела    
	    Command (m for help): n
	    Partition number (1-128, default 1): 
	    First sector (2048-20971486, default 2048): 
	    Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-20971486, default 20971486): 
	    
	    Created a new partition 1 of type 'Linux filesystem' and of size 10 GiB.
	    
	# отметка типа раздела
	    Command (m for help): t   
	    Selected partition 1
	    Partition type (type L to list all types): 31
	    Changed type of partition 'Linux filesystem' to 'Linux LVM'.
	    
	# просмотр информации о диске и разделах:
	    Command (m for help): p
	    Disk /dev/sdb: 10 GiB, 10737418240 bytes, 20971520 sectors
	    Disk model: PersistentDisk  
	    Units: sectors of 1 * 512 = 512 bytes
	    Sector size (logical/physical): 512 bytes / 4096 bytes
	    I/O size (minimum/optimal): 4096 bytes / 4096 bytes
	    Disklabel type: gpt
	    Disk identifier: BD5FD588-481A-1649-944B-C94FC70CCE10
	    
	    Device     Start      End  Sectors Size Type
	    /dev/sdb1   2048 20971486 20969439  10G Linux LVM
	    
	# запись изменений на диск. в связи с тем что этот диск еще не используется системой, нет нужды перечитывать таблицу разделов. (partprobe)
	    Command (m for help): w
	    The partition table has been altered.
	    Calling ioctl() to re-read partition table.
	    Syncing disks.

- работа с LVM.
	-  создание PV, создание VG из одного PV , создание LV внутри VG на 100% размера PV. создание файловой системы:

>     root@pg-02:~# pvcreate /dev/sdb1  
>     Physical volume "/dev/sdb1" successfully created.  
>     root@pg-02:~# vgcreate vg /dev/sdb1  
>     Volume group "vg" successfully created  
>     root@pg-02:~# lvcreate -n pgdata -l 100%PV vg  
>     Logical volume "pgdata" created.  
>     root@pg-02:~# mkfs -t ext4 -L pgdata /dev/vg/pgdata  
>     mke2fs 1.45.5 (07-Jan-2020)  
>     Discarding device blocks: done  
>     Creating filesystem with 2620416 4k blocks and 655360 inodes  
>     Filesystem UUID: c0c4ae92-e927-4a69-af15-a6b07a865f3a  
>     Superblock backups stored on blocks:  
>     32768, 98304, 163840, 229376, 294912, 819200, 884736, 1605632  
>       
>     Allocating group tables: done  
>     Writing inode tables: done  
>     Creating journal (16384 blocks): done  
>     Writing superblocks and filesystem accounting information: done

    
-   сделайте пользователя postgres владельцем /mnt/data - chown -R postgres:postgres /mnt/data/
	- монтируем файловую систему. меняем права.

> root@pg-02:~# mount /dev/vg/pgdata /mnt/data/ root@pg-02:~# chown -R
> postgres:postgres /mnt/data/
-
	- добавляем запись в /etc/fstab чтобы монтирование происходило автоматически при загрузке перационной системы.

> LABEL=pgdata /mnt/data ext4 defaults 0 0

-   перенесите содержимое /var/lib/postgres/13 в /mnt/data - mv /var/lib/postgresql/13 /mnt/data
	- ✅
    
-   попытайтесь запустить кластер - sudo -u postgres pg_ctlcluster 13 main start
    
-   напишите получилось или нет и почему

>     postgres@pg-02:~$ pg_ctlcluster 14 main start  
>     Error: /var/lib/postgresql/14/main is not accessible or does not exist
текст ошибки говорит что нет каталога с данными.
    
-   задание: найти конфигурационный параметр в файлах раположенных в /etc/postgresql/10/main который надо поменять и поменяйте его
    
-   напишите что и почему поменяли
> 
>     postgres@pg-02:~$ grep -R '/var/lib/postgresql/14/main' /etc/postgresql/14/main/  
>     /etc/postgresql/14/main/postgresql.conf:data_directory = '/var/lib/postgresql/14/main' # use data in another directory
    
меняем параметр на data_directory = '/mnt/data/14/main'  в файле /etc/postgresql/14/main/postgresql.conf

-   попытайтесь запустить кластер - sudo -u postgres pg_ctlcluster 13 main start
    
-   напишите получилось или нет и почему
	- получилось, об этом говорят строки в логе /var/log/postgresql/postgresql-14-main.log 
>     2021-10-17 10:44:48.150 UTC [6389] LOG:  database system was shut down at 2021-10-17 09:55:26 UTC
>     2021-10-17 10:44:48.158 UTC [6388] LOG:  database system is ready to accept connections
    
-   зайдите через через psql и проверьте содержимое ранее созданной таблицы
	- данные на месте. однако пришлось учесть что я создавал отдельную базу, загружал в неё данные. данные хранятся в отдельной схеме. не public чтобы "видеть" их в psql нужно изменить параметр search_path

>     demo=# SHOW search_path;  
>     search_path  
>     -----------------  
>     "$user", public  
>     (1 row)
>     demo=# SET search_path TO bookings, public;  
>     SET
>     demo=# \dt  
>     List of relations  
>     Schema | Name | Type | Owner  
>     ----------+-----------------+-------+----------  
>     bookings | aircrafts | table | postgres  
>     bookings | airports | table | postgres  
>     bookings | boarding_passes | table | postgres  
>     bookings | bookings | table | postgres  
>     bookings | flights | table | postgres  
>     bookings | seats | table | postgres  
>     bookings | ticket_flights | table | postgres  
>     bookings | tickets | table | postgres  
>     (8 rows)

или обращаться с полным путём. включая имя схемы:

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

-   задание со звездочкой *: не удаляя существующий GCE инстанс сделайте новый, поставьте на его PostgreSQL, удалите файлы с данными из /var/lib/postgres, перемонтируйте внешний диск который сделали ранее от первой виртуальной машины ко второй и запустите PostgreSQL на второй машине так чтобы он работал с данными на внешнем диске, расскажите как вы это сделали и что в итоге получилось.
