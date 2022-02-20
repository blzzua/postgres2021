import psycopg2 
import random
import datetime

conn = psycopg2.connect(
    host="localhost",
    database="demo",
    user="demo",
    password="demo")
rw_cur = conn.cursor()

ro_conn = psycopg2.connect(
    host="localhost",
    database="demo",
    user="demo",
    password="demo")
ro_cur = ro_conn.cursor()


ro_cur .execute('select dt from public.now_timetick;')
cur_dt = ro_cur.fetchone()[0]


def get_book_ref():
    """
    генерируем book_ref:
    у нас всего лишь  bpchar(6)
    в проде генерировать придется с помощью создания справочника на 16 млн, и удаления из него использованных значений. 
    пока использованных 2млн, емкость 16 млн. просто создаем случайный на 6 байт и  проверяем его наличие. если нет тогда используем.
    """
    while True:
        book_ref = format(random.randint(0,2**24), '#06x')[2:].upper()
        ro_cur.execute('select exists(select 1 from bookings.bookings where book_ref = %s ) ;',(book_ref,) )
        if not ro_cur.fetchone()[0]:
            # айдишник свободен. используем
            break
    return book_ref


def get_ticket_no():
    # генерация номера билета.
    # у каждого обработчика есть номерная серия вида 0005436 и номер в серии из 6 букв.
    ticket_serie = '0005436'
    ro_cur.execute("select max(ticket_no), ('x' || lpad(max(ticket_no), 13, '0'))::bit(64)::bigint AS int_val from bookings.tickets t where ticket_no like '0005436%';"  )
    ( max_ticket_no, int_val ) = ro_cur.fetchone()
    if max_ticket_no is None:
        ticket_no = ticket_serie + '000000'
    else:
        # TODO: обработку случая 999999
        ticket_no = str( int(max_ticket_no) + 1 ).zfill(13)
    return ticket_no 

def chose_fare_price(flight_no):
    query_price = """select max(amount), fare_conditions from bookings.ticket_flights tf
    where flight_id in (select flight_id  from bookings.flights f where flight_no = %s and status = 'Arrived' order by scheduled_departure desc limit 100 )
    group by fare_conditions;"""
    ro_cur.execute(query_price, (flight_no,))
    price_table = ro_cur.fetchall()
    amount, fare_conditions = random.choice(price_table)
    return amount, fare_conditions

def get_flight_id(flight_no, expected_date_departure):
    ro_cur.execute("select f.flight_id from bookings.flights f where flight_no = %s and status in ('Scheduled', 'On Time')  and scheduled_departure > %s order by scheduled_departure;", (flight_no, expected_date_departure))
    # TODO: получать несколько, и проверять наличие свободных на найденных рейсах.
    ids = ro_cur.fetchone()
    if ids:
        return ids[0]
    else:
        return -1


def booking(passenger_name = 'IVAN IVANOV', departure_airport='VKO',arrival_airport = 'SKX', expected_date_departure = cur_dt ):
    routes = ro_cur.execute('select * from bookings.routes where  (departure_airport, arrival_airport) = ( %s, %s );',
                        (departure_airport,arrival_airport));
    #{'departure_airport': departure_airport, 'arrival_airport': arrival_airport})
    routes = ro_cur.fetchone()
    if routes:
        flight_no = routes[0]
    else:
        #pass
        return {"ok": False, "book_ref": None, "reason":"No such route" }
    
    book_ref = get_book_ref()
    if book_ref:
        query_bookings_ins = """INSERT INTO bookings.bookings (book_ref, book_date, total_amount) VALUES (%s, %s, %s);"""
        query_bookings_arg = (book_ref, cur_dt, 0)
        passenger_id = '1234 132456';
        conn.commit()
    else: 
        return {"ok": False, "book_ref": None, "reason":"Cannot receive book_ref" }

    ticket_no = get_ticket_no()
    flight_id = get_flight_id(flight_no, expected_date_departure)
    amount, fare_conditions = chose_fare_price(flight_no)

    query_tickets_ins = "INSERT INTO bookings.tickets (ticket_no, book_ref, passenger_id, passenger_name) VALUES (%s, %s, %s, %s);"
    query_tickets_arg = (ticket_no, book_ref, passenger_id, passenger_name)
    rw_cur.execute(query_bookings_ins, query_bookings_arg)
    rw_cur.execute(query_tickets_ins, query_tickets_arg)

    rw_cur.execute("""INSERT INTO bookings.ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES (%s, %s, %s, %s)""", 
                   (ticket_no, flight_id, fare_conditions, amount) )

    query_bookings_ins = """INSERT INTO bookings.bookings (book_ref, book_date, total_amount) VALUES (%s, %s, %s);"""
    query_bookings_arg = (book_ref, cur_dt, 0)
    conn.commit()
    return {"ok": True, "book_ref": book_ref }
