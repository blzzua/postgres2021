
Создать два кластера GKE в разных регионах

Установить на первом Patroni HA кластер 

Установить на втором Patroni Standby кластер 

Настроить TCP LB между регионами 

Сделать в каждом регионе по клиентской ВМ 

Проверить как ходит трафик с клиентской ВМ 

Описать что и как делали и с какими проблемами столкнулись

# etcd
>     gcloud compute instances create etcd1 --project=postgres-2021-328610 --zone=europe-central2-a --machine-type=e2-micro --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=etcd1,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any

>     gcloud compute instances create etcd2 --project=postgres-2021-328610 --zone=europe-west3-c --machine-type=e2-micro --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=etcd2,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any 

>     gcloud compute instances create etcd3 --project=postgres-2021-328610 --zone=europe-west4-c --machine-type=e2-micro --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=etcd3,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any

на каждой ноде 

>     apt update ; apt -y install etcd mc
>     sudo mkdir /opt/etcd
>     sudo chown etcd:etcd /opt/etcd 
>     mcedit /etc/default/etcd

файлы с конфигами  /etc/default/etcd имеют вид:

>     ETCD_NAME="etcd1"
>     ETCD_DATA_DIR="/opt/etcd"
>     # необходимо вычислить ип и вставить именно его.
>     ETCD_LISTEN_PEER_URLS="http://10.186.0.3:2380"
>     ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"
>     ETCD_INITIAL_ADVERTISE_PEER_URLS="http://etcd1.europe-central2-a:2380"
>     ETCD_INITIAL_CLUSTER="etcd1=http://etcd1.europe-central2-a:2380,etcd2=http://etcd2.europe-west3-c:2380,etcd3=http://etcd3.europe-west4-c:2380"
>     ETCD_INITIAL_CLUSTER_STATE="new"
>     ETCD_INITIAL_CLUSTER_TOKEN="someotusclustertoken"
>     ETCD_ADVERTISE_CLIENT_URLS="http://etcd1.europe-central2-a:2379"
>     DAEMON_ARGS="--enable-v2=true "

>     ETCD_NAME="etcd2"
>     ETCD_DATA_DIR="/opt/etcd"
>     # необходимо вычислить ип и вставить именно его.
>     ETCD_LISTEN_PEER_URLS="http://10.156.0.3:2380"
>     ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"
>     ETCD_INITIAL_ADVERTISE_PEER_URLS="http://etcd2.europe-west3-c:2380"
>     ETCD_INITIAL_CLUSTER="etcd1=http://etcd1.europe-central2-a:2380,etcd2=http://etcd2.europe-west3-c:2380,etcd3=http://etcd3.europe-west4-c:2380"
>     ETCD_INITIAL_CLUSTER_STATE="new"
>     ETCD_INITIAL_CLUSTER_TOKEN="someotusclustertoken"
>     ETCD_ADVERTISE_CLIENT_URLS="http://etcd2.europe-west3-c:2379"
>     DAEMON_ARGS="--enable-v2=true "

>     ETCD_NAME="etcd3"
>     ETCD_DATA_DIR="/opt/etcd"
>     # необходимо вычислить ип и вставить именно его.
>     ETCD_LISTEN_PEER_URLS="http://10.164.0.24:2380"
>     ETCD_LISTEN_CLIENT_URLS="http://0.0.0.0:2379"
>     ETCD_INITIAL_ADVERTISE_PEER_URLS="http://etcd3.europe-west4-c:2380"
>     ETCD_INITIAL_CLUSTER="etcd1=http://etcd1.europe-central2-a:2380,etcd2=http://etcd2.europe-west3-c:2380,etcd3=http://etcd3.europe-west4-c:2380"
>     ETCD_INITIAL_CLUSTER_STATE="new"
>     ETCD_INITIAL_CLUSTER_TOKEN="someotusclustertoken"
>     ETCD_ADVERTISE_CLIENT_URLS="http://etcd3.europe-west4-c:2379"
>     DAEMON_ARGS="--enable-v2=true "


# postgres + patroni from github

>     gcloud compute instances create pg1 --project=postgres-2021-328610 --zone=europe-west4-c --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=pg1,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=an

>     gcloud compute ssh pg1


установка:
>     sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' ; 
>     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
>     apt-get update 
>     apt-get install -y python3 python3-pip git mc postgresql-14


## patroni setup
>     cd /opt ; git clone https://github.com/zalando/patroni

В качестве задела на будущее. можно откатить патрони на какую-то старую версию чтобы потом показать как неё обновить, а также различные методы установки патрони в операционную систему (pip/github):
>     git tag --list
>     git checkout tags/v2.1.1

чтобы решить ошибку при сборке:
>     FATAL: Patroni requires psycopg2>=2.5.4 or psycopg2-binary

>     pip3 install psycopg2-binary 
>     python3 setup.py --help 
>     python3 setup.py build 
>     python3 setup.py install 


