-- Canal de alta del usuario (HU-141): "web" o "android". Nullable porque los
-- usuarios ya existentes (antes de esta columna) no tienen ese dato y no hay
-- forma confiable de inferirlo retroactivamente -- se deja en blanco en vez
-- de inventar un valor.
ALTER TABLE ms_identidad.usuario
    ADD COLUMN IF NOT EXISTS canal TEXT;

ALTER TABLE ms_identidad.usuario DROP CONSTRAINT IF EXISTS ck_usuario_canal;
ALTER TABLE ms_identidad.usuario
    ADD CONSTRAINT ck_usuario_canal CHECK (canal IS NULL OR canal IN ('web', 'android'));
