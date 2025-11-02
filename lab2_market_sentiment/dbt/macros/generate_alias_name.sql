{#
  Custom naming convention: removes prefixes
  stg_reddit__posts → reddit_posts
  int_sentiment_unified → sentiment_unified
  fct_sentiment_events → sentiment_events
#}
{% macro generate_alias_name(custom_alias_name=none, node=none) %}
    {%- if custom_alias_name is none -%}
        {%- set model_name = node.name -%}
        {%- if model_name.startswith('stg_') -%}
            {{ model_name.replace('stg_', '').replace('__', '_') }}
        {%- elif model_name.startswith('int_') -%}
            {{ model_name.replace('int_', '') }}
        {%- elif model_name.startswith('fct_') -%}
            {{ model_name.replace('fct_', '') }}
        {%- elif model_name.startswith('dim_') -%}
            {{ model_name }}
        {%- elif model_name.startswith('mart_') -%}
            {{ model_name }}
        {%- else -%}
            {{ model_name }}
        {%- endif -%}
    {%- else -%}
        {{ custom_alias_name }}
    {%- endif -%}
{% endmacro %}