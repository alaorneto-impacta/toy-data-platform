-- Dimensão de gênero: um gênero por linha, derivado da ponte título-gênero.
--
-- Vem da ponte (e não da origem) por construção: assim toda chave da ponte existe
-- na dimensão, e não há gênero órfão.

select distinct
    genre_key
from {{ ref('bridge_title_genre') }}
