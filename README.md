# dynamo-sample-ledger

Dependencies:
- Docker

This is simple to demo, clone the repo...

```
git clone https://github.com/kukielp/dynamo-sample-ledger.git
```

Open a terminal and run:
```
docker-compose up --build
```

Open a browser window and seed the database:
[Seed the Database](http://127.0.0.1:5000/load)

Then play with the ledger
[The App](http://127.0.0.1:5000/)

If you want to look at the DynamoDB table ( locally ) download [No SQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.settingup.html) and open a new local connection.