юнит можно найти в /opt/patroni/extras/startup-scripts/patroni.service:
в нем исправить путь к patroni 
>     ExecStart=/usr/local/bin/patroni /etc/patroni.yml
>     cp /opt/patroni/extras/startup-scripts/patroni.service /etc/systemd/system

обратить внимание что сервис работает от 
>     User=postgres
>     Group=postgres

если не устанавливался postgresql-сервер, то логинов может еще не быть. 
>     grep postgres /etc/passwd

А даже если устанавливался, то может сильно мешать автоматически-запускающийся экземпляр.

установка постгреса, и удаление экземпляра-по-умолчанию
>     apt-get install -y  postgresql-14
>     systemctl stop postgresql
>     su - postgres 
>     pg_dropcluster 14 main

если при попытке стартануть будет ошибка:
>     2022-01-18 10:48:19,466 INFO: Failed to import patroni.dcs.etcd
нужно установить недостающие питоновские модули, в моём случае я не знал что именно за модуль, и устаналивается так:
>     pip3 install patroni[etcd]==2.1.1
но в процессе, стало ясно, это автоматически установит недостающую зависимость.
>  pip3 install 'python-etcd<0.5,>=0.4.3'

## patroni bootstap config
пример конфига для патрони который мы используем для бут-страпа, взял из примера /opt/patroni/postgres0.yml 
примечание: 
нужно использовать правильные доменные имена или ип-адреса в следующих местах:
restapi.connect_address: 10.164.0.25:8008
postgresql.connect_address: 10.164.0.25:5432

>     root@pg1:/etc# cat /etc/patroni-init.yml 
>     scope: otus
>     #namespace: /service/
>     name: pg1
>     
>     restapi:
>       listen: 0.0.0.0:8008
>       connect_address: pg1.europe-west4-c:8008
>     #  certfile: /etc/ssl/certs/ssl-cert-snakeoil.pem
>     #  keyfile: /etc/ssl/private/ssl-cert-snakeoil.key
>     #  authentication:
>     #    username: username
>     #    password: password
>     
>     # ctl:
>     #   insecure: false # Allow connections to SSL sites without certs
>     #   certfile: /etc/ssl/certs/ssl-cert-snakeoil.pem
>     #   cacert: /etc/ssl/certs/ssl-cacert-snakeoil.pem
>     
>     etcd:
>       #Provide host to do the initial discovery of the cluster topology:
>       #host: 127.0.0.1:2379
>       #Or use "hosts" to provide multiple endpoints
>       #Could be a comma separated string:
>       #hosts: host1:port1,host2:port2
>       #or an actual yaml list:
>       #hosts:
>       #- host1:port1
>       #- host2:port2
>       #Once discovery is complete Patroni will use the list of advertised clientURLs
>       #It is possible to change this behavior through by setting:
>       #use_proxies: true
>       hosts:
>       - etcd1.europe-central2-a:2379
>       - etcd2.europe-west3-c:2379
>       - etcd3.europe-west4-c:2379
>     
>     
>     bootstrap:
>       # this section will be written into Etcd:/<namespace>/<scope>/config after initializing new cluster
>       # and all other cluster members will use it as a `global configuration`
>       dcs:
>         ttl: 30
>         loop_wait: 10
>         retry_timeout: 10
>         maximum_lag_on_failover: 1048576
>     #    master_start_timeout: 300
>     #    synchronous_mode: false
>         #standby_cluster:
>           #host: 127.0.0.1
>           #port: 1111
>           #primary_slot_name: patroni
>         postgresql:
>           use_pg_rewind: true
>     #      use_slots: true
>           parameters:
>             wal_level: hot_standby
>             hot_standby: "on"
>     #        wal_keep_segments: 8
>     #        max_wal_senders: 10
>     #        max_replication_slots: 10
>     #        wal_log_hints: "on"
>     #        archive_mode: "on"
>     #        archive_timeout: 1800s
>     #        archive_command: mkdir -p ../wal_archive && test ! -f ../wal_archive/%f && cp %p ../wal_archive/%f
>           recovery_conf:
>             restore_command: cp ../wal_archive/%f %p
>     
>       # some desired options for 'initdb'
>       initdb:  # Note: It needs to be a list (some options need values, others are switches)
>       - encoding: UTF8
>       - data-checksums
>     
>       pg_hba:  # Add following lines to pg_hba.conf after running 'initdb'
>       # For kerberos gss based connectivity (discard @.*$)
>       #- host replication replicator 127.0.0.1/32 gss include_realm=0
>       #- host all all 0.0.0.0/0 gss include_realm=0
>       - host replication replicator 127.0.0.1/32 md5
>       - host all all 0.0.0.0/0 md5
>     #  - hostssl all all 0.0.0.0/0 md5
>     
>       # Additional script to be launched after initial cluster creation (will be passed the connection URL as parameter)
>     # post_init: /usr/local/bin/setup_cluster.sh
>     
>       # Some additional users users which needs to be created after initializing new cluster
>       users:
>         admin:
>           password: admin
>           options:
>             - createrole
>             - createdb
>     
>     postgresql:
>       listen: 127.0.0.1:5432
>       connect_address: 10.164.0.25:5432
>       data_dir: /var/lib/postgresql/data
>     #  bin_dir:
>       bin_dir: /usr/lib/postgresql/14/bin
>     #  config_dir: /etc/postgresql/14
>       pgpass: /tmp/pgpass0
>       authentication:
>         replication:
>           username: replicator
>           password: rep-pass
>         superuser:
>           username: postgres
>           password: zalando
>         rewind:  # Has no effect on postgres 10 and lower
>           username: rewind_user
>           password: rewind_password
>       # Server side kerberos spn
>     #  krbsrvname: postgres
>       parameters:
>         # Fully qualified kerberos ticket file for the running user
>         # same as KRB5CCNAME used by the GSS
>     #   krb_server_keyfile: /var/spool/keytabs/postgres
>         unix_socket_directories: '.'
>     
>     #watchdog:
>     #  mode: automatic # Allowed values: off, automatic, required
>     #  device: /dev/watchdog
>     #  safety_margin: 5
>     
>     tags:
>         nofailover: false
>         noloadbalance: false
>         clonefrom: false
>         nosync: false

