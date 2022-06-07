# compose_flask/app.py
from re import S
from flask import Flask, render_template, request, url_for
from redis import Redis
import boto3
from boto3.dynamodb.conditions import Key
import uuid
import time

app = Flask(__name__)

def create_table_and_seed(dynamodb_resource,dynamodb_client):
    existing_tables = dynamodb_client.list_tables()['TableNames']
    
    if 'transactions' in existing_tables:
        table_del = dynamodb_resource.Table('transactions')
        table_del.delete()
    
    if 'totals' in existing_tables:
        table_del = dynamodb_resource.Table('totals')
        table_del.delete()
    
    table = dynamodb_resource.create_table(
        TableName='totals',
        KeySchema=[
            {
                'AttributeName': 'account_name',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'account_name',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1,
        }
    )
    table = dynamodb_resource.create_table(
        TableName='transactions',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1,
        }
    )
    #let table create
    time.sleep(5)

    #seed initial Balance
    totals = dynamodb_resource.Table('totals')
    totals.put_item(
        Item={
            'account_name':'Paul',
            'balance':100
        }
    )
    totals.put_item(
        Item={
            'account_name':'Matt',
            'balance':100
        }
    )

    print("Table status:", table.table_status)

@app.route('/load')
def load():
    dynamodb_resource = boto3.resource('dynamodb', region_name='ap-northeast-1')
    dynamodb_client = boto3.client('dynamodb', region_name='ap-northeast-1')
    create_table_and_seed(dynamodb_resource, dynamodb_client)
    return 'Database Created and seeded'

@app.route('/', methods=['GET','POST'])
def transact():
    amount_paul = request.form.get('amount_paul')
    amount_matt = request.form.get('amount_matt')
    transact = False
    if amount_paul is not None:
         transact = True
    if amount_matt is not None:
         transact = True


    if transact:
        dynamodb_client = boto3.client('dynamodb', region_name='ap-northeast-1')
        transaction_details = {'debit':'','credit':'','amount':0}
        if amount_paul is None:
            transaction_details['debit'] = 'Matt'
            transaction_details['credit'] = 'Paul'
            transaction_details['amount'] = amount_matt
        else:
            transaction_details['debit'] = 'Paul'
            transaction_details['credit'] = 'Matt'
            transaction_details['amount'] = amount_paul
        try:
            response = dynamodb_client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': 'transactions',
                            'Item': {
                                'id': { 'S': str(uuid.uuid4()) },
                                'credit': { 'S': transaction_details['credit'] },
                                'debit': { 'S': transaction_details['debit'] },
                                'amount': { 'N': transaction_details['amount'] },
                            }
                        }
                    },
                    {
                        'Update': {
                            'TableName': 'totals',
                            'Key': {
                                'account_name': {
                                    'S': transaction_details['debit']
                                }
                            },
                            'ConditionExpression': 'balance >= :amount',
                            'UpdateExpression': 'set balance = balance - :amount',
                            'ExpressionAttributeValues': {
                                ':amount': {'N': transaction_details['amount'] }
                            }
                        }
                    },
                    {
                        'Update': {
                            'TableName': 'totals',
                            'Key': {
                                'account_name': {
                                    'S': transaction_details['credit']
                                }
                            },
                            'UpdateExpression': 'set balance = balance + :amount',
                            'ExpressionAttributeValues': {
                                ':amount': {'N': transaction_details['amount']}
                            }
                        }
                    },
                ]
            )
            mesage = 'Moved $' + str(transaction_details['amount']) + ' from ' + transaction_details['debit'] + ' to ' + transaction_details['credit']
        except:
            mesage = transaction_details['debit'] + ' has insufficient Funds'
    else:
        mesage = ''

    dynamodb_resource = boto3.resource('dynamodb', region_name='ap-northeast-1')
         
    balances =  dynamodb_resource.Table('totals').scan()['Items']
    transactions = dynamodb_resource.Table('transactions').scan()['Items']

    return render_template('index.html', title='Ledger', bank_message=mesage, balances=balances, transactions=transactions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
