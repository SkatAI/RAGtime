-- drop table groundtruth;

CREATE TABLE groundtruth (
    id SERIAL PRIMARY KEY,
    question TEXT,
    answer TEXT,
    source TEXT,
    answer_type TEXT,
    created_at TIMESTAMP default now(),
    modified_at TIMESTAMP default now()
);

Alter table groundtruth ADD COLUMN active BOOLEAN DEFAULT true;


CREATE TABLE live_qa (
    id SERIAL PRIMARY KEY,
    query TEXT,
    answer TEXT,
    search TEXT,
    filters TEXT,
    context TEXT,
    answer_type TEXT,
    created_at TIMESTAMP default now(),
    modified_at TIMESTAMP default now()
);
