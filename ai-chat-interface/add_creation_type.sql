-- Add creation_type column to projects table
-- This distinguishes between template-based and dynamic (conversational) projects

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS creation_type VARCHAR(20) DEFAULT 'template'
CHECK (creation_type IN ('template', 'dynamic'));

-- Add comment to describe the column
COMMENT ON COLUMN projects.creation_type IS 'Project creation method: template (traditional) or dynamic (AI conversational)';

-- Update existing projects to template type
UPDATE projects
SET creation_type = 'template'
WHERE creation_type IS NULL;
