"""initial version

Revision ID: f43c03634e55
Revises:
Create Date: 2017-06-03 16:14:19.529871

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f43c03634e55'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column(
            'username',
            sa.Unicode(length=255),
            nullable=False,
            unique=True
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'initial_tokens',
        sa.Column('user_id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('token', sa.Unicode(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'access_tokens',
        sa.Column('user_id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('token_hash', sa.Unicode(length=80), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )


def downgrade():
    pass
