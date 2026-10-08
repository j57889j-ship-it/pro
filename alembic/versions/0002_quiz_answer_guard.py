"""prevent duplicate answers in one quiz attempt"""
from alembic import op

revision = "0002_quiz_answer_guard"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the earliest answer and remove any duplicate rows created by older builds.
    op.execute(
        """
        DELETE FROM quiz_answers a
        USING quiz_answers b
        WHERE a.id > b.id
          AND a.attempt_id = b.attempt_id
          AND a.question_id = b.question_id
        """
    )
    op.create_unique_constraint(
        "uq_quiz_answer_attempt_question",
        "quiz_answers",
        ["attempt_id", "question_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_quiz_answer_attempt_question", "quiz_answers", type_="unique")
