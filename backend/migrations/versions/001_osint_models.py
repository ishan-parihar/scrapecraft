"""Add OSINT models tables

Revision ID: 001_osint_models
Revises: 
Create Date: 2025-11-02 18:50:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '001_osint_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create investigations table
    op.create_table(
        'investigations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('classification', sa.Enum('UNCLASSIFIED', 'CONFIDENTIAL', 'SECRET', name='investigationclassification'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='investigationpriority'), nullable=False),
        sa.Column('status', sa.Enum('PLANNING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED', name='investigationstatus'), nullable=False),
        sa.Column('current_phase', sa.Enum('PLANNING', 'RECONNAISSANCE', 'COLLECTION', 'ANALYSIS', 'SYNTHESIS', 'REPORTING', name='investigationphase'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create targets table
    op.create_table(
        'investigation_targets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('PERSON', 'ORGANIZATION', 'LOCATION', 'DOMAIN', 'SOCIAL_MEDIA', 'OTHER', name='investigationtargettype'), nullable=False),
        sa.Column('identifier', sa.String(), nullable=False),
        sa.Column('aliases', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='investigationpriority'), nullable=False),
        sa.Column('collection_requirements', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'COMPLETED', 'FAILED', name='targetstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create intelligence_requirements table
    op.create_table(
        'intelligence_requirements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='investigationpriority'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create agent_assignments table
    op.create_table(
        'agent_assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('agent_type', sa.Enum('PLANNING', 'COLLECTION', 'ANALYSIS', 'SYNTHESIS', name='agenttype'), nullable=False),
        sa.Column('assigned_targets', sa.Text(), nullable=True),
        sa.Column('current_task', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('IDLE', 'ACTIVE', 'WAITING', 'COMPLETED', 'ERROR', name='agentstatus'), nullable=False),
        sa.Column('performance_metrics', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create evidence table
    op.create_table(
        'collected_evidence',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_type', sa.Enum('SOCIAL_MEDIA', 'PUBLIC_RECORDS', 'WEB_CONTENT', 'DARK_WEB', 'HUMINT', name='evidencesourcetype'), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content_data', sa.Text(), nullable=False),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('content_tags', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('analyst_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('evidence_id', sa.String(), nullable=True),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('analysis_type', sa.String(), nullable=False),
        sa.Column('results', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('analyst_id', sa.String(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evidence_id'], ['collected_evidence.id']),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create threat_assessments table
    op.create_table(
        'threat_assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('threat_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='threatlevel'), nullable=False),
        sa.Column('threat_type', sa.String(), nullable=False),
        sa.Column('targets', sa.Text(), nullable=True),
        sa.Column('likelihood', sa.Float(), nullable=False),
        sa.Column('impact', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('analyst_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create phase_transitions table
    op.create_table(
        'phase_transitions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('from_phase', sa.Enum('PLANNING', 'RECONNAISSANCE', 'COLLECTION', 'ANALYSIS', 'SYNTHESIS', 'REPORTING', name='investigationphase'), nullable=False),
        sa.Column('to_phase', sa.Enum('PLANNING', 'RECONNAISSANCE', 'COLLECTION', 'ANALYSIS', 'SYNTHESIS', 'REPORTING', name='investigationphase'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create reports table
    op.create_table(
        'investigation_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('classification', sa.Enum('UNCLASSIFIED', 'CONFIDENTIAL', 'SECRET', name='investigationclassification'), nullable=False),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('recipients', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('distributed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create final_assessments table
    op.create_table(
        'final_assessments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('investigation_id', sa.String(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('key_findings', sa.Text(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('overall_threat_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='threatlevel'), nullable=False),
        sa.Column('classification', sa.Enum('UNCLASSIFIED', 'CONFIDENTIAL', 'SECRET', name='investigationclassification'), nullable=False),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop all OSINT tables
    op.drop_table('final_assessments')
    op.drop_table('investigation_reports')
    op.drop_table('phase_transitions')
    op.drop_table('threat_assessments')
    op.drop_table('analysis_results')
    op.drop_table('collected_evidence')
    op.drop_table('agent_assignments')
    op.drop_table('intelligence_requirements')
    op.drop_table('investigation_targets')
    op.drop_table('investigations')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS investigationclassification;")
    op.execute("DROP TYPE IF EXISTS investigationpriority;")
    op.execute("DROP TYPE IF EXISTS investigationstatus;")
    op.execute("DROP TYPE IF EXISTS investigationphase;")
    op.execute("DROP TYPE IF EXISTS investigationtargettype;")
    op.execute("DROP TYPE IF EXISTS targetstatus;")
    op.execute("DROP TYPE IF EXISTS agenttype;")
    op.execute("DROP TYPE IF EXISTS agentstatus;")
    op.execute("DROP TYPE IF EXISTS evidencesourcetype;")
    op.execute("DROP TYPE IF EXISTS threatlevel;")