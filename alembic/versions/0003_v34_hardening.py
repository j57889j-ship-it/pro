"""v34 quiz completion flag for abandoned/completed attempts"""
from alembic import op
import sqlalchemy as sa

revision = "0003_v34_hardening"
down_revision = "0002_quiz_answer_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quiz_attempts", sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_quiz_attempts_completed", "quiz_attempts", ["completed"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_completed", table_name="quiz_attempts")
    op.drop_column("quiz_attempts", "completed")