запуск patroni, впервый раз. режим bootstrap. в этом режиме патрони создаёт сервер согласно конфиг. опциям указанным в bootstrap. 
можно в ручную чтобы это всё увидеть, ну:

>     su - postgres
>     patroni  /etc/postgres.yml
> 
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,299 INFO: Selected new etcd server http://etcd1.europe-central2-a:2379
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,328 INFO: No PostgreSQL configuration items changed, nothing to reload.
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,414 WARNING: Postgresql is not running.
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,415 INFO: Lock owner: None; I am pg1
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,417 INFO: pg_controldata:
>     Jan 18 13:26:02 pg1 patroni[13421]:   pg_control version number: 1300
>     Jan 18 13:26:02 pg1 patroni[13421]:   Catalog version number: 202107181
>     Jan 18 13:26:02 pg1 patroni[13421]:   Database system identifier: 7054531535614542456
>     Jan 18 13:26:02 pg1 patroni[13421]:   Database cluster state: shut down
>     Jan 18 13:26:02 pg1 patroni[13421]:   pg_control last modified: Tue Jan 18 13:24:43 2022
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint location: 0/194EA60
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's REDO location: 0/194EA60
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's REDO WAL file: 000000020000000000000001
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's TimeLineID: 2
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's PrevTimeLineID: 2
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's full_page_writes: on
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's NextXID: 0:742
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's NextOID: 16387
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's NextMultiXactId: 1
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's NextMultiOffset: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestXID: 727
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestXID's DB: 1
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestActiveXID: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestMultiXid: 1
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestMulti's DB: 1
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's oldestCommitTsXid: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Latest checkpoint's newestCommitTsXid: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Time of latest checkpoint: Tue Jan 18 13:24:43 2022
>     Jan 18 13:26:02 pg1 patroni[13421]:   Fake LSN counter for unlogged rels: 0/3E8
>     Jan 18 13:26:02 pg1 patroni[13421]:   Minimum recovery ending location: 0/0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Min recovery ending loc's timeline: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Backup start location: 0/0
>     Jan 18 13:26:02 pg1 patroni[13421]:   Backup end location: 0/0
>     Jan 18 13:26:02 pg1 patroni[13421]:   End-of-backup record required: no
>     Jan 18 13:26:02 pg1 patroni[13421]:   wal_level setting: replica
>     Jan 18 13:26:02 pg1 patroni[13421]:   wal_log_hints setting: on
>     Jan 18 13:26:02 pg1 patroni[13421]:   max_connections setting: 100
>     Jan 18 13:26:02 pg1 patroni[13421]:   max_worker_processes setting: 8
>     Jan 18 13:26:02 pg1 patroni[13421]:   max_wal_senders setting: 10
>     Jan 18 13:26:02 pg1 patroni[13421]:   max_prepared_xacts setting: 0
>     Jan 18 13:26:02 pg1 patroni[13421]:   max_locks_per_xact setting: 64
>     Jan 18 13:26:02 pg1 patroni[13421]:   track_commit_timestamp setting: off
>     Jan 18 13:26:02 pg1 patroni[13421]:   Maximum data alignment: 8
>     Jan 18 13:26:02 pg1 patroni[13421]:   Database block size: 8192
>     Jan 18 13:26:02 pg1 patroni[13421]:   Blocks per segment of large relation: 131072
>     Jan 18 13:26:02 pg1 patroni[13421]:   WAL block size: 8192
>     Jan 18 13:26:02 pg1 patroni[13421]:   Bytes per WAL segment: 16777216
>     Jan 18 13:26:02 pg1 patroni[13421]:   Maximum length of identifiers: 64
>     Jan 18 13:26:02 pg1 patroni[13421]:   Maximum columns in an index: 32
>     Jan 18 13:26:02 pg1 patroni[13421]:   Maximum size of a TOAST chunk: 1996
>     Jan 18 13:26:02 pg1 patroni[13421]:   Size of a large-object chunk: 2048
>     Jan 18 13:26:02 pg1 patroni[13421]:   Date/time type storage: 64-bit integers
>     Jan 18 13:26:02 pg1 patroni[13421]:   Float8 argument passing: by value
>     Jan 18 13:26:02 pg1 patroni[13421]:   Data page checksum version: 1
>     Jan 18 13:26:02 pg1 patroni[13421]:   Mock authentication nonce: 74cbca90587ef7e9b98e459e7fca8769dcfac391c1438e928ec9009eb5288434
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,453 INFO: Lock owner: None; I am pg1
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,496 INFO: starting as a secondary
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,501 WARNING: Removing unexpected parameter=connect_address
> value=127.0.0.1:5434 from the config
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,501 WARNING: Removing unexpected parameter=listen value=0.0.0.0:5434 from
> the config
>     Jan 18 13:26:02 pg1 patroni[13436]: 2022-01-18 13:26:02.853 UTC [13436] LOG:  starting PostgreSQL 14.1 (Ubuntu 14.1-2.pgdg20.04+1) on
> x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 9.3.0-17ubuntu1~20.04)
> 9.3.0, 64-bit
>     Jan 18 13:26:02 pg1 patroni[13436]: 2022-01-18 13:26:02.853 UTC [13436] LOG:  listening on IPv4 address "0.0.0.0", port 5432
>     Jan 18 13:26:02 pg1 patroni[13436]: 2022-01-18 13:26:02.860 UTC [13436] LOG:  listening on Unix socket "./.s.PGSQL.5432"
>     Jan 18 13:26:02 pg1 patroni[13437]: 2022-01-18 13:26:02.870 UTC [13437] LOG:  database system was shut down at 2022-01-18 13:24:43 UTC
>     Jan 18 13:26:02 pg1 patroni[13439]: cp: cannot stat '../wal_archive/00000003.history': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13437]: 2022-01-18 13:26:02.877 UTC [13437] LOG:  entering standby mode
>     Jan 18 13:26:02 pg1 patroni[13441]: cp: cannot stat '../wal_archive/00000002.history': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13443]: cp: cannot stat '../wal_archive/000000020000000000000001': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,884 INFO: postmaster pid=13436
>     Jan 18 13:26:02 pg1 patroni[13437]: 2022-01-18 13:26:02.888 UTC [13437] LOG:  consistent recovery state reached at 0/194EAD8
>     Jan 18 13:26:02 pg1 patroni[13437]: 2022-01-18 13:26:02.888 UTC [13437] LOG:  invalid record length at 0/194EAD8: wanted 24, got 0
>     Jan 18 13:26:02 pg1 patroni[13436]: 2022-01-18 13:26:02.889 UTC [13436] LOG:  database system is ready to accept read-only connections
>     Jan 18 13:26:02 pg1 patroni[13449]: cp: cannot stat '../wal_archive/00000003.history': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13451]: cp: cannot stat '../wal_archive/000000020000000000000001': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13454]: cp: cannot stat '../wal_archive/00000003.history': No such file or directory
>     Jan 18 13:26:02 pg1 patroni[13444]: localhost:5432 - accepting connections
>     Jan 18 13:26:02 pg1 patroni[13455]: localhost:5432 - accepting connections
>     Jan 18 13:26:02 pg1 patroni[13421]: 2022-01-18 13:26:02,941 INFO: establishing a new patroni connection to the postgres cluster
>     Jan 18 13:26:03 pg1 patroni[13421]: 2022-01-18 13:26:03,011 WARNING: Could not activate Linux watchdog device: "Can't open
> watchdog device: [Errno 2] No such file or directory: '/dev/watchdog'"
>     Jan 18 13:26:03 pg1 patroni[13421]: 2022-01-18 13:26:03,056 INFO: promoted self to leader by acquiring session lock
>     Jan 18 13:26:03 pg1 patroni[13460]: server promoting
>     Jan 18 13:26:03 pg1 patroni[13462]: cp: cannot stat '../wal_archive/000000020000000000000001': No such file or directory
>     Jan 18 13:26:03 pg1 patroni[13437]: 2022-01-18 13:26:03.062 UTC [13437] LOG:  received promote request
>     Jan 18 13:26:03 pg1 patroni[13437]: 2022-01-18 13:26:03.062 UTC [13437] LOG:  redo is not required
>     Jan 18 13:26:03 pg1 patroni[13421]: 2022-01-18 13:26:03,061 INFO: cleared rewind state after becoming the leader
>     Jan 18 13:26:03 pg1 patroni[13465]: cp: cannot stat '../wal_archive/000000020000000000000001': No such file or directory
>     Jan 18 13:26:03 pg1 patroni[13467]: cp: cannot stat '../wal_archive/00000003.history': No such file or directory
>     Jan 18 13:26:03 pg1 patroni[13437]: 2022-01-18 13:26:03.074 UTC [13437] LOG:  selected new timeline ID: 3
>     Jan 18 13:26:03 pg1 patroni[13437]: 2022-01-18 13:26:03.254 UTC [13437] LOG:  archive recovery complete
>     Jan 18 13:26:03 pg1 patroni[13469]: cp: cannot stat '../wal_archive/00000002.history': No such file or directory
>     Jan 18 13:26:03 pg1 patroni[13436]: 2022-01-18 13:26:03.275 UTC [13436] LOG:  database system is ready to accept connections
>     Jan 18 13:26:04 pg1 patroni[13421]: 2022-01-18 13:26:04,265 INFO: no action. I am (pg1) the leader with the lock

