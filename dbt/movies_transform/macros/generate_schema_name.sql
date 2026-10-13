-- Usa o schema customizado declarado no dbt_project.yml como está.
--
-- O dbt, por padrão, prefixa o schema com o schema do target ("{{target.schema}}_{{custom}}"),
-- o que produziria `dev_lorransr_ml`/`prd_ml` em vez de `ml`. Este repositório declara os
-- schemas finais no projeto (`raw_movies`, `movies`, `delivery`, `ml`) — o mesmo padrão que a
-- ingestão já usa (`raw.raw_movies`) — então o schema customizado é usado verbatim.

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
