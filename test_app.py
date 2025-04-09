import pytest
import boto3
from moto import mock_dynamodb
from app import app
import io

@pytest.fixture
def client():
    """Set up the Flask testing client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_dynamodb_table():
    """Fixture to mock AWS DynamoDB with Moto."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='JobApplications',
            KeySchema=[{'AttributeName': 'JobID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'JobID', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
        )
        yield table

def test_index(client, mock_dynamodb_table):
    """Test the index route."""
    job_data = {
        'JobID': '1234',
        'Company': 'Test Company',
        'Role': 'Developer',
        'Status': 'Applied',
        'DateApplied': '2025-04-08',
        'ResumeURL': '/uploads/test_resume.pdf',
    }
    mock_dynamodb_table.put_item(Item=job_data)

    response = client.get('/')
    assert response.status_code == 200
    assert b'Test Company' in response.data
    assert b'Developer' in response.data

def test_add_job(client, mock_dynamodb_table):
    """Test the add_job route with file upload."""
    # Simulate a real file using BytesIO
    file_data = (io.BytesIO(b"Dummy resume content"), 'test_resume.pdf')

    data = {
        'company': 'New Company',
        'role': 'Tester',
        'status': 'Applied',
        'resume': file_data,
    }

    response = client.post('/add', data=data, content_type='multipart/form-data')
    assert response.status_code == 302  # Redirect after adding job

    response = mock_dynamodb_table.scan()
    items = response['Items']
    assert len(items) > 0
    assert items[0]['Company'] == 'New Company'


def test_edit_job(client, mock_dynamodb_table):
    """Test the edit_job route."""
    job_data = {
        'JobID': '1234',
        'Company': 'Test Company',
        'Role': 'Developer',
        'Status': 'Applied',
        'DateApplied': '2025-04-08',
        'ResumeURL': '/uploads/test_resume.pdf',
    }
    mock_dynamodb_table.put_item(Item=job_data)

    response = client.post('/edit/1234', data={'status': 'Interview'})
    assert response.status_code == 302

    response = mock_dynamodb_table.get_item(Key={'JobID': '1234'})
    item = response.get('Item')
    assert item['Status'] == 'Interview'

def test_delete_job(client, mock_dynamodb_table):
    """Test the delete_job route."""
    job_data = {
        'JobID': '1234',
        'Company': 'Test Company',
        'Role': 'Developer',
        'Status': 'Applied',
        'DateApplied': '2025-04-08',
        'ResumeURL': '/uploads/test_resume.pdf',
    }
    mock_dynamodb_table.put_item(Item=job_data)

    response = client.post('/delete/1234')
    assert response.status_code == 302

    response = mock_dynamodb_table.get_item(Key={'JobID': '1234'})
    assert 'Item' not in response