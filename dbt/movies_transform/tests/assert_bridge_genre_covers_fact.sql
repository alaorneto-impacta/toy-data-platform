-- Cobertura da ponte de gênero: a ponte deduplica os títulos com a mesma regra do fato,
-- então todo título do fato tem ao menos um gênero e nenhum título é multiplicado além
-- dos seus gêneros. Se as duas models divergirem no grão (ex.: a ponte parar de deduplicar
-- por `show_id`), este teste retorna linhas e falha.

with base as (

    select count(*) as n from {{ ref('fct_titles') }}

),

covered as (

    select count(distinct title_key) as n from {{ ref('bridge_title_genre') }}

)

select base.n as base_count, covered.n as covered_count
from base
cross join covered
where base.n <> covered.n
