"""add_created_status_to_device_status_enum

Revision ID: 26fb81d51999
Revises: 5008ccac06ed
Create Date: 2025-05-02 11:57:14.381981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26fb81d51999'
down_revision = '5008ccac06ed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a new temporary enum with the new value
    op.execute("CREATE TYPE device_status_new AS ENUM ('CREATED', 'PROVISIONED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'DECOMMISSIONED')")
    
    # Update the column to use the new enum type
    # First, create a new column with the new enum type
    op.add_column('devices', sa.Column('status_new', sa.Enum('CREATED', 'PROVISIONED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'DECOMMISSIONED', name='device_status_new'), nullable=True))
    
    # Copy data from the old column to the new one, mapping 'PROVISIONED' to 'CREATED' for devices without thing_name
    op.execute("""
    UPDATE devices 
    SET status_new = CASE 
        WHEN status = 'PROVISIONED' AND thing_name IS NULL THEN 'CREATED'::device_status_new 
        ELSE status::text::device_status_new 
    END
    """)
    
    # Drop the old column
    op.drop_column('devices', 'status')
    
    # Rename the new column to the original name
    op.alter_column('devices', 'status_new', new_column_name='status', nullable=False, 
                   server_default=sa.text("'CREATED'::device_status_new"))
    
    # Drop the old enum type
    op.execute("DROP TYPE device_status")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE device_status_new RENAME TO device_status")


def downgrade() -> None:
    # For downgrade, we'll convert all 'CREATED' statuses back to 'PROVISIONED'
    
    # Create a new temporary enum without 'CREATED'
    op.execute("CREATE TYPE device_status_old AS ENUM ('PROVISIONED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'DECOMMISSIONED')")
    
    # Create a new column with the old enum type
    op.add_column('devices', sa.Column('status_old', sa.Enum('PROVISIONED', 'ACTIVE', 'INACTIVE', 'MAINTENANCE', 'DECOMMISSIONED', name='device_status_old'), nullable=True))
    
    # Copy data, converting 'CREATED' to 'PROVISIONED'
    op.execute("""
    UPDATE devices 
    SET status_old = CASE 
        WHEN status = 'CREATED' THEN 'PROVISIONED'::device_status_old 
        ELSE status::text::device_status_old 
    END
    """)
    
    # Drop the current column
    op.drop_column('devices', 'status')
    
    # Rename the new column to the original name
    op.alter_column('devices', 'status_old', new_column_name='status', nullable=False, 
                   server_default=sa.text("'PROVISIONED'::device_status_old"))
    
    # Drop the new enum type
    op.execute("DROP TYPE device_status")
    
    # Rename the old enum type to the original name
    op.execute("ALTER TYPE device_status_old RENAME TO device_status")
