"""Initial DMS tables

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000

Creates all tables for the DMS (Device Management System) application:
- users
- devices
- documents
- maintenance_plan, maintenance_record, repair_record
- approval_requests, approval_steps
- audit_logs, system_settings
- borrow_records
- spare_parts, spare_part_inbounds, spare_part_consumptions, spare_part_alerts
- electronic_signatures
- device_status_requests
- password_reset_requests
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ───────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(128), unique=True, nullable=False),
        sa.Column("password", sa.String(256), nullable=False),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("permissions", sa.Text(), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("must_change_password", sa.Boolean(), server_default=sa.text("0"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp(), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"])

    # ── devices ─────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_code", sa.String(128), unique=True, nullable=False),
        sa.Column("device_name", sa.String(256), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_devices_id", "devices", ["id"])

    # ── documents ───────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        sa.Column("doc_name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("upload_time", sa.DateTime(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("download_count", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=True),
        sa.Column("calibration_due_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_documents_id", "documents", ["id"])

    # ── maintenance_plan ────────────────────────────────────────────────
    op.create_table(
        "maintenance_plan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("next_due_date", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=True),
        sa.Column("is_closed", sa.Boolean(), server_default=sa.text("0"), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("closed_by", sa.String(255), nullable=True),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp(), nullable=True),
    )
    op.create_index("ix_maintenance_plan_id", "maintenance_plan", ["id"])

    # ── maintenance_record ──────────────────────────────────────────────
    op.create_table(
        "maintenance_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("performed_by", sa.String(255), nullable=False),
        sa.Column("performed_at", sa.String(50), nullable=True),
        sa.Column("next_due_date", sa.String(50), nullable=True),
        sa.Column("parts_used", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )
    op.create_index("ix_maintenance_record_id", "maintenance_record", ["id"])

    # ── repair_record ───────────────────────────────────────────────────
    op.create_table(
        "repair_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("performed_by", sa.String(255), nullable=False),
        sa.Column("performed_at", sa.String(50), nullable=True),
        sa.Column("parts_used", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )
    op.create_index("ix_repair_record_id", "repair_record", ["id"])

    # ── approval_requests ───────────────────────────────────────────────
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("current_step", sa.Integer(), server_default=sa.text("1"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )
    op.create_index("ix_approval_requests_id", "approval_requests", ["id"])

    # ── approval_steps ──────────────────────────────────────────────────
    op.create_table(
        "approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("approval_requests.id"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("approver_role", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.String(255), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_approval_steps_id", "approval_steps", ["id"])

    # ── audit_logs ──────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user", sa.String(128), nullable=True),
        sa.Column("action", sa.String(128), nullable=True),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("before_value", sa.Text(), nullable=True),
        sa.Column("after_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("log_time", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])

    # ── system_settings ─────────────────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("setting_key", sa.String(128), unique=True, nullable=False),
        sa.Column("setting_value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(256), nullable=True),
        sa.Column("updated_by", sa.String(128), nullable=True),
    )
    op.create_index("ix_system_settings_id", "system_settings", ["id"])

    # ── borrow_records ──────────────────────────────────────────────────
    op.create_table(
        "borrow_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("borrower", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=True),
        sa.Column("borrow_date", sa.Date(), nullable=True),
        sa.Column("expected_return_date", sa.Date(), nullable=True),
        sa.Column("actual_return_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), server_default="borrowed", nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_borrow_records_id", "borrow_records", ["id"])

    # ── spare_parts ─────────────────────────────────────────────────────
    op.create_table(
        "spare_parts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(64), server_default="other", nullable=True),
        sa.Column("specification", sa.String(256), nullable=True),
        sa.Column("unit", sa.String(32), server_default=sa.text("'个'"), nullable=True),
        sa.Column("brand", sa.String(128), nullable=True),
        sa.Column("safety_stock_min", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("safety_stock_max", sa.Integer(), server_default=sa.text("9999"), nullable=True),
        sa.Column("current_stock", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("weighted_avg_price", sa.Float(), server_default=sa.text("0"), nullable=True),
        sa.Column("supplier_name", sa.String(256), nullable=True),
        sa.Column("supplier_contact", sa.String(128), nullable=True),
        sa.Column("supplier_phone", sa.String(64), nullable=True),
        sa.Column("supplier_doc_path", sa.String(512), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_spare_parts_id", "spare_parts", ["id"])

    # ── spare_part_inbounds ─────────────────────────────────────────────
    op.create_table(
        "spare_part_inbounds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("spare_part_id", sa.Integer(), sa.ForeignKey("spare_parts.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("unit_price", sa.Float(), server_default=sa.text("0"), nullable=True),
        sa.Column("batch_no", sa.String(128), nullable=True),
        sa.Column("inbound_date", sa.DateTime(), nullable=True),
        sa.Column("doc_path", sa.String(512), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_spare_part_inbounds_id", "spare_part_inbounds", ["id"])

    # ── spare_part_consumptions ─────────────────────────────────────────
    op.create_table(
        "spare_part_consumptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("spare_part_id", sa.Integer(), sa.ForeignKey("spare_parts.id"), nullable=False),
        sa.Column("maintenance_record_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("unit_price", sa.Float(), server_default=sa.text("0"), nullable=True),
        sa.Column("batch_no", sa.String(128), nullable=True),
        sa.Column("consumed_by", sa.String(128), nullable=True),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
    )
    op.create_index("ix_spare_part_consumptions_id", "spare_part_consumptions", ["id"])

    # ── spare_part_alerts ───────────────────────────────────────────────
    op.create_table(
        "spare_part_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("spare_part_id", sa.Integer(), sa.ForeignKey("spare_parts.id"), nullable=False),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("current_stock", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("threshold", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), server_default=sa.text("0"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_spare_part_alerts_id", "spare_part_alerts", ["id"])

    # ── electronic_signatures ───────────────────────────────────────────
    op.create_table(
        "electronic_signatures",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("signed_by", sa.String(128), nullable=False),
        sa.Column("signed_by_display", sa.String(128), nullable=False),
        sa.Column("sign_meaning", sa.String(32), nullable=False),
        sa.Column("sign_meaning_label", sa.String(64), nullable=False),
        sa.Column("signed_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=True),
    )
    op.create_index("ix_electronic_signatures_id", "electronic_signatures", ["id"])
    op.create_index("ix_esign_record", "electronic_signatures", ["record_type", "record_id"])

    # ── device_status_requests ──────────────────────────────────────────
    op.create_table(
        "device_status_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("current_status", sa.String(32), nullable=False),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending", nullable=True),
        sa.Column("decided_by", sa.String(128), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_device_status_requests_id", "device_status_requests", ["id"])

    # ── password_reset_requests ─────────────────────────────────────────
    op.create_table(
        "password_reset_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending", nullable=True),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("processed_by", sa.String(128), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_password_reset_requests_id", "password_reset_requests", ["id"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("password_reset_requests")
    op.drop_table("device_status_requests")
    op.drop_table("electronic_signatures")
    op.drop_table("spare_part_alerts")
    op.drop_table("spare_part_consumptions")
    op.drop_table("spare_part_inbounds")
    op.drop_table("spare_parts")
    op.drop_table("borrow_records")
    op.drop_table("system_settings")
    op.drop_table("audit_logs")
    op.drop_table("approval_steps")
    op.drop_table("approval_requests")
    op.drop_table("repair_record")
    op.drop_table("maintenance_record")
    op.drop_table("maintenance_plan")
    op.drop_table("documents")
    op.drop_table("devices")
    op.drop_table("users")
