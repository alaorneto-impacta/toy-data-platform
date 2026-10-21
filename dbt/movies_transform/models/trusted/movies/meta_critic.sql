WITH source AS (
    SELECT
        {{normalize("title")}} as title,
        -- a fonte traz "Mar 22, 1996" e votos com separador de milhar ("1,234")
        DATE(DATE_PARSE(release_date, '%b %e, %Y')) AS release_date,
        max(description) as description,
        max(rating) as rating,
        max(CAST(REPLACE(no_of_persons_voted, ',', '') AS BIGINT)) AS no_of_persons_voted,
        max(directed_by) as directed_by,
        max(written_by) as written_by,
        max(duration) as duration,
        max(genres) as genres
    FROM {{ source('raw', 'meta_critic') }}  
    group by 1, 2
)

SELECT * FROM source