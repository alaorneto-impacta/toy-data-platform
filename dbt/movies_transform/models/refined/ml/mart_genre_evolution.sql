
-- Evolução de títulos por gênero e ano de lançamento.
-- Grão: um registro por gênero e ano.
-- A ponte permite que um título pertença a vários gêneros.

with titles_by_genre as (

    select
        b.genre_key,
        f.year_key,
        f.title_key,
        f.rating,
        f.votes
    from {{ ref('fct_titles') }} f
    inner join {{ ref('bridge_title_genre') }} b
        on f.title_key = b.title_key

),

genre_year as (

    select
        genre_key,
        year_key,
        count(distinct title_key) as total_titles,
        avg(rating) as avg_rating,
        sum(votes) as total_votes
    from titles_by_genre
    group by genre_key, year_key

)

select
    genre_key,
    year_key,
    total_titles,
    avg_rating,
    total_votes
from genre_year
