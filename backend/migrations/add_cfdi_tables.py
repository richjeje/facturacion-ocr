# backend/migrations/add_cfdi_tables.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = 'add_cfdi_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Creación controlada de tablas CFDI con feature checks"""
    
    # Crear tabla cfdi_settings primero
    op.create_table(
        'cfdi_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pac_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('pac_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('is_test_mode', sa.Boolean(), nullable=True, default=True),
        sa.Column('feature_flags', sa.JSON(), nullable=True), # Changed from postgresql.JSONB to sa.JSON for compatibility
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_settings', 'cfdi_settings', ['user_id'], unique=False)
    
    # Tablas CFDI
    op.create_table(
        'cfdi_certificates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('certificate_name', sa.String(255), nullable=True),
        sa.Column('cer_file_content', sa.LargeBinary(), nullable=True),
        sa.Column('key_file_content', sa.LargeBinary(), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('sat_rfc', sa.String(13), nullable=True),
        sa.Column('certificate_number', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'cfdi_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('uuid', sa.String(36), nullable=True),
        sa.Column('xml_draft', sa.Text(), nullable=True),
        sa.Column('xml_signed', sa.Text(), nullable=True),
        sa.Column('xml_timbrado', sa.Text(), nullable=True),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        sa.Column('pac_name', sa.String(100), nullable=True, default='facturama'),
        sa.Column('pac_response', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='draft'),
        sa.Column('stamp_date', sa.DateTime(), nullable=True),
        sa.Column('cancel_date', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )

    op.create_table(
        'cfdi_catalogs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('catalog_type', sa.String(50), nullable=True),
        sa.Column('key', sa.String(10), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('version', sa.String(10), nullable=True, default='4.0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Insertar catálogos SAT iniciales
    # Note: Alembic's op.execute is safer than raw SQL for portability, but for data insertion raw SQL is often used.
    # The snippet provided uses PostgreSQL specific unnest/ARRAY syntax. I'll include it but wrap in try/except or comment
    # that it might fail on SQLite. For SQLite we should use individual inserts.
    
    # Simplified insertion for compatibility
    op.execute("INSERT INTO cfdi_catalogs (catalog_type, key, description, version) VALUES ('c_UsoCFDI', 'G01', 'Adquisición de mercancías', '4.0')")
    op.execute("INSERT INTO cfdi_catalogs (catalog_type, key, description, version) VALUES ('c_UsoCFDI', 'G02', 'Devoluciones, descuentos o bonificaciones', '4.0')")
    op.execute("INSERT INTO cfdi_catalogs (catalog_type, key, description, version) VALUES ('c_UsoCFDI', 'G03', 'Gastos en general', '4.0')")
    
def downgrade():
    """Reversión segura de migración"""
    op.drop_table('cfdi_catalogs')
    op.drop_table('cfdi_invoices')
    op.drop_table('cfdi_certificates')
    op.drop_table('cfdi_settings')
