INSERT INTO core.workspaces(workspace_id, name)
VALUES
('11111111-1111-4111-8111-111111111111', 'Fixture MVP demo workspace')
ON CONFLICT (workspace_id) DO UPDATE SET
    name = EXCLUDED.name;

INSERT INTO core.users(user_id, workspace_id, email)
VALUES
(
    '22222222-2222-4222-8222-222222222222',
    '11111111-1111-4111-8111-111111111111',
    'fixture-mvp-demo@example.test'
)
ON CONFLICT (user_id) DO UPDATE SET
    workspace_id = EXCLUDED.workspace_id,
    email = EXCLUDED.email;
