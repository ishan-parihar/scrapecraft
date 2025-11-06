"""Add data persistence tables

Revision ID: 002_data_persistence
Revises: 001_osint_models
Create Date: 2025-11-05 16:45:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '002_data_persistence'
down_revision = '001_osint_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create investigation_states table
    op.create_table(
        'investigation_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('state_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investigation_states_investigation_id'), 'investigation_states', ['investigation_id'], unique=True)

    # Create workflow_states table
    op.create_table(
        'workflow_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(), nullable=False),
        sa.Column('workflow_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_states_workflow_id'), 'workflow_states', ['workflow_id'], unique=True)

    # Create websocket_connections table
    op.create_table(
        'websocket_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.String(), nullable=False),
        sa.Column('pipeline_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_websocket_connections_connection_id'), 'websocket_connections', ['connection_id'], unique=True)
    op.create_index(op.f('ix_websocket_connections_pipeline_id'), 'websocket_connections', ['pipeline_id'], unique=False)

    # Create task_results table
    op.create_table(
        'task_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('task_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_results_task_id'), 'task_results', ['task_id'], unique=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, default='info'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('session_data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_session_id'), 'user_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)


def downgrade():
    # Drop all persistence tables
    op.drop_table('user_sessions')
    op.drop_table('audit_logs')
    op.drop_table('task_results')
    op.drop_table('websocket_connections')
    op.drop_table('workflow_states')
    op.drop_table('investigation_states')