в дальшейнем это будет запускать юнит. 
>     systemctl enable patroni 


## создание второй ноды в другом регионе europe-west3-a.

>     gcloud compute instances create pg2 --project=postgres-2021-328610 --zone=europe-west3-a --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=pg2,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west3-a/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any


установка ПО:
>     sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' ; 
>     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
>     apt-get update 

>     apt-get install -y python3 python3-pip git mc postgresql-14
>     pip3 install psycopg2-binary 

после установвки ПО останавливаем и удаляем экземлпяр постгреса который запускается по-умолчанию:

>     systemctl stop postgresql
>     su - postgres
>     pg_dropcluster 14 main 
>     ## убеждемся что их нет
>     pg_lsclusters

## установка патрони из репозитория pip. 
>     pip3 install patroni[etcd]==2.1.1  

но в нем конфигов, системд-юнита..

юнит: /etc/systemd/system/patroni.service

>     # This is an example systemd config file for Patroni
>     # You can copy it to "/etc/systemd/system/patroni.service",
>     
>     [Unit]
>     Description=Runners to orchestrate a high-availability PostgreSQL
>     After=syslog.target network.target
>     
>     [Service]
>     Type=simple
>     
>     User=postgres
>     Group=postgres
>     
>     # Read in configuration file if it exists, otherwise proceed
>     EnvironmentFile=-/etc/patroni_env.conf
>     
>     WorkingDirectory=~
>     
>     # Where to send early-startup messages from the server
>     # This is normally controlled by the global default set by systemd
>     #StandardOutput=syslog
>     
>     # Pre-commands to start watchdog device
>     # Uncomment if watchdog is part of your patroni setup
>     #ExecStartPre=-/usr/bin/sudo /sbin/modprobe softdog
>     #ExecStartPre=-/usr/bin/sudo /bin/chown postgres /dev/watchdog
>     
>     # Start the patroni process
>     ExecStart=/usr/local/bin/patroni /etc/patroni.yml
>     
>     # Send HUP to reload from patroni.yml
>     ExecReload=/bin/kill -s HUP $MAINPID
>     
>     # only kill the patroni process, not it's children, so it will gracefully stop postgres
>     KillMode=process
>     
>     # Give a reasonable amount of time for the server to start up/shut down
>     TimeoutSec=30
>     
>     # Do not restart the service if it crashes, we want to manually inspect database on failure
>     Restart=no
>     
>     [Install]
>     WantedBy=multi-user.target

