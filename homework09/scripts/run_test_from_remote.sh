cd /root/sysbench-tpcc
./tpcc.lua --pgsql-host=10.164.0.7  --pgsql-port=5432   --pgsql-user=sysbench --pgsql-password='sysbench' --pgsql-db='sysbench' --time=600 --threads=16 --report-interval=10 --tables=16 --scale=1 --trx_level=RC --db-driver=pgsql
