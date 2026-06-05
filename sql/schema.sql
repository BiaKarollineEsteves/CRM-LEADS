-- CRM GRUPO LLE — Schema Neon
-- Execute no SQL Editor do Neon

CREATE TABLE IF NOT EXISTS empresas (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);
INSERT INTO empresas (nome) VALUES ('King'),('Pisa'),('Trio') ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS regioes (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil     TEXT NOT NULL DEFAULT 'vendedor' CHECK (perfil IN ('gestor','vendedor','admin')),
    empresa_id INTEGER REFERENCES empresas(id),
    status     TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','aprovado','inativo')),
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);

-- Migração: permite perfil admin (execute se tabela já existia)
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_perfil_check;
ALTER TABLE usuarios ADD CONSTRAINT usuarios_perfil_check
    CHECK (perfil IN ('gestor','vendedor','admin'));

CREATE TABLE IF NOT EXISTS status_leads (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE,
    cor   TEXT NOT NULL DEFAULT '#6B7280',
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN DEFAULT TRUE
);
INSERT INTO status_leads (nome, cor, ordem) VALUES
    ('Sem contato',         '#6B7280', 0),
    ('Tentativa de contato','#F59E0B', 1),
    ('Contato realizado',   '#3B82F6', 2),
    ('Cadastrado',          '#10B981', 3)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS leads (
    id            SERIAL PRIMARY KEY,
    cnpj          TEXT,
    razao_social  TEXT NOT NULL,
    ramo          TEXT,
    endereco      TEXT,
    cidade        TEXT,
    estado        TEXT,
    telefone      TEXT,
    email         TEXT,
    empresa_id    INTEGER REFERENCES empresas(id),
    regiao_id     INTEGER REFERENCES regioes(id),
    vendedor_id   UUID REFERENCES usuarios(id),
    status_id     INTEGER REFERENCES status_leads(id),
    criado_em     TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Status padrão nos leads sem status
UPDATE leads SET status_id = (SELECT id FROM status_leads WHERE nome='Sem contato')
WHERE status_id IS NULL;

CREATE TABLE IF NOT EXISTS historico_status (
    id         SERIAL PRIMARY KEY,
    lead_id    INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    status_id  INTEGER NOT NULL REFERENCES status_leads(id),
    usuario_id UUID REFERENCES usuarios(id),
    anotacao   TEXT,
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comentarios (
    id         SERIAL PRIMARY KEY,
    lead_id    INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id),
    texto      TEXT NOT NULL,
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);

-- CONTATOS EXTRAS (telefones adicionais por lead)
CREATE TABLE IF NOT EXISTS contatos_extras (
    id         SERIAL PRIMARY KEY,
    lead_id    INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    telefone   TEXT NOT NULL,
    observacao TEXT,
    adicionado_por UUID REFERENCES usuarios(id),
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);

-- NOTIFICAÇÕES (novo número adicionado → avisa o vendedor)
CREATE TABLE IF NOT EXISTS notificacoes (
    id         SERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    lead_id    INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    mensagem   TEXT NOT NULL,
    lida       BOOLEAN DEFAULT FALSE,
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);
