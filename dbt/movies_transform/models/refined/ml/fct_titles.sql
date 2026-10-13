-- Fato de títulos: grão de exatamente um título (title_key).
--
-- Medidas: nota da crítica (`rating`), total de votos (`votes`) e duração em
-- minutos para filmes (`duration_minutes`; TV Show não tem duração, tem temporadas).
--
-- Regra de deduplicação: quando o mesmo título normalizado aparece em mais de um
-- registro na origem, mantém-se um único registro representativo — o de menor
-- `show_id` no Netflix e o de menor `release_date` na crítica — para que o grão
-- seja "um título" e a contagem não infle ao fatiar por dimensões.

with netflix as (

    select
        lower(trim(title)) as title_key,
        title,
        type,
        release_year,
        duration,
        row_number() over (
            partition by lower(trim(title)) order by show_id
        ) as rn
    from {{ ref('netflix_titles') }}

),

critic as (

    select
        lower(trim(title)) as title_key,
        rating,
        no_of_persons_voted,
        row_number() over (
            partition by lower(trim(title)) order by release_date
        ) as rn
    from {{ ref('meta_critic') }}

)

select
    n.title_key,
    n.title,
    n.release_year as year_key,
    n.type as type_key,
    c.rating,
    c.no_of_persons_voted as votes,
    try_cast(
        nullif(regexp_extract(n.duration, '(\d+)\s*min', 1), '') as integer
    ) as duration_minutes
from netflix n
inner join critic c on n.title_key = c.title_key
where n.rn = 1 and c.rn = 1
