-- Ponte título ↔ país: uma linha por par (título, país).
--
-- `country` também é multi-valor ("United States, India"). A ponte parte do fato
-- (`fct_titles`), então só cobre títulos que alguma medida alcança; títulos sem país na
-- origem não entram (por isso a ponte não cobre necessariamente todo o fato — os
-- `relationships` garantem que toda linha da ponte aponta para um título existente).

select
    f.title_key,
    trim(c.country) as country_key,
    f.title_key || '|' || trim(c.country) as title_country_key
from {{ ref('fct_titles') }} f
inner join {{ ref('int_titles_attributes') }} t on t.title_key = f.title_key
cross join unnest(split(t.country, ',')) as c (country)
where trim(c.country) <> ''