## конфиг патрони на ноде pg2
конфиг патрони на второй ноде( удалил закомментированное, секцию бутстрап, и главное - изменил name: на pg2)
а в качестве необходимых параметров, типа restapi.connect_address   указал внешний адрес.10.156.0.5 

>     scope: otus
>     #namespace: /service/
>     name: pg2
>     
>     restapi:
>       listen: 0.0.0.0:8008
>       connect_address: 10.156.0.5:8008
>     
>     etcd:
>       hosts:
>       - etcd1.europe-central2-a:2379
>       - etcd2.europe-west3-c:2379
>       - etcd3.europe-west4-c:2379
>     
>     postgresql:
>       listen: 0.0.0.0:5432
>       connect_address: 10.156.0.5:5432
>       data_dir: /var/lib/postgresql/data
>     #  bin_dir:
>       bin_dir: /usr/lib/postgresql/14/bin
>     #  config_dir: /etc/postgresql/14
>       pgpass: /tmp/pgpass0
>       authentication:
>         replication:
>           username: replicator
>           password: rep-pass
>         superuser:
>           username: postgres
>           password: zalando
>         rewind:  # Has no effect on postgres 10 and lower
>           username: rewind_user
>           password: rewind_password
>       # Server side kerberos spn
>     #  krbsrvname: postgres
>       parameters:
>         # Fully qualified kerberos ticket file for the running user
>         # same as KRB5CCNAME used by the GSS
>     #   krb_server_keyfile: /var/spool/keytabs/postgres
>         unix_socket_directories: '.'
>     
>     watchdog:
>        mode: off
>     
>     tags:
>         nofailover: false
>         noloadbalance: false
>         clonefrom: false
>         nosync: false

