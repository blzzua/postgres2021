
-- запрос для формирования декларативного расписания
select  count(1), flight_no, departure_airport, arrival_airport, scheduled_departure_time, scheduled_arrival_time, lg1, lg2 from
(
    select flight_no, departure_airport, arrival_airport,
	       (scheduled_departure AT TIME ZONE 'UTC')::timestamp::time as scheduled_departure_time, 
		   (scheduled_arrival AT TIME ZONE 'UTC')::timestamp::time as scheduled_arrival_time,
			scheduled_departure - LAG(scheduled_departure) OVER ( PARTITION  by flight_no ORDER BY scheduled_departure ) as lg1,
			scheduled_arrival- scheduled_departure  as lg2
	from bookings.flights

) as t1
	where lg1 is not  null 
	group by flight_no, departure_airport, arrival_airport, scheduled_departure_time, scheduled_arrival_time, lg1, lg2
	order by flight_no;
	
-- запрос возвращает нормированное среднее время опоздания на рейсе. (нормированное к продолжиттельности полёта. время отклоняется "нормально" со средним 0 и дисперсией 5.775296818729433e-07**0.5
-- norm_delay = np.array([..])
-- plt.hist(norm_delay, bins=40)

select
	avg( (extract( EPOCH from ((scheduled_arrival-scheduled_departure) - (actual_arrival- actual_departure)))) 
	     / extract( EPOCH from (scheduled_arrival-scheduled_departure) )) as norm_avg_lag_diff
from  bookings.flights
where status = 'Arrived'
and scheduled_arrival <> scheduled_departure
group by flight_no

получается
фактическая_продолжительность_полёта =  продолжительность полёта + округлить_до_минуты ( max(-0.005, np.random.normal(0, 0.00076)) * продолжительность полёта) 
-0.005 - это отсечка максимальное время сокращения полёта, потому что нормальное распределение может и -0.9 выдать и тогда мы прилетим в 10 раз быстрее плана. 

-- тоже но абсолютные числа. 
select flight_no,
    count(1) as cnt,
	max( (scheduled_arrival-scheduled_departure) - (actual_arrival- actual_departure)) as max_lag_diff,
	avg((scheduled_arrival-scheduled_departure) - (actual_arrival- actual_departure)) as avg_lag_diff,
	max( (extract( EPOCH from ((scheduled_arrival-scheduled_departure) - (actual_arrival- actual_departure)))) 
	     / extract( EPOCH from (scheduled_arrival-scheduled_departure) )) as norm_avg_lag_diff
from  bookings.flights
where status = 'Arrived'
and scheduled_arrival <> scheduled_departure
group by flight_no


