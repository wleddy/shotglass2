import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app


@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        with app.app.test_request_context():
            #this context sets up a dummy request with a url of 'http://localhost/'
            app.initalize_all_tables((app.get_db(app.app.config['DATABASE_PATH'])))
            app.get_db()
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE_PATH'])