при первой попытке стартануть- ошибка:

>     Jan 19 15:38:49 pg2 patroni[10712]: pg_basebackup: error: connection to server at "10.164.0.25", port 5432 failed: FATAL:  no pg_hba.conf entry for replication connection from host "10.156.0.5", user "replicato>
>     Jan 19 15:38:49 pg2 patroni[10705]: 2022-01-19 15:38:49,492 ERROR: Error when fetching backup: pg_basebackup exited with code=1
>     Jan 19 15:38:49 pg2 patroni[10705]: 2022-01-19 15:38:49,492 WARNING: Trying again in 5 seconds

**no pg_hba.conf** entry 

решение: добавляем опцию в pg_hba.conf:
host replication replicator 10.156.0.5/32 md5

применяем изменения в pg_hba.conf с помощью:

>     patronictl -c /etc/patroni.yml reload otus pg1

если всё ок, то на второй ноде в конце-концов стартанёт патрони 

>     root@pg2:/# systemctl start patroni.service 
>     root@pg2:/# journalctl -fu  patroni.service  
>     -- Logs begin at Wed 2022-01-19 15:27:19 UTC. --
>     Jan 19 15:49:17 pg2 patroni[11258]: cp: cannot stat '../wal_archive/000000050000000000000005': No such file or directory
>     Jan 19 15:49:18 pg2 patroni[11259]: 2022-01-19 15:49:18.039 UTC [11259] FATAL:  could not start WAL streaming: ERROR:  replication  slot "pg2" does not exist
>     Jan 19 15:49:18 pg2 patroni[11261]: cp: cannot stat '../wal_archive/00000006.history': No such file or directory
>     Jan 19 15:49:18 pg2 patroni[11263]: cp: cannot stat '../wal_archive/000000050000000000000005': No such file or directory
>     Jan 19 15:49:18 pg2 patroni[11264]: 2022-01-19 15:49:18.109 UTC [11264] FATAL:  could not start WAL streaming: ERROR:  replication  slot "pg2" does not exist
>     Jan 19 15:49:18 pg2 patroni[11266]: cp: cannot stat '../wal_archive/00000006.history': No such file or directory
>     Jan 19 15:49:18 pg2 patroni[11267]: localhost:5432 - accepting connections
>     Jan 19 15:49:18 pg2 patroni[11230]: 2022-01-19 15:49:18,958 INFO: Lock owner: pg1; I am pg2
>     Jan 19 15:49:18 pg2 patroni[11230]: 2022-01-19 15:49:18,959 INFO: establishing a new patroni connection to the postgres cluster
>     Jan 19 15:49:18 pg2 patroni[11230]: 2022-01-19 15:49:18,993 INFO: no action. I am a secondary (pg2) and following a leader (pg1)
>     Jan 19 15:49:23 pg2 patroni[11274]: cp: cannot stat '../wal_archive/000000050000000000000005': No such file or directory
>     Jan 19 15:49:23 pg2 patroni[11275]: 2022-01-19 15:49:23.116 UTC [11275] FATAL:  could not start WAL streaming: ERROR:  replication  slot "pg2" does not exist
>     Jan 19 15:49:23 pg2 patroni[11277]: cp: cannot stat '../wal_archive/00000006.history': No such file or directory
>     Jan 19 15:49:26 pg2 patroni[11230]: 2022-01-19 15:49:26,798 INFO: no action. I am a secondary (pg2) and following a leader (pg1)
>     Jan 19 15:49:28 pg2 patroni[11279]: cp: cannot stat '../wal_archive/000000050000000000000005': No such file or directory
>     Jan 19 15:49:28 pg2 patroni[11280]: 2022-01-19 15:49:28.117 UTC [11280] LOG:  started streaming WAL from primary at 0/5000000 on  timeline 5
>     Jan 19 15:49:36 pg2 patroni[11230]: 2022-01-19 15:49:36,799 INFO: no action. I am a secondary (pg2) and following a leader (pg1)
>     Jan 19 15:49:46 pg2 patroni[11230]: 2022-01-19 15:49:46,796 INFO: no action. I am a secondary (pg2) and following a leader (pg1)

пример вывода patronictl -c /etc/patroni.yml list 

>     +--------+-------------+---------+---------+----+-----------+
>     | Member | Host        | Role    | State   | TL | Lag in MB |
>     + Cluster: otus (7054531535614542456) -----+----+-----------+
>     | pg1    | 10.164.0.25 | Leader  | running |  5 |           |
>     | pg2    | 10.156.0.5  | Replica | running |  5 |         0 |
>     +--------+-------------+---------+---------+----+-----------+


# настройка балансера напримере haproxy 


