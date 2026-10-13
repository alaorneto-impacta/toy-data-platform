-- Dimensão de país: um país por linha, derivado da ponte título-país.

select distinct
    country_key
from {{ ref('bridge_title_country') }}
