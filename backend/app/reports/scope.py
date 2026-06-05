from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def validate_scope_refs(
    session: Session,
    *,
    workspace_id: UUID | None,
    requested_by: UUID | None,
) -> None:
    if workspace_id is not None and not _workspace_exists(session, workspace_id):
        raise ValueError(f"Workspace '{workspace_id}' was not found")
    if requested_by is None:
        return
    row = session.execute(
        text(
            """
            SELECT workspace_id
            FROM core.users
            WHERE user_id = :requested_by
            LIMIT 1
            """
        ),
        {"requested_by": requested_by},
    ).one_or_none()
    if row is None:
        raise ValueError(f"User '{requested_by}' was not found")
    user_workspace_id = UUID(str(row[0]))
    if workspace_id is not None and user_workspace_id != workspace_id:
        raise ValueError(
            f"User '{requested_by}' does not belong to workspace '{workspace_id}'"
        )


def _workspace_exists(session: Session, workspace_id: UUID) -> bool:
    return (
        session.execute(
            text(
                """
                SELECT 1
                FROM core.workspaces
                WHERE workspace_id = :workspace_id
                LIMIT 1
                """
            ),
            {"workspace_id": workspace_id},
        ).one_or_none()
        is not None
    )


__all__ = ["validate_scope_refs"]