>     $ apt install haproxy 
пример конфига
>     global
>         maxconn 200
>     
>     defaults
>         log global
>         mode tcp
>         retries 2
>         timeout client 30m
>         timeout connect 4s
>         timeout server 30m
>         timeout check 5s
>     
>     frontend master_postgresql:5000
>         bind *:5000
>         default_backend backend_master
>     
>     backend backend_master                                                                                                                                                                                             
>         option httpchk OPTIONS/primary
>         http-check expect status 200                                                                                                                                                                                   
>         default-server inter 3s fall 3 rise 2                                                                                                                                                                          
>         server pg1 10.164.0.25:5432 maxconn 200 check port 8008 on-marked-down shutdown-sessions                                                                                                         
>         server pg2 10.156.0.5:5432 maxconn 200 check port 8008 on-marked-down shutdown-sessions                                                                                                         
>                                                                                                                                                                                                                        
>     listen standby                                                                                                                                                                                                     
>         bind *:5001                                                                                                                                                                                                    
>         option httpchk OPTIONS/replica                                                                                                                                                                                 
>         http-check expect status 200                                                                                                                                                                                   
>         default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions                                                                                                                                         
>         server pg1 10.164.0.25:5432 maxconn 100 check port 8008
>         server pg2 10.156.0.5:5432 maxconn 100 check port 8008
>                                                                                                                                                                                                                        
>     listen stats # Define a listen section called "stats"                                                                                                                                                              
>       bind :9000 # Listen on localhost:9000                                                                                                                                                                            
>       mode http
>       maxconn 10
>       stats enable  # Enable stats page
>       stats hide-version  # Hide HAProxy version
>       stats show-node
>       stats refresh 30s
>       stats realm Haproxy\ Statistics  # Title text for popup window
>       stats uri /stats  # Stats URI
>       stats auth admin:otusopass # Authentication credentials


в ситуации когда у нас несколько нод, а клиентское приложение будет регулярно пытаться присоединиться в одному и тому-же хост-ип, нам надо обеспечить баласировку с помощью своего ПО. я выбрал с помощью локального днс. в каждой зоне создам хост с именем **pg-balancer**, где будет находиться балансер который будет направлять мои запросы на рабочий хост постгреса.
В пределах одной сети,  обычно используется балансер на базе keepalived + haproxy.

                                                                                                                                                                                                
>     gcloud compute instances create pg-balancer --project=postgres-2021-328610 --zone=europe-west4-c --machine-type=e2-micro --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=pg-balancer,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any                                                                                                                                             
                                                                                                                                                                                                                   
>     gcloud compute instances create pg-balancer --project=postgres-2021-328610 --zone=europe-west4-a --machine-type=e2-micro --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=pg-balancer,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-a/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any                                                                                                                                             
                                                                                                                                                                                                                   
на каждой ноде поднимем баласер  haproxy с конфигом: 
>     global                                                                                                                                                                                                             
>         maxconn 200                                                                                                                                                                                                    
>                                                                                                                                                                                                                        
>     defaults                                                                                                                                                                                                           
>         log global                                                                                                                                                                                                     
>         mode tcp                                                                                                                                                                                                       
>         retries 2                                                                                                                                                                                                      
>         timeout client 30m                                                                                                                                                                                             
>         timeout connect 4s                                                                                                                                                                                             
>         timeout server 30m                                                                                                                                                                                             
>         timeout check 5s                                                                                                                                                                                               
>                                                                                                                                                                                                                        
>     frontend master_postgresql:5000                                                                                                                                                                                    
>         bind *:5000                                                                                                                                                                                                    
>         default_backend backend_master
>     
>     backend backend_master
>         option httpchk OPTIONS/primary
>         http-check expect status 200
>         default-server inter 3s fall 3 rise 2
>         server pg1 10.164.0.25:5432 maxconn 200 check port 8008 on-marked-down shutdown-sessions
>         server pg2 10.156.0.5:5432 maxconn 200 check port 8008 on-marked-down shutdown-sessions
>     
>     listen standby
>         bind *:5001
>         option httpchk OPTIONS/replica
>         http-check expect status 200
>         default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
>         server pg1 10.164.0.25:5432 maxconn 100 check port 8008
>         server pg2 10.156.0.5:5432 maxconn 100 check port 8008
>     
>     listen stats # Define a listen section called "stats"
>       bind :9000 # Listen on localhost:9000
>       mode http
>       maxconn 10
>       stats enable  # Enable stats page
>       stats hide-version  # Hide HAProxy version
>       stats show-node
>       stats refresh 30s
>       stats realm Haproxy\ Statistics  # Title text for popup window
>       stats uri /stats  # Stats URI
>       stats auth admin:otusopass # Authentication credentials

чтобы зайди на каждую ноду приходится указывать зону:
gcloud compute ssh pg-balancer  --zone=europe-west4-a
gcloud compute ssh pg-balancer  --zone=europe-west4-a
 
 
  
# Установка расширения pg-hostname


погуглил и нашёл например это: https://github.com/theory/pg-hostname 

