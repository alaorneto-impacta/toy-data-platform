-- Grão do fato: juntar as dimensões não altera a contagem de títulos.
-- Se o grão deixar de ser "um título" (ou as dimensões tiverem chave duplicada),
-- este teste retorna linhas e falha.

with base as (

    select count(*) as n from {{ ref('fct_titles') }}

),

sliced as (

    select count(*) as n
    from {{ ref('fct_titles') }} f
    inner join {{ ref('dim_year') }} y on f.year_key = y.year_key
    inner join {{ ref('dim_type') }} t on f.type_key = t.type_key

)

select base.n as base_count, sliced.n as sliced_count
from base
cross join sliced
where base.n <> sliced.n
