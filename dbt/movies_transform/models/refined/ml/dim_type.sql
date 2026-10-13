-- Dimensão de tipo de título: Movie / TV Show, um por linha.

select distinct
    type as type_key
from {{ ref('netflix_titles') }}
where type is not null
