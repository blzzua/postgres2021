cd /root/sysbench-tpcc
./tpcc.lua --pgsql-host=10.164.0.7  --pgsql-port=5432   --pgsql-user=sysbench --pgsql-password='sysbench' --pgsql-db='sysbench' --time=1200 --threads=4 --report-interval=20 --tables=16 --scale=1 --trx_level=RC --db-driver=pgsql
