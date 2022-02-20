import psycopg2
from numpy.random import choice
import itertools
import random
import datetime

ro_conn = psycopg2.connect(
    host="localhost",
    database="demo",
    user="demo",
    password="demo")
ro_cur = ro_conn.cursor()



ro_cur.execute('select departure_airport, arrival_airport, min(duration) as duration from bookings.routes group by departure_airport,arrival_airport;');
all_routes_duration  = ro_cur.fetchall()
all_routes = [(departure_airport, arrival_airport) for departure_airport, arrival_airport, duration in all_routes_duration]

ro_cur.execute('select departure_airport, count(1) from bookings.routes group by departure_airport;');
all_airport = ro_cur.fetchall()
routes, density_int = zip(*all_airport)
density_sum = sum(density_int)
density = [d/density_sum for r,d in all_airport]

def gen_random_route():
    ro_cur.execute('select departure_airport, count(1) from bookings.routes group by departure_airport;');
    all_airport = ro_cur.fetchall()
    routes, density_int = zip(*all_airport)
    density_sum = sum(density_int)
    density = [d/density_sum for r,d in all_airport]
    departure_airport,arrival_airport  = choice(routes, size=2,  replace=False, p=density)
    return departure_airport,arrival_airport 

def test_route_solver(n):
    cnt2=0
    cnt3=0
    cnt4=0
    for i in range(n):
        departure_airport,arrival_airport  = choice(routes, size=2,  replace=False, p=density)
        if (departure_airport,arrival_airport) in all_routes:
            cnt2+=1
            print("2:", (departure_airport,arrival_airport))
        else:
            transit = {a for (d,a) in all_routes if d == departure_airport} & {d for (d,a) in all_routes if a == arrival_airport}
            if transit:
                cnt3+=1
                # TODO: выбирать оптимальный маршрут вместо случайного.
                print("3:", (departure_airport,random.choice(list(transit)),arrival_airport))
            else:
                cnt4+=1
                possible_routes = []
                min_duration = datetime.timedelta(days=999)
                t1 = [a1 for a1 in routes if (departure_airport,a1) in all_routes]
                t2 = [d1 for d1 in routes if (d1, arrival_airport) in all_routes]
                possible_transit_routes = [r for r in itertools.product(t1,t2) if r in all_routes]
                for t1,t2 in possible_transit_routes:
                    (a1,a2,d1) = [(a1,a2,d1) for a1,a2,d1 in all_routes_duration if (a1,a2) == (departure_airport, t1)][0]
                    (a2,a3,d2) = [(a2,a3,d2) for a2,a3,d2 in all_routes_duration if (a2,a3) == (t1, t2)][0]
                    (a3,a4,d3) = [(a3,a4,d3) for a3,a4,d3 in all_routes_duration if (a3,a4) == (t2, arrival_airport)][0]
                    d = d1+d2+d3
                    possible_routes.append((a1,a2,a3,a4,d))
                    if (d < min_duration):
                        min_duration = d
                        best_route = (a1,a2,a3,a4)
                    print("4:", best_route)

test_route_solver(100)