очень простое расширение, https://github.com/theory/pg-hostname/blob/main/src/hostname.c реализация обёрточки единственного вызова gethostname()
Незнаю почему постгрес-ванильный не реализует его себе нативной функцией, предполагаю что они говорят "у нас модульная архитектура, добавляйте необходимые себе экстеншны сами". 

>     root@pg1:~# git clone https://github.com/theory/pg-hostname 
>     Cloning into 'pg-hostname'...
>     remote: Enumerating objects: 162, done.
>     remote: Counting objects: 100% (5/5), done.
>     remote: Compressing objects: 100% (4/4), done.
>     remote: Total 162 (delta 0), reused 3 (delta 0), pack-reused 157
>     Receiving objects: 100% (162/162), 47.02 KiB | 4.70 MiB/s, done.
>     Resolving deltas: 100% (70/70), done.
>     root@pg1:~# cd pg-hostname/
>     root@pg1:~/pg-hostname# make 
>     gcc -Wall -Wmissing-prototypes -Wpointer-arith -Wdeclaration-after-statement -Werror=vla -Wendif-labels -Wmissing-format-attribute -Wimplicit-fallthrough=3 -Wcast-function-type -Wformat-security -fno-strict-aliasing -fwrapv -fexcess-precision=standard -Wno-format-truncation -Wno-stringop-truncation -g -g -O2 -fstack-protector-strong -Wformat -Werror=format-security -fno-omit-frame-pointer -fPIC -I. -I./ -I/usr/include/postgresql/14/server -I/usr/include/postgresql/internal  -Wdate-time -D_FORTIFY_SOURCE=2 -D_GNU_SOURCE -I/usr/include/libxml2   -c -o src/hostname.o src/hostname.c
>     src/hostname.c:8:10: fatal error: postgres.h: No such file or directory
>         8 | #include "postgres.h"
>           |          ^~~~~~~~~~~~
> 
> 
> apt install -y postgresql-server-dev-14
> 
>     cd pg-hostname
>     make 
>     make install
> 
>     psql 
>     postgres=# CREATE EXTENSION hostname;
>     CREATE EXTENSION
>     postgres=# SELECT hostname();
>      hostname 
>     ----------
>      pg1

при этом, при работающей репликации нет необходимости делать CREATE EXTENSION hostname на репликах, эти изменения приедут по реплике, главное чтобы были необходимые библиотеки-бинарники. (кстати, их отстутствие, несовпадение версии, может привести к падению сервера).

>     postgres=# select hostname();
>      hostname 
>     ----------
>      pg2

# клиентская нагрузка
 хост клиентской нагрузки **pg-bench** 
 
 >     gcloud compute instances create pg-bench --project=postgres-2021-328610 --zone=europe-west4-c --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=749253047153-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --create-disk=auto-delete=yes,boot=yes,device-name=pg-bench,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20220110,mode=rw,size=10,type=projects/postgres-2021-328610/zones/europe-west4-c/diskTypes/pd-balanced --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any
 

 >     sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' ; 
 >     wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
 >     apt-get update 
 >     apt install mc postgresql-client-common postgresql-client-14
 >     apt install postgresql-14 #нужен для утилиты pgbench

 

чтобы избежать ввода пароля создадим файл с паролем: 
 >     oleg@pg-bench:~$ touch ~/.pgpass
 >     oleg@pg-bench:~$ chmod 600 ~/.pgpass
 >     oleg@pg-bench:~$ cat ~/.pgpass
 >     pg-balancer:*:*:postgres:zalando

 >     oleg@pg-bench:~$ psql -h pg-balancer -p 5000 -U postgres
 >     postgres=# select hostname();
 >      hostname 
 >     ----------
 >      pg1
 >     (1 row)
 >     
 >     postgres=# \q
 >     oleg@pg-bench:~$ psql -h pg-balancer -p 5001 -U postgres
 >     postgres=# select hostname();
 >      hostname 
 >     ----------
 >      pg2
 >     (1 row)

небольшая нагрузка 5 транзакций в секунду, автоматически переприсоединяться приложение не умеет, умеет лишь создавать каждый раз новый коннект но если будет отказ в создании соединения - приложение прекратит попытки работать дальше. поэтому просто :

>     while true ; do pgbench -h pg-balancer -p 5000 -U postgres -T 60 -R 5 -d -C  postgres  ; sleep 1 ; done 

Еще информация куда в данный момент смотрит балансер на 5000-м порту, который должен перенаправлять на лидера.
>     while true ; do psql -h pg-balancer -tA -p 5000 -U postgres -c 'select hostname(), now();'; sleep 1 ; done 

Видео с тем как патрони переключает лидера на другой хост. и как на это реагирует данные клиенты:
https://www.youtube.com/watch?v=bYzcn8qP5D0


# Заключение

Конечно, в проде, все эти работы по развёртыванию должен автоматизировать ansible-плейбук. Я показываю как это сделать неавтоматизируя. И показывая ньюансы как это всё работает изнутри.

