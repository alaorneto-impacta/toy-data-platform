WITH source AS (
    SELECT
        show_id,
        type,
        TRIM(title) as title,
        director,
        country,
        -- a fonte traz "September 25, 2021"; um CAST para DATE só aceita "2021-09-25"
        DATE(DATE_PARSE(TRIM(date_added), '%M %e, %Y')) AS date_added,
        release_year,
        rating,
        duration,
        listed_in,
        "description",
        "cast"
    FROM {{ source('raw', 'netflix_titles') }}
)

SELECT * FROM source