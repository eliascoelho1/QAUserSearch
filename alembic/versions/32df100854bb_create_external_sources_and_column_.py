"""create_external_sources_and_column_metadata

Revision ID: 32df100854bb
Revises: 
Create Date: 2026-01-29 22:02:32.293093

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '32df100854bb'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create external_sources and column_metadata tables."""
    # Create external_sources table
    op.create_table(
        'external_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('db_name', sa.String(length=100), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('cataloged_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('document_count', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('db_name', 'table_name', name='uq_source_identity')
    )
    op.create_index('ix_external_sources_db_name', 'external_sources', ['db_name'])
    op.create_index('ix_external_sources_table_name', 'external_sources', ['table_name'])

    # Create column_metadata table
    op.create_table(
        'column_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('column_name', sa.String(length=255), nullable=False),
        sa.Column('column_path', sa.String(length=500), nullable=False),
        sa.Column('inferred_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_enumerable', sa.Boolean(), nullable=False, default=False),
        sa.Column('unique_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('presence_ratio', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('enrichment_status', sa.String(length=20), nullable=False, default='not_enriched'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['external_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', 'column_path', name='uq_column_identity'),
        sa.CheckConstraint('presence_ratio >= 0.0 AND presence_ratio <= 1.0', name='ck_presence_ratio'),
        sa.CheckConstraint(
            "enrichment_status IN ('not_enriched', 'pending_enrichment', 'enriched')",
            name='ck_enrichment_status'
        )
    )
    op.create_index('ix_column_metadata_source_id', 'column_metadata', ['source_id'])
    op.create_index('ix_column_metadata_inferred_type', 'column_metadata', ['inferred_type'])
    op.create_index('ix_column_metadata_is_enumerable', 'column_metadata', ['is_enumerable'])
    op.create_index('ix_column_metadata_enrichment_status', 'column_metadata', ['enrichment_status'])


def downgrade() -> None:
    """Drop external_sources and column_metadata tables."""
    op.drop_index('ix_column_metadata_enrichment_status', table_name='column_metadata')
    op.drop_index('ix_column_metadata_is_enumerable', table_name='column_metadata')
    op.drop_index('ix_column_metadata_inferred_type', table_name='column_metadata')
    op.drop_index('ix_column_metadata_source_id', table_name='column_metadata')
    op.drop_table('column_metadata')

    op.drop_index('ix_external_sources_table_name', table_name='external_sources')
    op.drop_index('ix_external_sources_db_name', table_name='external_sources')
    op.drop_table('external_sources')
