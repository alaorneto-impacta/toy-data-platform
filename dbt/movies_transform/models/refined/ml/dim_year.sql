-- Dimensão de tempo: um ano de lançamento por linha.

select distinct
    release_year as year_key
from {{ ref('netflix_titles') }}
where release_year is not null
