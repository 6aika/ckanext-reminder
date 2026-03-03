"""Create ckanext-reminder tables

Revision ID: c308a188cbdc
Revises: 
Create Date: 2026-01-12 08:14:22.340015

"""
from alembic import op
import sqlalchemy as sa
import datetime
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = 'c308a188cbdc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()

    if "reminder_subscription" not in tables:
        op.create_table(
            "reminder_subscription",
            sa.Column("id", sa.UnicodeText, primary_key=True, default=uuid4),
            sa.Column("subscriber_email", sa.UnicodeText, nullable=False),
            sa.Column("previous_reminder_sent", sa.DateTime, default=datetime.datetime.now),
            sa.Column("unsubscribe_token", sa.UnicodeText, nullable=False, default=uuid4),
            sa.Column("created", sa.DateTime, default=datetime.datetime.now),
            sa.Column("updated", sa.DateTime, default=datetime.datetime.now),
        )


def downgrade():
    op.drop_table('reminder_subscription')
