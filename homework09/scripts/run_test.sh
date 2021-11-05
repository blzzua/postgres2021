BASE_PG_TUNE_CONFIG=/root/script/03-pgtune.conf ## конфиг предложенный pgtune
TEST_CONFIG=/root/script/04-test.conf           ## изменения, которые скрипт вносит в конфиг предложенный pgtune
cp -f $BASE_PG_TUNE_CONFIG $TEST_CONFIG


reload_conf(){
    PGPASSWORD=sysbench psql -h 127.0.0.1 -U sysbench -c 'select pg_reload_conf();'
}

restart_conf(){
    systemctl restart postgresql@13-main.service
    echo 1 > /proc/sys/vm/drop_caches
}
warm_caches(){
    ssh 10.164.0.9 < run_warm_from_remote.sh | tee warm.txt
    mv warm.txt /root/script/results/warm-$shared_buffers.txt
}


for shared_buffers in 2048 1024 512 256 128
do
    echo "shared_buffers = ${shared_buffers}MB" > $TEST_CONFIG
    restart_conf;
    warm_caches;

    for work_mem in 16384 8192 4096 2048 512 256
    do
        echo "work_mem = ${work_mem}kB" >> $TEST_CONFIG
        cp $TEST_CONFIG /etc/postgresql/13/main/conf.d/
        reload_conf;
        ssh 10.164.0.9 < run_test_from_remote.sh | tee  res.txt
        mv res.txt /root/script/results/${shared_buffers}_mb_x_${work_mem}_kb.txt
    done
done


# еще использовал удалнный вызов скриптов:
# run_test_from_remote.sh 
#cd /root/sysbench-tpcc
#./tpcc.lua --pgsql-host=10.164.0.7  --pgsql-port=5432   --pgsql-user=sysbench --pgsql-password='sysbench' --pgsql-db='sysbench' --time=600 --threads=16 --report-interval=10 --tables=16 --scale=1 --trx_level=RC --db-driver=pgsql
# run_warm_from_remote.sh 
#cd /root/sysbench-tpcc
#./tpcc.lua --pgsql-host=10.164.0.7  --pgsql-port=5432   --pgsql-user=sysbench --pgsql-password='sysbench' --pgsql-db='sysbench' --time=1200 --threads=4 --report-interval=20 --tables=16 --scale=1 --trx_level=RC --db-driver=pgsql
