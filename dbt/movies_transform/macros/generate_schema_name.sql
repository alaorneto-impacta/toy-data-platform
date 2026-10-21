-- Em prod, usa o schema customizado do dbt_project.yml como está (`movies`, `ml`), o mesmo
-- padrão da ingestão (`raw.raw_movies`). Fora de prod, prefixa com o schema do target
-- (`dev_lorransr_ml`), para que cada pessoa construa sem sobrescrever produção.

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
