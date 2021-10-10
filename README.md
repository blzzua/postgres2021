#### научиться работать с Google Cloud Platform на уровне Google Compute Engine (IaaS)
#### научиться управлять уровнем изолции транзации в PostgreSQL и понимать особенность работы уровней read commited и repeatable read
#### создать новый проект в Google Cloud Platform, например postgres2021-, где yyyymmdd год, месяц и день вашего рождения (имя проекта должно быть уникально на уровне GCP)


1. регистрация в cloud.google.com
2. создание проекта.
3. дать возможность доступа к этому проекту пользователю ifti@yandex.ru с ролью Project Editor 
  - Выбрать проект. 
  - Открыть https://console.cloud.google.com/iam-admin/iam
  - IAM -> IAM -> +ADD

4.  далее создать инстанс виртуальной машины Compute Engine с дефолтными параметрами
  - Compute -> Compute Engine ->  VM instances -> Create instance 
  - Выбрать имя, натыкать нужную конфигурацию, локацию, не забыть выбрать операционную систему в разделе Boot disk (ubuntu 20.04 as current lts)
  - Create  или equivalent command line 
  
5. добавить свой ssh ключ в GCE metadata
    - compute engine -> Metadata  -> SSH Keys
    - во время генерациия имя файла ключа лучше всего использовать 
    - ssh-keygen -f ~/.ssh/google_compute_engine
Если эту опцию выполнить раньше чем создать машину, тогда нет необходимости добавлять публичный ключ на удалённый хост. ssh-add 

6.    зайти удаленным ssh (первая сессия), не забывайте про ssh-add
  - установка gcloud cli для linux (не через snap), а через apt описано в https://cloud.google.com/sdk/docs/install: 
    - добавить урл репозитория, 
    - если в репо проверка подписи, то добавить добавить ключи в операционную систему
    - ``sudo apt-get install google-cloud-sdk``
  - при первом входе необходима аутентификация:
    gcloud auth login – запускает браузер, получает токен для дальнейшей работы. 
  - ``gcloud compute ssh pg-01 ``

***
    поставить PostgreSQL
    зайти вторым ssh (вторая сессия)
    запустить везде psql из под пользователя postgres
    выключить auto commit
    сделать в первой сессии новую таблицу и наполнить ее данными create table persons(id serial, first_name text, second_name text); insert into persons(first_name, second_name) values('ivan', 'ivanov'); insert into persons(first_name, second_name) values('petr', 'petrov'); commit;
    посмотреть текущий уровень изоляции: show transaction isolation level
    начать новую транзакцию в обоих сессиях с дефолтным (не меняя) уровнем изоляции
    в первой сессии добавить новую запись insert into persons(first_name, second_name) values('sergey', 'sergeev');
    сделать select * from persons во второй сессии
    видите ли вы новую запись и если да то почему?
    завершить первую транзакцию - commit;
    сделать select * from persons во второй сессии
    видите ли вы новую запись и если да то почему?
    завершите транзакцию во второй сессии
    начать новые но уже repeatable read транзации - set transaction isolation level repeatable read;
    в первой сессии добавить новую запись insert into persons(first_name, second_name) values('sveta', 'svetova');
    сделать select * from persons во второй сессии
    видите ли вы новую запись и если да то почему?
    завершить первую транзакцию - commit;
    сделать select * from persons во второй сессии
    видите ли вы новую запись и если да то почему?
    завершить вторую транзакцию
    сделать select * from persons во второй сессии
    видите ли вы новую запись и если да то почему?
    остановите виртуальную машину но не удаляйте ее
    
