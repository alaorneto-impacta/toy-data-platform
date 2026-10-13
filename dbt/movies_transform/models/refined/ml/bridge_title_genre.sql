-- Ponte título ↔ gênero: uma linha por par (título, gênero).
--
-- `listed_in` é multi-valor ("Dramas, Comedies, ..."): o `unnest` transforma a lista
-- em linhas. Um título com N gêneros aparece exatamente N vezes — então uma métrica
-- fatiada por gênero conta cada título uma vez por gênero que ele tem, e nunca duas
-- vezes pelo mesmo gênero.
--
-- A ponte parte do fato (`fct_titles`): um gênero só interessa se o título está no fato,
-- senão a ponte teria títulos que nenhuma medida alcança.

select
    f.title_key,
    trim(g.genre) as genre_key,
    f.title_key || '|' || trim(g.genre) as title_genre_key
from {{ ref('fct_titles') }} f
inner join {{ ref('int_titles_attributes') }} t on t.title_key = f.title_key
cross join unnest(split(t.listed_in, ',')) as g (genre)
where trim(g.genre) <> ''
