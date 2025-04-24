import click
from flask import current_app
from app import db

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    with current_app.open_resource('schema.sql') as f:
        connection = db.connect()
        with connection.cursor() as cursor:
            for _ in cursor.execute(f.read().decode('utf8'), multi=True):
                pass
        connection.commit()
    click.echo('Initialized the database.')