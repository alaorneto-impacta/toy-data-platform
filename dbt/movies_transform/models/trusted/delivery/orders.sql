{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='order_id'
    )
}}

select * from {{ref("orders_seed")}}

{% if is_incremental() %}

where
  updated_at > (select max(updated_at) from {{ this }})

{% endif %}