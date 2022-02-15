
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
	order by flight_no
