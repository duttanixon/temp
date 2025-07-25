"""Add IoT Thing Group fields to Customer

Revision ID: e38fa73a76c9
Revises: 0001
Create Date: 2025-04-26 10:53:44.478767

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e38fa73a76c9'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('customers', sa.Column('iot_thing_group_name', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('iot_thing_group_arn', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('customers', 'iot_thing_group_arn')
    op.drop_column('customers', 'iot_thing_group_name')
    # ### end Alembic commands ###